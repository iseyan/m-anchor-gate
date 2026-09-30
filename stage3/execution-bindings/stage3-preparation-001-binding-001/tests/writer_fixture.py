"""Finite offline writer, exits before reader processes begin."""
import argparse
from contextlib import closing
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from contracts import Contracts, decode, digest, encode, now
from gate import init_store, make_proposal, read_state, read_view, state_signature, connect, set_meta, submit_raw
from api_client import Journal, OfflineTransport, OneShotClient, Reply
from pipeline import proposal_call, fixed_replays, restart_controls

def no_network(event,args):
    if event in {'socket.connect','socket.getaddrinfo'}:
        raise RuntimeError('offline_writer_network_disabled')

def response(text,form):
    return {'id':'offline-response','object':'response','status':'completed','model':form['model']['model_identifier'],
            'service_tier':'default','usage':{'input_tokens':900,'output_tokens':160},
            'output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':text}]}]}

def main():
    sys.addaudithook(no_network)
    p=argparse.ArgumentParser()
    p.add_argument('output');p.add_argument('--structural-only',action='store_true');a=p.parse_args()
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    contracts=Contracts(offline_structural=a.structural_only)
    journal=Journal(out/'journal')
    records=[]
    paths={}
    for number,trial_id in [(1,'P001'),(2,'P002'),(3,'P003')]:
        case=f'stage3-preparation-001-r{number}'
        checked,unchecked=out/f'checked/r{number}.sqlite',out/f'unchecked/r{number}.sqlite'
        read_trial={1:'A001',2:'A002',3:None}[number]
        state=init_store(checked,case,contracts,read_trial_id=read_trial)
        init_store(unchecked,case,contracts,comparison=True,read_trial_id=read_trial)
        proposal=make_proposal(state,trial_id,K=['h_B'] if number!=3 else ['h_A','h_B'],
                               evidence=[] if number==1 else ['e_B'],reason='Explicit offline fixture; not a model response.')
        transport=OfflineTransport(Reply(200,'offline-'+trial_id,encode(response(encode(proposal).decode(),contracts.form))))
        record=proposal_call(checked,unchecked,case,trial_id,contracts,OneShotClient(contracts,journal,transport))
        record['fixture_dispatches']=transport.calls
        records.append(record)
        paths[case]=str(checked)
    r4case='stage3-preparation-001-r4'
    r4a,r4b=out/'checked/r4.sqlite',out/'unchecked/r4.sqlite'
    init_store(r4a,r4case,contracts);init_store(r4b,r4case,contracts,comparison=True)
    before=[state_signature(p,r4case) for p in [r4a,r4b]]
    replays=fixed_replays(r4a,r4b,r4case,contracts)
    after=[state_signature(p,r4case) for p in [r4a,r4b]]
    ref=Path(paths['stage3-preparation-001-r1'])
    action,summary,action_audit=restart_controls(ref,out/'restart','stage3-preparation-001-r1',contracts)
    restart_paths=[('A001',ref,'stage3-preparation-001-r1'),('A002',Path(paths['stage3-preparation-001-r2']),'stage3-preparation-001-r2'),
                   ('A003',action,'stage3-preparation-001-r1'),('A004',summary,'stage3-preparation-001-r1')]
    for trial,path,case in restart_paths:
        state=read_state(path,case)
        # Independently declared mock decisions for these known fixtures.
        decision={'schema_version':'stage3-decision/v0.1','case_id':case,'state_version_read':state['version'],
                  'state_sha256_read':digest(state),'selected_action':'a_A' if trial=='A003' else 'a_B',
                  'retained_candidates':['h_B'] if trial=='A002' else ['h_A','h_B'],
                  'cause_status':'single_candidate_under_interpretation' if trial=='A002' else 'unresolved'}
        with closing(connect(path)) as con,con:
            set_meta(con,'offline_reply_fixture',{'journal':str(journal.root),'response':response(encode(decision).decode(),contracts.form)})
    report={'kind':'offline_writer_fixtures','writer_pid':os.getpid(),'ended_at':now(),'model_api_calls':0,'network_disabled':True,
            'validation':contracts.validation_status,'proposal_records':records,'r4_replays':replays,
            'r4_before':before,'r4_after':after,'action_control_audit':action_audit,
            'restart_paths':[{'trial_id':t,'store':str(p),'case_id':c} for t,p,c in restart_paths]}
    (out/'writer-record.json').write_bytes(encode(report)+b'\n')
    print(encode({'writer_pid':os.getpid(),'record':str(out/'writer-record.json')}).decode())

if __name__=='__main__':
    main()
