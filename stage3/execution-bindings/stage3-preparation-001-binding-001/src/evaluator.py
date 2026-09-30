"""Host-only evaluation. Never import this module into request construction."""
from contracts import decode, digest

def expected_decision(view):
    state = view['state']
    cause = 'unresolved' if len(state['K']) > 1 else 'single_candidate_under_interpretation' if state['K'] else 'candidate_exhaustion'
    return {'schema_version':'stage3-decision/v0.1','case_id':state['case_id'],
            'state_version_read':state['version'],'state_sha256_read':digest(state),
            'selected_action':view['action']['selected_action'],'retained_candidates':state['K'],'cause_status':cause}

def score_decision(view, raw, contracts):
    expected = expected_decision(view)
    try:
        decision = decode(raw)
        contracts.validate('decision',decision)
    except (ValueError,UnicodeDecodeError) as error:
        return {'status':'invalid_decision','reason':str(error),'expected':expected,'matches':False}
    fields = {key:(set(value)==set(expected[key]) if key=='retained_candidates' else value==expected[key]) for key,value in decision.items()}
    return {'status':'scored','matches':all(fields.values()),'fields':fields,'expected':expected,'observed':decision,
            'host_read_linkage_still_required':True}

def score_transition(audit, contracts, *, full_incorporation=False):
    p = audit.get('proposal')
    if not isinstance(p,dict):
        return {'interpretable':False,'preservation_legal':None,'task_met':False}
    try:
        contracts.validate('proposal',p)
    except ValueError:
        return {'interpretable':False,'preservation_legal':None,'task_met':False}
    row = contracts.case_row(audit['case_id'])
    basis = set(p['evidence_ids'])
    admitted = set(row['admitted_valid_ids'])
    compatible = {'h_A','h_B'}
    admissible = basis <= admitted and basis <= contracts.registry['registry'].keys()
    if admissible:
        for e in basis:
            compatible &= set(contracts.registry['registry'][e]['permitted_candidates'])
    before, proposed = set(audit['state_before']['K']),set(p['proposed_K'])
    legal = admissible and before & compatible <= proposed <= before
    metadata_match = (p['case_id']==audit['case_id'] and type(p['expected_version']) is int
                      and p['expected_version']==audit['state_before']['version']
                      and p['expected_state_sha256']==digest(audit['state_before']))
    required = before.copy()
    for e in admitted:
        required &= set(contracts.registry['registry'][e]['permitted_candidates'])
    task_met = audit['status']=='accepted' and (not full_incorporation or (admitted <= basis and proposed==required))
    return {'interpretable':True,'evidence_admissible':admissible,'preservation_legal':legal,
            'case_version_hash_match':metadata_match,
            'task_met':task_met,'full_incorporation_requested':full_incorporation,
            'valid_partial_incorporation':bool(legal and full_incorporation and proposed!=required),
            'model_improvement_inferred_from_commit':False}

def compare_decisions(reference, changed, kind):
    a,b = reference['observed'],changed['observed']
    if not reference['matches'] or not changed['matches']:
        return {'kind':kind,'passed':False,'reason':'decision_does_not_match_authoritative_read'}
    if kind == 'changed_K':
        contrast = set(a['retained_candidates']) != set(b['retained_candidates'])
        passed = contrast and a['cause_status'] != b['cause_status']
    elif kind == 'response_only':
        contrast = a['selected_action'] != b['selected_action']
        passed = contrast and set(a['retained_candidates'])==set(b['retained_candidates']) and a['cause_status']==b['cause_status']
    elif kind == 'summary_only':
        contrast = True
        passed = a==b
    else:
        raise ValueError('unknown_comparison')
    return {'kind':kind,'passed':passed,'contrast_available':contrast,'inference':'observable_correspondence_only'}
