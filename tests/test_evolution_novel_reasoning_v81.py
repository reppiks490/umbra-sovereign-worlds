import unittest,json
import evolution_novel_reasoning_v81 as m
class Tests(unittest.TestCase):
 def test_generation_and_family_coverage(self):
  a=m.cases(1);b=m.cases(2)
  self.assertEqual(a,m.cases(1));self.assertNotEqual(a,b)
  self.assertEqual(len(a),4)
  self.assertEqual({c['family'] for c in a+b},set(m.FAMILIES))
  for c in a+b:
   self.assertEqual(set(c),{'id','family','question','input'})
   self.assertEqual(set(m.reference(c)),{'answer','witness'})
  with self.assertRaises(ValueError):m.cases(True)
 def test_exact_fixture_oracles(self):
  examples=[
   ('knapsack_mask',{'weights':[2,3,4],'values':[3,4,5],'capacity':5},(7,3)),
   ('bayes_fraction',{'prior_num':1,'prior_den':4,'positive_if_true':3,'positive_if_false':1,'rate_den':4},(1,2)),
   ('parity_system',{'variables':3,'equations':[[3,1],[6,0]]},(2,1)),
   ('robust_choice',{'payoffs':[[5,1,4],[2,3,2],[4,3,3]]},(3,2)),
   ('critical_path',{'durations':[2,3,4],'edges':[[0,2],[1,2]]},(7,6)),
   ('nonoverlap_mask',{'intervals':[[0,2,5],[2,4,6],[1,4,10]]},(11,3)),
   ('shortest_avoiding',{'nodes':4,'edges':[[0,1,1],[1,3,1],[0,2,4],[2,3,5]],'forbidden':1},(9,13)),
   ('bounded_inventory',{'demand':[2,3,4],'stock':5,'value':[4,3,2]},(17,230))]
  for family,inp,expected in examples:
   with self.subTest(family=family):
    r=m.reference({'family':family,'input':inp})
    self.assertEqual((r['answer'],r['witness']),expected)
 def test_score_and_no_key(self):
  c=m.cases(4)
  raw=json.dumps([{'id':x['id'],**m.reference(x)} for x in c])
  self.assertEqual(m.score(c,raw)['joint_correct'],4)
  self.assertNotIn('"expected"',m.prompt(c))
  rows=json.loads(raw);rows[0]['witness']+=1
  self.assertEqual(m.score(c,json.dumps(rows))['joint_correct'],3)
  rows[0]['answer']=True
  with self.assertRaises(ValueError):m.score(c,json.dumps(rows))
  with self.assertRaises(ValueError):m.score(c,raw[:-1]+','+json.dumps(rows[1])+']')
 def test_many_generated_cases(self):
  for seed in range(60):
   c=m.cases(seed)
   self.assertEqual(len({x['id'] for x in c}),4)
   raw=json.dumps([{'id':x['id'],**m.reference(x)} for x in c])
   self.assertEqual(m.score(c,raw)['joint_correct'],4)
 def test_objectives_against_independent_algorithms(self):
  import evolution_algorithms_v49 as a
  import evolution_algorithms_v56 as b
  for seed in range(60):
   for c in m.cases(seed):
    f=c['family'];x=c['input'];expected=m.reference(c)['answer']
    if f=='knapsack_mask':
     actual=b.knapsack(x['weights'],x['values'],x['capacity'])
    elif f=='critical_path':
     dp=list(x['durations'])
     for u,v in sorted(x['edges']):dp[v]=max(dp[v],dp[u]+x['durations'][v])
     actual=max(dp)
    elif f=='shortest_avoiding':
     g={i:{} for i in range(x['nodes']) if i!=x['forbidden']}
     for u,v,w in x['edges']:
      if u in g and v in g:g[u][v]=w
     actual=a.dijkstra(g,0)[x['nodes']-1]
    elif f=='nonoverlap_mask':
     q=sorted(x['intervals'],key=lambda v:v[1]);dp=[0]
     for i,(lo,hi,val) in enumerate(q):
      j=sum(1 for u in q[:i] if u[1]<=lo)
      dp.append(max(dp[-1],dp[j]+val))
     actual=dp[-1]
    elif f=='bounded_inventory':
     left=x['stock'];actual=0
     for i in sorted(range(3),key=lambda i:-x['value'][i]):
      take=min(left,x['demand'][i]);left-=take;actual+=take*x['value'][i]
    elif f=='parity_system':
     rows=[mask|(rhs<<x['variables']) for mask,rhs in x['equations']];rank=0
     for j in range(x['variables']):
      k=next((i for i in range(rank,len(rows)) if rows[i]>>j&1),None)
      if k is None:continue
      rows[rank],rows[k]=rows[k],rows[rank]
      for i in range(len(rows)):
       if i!=rank and rows[i]>>j&1:rows[i]^=rows[rank]
      rank+=1
     actual=0 if 1<<x['variables'] in rows else 1<<(x['variables']-rank)
    elif f=='bayes_fraction':
     import math
     num=x['prior_num']*x['positive_if_true'];den=num+(x['prior_den']-x['prior_num'])*x['positive_if_false'];g=math.gcd(num,den);actual=num//g
     self.assertEqual(m.reference(c)['witness'],den//g)
    else:
     actual=next(v for v in sorted({v for row in x['payoffs'] for v in row},reverse=True) if any(all(w>=v for w in row) for row in x['payoffs']))
    self.assertEqual(expected,actual,(seed,f))
if __name__=='__main__':unittest.main()
