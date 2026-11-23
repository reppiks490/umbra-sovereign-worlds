#!/usr/bin/env node
/**
 * UMBRA Ω: 300 independently addressable, manually launched synthetic lab cases.
 * This is NOT a scientific model validation, LLM trainer, auto-deployer, or trading system.
 * Only reads repository simulation code and writes local, checksum-bound JSON evidence.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname, join, resolve} from 'node:path';
import {createWorld, advanceWorld, stepWorld, simulate, pairedExperiment, sensitivityExperiment, policyOf,
        DEFAULT_POLICY, SITE_COUNT, noise, buildPassport, validateImport, ENGINE_VERSION} from '../engine.mjs';
import {civicAudit, FACTIONS} from '../society.mjs';
import {runCourt} from '../court.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REGISTRY = join(ROOT,'scripts','umbra_workflow_registry.json');
const POLICIES = Object.keys(DEFAULT_POLICY);
const VARIANTS = ['baseline','edge','stress','cross-seed','adversarial'];
const STAGES=['verification','research','evolution'];
const toDigest=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const decimal=(x,n=6)=>finite(x)?Number(x.toFixed(n)):null;
const syncSummary=w=>({tick:w.tick,seed:w.seed,population:decimal(w.population),food:decimal(w.food),water:decimal(w.water),energy:decimal(w.energy),wealth:decimal(w.wealth),knowledge:decimal(w.knowledge),infected:decimal(w.infected),carbon:decimal(w.carbon),biodiversity:decimal(w.biodiversity),inequality:decimal(w.inequality),elections:w.society.elections,civicAudit:civicAudit(w).valid});
const bound=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const variantSeed=r=>r.variant==='cross-seed'?(r.seed*3+17)>>>0:r.seed;
const stressedPolicy=(r,axis='trade',adjust=.2)=>{
 const index=POLICIES.indexOf(axis);if(index<0)throw Error(`Unknown axis ${axis}`);
 const val=DEFAULT_POLICY[axis];
 const sign=(r.rank%2)?1:-1;
 return policyOf({...DEFAULT_POLICY,[axis]:bound(val+sign*adjust)});
};
function validateCatalog(){
 const a=JSON.parse(readFileSync(REGISTRY,'utf8'));
 assert.equal(a.workflow_count,300);assert.equal(a.items.length,300);
 const names=new Set(),ids=new Set();const counts={verification:0,research:0,evolution:0};
 for(let i=0;i<a.items.length;i++){
  const r=a.items[i],id=`U${String(i+1).padStart(3,'0')}`;
  assert.equal(r.id,id);assert.equal(r.number,i+1);assert.ok(STAGES.includes(r.stage));
  assert.ok(VARIANTS.includes(r.variant));assert.ok(Number.isInteger(r.seed)&&r.seed>0);
  assert.ok(Number.isInteger(r.steps)&&r.steps>=20&&r.steps<=150);
  assert.ok(typeof r.purpose==='string'&&r.purpose.includes('synthetic-only'));
  if(i<100)assert.equal(r.stage,'verification');else if(i<200)assert.equal(r.stage,'research');else assert.equal(r.stage,'evolution');
  assert.ok(!ids.has(r.id)&&!names.has(r.name));ids.add(r.id);names.add(r.name);counts[r.stage]++;
 }
 assert.deepEqual(counts,{verification:100,research:100,evolution:100});
 return {schema:a.schema,counts,registered:300,sha256:toDigest(a.items)};
}
function verifyCase(r){
 const seed=variantSeed(r),p=stressedPolicy(r),w=simulate(seed,p,r.steps);
 const metrics=syncSummary(w);
 assert.equal(w.tick,r.steps);assert.ok(civicAudit(w).valid,'Civic audit failed');
 const family=r.family;
 let detail={assertion:family};
 switch(family){
 case 'seed-replay':{
  const other=simulate(seed,p,r.steps);
  assert.deepEqual(syncSummary(w),syncSummary(other));
  detail={assertion:'identical seed, policy and horizon produce identical states',digest:toDigest(metrics)};break;}
 case 'chunk-equivalence':{
  const one=createWorld(seed,p);advanceWorld(one,Math.floor(r.steps/2));advanceWorld(one,r.steps-Math.floor(r.steps/2));
  assert.deepEqual(syncSummary(one),metrics);detail={assertion:'chunked stepping equals direct simulation'};break;}
 case 'world-regions':{
  assert.equal(w.sites.length,SITE_COUNT);assert.equal(w.towns.length,SITE_COUNT);assert.equal(w.near.length,SITE_COUNT);
  assert.equal(new Set(w.sites.map(s=>s.name)).size,SITE_COUNT);detail={regions:SITE_COUNT};break;}
 case 'resource-bounds':{
  for(const t of w.towns)for(const f of ['p','food','water','energy','knowledge','wealth','infected','trait','health'])assert.ok(finite(t[f])&&t[f]>=0,`${f} invalid`);
  detail={assertion:'finite nonnegative settlement resource stocks',regions:w.towns.length};break;}
 case 'census-balance':{
  assert.ok(Math.abs(w.population-w.towns.reduce((n,t)=>n+t.p,0))<1e-6);detail={assertion:'regional and total population reconcile'};break;}
 case 'civic-accounting':{
  const a=civicAudit(w);assert.ok(a.valid);assert.equal(a.fiscalResidual,0);assert.equal(a.foodResidual,0);detail={assertion:'civic balances reconcile',ledgerEntries:w.society.ledger.length};break;}
 case 'faction-coverage':{
  assert.equal(w.society.councils.length,SITE_COUNT);assert.ok(w.society.councils.every(c=>FACTIONS.some(f=>f.id===c.faction)));detail={assertion:'every region has an allowed faction'};break;}
 case 'corridor-geometry':{
  const corridors=w.society.corridors;assert.equal(new Set(corridors.map(c=>`${c.a}:${c.b}`)).size,corridors.length);
  assert.ok(corridors.every(c=>c.a<c.b&&c.relation>=-1&&c.relation<=1));detail={corridors:corridors.length};break;}
 case 'treasury-solvency':{
  assert.ok(w.society.councils.every(c=>finite(c.treasury)&&c.treasury>=0));detail={assertion:'all council treasuries finite and nonnegative'};break;}
 case 'passport-roundtrip':{
  const passport=buildPassport(w);const x=validateImport(passport);assert.equal(x.tick,r.steps);assert.equal(x.seed,w.seed);assert.deepEqual(x.policy,w.policy);
  assert.ok(passport.mode.includes('synthetic'));detail={assertion:'passport roundtrip remains synthetic and input-valid'};break;}
 case 'passport-rejection':{
  const passport=buildPassport(w);assert.throws(()=>validateImport({...passport,tick:-1}));
  assert.throws(()=>validateImport({...passport,version:'unrecognized'}));detail={assertion:'malformed and incompatible passports rejected'};break;}
 case 'policy-clamping':{
  const x=policyOf({trade:20,climate:-9,medicine:NaN});assert.equal(x.trade,1);assert.equal(x.climate,0);
  assert.equal(x.medicine,DEFAULT_POLICY.medicine);detail={assertion:'out-of-range and invalid interventions clamped'};break;}
 case 'paired-null':{
  const nullTrial=pairedExperiment({seed,trials:2,steps:Math.min(r.steps,100),baseline:p,treatment:p});
  assert.equal(nullTrial.mean,0);assert.equal(nullTrial.sd,0);detail={assertion:'same-policy paired control gives zero difference'};break;}
 case 'paired-repeatability':{
  const cfg={seed,trials:2,steps:Math.min(r.steps,90),baseline:p,treatment:stressedPolicy(r,'climate')};
  const x=pairedExperiment(cfg),y=pairedExperiment(cfg);assert.deepEqual(x,y);detail={assertion:'paired experiment repeatability',mean:decimal(x.mean),sd:decimal(x.sd)};break;}
 case 'weather-noise':{
  assert.equal(noise(seed,r.steps,3,4),noise(seed,r.steps,3,4));const n=noise(seed,r.steps,3,4);
  assert.ok(n>=0&&n<1);detail={assertion:'bounded deterministic exogenous noise',value:decimal(n)};break;}
 case 'timeline-consistency':{
  const a=createWorld(seed,p);for(let i=0;i<r.steps;i++)stepWorld(a);
  assert.deepEqual(syncSummary(a),metrics);detail={assertion:'iterated time steps equal direct horizon'};break;}
 case 'history-samples':{
  assert.ok(w.series.length>0);assert.ok(w.series.every((e,i)=>finite(e.pop)&&(i===0||e.tick>w.series[i-1].tick)));
  detail={samples:w.series.length,assertion:'monotonic, finite recorded series'};break;}
 case 'reality-court':{
  const c=runCourt(w,{replayLimit:Math.max(150,r.steps)});assert.equal(c.counts.fail,0);
  assert.ok(c.counts.blocked>=5);detail={engineeringCourt:c.counts,assertion:'engineering checks do not grant real science validation'};break;}
 case 'scientific-gate':{
  const c=runCourt(w);assert.ok(c.rows.filter(x=>x.id.startsWith('V')).every(x=>x.status==='blocked'));
  detail={assertion:'scientific extrapolation is blocked',blocked:c.counts.blocked};break;}
 case 'stress-replay':{
  const stress=policyOf({trade:r.rank%2?0:1,climate:1,medicine:0,conflict:1,innovation:0});
  const x=simulate(seed,stress,r.steps),y=simulate(seed,stress,r.steps);
  assert.deepEqual(syncSummary(x),syncSummary(y));assert.ok(civicAudit(x).valid);detail={assertion:'bounded worst-case synthetic policies retain invariants'};break;}
 default:throw Error('Unsupported verification family: '+family);
 }
 return {family,metrics,detail};
}
const RESEARCH_FAMILY_TO_AXIS={
 'climate-response':'climate','trade-response':'trade','conservation-response':'conservation',
 'medicine-response':'medicine','innovation-response':'innovation','migration-response':'migration',
 'conflict-response':'conflict','paired-uncertainty':'climate','seasonal-trajectory':'climate',
 'biodiversity-profile':'conservation','food-security':'trade','water-security':'climate',
 'energy-resilience':'innovation','epidemic-path':'medicine','migration-network':'migration',
 'civic-legitimacy':'conflict','fiscal-transfers':'trade','emissions-trajectory':'conservation',
 'inequality-profile':'migration', 'sensitivity-map':'trade'};
function researchCase(r){
 const family=r.family,axis=RESEARCH_FAMILY_TO_AXIS[family];if(!axis)throw Error('Unsupported research family: '+family);
 const seed=variantSeed(r),policy=stressedPolicy(r,axis,.10+.06*r.rank);
 let experiment=null;
 if(family==='sensitivity-map'){
  const s=sensitivityExperiment({seed,trials:2,steps:Math.min(r.steps,80),delta:.1+.02*r.rank,base:DEFAULT_POLICY});
  assert.equal(s.results.length,7);experiment={kind:'seven-axis-sensitivity',points:s.results};
 }else{
  const x=pairedExperiment({seed,trials:3,steps:r.steps,baseline:DEFAULT_POLICY,treatment:policy});
  assert.equal(x.paths.length,3);assert.ok(finite(x.mean)&&finite(x.sd));
  experiment={kind:'paired-model-counterfactual',axis,meanPopulationDifference:decimal(x.mean),sdPopulationDifference:decimal(x.sd),paths:x.paths};
 }
 const w=simulate(seed,policy,r.steps),baseline=simulate(seed,DEFAULT_POLICY,r.steps);
 const outcome=syncSummary(w),control=syncSummary(baseline);
 assert.ok(outcome.civicAudit&&control.civicAudit);
 return {family,axis,intervention:policy,baseline:DEFAULT_POLICY,modelResults:experiment,treated:outcome,control,
  syntheticOnly:true,causalInferenceFromRealWorld:false};
}
const EVOLUTION_FAMILY_OBJECTIVES={
 'policy-tournament':['population','food'],'pareto-frontier':['wealth','biodiversity'],
 'shock-resilience':['water','food'],'bounded-search':['population','wealth'],
 'minimax-stability':['food','water'],'seed-transfer':['wealth','population'],
 'drought-response':['water','biodiversity'],'trade-fragility':['food','wealth'],
 'equity-growth':['population','inequality'],'conservation-innovation':['biodiversity','knowledge'],
 'epidemic-resilience':['infected','population'],'carbon-efficiency':['carbon','wealth'],
 'regional-survival':['population','food'],'regime-rotation':['water','energy'],
 'resource-portfolio':['energy','food'],'replication-audit':['population','food'],
 'counterfactual-race':['wealth','water'],'adversarial-seeds':['food','population'],
 'null-contender':['wealth','knowledge'],'policy-tradeoffs':['carbon','inequality']};
function scores(x,objectives){let total=0;
 for(const name of objectives){const value=x[name]??0;
  if(!finite(value))throw Error('Nonfinite scoreboard '+name);
  const sign=['inequality','infected','carbon'].includes(name)?-1:1;
  const denom= ['carbon','wealth','population','food','water','energy','knowledge'].includes(name)?Math.max(1,Math.abs(value)):1;
  total+=sign*Math.log1p(Math.abs(value))/Math.log1p(denom+1000);
 }return decimal(total);
}
function evolutionCase(r){
 const obj=EVOLUTION_FAMILY_OBJECTIVES[r.family];if(!obj)throw Error('Unsupported evolution family: '+r.family);
 const index=Math.floor((r.number-201)/5),axis=POLICIES[index%POLICIES.length];
 const candidates=[DEFAULT_POLICY];
 for(let j=1;j<=4;j++){
  const a=POLICIES[(index+j)%POLICIES.length];
  candidates.push(policyOf({...DEFAULT_POLICY,[axis]:bound(DEFAULT_POLICY[axis]+(j-2.5)*.14),[a]:bound(DEFAULT_POLICY[a]+(r.rank-3)*.08)}));
 }
 const seeds=[variantSeed(r),variantSeed(r)+17+(r.rank*3)];
 const records=candidates.map((p,i)=>{
  const outcomes=seeds.map(seed=>syncSummary(simulate(seed,p,r.steps)));
  assert.ok(outcomes.every(x=>x.civicAudit));
  const vals=outcomes.map(o=>scores(o,obj));const worst=Math.min(...vals);
  const average=decimal(vals.reduce((a,b)=>a+b,0)/vals.length);
  return {candidateIndex:i,policy:p,seedResults:outcomes,score:average,worstScore:decimal(worst)};
 });
 const rank=[...records].sort((a,b)=>b.score-a.score||a.candidateIndex-b.candidateIndex);
 const champion=rank[0];
 const replay=syncSummary(simulate(seeds[0],champion.policy,r.steps));
 assert.deepEqual(replay,champion.seedResults[0]);
 return {family:r.family,objectives:obj,policyAxis:axis,seedGrid:seeds,candidates:records,
  selectedForOfflineComparison:champion.candidateIndex,selectionScore:champion.score,
  policyPromoted:false,realWorldUseAuthorized:false,syntheticOnly:true};
}
function analyzeCase(r){
 if(r.stage==='verification')return verifyCase(r);
 if(r.stage==='research')return researchCase(r);
 if(r.stage==='evolution')return evolutionCase(r);
 throw Error('Unsupported stage');
}
function main(){
 const args=process.argv.slice(2),idPos=args.indexOf('--id'),outPos=args.indexOf('--out-dir');
 const catalog=validateCatalog();
 if(args.includes('--validate')){console.log(JSON.stringify({status:'catalog-valid',...catalog}));return;}
 if(args.includes('--audit-all')){
  const cases=JSON.parse(readFileSync(REGISTRY,'utf8')).items;
  const failures=[];let passed=0;
  for(const rec of cases){try{const results=analyzeCase(rec);assert.ok(results&&typeof results==='object');passed++;}
    catch(err){failures.push({id:rec.id,error:String(err?.stack||err).slice(0,750)});}}
  const summary={schema:'umbra.synthetic.catalog.audit.v1',passed,failed:failures.length,total:cases.length,
    failures,scientificValidation:false,liveDeployment:false};
  console.log(JSON.stringify(summary,null,2));
  if(failures.length)process.exitCode=1;
  return;
 }
 const id=idPos>=0?args[idPos+1]:null;
 if(!/^U\d{3}$/.test(id||''))throw Error('Expected --id U001..U300');
 const a=JSON.parse(readFileSync(REGISTRY,'utf8'));const r=a.items.find(x=>x.id===id);
 if(!r)throw Error('Unknown registry ID '+id);
 const run=analyzeCase(r);
 const content={schema:'umbra.synthetic.evidence.v1',engine:ENGINE_VERSION,caseId:r.id,stage:r.stage,variant:r.variant,
  name:r.name,seed:r.seed,steps:r.steps,scope:'fictional deterministic scientific research model only',
  evidence:run,claims:{automatedDeployment:false,trainedIntelligentAgents:false,
  productionAuthority:false,independentRealWorldScientificValidation:false,profitableTrading:false}};
 const sealed={...content,evidenceSha256:toDigest(content)};
 const output=resolve(outPos>=0?args[outPos+1]:'workflow-artifacts');
 mkdirSync(output,{recursive:true});const path=join(output,`${id}.json`);
 writeFileSync(path,JSON.stringify(sealed,null,2)+'\n');
 if(process.env.GITHUB_STEP_SUMMARY){appendFileSync(process.env.GITHUB_STEP_SUMMARY,
  `## ${r.name}\n\nResult: **local synthetic evidence generated** (not real-world validation).\n\nEvidence SHA-256: \`${sealed.evidenceSha256}\`\n\nCase: ${id}; engine ${ENGINE_VERSION}. No deployment or live service actions.\n`)}
 console.log(JSON.stringify({id,status:'passed',stage:r.stage,sha256:sealed.evidenceSha256,output:path}));
}
try{main()}catch(err){console.error(err.stack||String(err));process.exitCode=1;}
