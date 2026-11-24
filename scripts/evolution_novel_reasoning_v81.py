"""Procedurally generated exact-answer and witness benchmark, research-only."""
import itertools,json,random,math
from fractions import Fraction
import evolution_research_v37 as research
FAMILIES=('knapsack_mask','bayes_fraction','parity_system','robust_choice','critical_path','nonoverlap_mask','shortest_avoiding','bounded_inventory')
QUESTIONS=(
 'Maximize item value under capacity. Answer total value; witness smallest optimal bitmask (bit i selects item i).',
 'Compute posterior probability of truth after a positive test. Answer reduced numerator; witness reduced denominator.',
 'Count binary assignments satisfying every XOR equation [bitmask,rhs]. Answer count; witness smallest satisfying bitmask, or -1 if none.',
 'Choose the row maximizing its worst payoff. Answer that minimum payoff; witness smallest maximizing row index.',
 'Find the longest weighted directed path in the DAG. Vertex durations contribute to path length. Answer length; witness smallest vertex bitmask among maximizing paths.',
 'Select compatible intervals [start,end,value]; touching endpoints permitted. Answer max total value; witness smallest optimal bitmask.',
 'Find shortest directed path from vertex 0 to nodes-1, avoiding forbidden vertex. Answer cost; witness smallest optimal path vertex bitmask. If unreachable return -1,-1.',
 'Allocate integer stock among three products up to their demand, maximizing total value. Answer value; witness decimal encoding 100*q0+10*q1+q2, smallest among optimal allocations.'
)
def cases(seed):
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('invalid seed')
    r=random.Random(seed^810039);out=[]
    for i in range((seed%2)*4,(seed%2)*4+4):
        if i==0:x={'weights':[r.randint(1,6) for _ in range(5)],'values':[r.randint(1,12) for _ in range(5)],'capacity':r.randint(5,12)}
        elif i==1:x={'prior_num':r.randint(1,7),'prior_den':8,'positive_if_true':r.randint(4,8),'positive_if_false':r.randint(1,4),'rate_den':8}
        elif i==2:x={'variables':4,'equations':[[r.randint(1,15),r.randrange(2)] for _ in range(3)]}
        elif i==3:x={'payoffs':[[r.randint(-5,15) for _ in range(3)] for _ in range(4)]}
        elif i==4:x={'durations':[r.randint(1,9) for _ in range(5)],'edges':[[u,v] for u in range(5) for v in range(u+1,5) if r.random()<.45]}
        elif i==5:
            intervals=[]
            for _ in range(5):
                a=r.randint(0,9);intervals.append([a,a+r.randint(1,4),r.randint(1,12)])
            x={'intervals':intervals}
        elif i==6:x={'nodes':5,'edges':[[u,v,r.randint(1,9)] for u in range(5) for v in range(u+1,5) if r.random()<.65 or (u,v)==(0,4)],'forbidden':r.randint(1,3)}
        else:x={'demand':[r.randint(1,5) for _ in range(3)],'stock':r.randint(3,9),'value':[r.randint(1,7) for _ in range(3)]}
        out.append({'id':i,'family':FAMILIES[i],'question':QUESTIONS[i],'input':x})
    r.shuffle(out);return out
def choose(rows,minimum=False):
    if not rows:return {'answer':-1,'witness':-1}
    a,w=min(rows,key=lambda v:(v[0] if minimum else -v[0],v[1]))
    return {'answer':a,'witness':w}
def reference(case):
    f=case['family'];x=case['input']
    if f=='knapsack_mask':
        w=x['weights'];v=x['values'];n=len(w)
        return choose([(sum(v[j] for j in range(n) if mask>>j&1),mask) for mask in range(1<<n) if sum(w[j] for j in range(n) if mask>>j&1)<=x['capacity']])
    if f=='bayes_fraction':
        p=Fraction(x['prior_num'],x['prior_den']);a=p*Fraction(x['positive_if_true'],x['rate_den']);b=(1-p)*Fraction(x['positive_if_false'],x['rate_den']);z=a/(a+b)
        return {'answer':z.numerator,'witness':z.denominator}
    if f=='parity_system':
        ok=[mask for mask in range(1<<x['variables']) if all((mask&e).bit_count()%2==b for e,b in x['equations'])]
        return {'answer':len(ok),'witness':min(ok) if ok else -1}
    if f=='robust_choice':return choose([(min(row),i) for i,row in enumerate(x['payoffs'])])
    if f=='critical_path':
        n=len(x['durations']);edges={tuple(e) for e in x['edges']};rows=[]
        for k in range(1,n+1):
            for path in itertools.combinations(range(n),k):
                if all((u,v) in edges for u,v in zip(path,path[1:])):rows.append((sum(x['durations'][i] for i in path),sum(1<<i for i in path)))
        return choose(rows)
    if f=='nonoverlap_mask':
        intervals=x['intervals'];n=len(intervals);rows=[]
        for mask in range(1<<n):
            chosen=[intervals[j] for j in range(n) if mask>>j&1]
            if all(a[1]<=b[0] or b[1]<=a[0] for a,b in itertools.combinations(chosen,2)):rows.append((sum(a[2] for a in chosen),mask))
        return choose(rows)
    if f=='shortest_avoiding':
        n=x['nodes'];g={(u,v):w for u,v,w in x['edges']};mid=[i for i in range(1,n-1) if i!=x['forbidden']];rows=[]
        for k in range(len(mid)+1):
            for p in itertools.combinations(mid,k):
                path=(0,)+p+(n-1,);edges=list(zip(path,path[1:]))
                if all(e in g for e in edges):rows.append((sum(g[e] for e in edges),sum(1<<i for i in path)))
        return choose(rows,True)
    if f=='bounded_inventory':
        rows=[]
        for q in itertools.product(*(range(n+1) for n in x['demand'])):
            if sum(q)<=x['stock']:rows.append((sum(a*b for a,b in zip(q,x['value'])),100*q[0]+10*q[1]+q[2]))
        return choose(rows)
    raise ValueError('unknown family')
def prompt(c):
    return 'Solve each generated problem using its supplied data. Return only a JSON array of objects {id,answer,witness}, all integers. Use the exact witness convention and tie rule. '+json.dumps(c,separators=(',',':'))
def score(c,raw):
    if not isinstance(raw,str) or len(raw)>8192:raise ValueError('invalid response size')
    rows=json.loads(raw,object_pairs_hook=research.unique_pairs)
    expected={x['id']:reference(x) for x in c}
    if not isinstance(rows,list) or len(rows)!=len(expected) or len(expected)!=len(c):raise ValueError('incomplete batch')
    seen=set();out=[]
    for r in rows:
        if not isinstance(r,dict) or set(r)!={'id','answer','witness'} or any(type(r[k]) is not int for k in r) or r['id'] not in expected or r['id'] in seen:raise ValueError('invalid answer')
        i=r['id'];seen.add(i);a=r['answer']==expected[i]['answer'];w=r['witness']==expected[i]['witness']
        out.append({'id':i,'answer_correct':a,'witness_correct':w,'joint_correct':a and w})
    return {'total':len(c),'answer_correct':sum(r['answer_correct'] for r in out),'witness_correct':sum(r['witness_correct'] for r in out),'joint_correct':sum(r['joint_correct'] for r in out),'rows':sorted(out,key=lambda r:r['id']),'production_authority':False,'semantic_mastery_certified':False}
