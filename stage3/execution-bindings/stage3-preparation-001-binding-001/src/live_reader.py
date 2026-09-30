"""Future live R5 entry. Not executed by the binding checks.

Only case ID and store path are handed to this process. Host-owned store
metadata must point to separately fixed execution context, journal and exact
input-bound records. None is installed by this binding; absent records stop
before credential access or network dispatch. No prior conversation is used.
"""
import argparse
from contextlib import closing
from pathlib import Path
from contracts import Contracts, decode, encode
from gate import connect, meta
from api_client import Journal, LiveHTTPTransport, OneShotClient
from pipeline import decision_call

def main():
    p=argparse.ArgumentParser()
    p.add_argument('store');p.add_argument('case_id');a=p.parse_args()
    contracts=Contracts()
    with closing(connect(a.store,readonly=True)) as con:
        context_file=meta(con,'execution_context_file')
        bound_file=meta(con,'input_bound_file')
        journal_directory=meta(con,'journal_directory')
    context=decode(Path(context_file).read_bytes())
    bound=decode(Path(bound_file).read_bytes())
    client=OneShotClient(contracts,Journal(journal_directory),LiveHTTPTransport(context))
    result=decision_call(a.store,a.case_id,contracts,client,bound_record=bound)
    print(encode(result).decode('utf-8'))

if __name__=='__main__':
    main()
