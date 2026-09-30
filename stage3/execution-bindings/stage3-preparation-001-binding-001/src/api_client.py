"""One-shot Responses transport and immutable receipts. No API-running CLI.

Live dispatch requires a separate host execution-context record and an
input-bound record for the exact bytes. Neither is supplied by this binding.
No automatic retry, model fallback, SDK retry or counting API is used.
"""
from dataclasses import dataclass
from decimal import Decimal
import http.client
import os
from pathlib import Path
import ssl
from contracts import decode, digest, encode, now

class DispatchBlocked(RuntimeError):
    pass

@dataclass(frozen=True)
class Reply:
    status: int
    request_id: str | None
    raw: bytes

class LiveHTTPTransport:
    mode = 'live_http'

    def __init__(self, execution_context):
        self.execution_context = execution_context

    def preflight(self, contracts, body, bound_record):
        ctx = self.execution_context
        if not ctx or not ctx.get('execution_ready'):
            raise DispatchBlocked('execution_context_not_ready')
        if contracts.offline_structural:
            raise DispatchBlocked('external_schema_required')
        from contracts import FORM_SHA256
        if (ctx.get('conditions_sha256') != FORM_SHA256 or ctx.get('pricing_checked') is not True
            or ctx.get('runtime_manifest_sha256') != contracts.runtime_manifest_sha256):
            raise DispatchBlocked('execution_context_not_bound')
        if not bound_record or bound_record.get('origin') != 'verified_host_token_bound':
            raise DispatchBlocked('input_token_bound_not_verified')
        if (bound_record.get('api_input_sha256') != digest(body)
            or bound_record.get('model') != contracts.form['model']['model_identifier']
            or type(bound_record.get('upper_bound')) is not int
            or not 0 <= bound_record['upper_bound'] <= contracts.form['model']['maximum_input_tokens']
            or not bound_record.get('method_record_sha256')):
            raise DispatchBlocked('input_token_bound_mismatch')
        if not os.environ.get('OPENAI_API_KEY'):
            raise DispatchBlocked('api_key_not_present')

    def send_once(self, body, timeout):
        # Called only by OneShotClient after preflight. No retries or redirects.
        con = http.client.HTTPSConnection('api.openai.com', timeout=timeout, context=ssl.create_default_context())
        try:
            con.request('POST','/v1/responses',body=body,
                        headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ['OPENAI_API_KEY']})
            response = con.getresponse()
            return Reply(response.status,response.getheader('x-request-id'),response.read())
        finally:
            con.close()

class OfflineTransport:
    mode = 'offline_fixture'

    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.calls = reply, error, 0

    def preflight(self, contracts, body, bound_record):
        # No bound certificate is claimed: no HTTP or paid inference occurs.
        return

    def send_once(self, body, timeout):
        self.calls += 1
        if self.error:
            raise self.error
        if self.reply is None:
            raise ValueError('offline_reply_missing')
        return self.reply

class Journal:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True,exist_ok=True)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True,exist_ok=True)
        data = content if isinstance(content,bytes) else encode(content) + b'\n'
        with path.open('xb') as f:
            f.write(data)
        return {'path':str(path),'sha256':digest(data)}

    def stopped(self):
        return (self.root/'STOP.json').exists()

    def stop(self, reason, trial_id):
        if not self.stopped():
            self.write('STOP.json',{'reason':reason,'trial_id':trial_id,'at':now()})

    def reserve(self, trial_id, form, transport_mode):
        if self.stopped():
            raise DispatchBlocked('run_stopped')
        planned = ['P001','P002','P003','A001','A002','A003','A004']
        reserves = sorted((self.root/'budget').glob('*.reserve.json')) if (self.root/'budget').exists() else []
        if trial_id not in planned or len(reserves)>=7 or any(decode(p.read_bytes())['trial_id']==trial_id for p in reserves):
            raise DispatchBlocked('unplanned_duplicate_or_excess_call')
        if trial_id != planned[len(reserves)]:
            raise DispatchBlocked('call_order_mismatch')
        total = Decimal('0')
        for path in reserves:
            record = decode(path.read_bytes())
            settled = path.with_name(path.name.replace('.reserve.json','.settled.json'))
            total += Decimal(decode(settled.read_bytes())['charge_usd']) if settled.exists() else Decimal(record['reservation_usd'])
            if record['transport_mode'] != transport_mode:
                raise DispatchBlocked('mixed_live_and_offline_journal')
        amount = Decimal(form['budget']['reservation_usd_per_call'])
        if total + amount > Decimal(form['budget']['limit']):
            raise DispatchBlocked('budget_limit')
        self.write(f'budget/{trial_id}.reserve.json',{'trial_id':trial_id,'reservation_usd':str(amount),
                   'transport_mode':transport_mode,'at':now()})

    def settle(self, trial_id, usage, form):
        if not isinstance(usage,dict) or any(type(usage.get(k)) is not int or usage[k]<0 for k in ['input_tokens','output_tokens']):
            self.stop('usage_unresolved_reservation_retained',trial_id)
            return None
        rates = form['budget']['rate_basis']
        charge = (Decimal(usage['input_tokens'])*Decimal(rates['uncached_input_usd_per_million'])
                  +Decimal(usage['output_tokens'])*Decimal(rates['output_usd_per_million']))/Decimal(1000000)
        self.write(f'budget/{trial_id}.settled.json',{'trial_id':trial_id,'usage':usage,'charge_usd':str(charge),
                   'cost_basis':'frozen_rates_no_cache_discount',
                   'simulated_charge':decode((self.root/f'budget/{trial_id}.reserve.json').read_bytes())['transport_mode']=='offline_fixture','at':now()})
        if usage['input_tokens']>form['model']['maximum_input_tokens'] or usage['output_tokens']>form['model']['settings']['max_output_tokens']:
            self.stop('observed_token_cap_deviation',trial_id)
        return charge

