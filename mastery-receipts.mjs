/**
 * Read-only, fail-closed projection of *sanitized* UMBRA synthetic world-intelligence
 * evaluation receipts. This module cannot authenticate producers, verify optimizer
 * activity, run models, or qualify deployment. No raw answers or filesystem paths.
 */
export const RECEIPT_SCHEMA = 'umbra.mastery.receipt.v1';
const FIELDS = Object.freeze([
  'schema','model_id','checkpoint_sha256','source_id','source_sha256',
  'evaluator_version','skill','difficulty','question_id','attempt_id',
  'split','grade','failure_category','observed_at','tokens','latency_ms'
]);
const FIELD_SET = new Set(FIELDS);
const SPLITS = Object.freeze(['development','transfer','retention','final-holdout']);
const GRADES = Object.freeze(['pass','fail','abstain']);
const SKILLS = Object.freeze(['navigation','event-understanding','state-prediction',
  'planning','resource-management','adaptive-entities','constraint-following',
  'recovery','long-horizon','visual-perception']);
const FAILURES = Object.freeze(['state','causal','constraint','navigation','resource',
  'format','unsupported','uncertainty','other']);
const IDENTIFIER = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$/;
const DIGEST = /^[a-f0-9]{64}$/;
const ISO = /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/;
const own = (o,k) => Object.prototype.hasOwnProperty.call(o,k);
const fail = (code) => { throw new TypeError(code); };

function utcTime(v) {
  if(typeof v !== 'string' || !ISO.test(v)) return null;
  const time = Date.parse(v);
  return Number.isFinite(time) && new Date(time).toISOString()===v ? time : null;
}
function dataOnlyRecord(input) {
  if(input===null || typeof input!=='object' || Array.isArray(input) ||
     (Object.getPrototypeOf(input)!==Object.prototype && Object.getPrototypeOf(input)!==null)) fail('INVALID_RECORD');
  const names = Reflect.ownKeys(input);
  if(names.length!==FIELDS.length) {
    if(names.some(n=>typeof n!=='string'||!FIELD_SET.has(n))) fail('UNKNOWN_FIELD');
    fail('INVALID_RECORD');
  }
  const out=Object.create(null);
  for(const key of names) {
    if(typeof key!=='string'||!FIELD_SET.has(key)) fail('UNKNOWN_FIELD');
    const descriptor=Object.getOwnPropertyDescriptor(input,key);
    if(!descriptor||!own(descriptor,'value')||!descriptor.enumerable) fail('INVALID_RECORD');
    out[key]=descriptor.value;
  }
  return out;
}
function validReceipt(input) {
  const r=dataOnlyRecord(input);
  if(r.schema!==RECEIPT_SCHEMA) fail('INVALID_SCHEMA');
  for(const key of ['model_id','source_id','evaluator_version','question_id','attempt_id']) {
    if(typeof r[key]!=='string'||!IDENTIFIER.test(r[key])) fail('INVALID_IDENTIFIER');
  }
  for(const key of ['checkpoint_sha256','source_sha256']) {
    if(typeof r[key]!=='string'||!DIGEST.test(r[key])) fail('INVALID_DIGEST');
  }
  if(!SKILLS.includes(r.skill)||!SPLITS.includes(r.split)||!GRADES.includes(r.grade)) fail('INVALID_ENUM');
  if(!Number.isInteger(r.difficulty)||r.difficulty<1||r.difficulty>5) fail('INVALID_DIFFICULTY');
  if(r.grade==='fail' ? !FAILURES.includes(r.failure_category) : r.failure_category!==null) fail('INVALID_FAILURE_CATEGORY');
  if(utcTime(r.observed_at)===null) fail('INVALID_OBSERVATION_TIME');
  if(!Number.isSafeInteger(r.tokens)||r.tokens<0||r.tokens>1000000 ||
     !Number.isSafeInteger(r.latency_ms)||r.latency_ms<0||r.latency_ms>10000000) fail('INVALID_METRICS');
  return r;
}
function gradeCounts() {return {pass:0,fail:0,abstain:0};}
function splitCounts() {return {'development':0,'transfer':0,'retention':0,'final-holdout':0};}
function safeArray(receipts) {
  if(!Array.isArray(receipts)||Object.getPrototypeOf(receipts)!==Array.prototype||receipts.length>1000) fail('INVALID_ARRAY');
  const keys=Reflect.ownKeys(receipts);
  if(keys.length!==receipts.length+1) fail('INVALID_ARRAY');
  const out=[];
  for(let i=0;i<receipts.length;i++) {
    const d=Object.getOwnPropertyDescriptor(receipts,String(i));
    if(!d||!own(d,'value')||!d.enumerable) fail('INVALID_ARRAY');
    out.push(d.value);
  }
  return out;
}
/**
 * @param {unknown} receipts Schema-v1 sanitized data, up to 1000 receipts.
 * @param {{asOf:string,maxAgeHours?:number}} options Explicit UTC observation clock.
 * @returns {object} Non-authoritative numeric summary; no raw content or weight claims.
 */
