#!/usr/bin/env node
/**
 * UMBRA Sovereign Worlds — deterministic advanced synthetic research laboratory.
 * 5,000 distinct cases, 25 bounded methods x 10 observables x 20 protocols.
 * Does not infer scientific causality, optimize real policies, trade, learn weights,
 * deploy, commit, self-promote, access secrets, or call an external service.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,mkdirSync,appendFileSync} from 'node:fs';
import {dirname,join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createWorld,advanceWorld,simulate,policyOf,DEFAULT_POLICY,SITE_COUNT,ENGINE_VERSION} from '../engine.mjs';
import {civicAudit} from '../society.mjs';
import {runCourt} from '../court.mjs';
import {createSimulationRunner} from './umbra_independent_replay.mjs';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const catalog=JSON.parse(readFileSync(join(ROOT,'scripts','umbra_advanced_registry.json'),'utf8'));
catalog.items=catalog.shards.flatMap(name=>JSON.parse(readFileSync(join(ROOT,'scripts',name),'utf8')));
const SHA=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const METRICS=['population','food','water','energy','wealth','knowledge','infected','carbon','biodiversity','inequality'];
const NEGATIVE=new Set(['infected','carbon','inequality']);
const POLICY=Object.keys(DEFAULT_POLICY);
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const clamp=n=>Math.max(0,Math.min(1,n));
const clean=n=>{assert.ok(finite(n),'Nonfinite statistic');return Math.round(n*1e7)/1e7};
const mean=a=>clean(a.reduce((s,n)=>s+n,0)/a.length);
const variance=a=>mean(a.map(n=>(n-mean(a))**2));
const risk=x=>NEGATIVE.has(x)?-1:1;
const normal=(value,metric)=>clean(risk(metric)*Math.log1p(Math.max(0,value)));
const METRIC_COLUMNS={population:'p',food:'food',water:'water',energy:'energy',wealth:'wealth',knowledge:'knowledge',infected:'infected',carbon:'p',biodiversity:'p',inequality:'wealth'};
const hasOwn=(obj,key)=>Object.prototype.hasOwnProperty.call(obj,key);
const methodNames=Object.values(catalog.tiers).flatMap(x=>x.methods);
const caseMap=new Map(catalog.items.map(x=>[x.id,x]));
if(catalog.schema!=='umbra.advanced.5000.v1'||catalog.count!==5000||catalog.items.length!==5000||caseMap.size!==5000||methodNames.length!==25)
 throw Error('Invalid advanced registry structural counts');
const metricValue=(w,metric)=>{assert.ok(METRICS.includes(metric));let v=w[metric];assert.ok(finite(v),`bad ${metric}`);return v};
const sample=(w,metric)=>({seed:w.seed,tick:w.tick,metric,metricValue:clean(metricValue(w,metric)),population:clean(w.population),
 food:clean(w.food),water:clean(w.water),energy:clean(w.energy),carbon:clean(w.carbon),biodiversity:clean(w.biodiversity),
 civicValid:civicAudit(w).valid,seriesLength:w.series.length});
function makePolicies(r){
 const primary=r.axis,secondary=r.otherAxis;
 assert.ok(POLICY.includes(primary)&&POLICY.includes(secondary)&&primary!==secondary);
 const amp=r.amplitude,sign=r.variant%2?1:-1;
 const mutation=(axis,amount,source=DEFAULT_POLICY)=>policyOf({...source,[axis]:clamp(source[axis]+amount)});
 const baseline=policyOf(DEFAULT_POLICY);
 const p1=mutation(primary,sign*amp),p2=mutation(secondary,-sign*amp),
 p3=mutation(secondary,-sign*amp,p1),p4=mutation(primary,-sign*amp),
 extreme=policyOf({...baseline,[primary]:r.variant%2?1:0,[secondary]:r.variant%3?0:1});
 return {baseline,p1,p2,p3,p4,extreme,mutation};
}
function run(r){
 const runner=createSimulationRunner({
  simulate:(seed,policy,steps)=>{assert.ok(Number.isInteger(steps)&&steps>=1&&steps<=1000);return simulate(seed,policy,steps);},
  keyFor:(seed,policy,steps)=>`${seed}|${steps}|${POLICY.map(a=>policy[a].toFixed(6)).join(',')}`,
  validate:(w,steps)=>{
   assert.equal(w.tick,steps);
   const check=civicAudit(w);assert.ok(check.valid,`civic audit failed: ${check.issues.join(';')}`);
   for(const m of METRICS)assert.ok(finite(metricValue(w,m)),`${m} not finite`);
   assert.equal(w.towns.length,SITE_COUNT);
  }
 });
 const world=(seed,policy,steps=r.steps)=>runner.world(seed,policy,steps);
 const p=makePolicies(r),S=r.seed,M=r.metric,n=r.steps,d=r.amplitude;
 const A=(seed,policy,steps=n)=>sample(world(seed,policy,steps),M);
 const U=(seed,policy,steps=n)=>normal(metricValue(world(seed,policy,steps),M),M);
 const SEEDS=[S,S+11,S+23,S+47,S+91];
 const policyGrid=[p.baseline,p.p1,p.p2,p.p3,p.p4];
 let detail={};
 const results=()=>policyGrid.map((q,index)=>({index,policy:q,utility:mean(SEEDS.slice(0,2).map(seed=>U(seed,q)))}));
 switch(r.method){
 case 'paired-delta':{
  const diffs=SEEDS.slice(0,3).map(seed=>clean(U(seed,p.p1)-U(seed,p.baseline)));
  detail={design:'common-seed paired intervention',diffs,meanEffect:mean(diffs),sd:clean(Math.sqrt(variance(diffs))),causalClaim:false};break;}
 case 'dose-gradient':{
  const levels=[-.8,-.3,.3,.8].map(x=>({dose:x*d,policy:p.mutation(r.axis,x*d)}));
  const vals=levels.map(x=>U(S,x.policy));detail={design:'4-point finite dose response',levels:levels.map((x,i)=>({dose:clean(x.dose),score:vals[i]})),slope:clean((vals.at(-1)-vals[0])/(1.6*d))};break;}
 case 'local-curvature':{
  const left=U(S,p.mutation(r.axis,-d)),center=U(S,p.baseline),right=U(S,p.mutation(r.axis,d));
  detail={design:'local finite-difference Hessian diagonal',left,center,right,curvature:clean((left-2*center+right)/(d*d))};break;}
 case 'interaction-synergy':{
  const u00=U(S,p.baseline),u10=U(S,p.p1),u01=U(S,p.p2),u11=U(S,p.p3);
  detail={design:'two-axis factorial interaction',axis:[r.axis,r.otherAxis],interaction:clean(u11-u10-u01+u00),quadrants:[u00,u10,u01,u11]};break;}
 case 'placebo-falsification':{
  const replay=runner.independentReplay(S,p.p1,n);
  const value=normal(metricValue(replay.first,M),M),other=normal(metricValue(replay.second,M),M);assert.equal(value,other);
  detail={design:'independently executed identical treatment placebo',difference:clean(other-value),pass:true,replayDigest:SHA(sample(replay.first,M)),firstStateDigest:replay.firstDigest,secondStateDigest:replay.secondDigest,independentExecutions:replay.executions};break;}
 case 'shock-recovery':{
  const before=U(S,p.baseline,Math.max(10,Math.floor(n/2))),during=U(S,p.extreme,n),after=U(S,p.extreme,Math.min(800,n+35));
  detail={design:'synthetic intervention stress trajectories, not real post-shock recovery',before,during,after,delta:clean(after-during)};break;}
 case 'cvar-tail-risk':{
  const scores=SEEDS.map(seed=>U(seed,p.extreme)).sort((a,b)=>a-b);
  detail={design:'lower 40% CVaR-like outcome on five scenarios',scoreGrid:scores,lowerTail:mean(scores.slice(0,2)),worst:scores[0]};break;}
 case 'adversarial-seed-search':{
  const scores=SEEDS.map(seed=>({seed,utility:U(seed,p.p3)}));const ordered=[...scores].sort((a,b)=>a.utility-b.utility);
  detail={design:'enumerated worst-seed stress search',scores,worstSeed:ordered[0].seed,spread:clean(ordered.at(-1).utility-ordered[0].utility)};break;}
 case 'seed-invariance':{
  const scores=SEEDS.map(seed=>U(seed,p.p2));assert.equal(U(S,p.p2),scores[0]);
  detail={design:'seed stability, not policy-independent universality',scores,variation:variance(scores)};break;}
 case 'multi-horizon-stability':{
  const horizons=[Math.max(10,Math.floor(n/2)),n,Math.min(800,2*n)];
  const readings=horizons.map(steps=>({steps,metric:U(S,p.p1,steps)}));
  detail={design:'time-horizon drift map',readings,totalDrift:clean(readings.at(-1).metric-readings[0].metric)};break;}
 case 'policy-tournament':{
  const grid=results().sort((a,b)=>b.utility-a.utility||a.index-b.index);
  detail={design:'bounded 5-policy 2-seed tournament',ranking:grid,offlineChampion:grid[0].index,policyPromoted:false};break;}
 case 'heldout-seed-transfer':{
  const trained=policyGrid.map((q,index)=>({index,avg:mean(SEEDS.slice(0,2).map(s=>U(s,q)))})).sort((a,b)=>b.avg-a.avg||a.index-b.index);
  const best=policyGrid[trained[0].index];const holdout=SEEDS.slice(3).map(s=>clean(U(s,best)-U(s,p.baseline)));
  detail={design:'separate selection and held-out seed evaluation',chosen:trained[0].index,selectionSeeds:SEEDS.slice(0,2),holdoutSeeds:SEEDS.slice(3),holdoutEffects:holdout,allPositive:holdout.every(x=>x>0),policyPromoted:false};break;}
 case 'bounded-mutation':{
  const gen0=results();const champ=[...gen0].sort((a,b)=>b.utility-a.utility||a.index-b.index)[0];
  const parent=policyGrid[champ.index];const children=[p.mutation(r.axis,d/2,parent),p.mutation(r.otherAxis,-d/2,parent),parent];
  const gen1=children.map((q,index)=>({index,utility:mean(SEEDS.slice(0,2).map(s=>U(s,q)))}));
  detail={design:'two-generation bounded mutation search',gen0,gen1,selectedParent:champ.index,noWeightTraining:true};break;}
 case 'pareto-frontier':{
  const alt=METRICS[(METRICS.indexOf(M)+3)%METRICS.length];
  const vecs=policyGrid.map((q,index)=>({index,objectives:[U(S,q),normal(metricValue(world(S,q),alt),alt)]}));
  const frontier=vecs.filter(a=>!vecs.some(b=>b.index!==a.index&&b.objectives.every((v,i)=>v>=a.objectives[i])&&b.objectives.some((v,i)=>v>a.objectives[i]))).map(a=>a.index);
  assert.ok(frontier.length>=1);detail={design:'non-dominated two-objective frontier',alternate:alt,vectors:vecs,frontier};break;}
 case 'regime-transition':{
  const early=Math.max(10,Math.floor(n/2)),late=Math.min(800,n+40);
  const scores=policyGrid.slice(0,3).map((q,index)=>({index,early:U(S,q,early),late:U(S,q,late)}));
  const bestEarly=[...scores].sort((a,b)=>b.early-a.early||a.index-b.index)[0].index;
  const bestLate=[...scores].sort((a,b)=>b.late-a.late||a.index-b.index)[0].index;
  detail={design:'in-model regime/time horizon choice stability',scores,bestEarly,bestLate,rankingSwitched:bestEarly!==bestLate};break;}
 case 'minimax-regret':{
  const grid=policyGrid.map((q,index)=>({index,values:SEEDS.slice(0,3).map(seed=>U(seed,q))}));
  const top=SEEDS.slice(0,3).map((_,i)=>Math.max(...grid.map(g=>g.values[i])));
  const regrets=grid.map(g=>({index:g.index,maxRegret:clean(Math.max(...g.values.map((x,i)=>top[i]-x)))}));
  const best=[...regrets].sort((a,b)=>a.maxRegret-b.maxRegret||a.index-b.index)[0].index;
  detail={design:'minimax regret over three independently seeded worlds',regrets,offlineChampion:best};break;}
 case 'preference-robustness':{
  const alt=METRICS[(METRICS.indexOf(M)+4)%METRICS.length];const weights=[.2,.5,.8];
  const choices=weights.map(weight=>{const grid=policyGrid.map((q,index)=>({index,score:clean(weight*U(S,q)+(1-weight)*normal(metricValue(world(S,q),alt),alt))}));
   grid.sort((a,b)=>b.score-a.score||a.index-b.index);return {weight,champion:grid[0].index};});
  detail={design:'preference-weight sensitivity, no real utility calibration',secondary:alt,choices,sensitive:new Set(choices.map(x=>x.champion)).size>1};break;}
 case 'budget-constrained-search':{
  const distance=q=>clean(POLICY.reduce((acc,k)=>acc+Math.abs(q[k]-DEFAULT_POLICY[k]),0));
  const cap=clean(2*d+.001);const options=policyGrid.map((q,index)=>({index,distance:distance(q),value:U(S,q)}));
  const feasible=options.filter(x=>x.distance<=cap+1e-8);assert.ok(feasible.length>=1);
  feasible.sort((a,b)=>b.value-a.value||a.index-b.index);detail={design:'synthetic policy L1 intervention budget',cap,options,feasibleChampion:feasible[0].index};break;}
 case 'regional-fairness':{
  const w=world(S,p.p1);const key=METRIC_COLUMNS[M];const values=w.towns.map(t=>t[key]);assert.ok(values.every(finite));
  const ordered=[...values].sort((a,b)=>a-b),med=ordered[Math.floor(ordered.length/2)],spread=ordered.at(-1)-ordered[0];
  detail={design:'cross-region synthetic outcome dispersion',proxyField:key,regions:values.length,median:clean(med),maxMinSpread:clean(spread),note:'regional proxy, not demographic fairness certification'};break;}
 case 'composite-utility':{
  const alt=METRICS[(METRICS.indexOf(M)+1)%METRICS.length];const third=METRICS[(METRICS.indexOf(M)+7)%METRICS.length];
  const weights=[.5,.3,.2];const grid=policyGrid.map((q,index)=>({index,score:clean(weights[0]*U(S,q)+weights[1]*normal(metricValue(world(S,q),alt),alt)+weights[2]*normal(metricValue(world(S,q),third),third))}));
  grid.sort((a,b)=>b.score-a.score||a.index-b.index);detail={design:'explicit synthetic three-objective scalarization',metrics:[M,alt,third],weights,grid,winner:grid[0].index};break;}
 case 'exact-replay':{
  const replay=runner.independentReplay(S,p.p1,n);
  assert.deepEqual(sample(replay.first,M),sample(replay.second,M));
  detail={design:'independently executed full-state seed replay',first:SHA(sample(replay.first,M)),second:SHA(sample(replay.second,M)),firstStateDigest:replay.firstDigest,secondStateDigest:replay.secondDigest,independentExecutions:replay.executions,pass:true};break;}
 case 'chunk-equivalence':{
  const q=p.p2;const a=createWorld(S,q),first=Math.max(1,Math.floor(n/3));advanceWorld(a,first);advanceWorld(a,n-first);
  const b=world(S,q);assert.deepEqual(sample(a,M),sample(b,M));
  detail={design:'partition-invariant state advancement',firstChunk:first,secondChunk:n-first,pass:true};break;}
 case 'invariant-fuzz':{
  const observations=SEEDS.slice(0,3).map((seed,i)=>{const q=policyOf({...p.extreme,[r.axis]:i/2});const w=world(seed,q);const a=civicAudit(w);
   assert.ok(a.valid);assert.ok(w.towns.every(t=>Number.isFinite(t.p)&&t.p>=0));assert.ok(Math.abs(w.population-w.towns.reduce((v,t)=>v+t.p,0))<1e-5);
   return {seed,policy:q,metric:clean(metricValue(w,M)),valid:true};});detail={design:'three-seed property fuzz against numerical/accounting invariants',observations};break;}
 case 'robustness-dominance':{
  const grid=policyGrid.map((q,index)=>({index,values:SEEDS.slice(0,3).map(seed=>U(seed,q))}));
  const baseline=grid[0];const dominance=grid.slice(1).map(g=>({index:g.index,dominatesBaseline:g.values.every((x,i)=>x>=baseline.values[i])&&g.values.some((x,i)=>x>baseline.values[i])}));
  detail={design:'seed-grid Pareto dominance, not real-world preference',baseline:baseline.values,dominance};break;}
 case 'corruption-falsification':{
  const w=world(S,p.baseline);const altered=structuredClone(w);altered.population+=Math.max(1,d*10);
  const check=runCourt(altered,{replayLimit:Math.min(n,10)});
  assert.equal(check.rows.find(x=>x.id==='G03').status,'fail');
  detail={design:'fault injection detected by independent engineering court',status:'detected',failedChecks:check.rows.filter(x=>x.status==='fail').map(x=>x.id),modelValidatedForRealWorld:false};break;}
 default:throw Error('Unsupported experimental method '+r.method);
 }
 const verification={caseId:r.id,method:r.method,metric:M,seed:S,horizon:n,uniqueWorldStates:runner.stats().distinctParameterKeys,simulationExecutions:runner.stats().simulationExecutions,
  data:detail,claim:'synthetic engineering research only',productionAuthorized:false,autoPromoted:false};
 const signature=SHA(verification);return {verification,sha256:signature};
}
function verifySchema(){
 assert.equal(catalog.first,'U0301');assert.equal(catalog.last,'U5300');
 assert.equal(Object.keys(catalog.tiers).length,5);assert.equal(catalog.metrics.length,10);
 for(let i=0;i<catalog.items.length;i++){
  const r=catalog.items[i];assert.equal(r.id,`U${String(i+301).padStart(4,'0')}`);
  assert.ok(methodNames.includes(r.method));assert.ok(METRICS.includes(r.metric));
  assert.ok(Number.isInteger(r.seed)&&r.seed>0&&r.seed<=2**32-1);
  assert.ok(r.steps>=10&&r.steps<=200);assert.ok(Number.isInteger(r.variant)&&r.variant>=0&&r.variant<20);
 }
 return {status:'catalog-valid',count:catalog.count,tiers:Object.fromEntries(Object.entries(catalog.tiers).map(([t,v])=>[t,v.count])),
  noAutonomousDeployment:true,trainingClaim:false,catalogDigest:SHA(catalog.items)};
}
function main(){
 const args=process.argv.slice(2);const pos=k=>args.indexOf(k);const get=k=>pos(k)>=0?args[pos(k)+1]:null;
 if(args.includes('--validate')){console.log(JSON.stringify(verifySchema()));return;}
 const shard=get('--audit-shard');if(shard){const m=/^(\d+)\/(\d+)$/.exec(shard);if(!m)throw Error('Expected --audit-shard N/T');
  const index=Number(m[1]),total=Number(m[2]);if(!Number.isSafeInteger(index)||!Number.isSafeInteger(total)||total<1||total>100||index<0||index>=total)throw Error('Invalid shard indices');
  const records=catalog.items.filter((_,i)=>i%total===index);let passed=0;const failed=[],digests=[];
  for(const r of records){try{const result=run(r);assert.ok(result.verification.uniqueWorldStates>=1);digests.push([r.id,result.sha256]);passed++;}
   catch(e){failed.push({id:r.id,error:String(e.stack||e).slice(0,900)});}}
  const report={schema:'umbra.synthetic.advanced-shard.v1',shard:index,totalShards:total,passed,failed:failed.length,
    expected:records.length,failures:failed,aggregateDigest:SHA(digests),claims:{realWorldValidation:false,productionAuthorized:false}};
  const path=get('--summary-file');if(path){mkdirSync(dirname(resolve(path)),{recursive:true});writeFileSync(resolve(path),JSON.stringify(report,null,2)+'\n');}
  console.log(JSON.stringify(report));if(failed.length)process.exitCode=1;return;
 }
 const id=get('--id');if(!/^U\d{4}$/.test(id||'')||!caseMap.has(id))throw Error('Unknown advanced case id: use U0301–U5300');
 const r=caseMap.get(id),evidence=run(r);
 const payload={schema:'umbra.synthetic.advanced-evidence.v1',engine:ENGINE_VERSION,caseId:id,method:r.method,tier:r.tier,stage:r.stage,metric:r.metric,
  protocol:r,results:evidence.verification,hash:evidence.sha256,
  flags:{synthetic:true,independentRealWorldValidity:false,neuralTraining:false,autonomousDeployment:false,brokerage:false}};
 const dir=resolve(get('--out-dir')||'advanced-evidence');mkdirSync(dir,{recursive:true});const path=join(dir,`${id}.json`);
 writeFileSync(path,JSON.stringify(payload,null,2)+'\n');
 if(process.env.GITHUB_STEP_SUMMARY){appendFileSync(process.env.GITHUB_STEP_SUMMARY,
  `## ${id} — ${r.stage} / ${r.method} / ${r.metric}\n\nSynthetic experiment recorded. SHA256: \`${evidence.sha256}\`. No scientific or production certification.\n`)}
 console.log(JSON.stringify({id,status:'passed',sha256:evidence.sha256,output:path}));
}
try{main()}catch(e){console.error(e.stack||String(e));process.exitCode=1;}