def extract_output(response):
    if response.get('status') != 'completed':
        raise ValueError('response_not_completed:' + str(response.get('status')))
    messages = [x for x in response.get('output',[]) if x.get('type')=='message' and x.get('role')=='assistant']
    if len(messages) != 1:
        raise ValueError('expected_one_assistant_message')
    content = messages[0].get('content',[])
    if any(x.get('type')=='refusal' for x in content):
        raise ValueError('model_refusal')
    if not content or any(x.get('type')!='output_text' or not isinstance(x.get('text'),str) for x in content):
        raise ValueError('unexpected_output_content')
    return ''.join(x['text'] for x in content).encode('utf-8')

class OneShotClient:
    def __init__(self, contracts, journal, transport):
        self.contracts, self.journal, self.transport = contracts,journal,transport

    def call(self, body, read_trace, *, bound_record=None):
        trial_id = read_trace['trial_id']
        if digest(body) != read_trace['api_input_sha256']:
            raise ValueError('request_bytes_changed_after_read')
        form = self.contracts.form
        request = decode(body)
        if request.get('model')!=form['model']['model_identifier'] or any(request.get(k)!=v for k,v in form['model']['settings'].items()):
            raise ValueError('request_settings_changed')
        allowed = {'model','instructions','input'} | set(form['model']['settings'])
        if set(request)!=allowed:
            raise ValueError('unexpected_request_fields')
        payload = decode(request['input'])
        if digest(payload['read_only_view']) != read_trace['read_input_sha256']:
            raise ValueError('request_view_changed_after_read')
        self.journal.write(f'calls/{trial_id}/request.json',body)
        request_record = self.journal.write(f'calls/{trial_id}/request-record.json',{'read_trace':read_trace,'transport_mode':self.transport.mode,
                         'request_sha256':digest(body),'dispatch_pid':os.getpid(),'bound_record':bound_record,'at':now()})
        try:
            self.transport.preflight(self.contracts,body,bound_record)
            self.journal.reserve(trial_id,form,self.transport.mode)
        except DispatchBlocked as error:
            self.journal.write(f'calls/{trial_id}/preflight-blocked.json',{'reason':str(error),'dispatched':False,'at':now()})
            raise
        record = {'trial_id':trial_id,'transport_mode':self.transport.mode,'started_at':now(),
                  'dispatch_pid':os.getpid(),'api_input_sha256':digest(body),'request_record_sha256':request_record['sha256'],
                  'model_api_calls':1 if self.transport.mode=='live_http' else 0,'offline_fixture_calls':1 if self.transport.mode=='offline_fixture' else 0}
        try:
            reply = self.transport.send_once(body,form['model']['request_timeout_seconds'])
        except Exception as error:
            # No exception message or request headers: credentials never enter logs.
            record.update(status='transport_failure',error_type=type(error).__name__,ended_at=now(),usage=None)
            self.journal.write(f'calls/{trial_id}/result.json',record)
            self.journal.stop('usage_unresolved_reservation_retained',trial_id)
            return record, None
        raw_record = self.journal.write(f'calls/{trial_id}/response.raw',reply.raw)
        record.update(http_status=reply.status,api_request_id=reply.request_id,raw_response_sha256=raw_record['sha256'],ended_at=now())
        try:
            response = decode(reply.raw)
            if not isinstance(response,dict):
                raise ValueError('non_object_response')
        except (ValueError,UnicodeDecodeError) as error:
            self.journal.settle(trial_id,None,form)
            record.update(status='malformed_api_envelope',error_type=type(error).__name__)
            self.journal.write(f'calls/{trial_id}/result.json',record)
            return record,None
        charge = self.journal.settle(trial_id,response.get('usage'),form)
        record.update(usage=response.get('usage'),estimated_charge_usd=None if charge is None else str(charge),
                      returned_model=response.get('model'),returned_service_tier=response.get('service_tier'))
        output = None
        try:
            if self.journal.stopped():
                raise ValueError('run_stopped_after_response')
            if response.get('model')!=form['model']['model_identifier'] or response.get('service_tier')!='default':
                self.journal.stop('model_or_service_tier_deviation',trial_id)
                raise ValueError('configuration_deviation')
            if not reply.request_id:
                self.journal.stop('missing_request_id',trial_id)
                raise ValueError('missing_request_id')
            if reply.status!=200:
                raise ValueError('http_status:' + str(reply.status))
            output = extract_output(response)
            output_record = self.journal.write(f'calls/{trial_id}/output.raw',output)
            record.update(status='output_recorded',output_sha256=output_record['sha256'])
        except ValueError as error:
            record.update(status='no_usable_output',reason=str(error))
        self.journal.write(f'calls/{trial_id}/result.json',record)
        binding = None
        if output is not None:
            binding = {**read_trace,**record,'output_sha256':digest(output),
                       'origin':'model_output' if self.transport.mode=='live_http' else 'offline_transport_fixture'}
        return record, None if output is None else (output,binding)
