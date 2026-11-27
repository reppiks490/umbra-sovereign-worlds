/**
 * UM-103: pre-registered, reproducible *synthetic* experiments, not empirical science.
 * No network calls, account data, background agents, fitting, p-values or real-world causal claims.
 * World rules are unchanged; this is an opt-in research layer.
 */
import {createWorld, advanceWorld, noise, DEFAULT_POLICY, ENGINE_VERSION, SITE_COUNT} from './engine.mjs';
import {civicAudit} from './society.mjs';

export const RESEARCH_SCHEMA = 'umbra.research.v1';
export const RESEARCH_OUTCOMES = Object.freeze(['population','food','water','energy','wealth','knowledge','carbon','biodiversity','trust']);
const POLICY_KEYS = Object.keys(DEFAULT_POLICY).sort();
const FIELDS = ['schema','engine','mode','seed','trials','steps','outcome','baseline','treatment','replicateSeeds','explorationCount'];
const ensure = (good,reason) => {if (!good) throw new Error('UMBRA research: '+reason);};
const isObject = x => x !== null && typeof x === 'object' && !Array.isArray(x) && Object.getPrototypeOf(x)===Object.prototype;
const exactKeys = (x,keys) => isObject(x) && JSON.stringify(Object.keys(x).sort())===JSON.stringify([...keys].sort());
const round = x => Math.round((x + Number.EPSILON)*1e6)/1e6;
const metric = (w,name) => name==='trust'?w.society.trust:w[name];

function strictPolicy(input) {
  ensure(exactKeys(input,POLICY_KEYS),'policy must declare exactly the seven named parameters');
  const result={};
  for (const key of POLICY_KEYS){
    const v=input[key];
    ensure(typeof v==='number' && Number.isFinite(v) && v>=0 && v<=1,'invalid policy parameter '+key);
    result[key]=v;
  }
  return result;
}
function seedsFor(seed,trials) {
  const used=new Set(),values=[];
  for(let k=0;k<trials;k++){
    let v=(Math.floor(noise(seed,k,13,61)*4294967296)>>>0)||1;
    while(used.has(v))v=((v+1)>>>0)||1;
    used.add(v);values.push(v);
  }
  return values;
}

/**
 * Freeze the design BEFORE comparing outcomes. The last quarter of generated
 * seeds is a separate confirmatory replicate set, NOT real external holdout data.
 */
export function defineResearchPlan({
  seed=49021,trials=24,steps=90,outcome='population',
  baseline=DEFAULT_POLICY,treatment={...DEFAULT_POLICY,trade:0}
}={}) {
  ensure(Number.isSafeInteger(seed)&&seed>=1&&seed<=0xffffffff,'invalid seed');
  ensure(Number.isInteger(trials)&&trials>=20&&trials<=64,'trials must be between 20 and 64');
  ensure(Number.isInteger(steps)&&steps>=1&&steps<=240,'steps must be between 1 and 240');
  ensure(RESEARCH_OUTCOMES.includes(outcome),'unsupported outcome');
  return {schema:RESEARCH_SCHEMA,engine:ENGINE_VERSION,mode:'synthetic-only',
    seed,trials,steps,outcome,baseline:strictPolicy(baseline),treatment:strictPolicy(treatment),
    replicateSeeds:seedsFor(seed,trials),explorationCount:Math.floor(trials*.75)};
}

export function validateResearchPlan(plan) {
  ensure(exactKeys(plan,FIELDS),'unexpected or missing plan fields');
  ensure(plan.schema===RESEARCH_SCHEMA&&plan.engine===ENGINE_VERSION&&plan.mode==='synthetic-only',
    'unsupported schema, engine or mode');
  const expected=defineResearchPlan(plan);
  ensure(plan.explorationCount===expected.explorationCount,'changed split');
  ensure(Array.isArray(plan.replicateSeeds) && plan.replicateSeeds.length===expected.replicateSeeds.length &&
    expected.replicateSeeds.every((seed,i)=>Object.hasOwn(plan.replicateSeeds,i)&&plan.replicateSeeds[i]===seed),'modified or inconsistent replicate seeds');
  return expected;
}

