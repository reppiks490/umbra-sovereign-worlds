"""Counterbalanced paired research design and authenticated, seed-level analysis.

Legacy v67 receipts remain readable; no result authorizes model routing.
"""
import math
WINDOW_SECONDS=4*60*60
MAX_PAIRS=4096

def plan(epoch_seconds):
    if type(epoch_seconds) is not int or epoch_seconds<0:
        raise ValueError('invalid experiment clock')
    seed=epoch_seconds//WINDOW_SECONDS
    return {'seed':seed,'family':seed%4,
            'first':'compact' if (seed//4)%2==0 else 'explicit'}

def _sign_p(wins,losses):
    n=wins+losses
    if not n:return 1.0
    return min(1.0,2*sum(math.comb(n,k) for k in range(min(wins,losses)+1))/(1<<n))

def audit(records,key):
    # Import lazily: the paired runner itself uses plan().
    import evolution_research_protocol_v67 as protocol
    if not isinstance(records,list) or len(records)>MAX_PAIRS:
        raise ValueError('bounded receipt list required')
    seen=set(); wins=losses=ties=explicit_only=compact_only=both=neither=failed=0
    families={str(i):{'attempts':0,'completed':0,'compact_first':0,'explicit_first':0} for i in range(4)}
    for r in records:
        if protocol.verify(r,key) is not True:
            raise ValueError('unverified receipt')
        seed=r['seed']
        if seed in seen:raise ValueError('duplicate experiment seed')
        seen.add(seed);f=families[str(seed%4)];f['attempts']+=1
        if r['status']!='completed':
            failed+=1;continue
        f['completed']+=1;f[r['results'][0]['protocol']+'_first']+=1
        indexed={v['protocol']:{x['n']:x['joint_correct'] for x in v['rows']} for v in r['results']}
        delta=0
        for n,c in indexed['compact'].items():
            e=indexed['explicit'][n];delta+=int(e)-int(c)
            if e and c:both+=1
            elif e:explicit_only+=1
            elif c:compact_only+=1
            else:neither+=1
        wins+=int(delta>0);losses+=int(delta<0);ties+=int(delta==0)
    return {'schema':'myriad.paired_audit.v71','attempted_pairs':len(records),
            'completed_pairs':len(records)-failed,'failed_pairs':failed,
            'seed_wins':wins,'seed_losses':losses,'seed_ties':ties,
            'explicit_only_cases':explicit_only,'compact_only_cases':compact_only,
            'both_correct_cases':both,'neither_correct_cases':neither,
            'family_coverage':families,'two_sided_sign_p':_sign_p(wins,losses),
            'inference_limitation':'Descriptive seed-level sign test; independence and representativeness unproven.',
            'routing_authorized':False,'production_authority':False}