export function summarizeMasteryReceipts(receipts,options={}) {
  const opts=dataOnlyOptions(options), now=utcTime(opts.asOf);
  if(now===null||!Number.isFinite(opts.maxAgeHours)||opts.maxAgeHours<=0||opts.maxAgeHours>8760) fail('INVALID_OPTIONS');
  const items=safeArray(receipts);
  const models=new Map(),attemptIds=new Set();
  for(const source of items) {
    const r=validReceipt(source),time=utcTime(r.observed_at);
    if(time>now) fail('FUTURE_RECEIPT');
    const id=r.model_id+'|'+r.checkpoint_sha256;
    const aid=id+'|'+r.attempt_id;
    if(attemptIds.has(aid)) fail('DUPLICATE_ATTEMPT');
    attemptIds.add(aid);
    let m=models.get(id);
    if(!m) {
      m={modelId:r.model_id,checkpointSha256:r.checkpoint_sha256,attempts:0,
        grades:gradeCounts(),splits:splitCounts(),questionSplits:new Map(),
        latestObservedAt:r.observed_at,sourceIds:new Set(),skills:new Map()};
      models.set(id,m);
    }
    const oldSplit=m.questionSplits.get(r.question_id);
    if(oldSplit!==undefined && oldSplit!==r.split) fail('CROSS_SPLIT_QUESTION');
    m.questionSplits.set(r.question_id,r.split);
    m.attempts++;m.grades[r.grade]++;m.splits[r.split]++;
    if(time>utcTime(m.latestObservedAt))m.latestObservedAt=r.observed_at;
    m.sourceIds.add(r.source_id+':'+r.source_sha256);
    let sk=m.skills.get(r.skill);
    if(!sk){sk={skill:r.skill,attempts:0,grades:gradeCounts(),failures:{},highestPassedDifficulty:null};m.skills.set(r.skill,sk);}
    sk.attempts++;sk.grades[r.grade]++;
    if(r.grade==='fail')sk.failures[r.failure_category]=(sk.failures[r.failure_category]||0)+1;
    if(r.grade==='pass')sk.highestPassedDifficulty=Math.max(sk.highestPassedDifficulty??0,r.difficulty);
  }
  const output=[...models.values()].sort((a,b)=>a.modelId.localeCompare(b.modelId)||a.checkpointSha256.localeCompare(b.checkpointSha256)).map(m=>{
    const freshness=now-utcTime(m.latestObservedAt)>opts.maxAgeHours*3600000?'STALE':'CURRENT';
    return {modelId:m.modelId,checkpointSha256:m.checkpointSha256,attempts:m.attempts,
      uniqueQuestions:m.questionSplits.size,grades:m.grades,splits:m.splits,
      latestObservedAt:m.latestObservedAt,freshness,sourceIds:[...m.sourceIds].sort(),
      skills:[...m.skills.values()].sort((a,b)=>a.skill.localeCompare(b.skill))};
  });
  return {
    schema:'umbra.mastery.summary.v1',
    status:output.length===0?'EMPTY':output.some(m=>m.freshness==='STALE')?'STALE':'READY',
    inputTrust:'UNVERIFIED_SANITIZED_DATA',weightTraining:'NOT_EVALUATED',
    asOf:opts.asOf,models:output
  };
}
function dataOnlyOptions(options) {
  if(options===null||typeof options!=='object'||Array.isArray(options)||Object.getPrototypeOf(options)!==Object.prototype) fail('INVALID_OPTIONS');
  const keys=Reflect.ownKeys(options);
  if(keys.some(k=>k!=='asOf'&&k!=='maxAgeHours')) fail('INVALID_OPTIONS');
  const copy=Object.create(null);
  for(const k of keys){const d=Object.getOwnPropertyDescriptor(options,k);if(!d||!own(d,'value'))fail('INVALID_OPTIONS');copy[k]=d.value;}
  return {asOf:copy.asOf,maxAgeHours:copy.maxAgeHours??24};
}