/** Independent structural invariants; these DO NOT measure real-world model fidelity. */
export function inspectResearchWorld(world){
  ensure(world&&typeof world==='object','invalid world');
  const dense = xs => Array.isArray(xs)&&xs.length===SITE_COUNT&&
    Array.from({length:SITE_COUNT},(_,i)=>Object.hasOwn(xs,i)&&isObject(xs[i])).every(Boolean);
  const townsValid=dense(world.towns)&&world.towns.every(t=>
    ['p','food','water','energy','knowledge','wealth','infected','health','trait'].every(k=>
      Object.hasOwn(t,k)&&typeof t[k]==='number'&&Number.isFinite(t[k])&&t[k]>=0));
  const checks=[
    {id:'version',pass:world.engine===ENGINE_VERSION},
    {id:'topology',pass:dense(world.towns)&&dense(world.sites)},
    {id:'population',pass:townsValid&&Number.isFinite(world.population)&&
      Math.abs(world.population-world.towns.reduce((s,t)=>s+t.p,0))<1e-6},
    {id:'finite-resources',pass:townsValid},
    {id:'civic-conservation',pass:false}
  ];
  try {checks.at(-1).pass=civicAudit(world).valid;}catch {checks.at(-1).pass=false;}
  return {passed:checks.every(x=>x.pass),checks};
}

function summarize(records) {
  const sorted=records.map(x=>x.diff).sort((a,b)=>a-b);
  const n=sorted.length;
  const q=p=>{const v=(n-1)*p,lo=Math.floor(v),hi=Math.ceil(v);return sorted[lo]+(sorted[hi]-sorted[lo])*(v-lo);};
  const mean=sorted.reduce((s,x)=>s+x,0)/n;
  return {n,mean:round(mean),median:round(q(.5)),p05:round(q(.05)),p95:round(q(.95)),
    positive:sorted.filter(x=>x>0).length,zero:sorted.filter(x=>x===0).length,
    negative:sorted.filter(x=>x<0).length};
}

/**
 * Runs an independent same-policy negative control on EVERY replicate.
 * Both arms share the same exogenous keyed signals through their run seed.
 */
export function evaluateResearchPlan(input){
  const plan=validateResearchPlan(input),rows=[];
  for (let i=0;i<plan.trials;i++){
    const seed=plan.replicateSeeds[i];
    const baseline=advanceWorld(createWorld(seed,plan.baseline),plan.steps);
    const treatment=advanceWorld(createWorld(seed,plan.treatment),plan.steps);
    const nullControl=advanceWorld(createWorld(seed,plan.baseline),plan.steps);
    ensure(JSON.stringify(nullControl)===JSON.stringify(baseline),'same-policy negative control diverged');
    ensure(inspectResearchWorld(baseline).passed,'baseline structural audit failed at replicate '+i);
    ensure(inspectResearchWorld(treatment).passed,'treatment structural audit failed at replicate '+i);
    const a=metric(baseline,plan.outcome),b=metric(treatment,plan.outcome);
    ensure(Number.isFinite(a)&&Number.isFinite(b),'nonfinite outcome at replicate '+i);
    rows.push({seed,partition:i<plan.explorationCount?'exploration':'confirmation',
      baseline:round(a),treatment:round(b),diff:round(a-b)});
  }
  return {schema:RESEARCH_SCHEMA,engine:ENGINE_VERSION,plan,
    checks:{samePolicyNullControl:'pass',structuralInvariants:'pass',
      externalCalibration:'blocked',realWorldPrediction:'blocked',empiricalCausality:'blocked'},
    exploration:summarize(rows.slice(0,plan.explorationCount)),
    confirmation:summarize(rows.slice(plan.explorationCount)),rows,
    caution:'All results arise from synthetic UMBRA rules. Percentiles summarize synthetic replicates and are NOT empirical confidence intervals or measured policy effects.'};
}
