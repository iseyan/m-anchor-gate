"""Fresh-process read/request export. Only store path and case ID are handed in.

This command has no HTTP transport and makes no model call. The exported exact
bytes are a dispatch candidate; a future live receipt must link them to the API.
"""
import argparse
import base64
from contextlib import closing
import sys
from contracts import Contracts, encode
from gate import connect, meta, read_view
from request_builder import build_request

def no_network(event, args):
    if event in {'socket.connect','socket.getaddrinfo'}:
        raise RuntimeError('reader_command_network_disabled')

def main():
    sys.addaudithook(no_network)
    p = argparse.ArgumentParser()
    p.add_argument('store')
    p.add_argument('case_id')
    a = p.parse_args()
    with closing(connect(a.store,readonly=True)) as con:
        mode = meta(con,'validation_mode')
        row = con.execute("SELECT value FROM metadata WHERE key='offline_reply_fixture'").fetchone()
        fixture = None if row is None else __import__('contracts').decode(row[0])
    contracts = Contracts(offline_structural=mode=='external_schema_not_performed_offline_structural_only')
    view, trace = read_view(a.store,a.case_id,contracts)
    request, trace = build_request(view,trace,contracts)
    result = {'view':view,'trace':trace,'api_request_base64':base64.b64encode(request).decode(),
              'http_dispatched':False,'model_api_calls':0}
    if fixture is not None:
        from api_client import Journal, OfflineTransport, OneShotClient, Reply
        from pipeline import decision_call
        client = OneShotClient(contracts,Journal(fixture['journal']),OfflineTransport(Reply(200,'offline-'+trace['trial_id'],encode(fixture['response']))))
        observation = decision_call(a.store,a.case_id,contracts,client)
        result.update(view=observation['view'],trace=observation['trace'],api_request_base64=observation['api_request_base64'],
                      offline_call_record=observation['call_record'],offline_output=observation['output'],
                      offline_assessment=observation['assessment'],store_unchanged=observation['store_unchanged'])
    print(encode(result).decode('utf-8'))

if __name__=='__main__':
    main()
