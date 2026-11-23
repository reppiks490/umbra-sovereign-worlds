import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorld,advanceWorld,DEFAULT_POLICY} from '../engine.mjs';
import {RESEARCH_SCHEMA,RESEARCH_OUTCOMES,defineResearchPlan,validateResearchPlan,
  inspectResearchWorld,evaluateResearchPlan} from '../research.mjs';

const copy=x=>JSON.parse(JSON.stringify(x));

test('research plans are versioned, synthetic-only and require >=20 unique predeclared seeds',()=>{
 const a=defineResearchPlan({seed:421,trials:24,steps:70});
 assert.equal(a.schema,RESEARCH_SCHEMA);
 assert.equal(a.mode,'synthetic-only');
 assert.equal(a.replicateSeeds.length,24);
 assert.equal(new Set(a.replicateSeeds).size,24);
 assert.equal(a.explorationCount,18);
 assert.deepEqual(defineResearchPlan({seed:421,trials:24,steps:70}),a);
 assert.deepEqual(validateResearchPlan(copy(a)),a);
});

test('evaluation checks twenty same-policy negative controls and invariant audits',()=>{
 const same=defineResearchPlan({seed:6,trials:20,steps:50,
   baseline:DEFAULT_POLICY,treatment:DEFAULT_POLICY});
 const result=evaluateResearchPlan(same);
 assert.equal(result.rows.length,20);
 assert.deepEqual(result.checks,{
   samePolicyNullControl:'pass',structuralInvariants:'pass',
   externalCalibration:'blocked',realWorldPrediction:'blocked',empiricalCausality:'blocked'
 });
 assert.equal(result.exploration.n,15);
 assert.equal(result.confirmation.n,5);
 assert.equal(result.exploration.mean,0);
 assert.equal(result.confirmation.mean,0);
 assert.ok(result.rows.every(x=>x.diff===0));
});

test('synthetic trade forks return paired records without claiming causal identification',()=>{
 const plan=defineResearchPlan({seed:177,trials:20,steps:86,outcome:'food',
   treatment:{...DEFAULT_POLICY,trade:0,climate:.75}});
 const data=evaluateResearchPlan(plan);
 assert.equal(data.rows[0].seed,plan.replicateSeeds[0]);
 assert.equal(data.exploration.n+data.confirmation.n,20);
 assert.ok(data.rows.every(x=>Number.isFinite(x.diff)&&Number.isFinite(x.baseline)));
 assert.match(data.caution,/NOT empirical confidence intervals/);
 assert.ok(Object.values(data.checks).filter(x=>x==='blocked').length>=3);
});

test('the same plan yields exactly the same scientific report on repeated runs',()=>{
 const plan=defineResearchPlan({seed:901,trials:20,steps:30,outcome:'trust'});
 assert.deepEqual(evaluateResearchPlan(plan),evaluateResearchPlan(copy(plan)));
});

test('frozen plan rejects falsified seeds, split, model version and extra fields',()=>{
 const a=defineResearchPlan({seed:1729,trials:20,steps:36});
 const mutations=[
   p=>{p.replicateSeeds[0]++;},
   p=>{p.replicateSeeds[4]=p.replicateSeeds[3];},
   p=>{p.explorationCount=1;},
   p=>{p.mode='validated-real-world';},
   p=>{p.engine='future';},
   p=>{p.hidden='true';}
 ];
 for(const mutate of mutations){
   const bad=copy(a);mutate(bad);
   assert.throws(()=>validateResearchPlan(bad),/UMBRA research:/);
   assert.throws(()=>evaluateResearchPlan(bad),/UMBRA research:/);
 }
});

test('invalid manifest inputs fail instead of being clamped or silently coerced',()=>{
 for(const invalid of [
   {trials:19},{trials:65},{trials:20.7},
   {steps:0},{steps:241},{steps:NaN},{seed:0},{seed:-1},{seed:Infinity},
   {outcome:'profit'},{baseline:{...DEFAULT_POLICY,trade:Infinity}},
   {treatment:{...DEFAULT_POLICY,conflict:-.01}},
   {baseline:{...DEFAULT_POLICY,unknown:0.2}}
 ])assert.throws(()=>defineResearchPlan(invalid),/UMBRA research:/);
});

test('all supported outcome channels are prespecified and report finite values',()=>{
 assert.ok(RESEARCH_OUTCOMES.length>=5);
 const probes=['population','wealth','carbon','trust','biodiversity'];
 for(const outcome of probes){
   const plan=defineResearchPlan({seed:79,trials:20,steps:24,outcome});
   const data=evaluateResearchPlan(plan);
   assert.equal(data.rows.length,20);
   assert.ok(data.rows.every(x=>Number.isFinite(x.baseline)&&Number.isFinite(x.treatment)));
 }
});

test('falsification catches population and fiscal corruption in the input world',()=>{
 const a=advanceWorld(createWorld(79),45);
 assert.equal(inspectResearchWorld(a).passed,true);
 a.population+=4;
 assert.equal(inspectResearchWorld(a).checks.find(x=>x.id==='population').pass,false);
 a.population-=4;
 a.society.foodResidual=10;
 assert.equal(inspectResearchWorld(a).checks.find(x=>x.id==='civic-conservation').pass,false);
});

test('exploration and confirmation partitions stay disjoint at maximum run count',()=>{
 const plan=defineResearchPlan({seed:0xffffffff,trials:64,steps:1});
 assert.equal(plan.replicateSeeds.length,64);
 assert.equal(new Set(plan.replicateSeeds).size,64);
 assert.equal(plan.explorationCount,48);
 const out=evaluateResearchPlan(plan);
 assert.equal(out.exploration.n,48);
 assert.equal(out.confirmation.n,16);
 assert.ok(out.rows.slice(0,48).every(x=>x.partition==='exploration'));
 assert.ok(out.rows.slice(48).every(x=>x.partition==='confirmation'));
});
