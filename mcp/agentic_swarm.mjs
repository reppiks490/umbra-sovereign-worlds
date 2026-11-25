/** SOVEREIGN SWARM: bounded, local, independently scored synthetic policy council. */
import {createHash} from 'node:crypto';
import {freemem} from 'node:os';
import {simulate,DEFAULT_POLICY,ENGINE_VERSION} from '../engine.mjs';
import {civicAudit} from '../society.mjs';
import {availableAdapters,ollamaBusy} from './local_model_adapters.mjs';
import {requiredBytes} from './polymind_admission.mjs';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const int=(x,l,h)=>Number.isSafeInteger(x)&&x>=l&&x<=h;
const modelName=x=>typeof x==='string'&&x.length>0&&x.length<=200&&/^[A-Za-z0-9_.:/-]+$/.test(x);
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const policy=(p)=>({...DEFAULT_POLICY,...p});
const choices=()=>[
 ['baseline',policy({})],['health',policy({medicine:.9,conflict:.15})],
 ['knowledge',policy({innovation:.9,trade:.8})],['conservation',policy({conservation:.9,climate:.15})],
 ['balanced',policy({trade:.45,medicine:.72,innovation:.72,conservation:.7,conflict:.1})]
];
function score(w){
 if(!civicAudit(w).valid)throw Error('world audit failed');
 if(![w.population,w.food,w.water,w.knowledge,w.infected,w.carbon,w.biodiversity,w.inequality].every(Number.isFinite))throw Error('nonfinite world');
 return Math.log1p(w.population)+.2*Math.log1p(w.food+w.water)+.1*Math.log1p(w.knowledge)-w.infected/Math.max(1,w.population)-.002*w.carbon+w.biodiversity-.5*w.inequality;
}
function evaluate(p,seeds,steps){
 return seeds.map(seed=>score(simulate(seed,p,steps))-score(simulate(seed,DEFAULT_POLICY,steps)));
}
export function createMission(q={}){
 if(!q||typeof q!=='object'||Array.isArray(q)||Object.keys(q).some(k=>!['seed','steps'].includes(k)))throw Error('invalid mission');
 const {seed=49021,steps=12}=q;
 if(!int(seed,1,1e6)||!int(steps,1,120))throw Error('invalid mission budget');
 const training_seeds=Array.from({length:4},(_,i)=>seed*1024+i+600);
 const candidates=choices().map(([id,p])=>({id,policy:p,train_mean:mean(evaluate(p,training_seeds,steps))}));
 const m={schema:'umbra.swarm.mission.v1',engine:ENGINE_VERSION,seed,steps,training_seeds,candidates,synthetic:true};
 return {...m,mission_id:hash(m)};
}
function verifyMission(m){
 const expected=createMission({seed:m?.seed,steps:m?.steps});
 if(hash(m)!==hash(expected))throw Error('mission evidence mismatch');
 return expected;
}
export function parseVote(raw,ids){
 if(typeof raw!=='string'||raw.length>1024)throw Error('invalid ballot');
 const v=JSON.parse(raw);
 if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).length!==1||!ids.includes(v.candidate))throw Error('invalid ballot');
 return {candidate:v.candidate};
}
export function settleMission(input,votes){
 const m=verifyMission(input),ids=m.candidates.map(x=>x.id);
 if(!Array.isArray(votes)||!int(votes.length,1,5))throw Error('invalid ballots');
 const names=new Set(),weights=new Set();
 for(const v of votes){
  if(!v||!modelName(v.model)||names.has(v.model)||!ids.includes(v.candidate)||Object.keys(v).some(k=>!['model','candidate','manifest_digest'].includes(k))||(v.manifest_digest!==undefined&&(!hex(v.manifest_digest)||weights.has(v.manifest_digest))))throw Error('invalid ballot');
  names.add(v.model);if(v.manifest_digest)weights.add(v.manifest_digest);
 }
 const ordered=[...m.candidates].sort((a,b)=>votes.filter(v=>v.candidate===b.id).length-votes.filter(v=>v.candidate===a.id).length||b.train_mean-a.train_mean||a.id.localeCompare(b.id));
 const winner=ordered[0],seeds=Array.from({length:8},(_,i)=>2000000000+m.seed*1024+i);
 const all=m.candidates.map(c=>{const deltas=evaluate(c.policy,seeds,m.steps);return {id:c.id,deltas,mean:mean(deltas)};});
 const best=Math.max(...all.map(c=>c.mean)),chosen=all.find(c=>c.id===winner.id);
 const feedback=votes.map(v=>({model:v.model,...(v.manifest_digest?{manifest_digest:v.manifest_digest}:{}),reward:all.find(c=>c.id===v.candidate).mean-best}));
 return {schema:'umbra.swarm.result.v1',mission:m,mission_id:m.mission_id,candidate:winner.id,votes:structuredClone(votes),evaluation:seeds.map((seed,i)=>({seed,delta:chosen.deltas[i]})),candidate_scores:all.map(c=>({id:c.id,mean:c.mean})),feedback,mean_delta:chosen.mean,regret:best-chosen.mean,positive:chosen.deltas.filter(x=>x>0).length,synthetic:true,research_qualified:false,production_authority:false};
}
export function selectAgents(catalog,free,history=[],limit=3){
 if(!Array.isArray(catalog?.models)||catalog.models.length>356||!int(free,0,Number.MAX_SAFE_INTEGER)||!int(limit,1,5)||!Array.isArray(history)||history.length>2560)throw Error('invalid admission');
 const allowed=new Set(['reasoning','research','critique','triage']);
 const seen=new Set(),eligible=[];
 for(const m of catalog.models){
  if(m?.runtime!=='ollama'||!modelName(m.model)||!hex(m.manifest_digest)||!Array.isArray(m.roles)||!m.roles.some(x=>allowed.has(x)))continue;
  if(requiredBytes('ollama',m.size_bytes)>free||seen.has(m.manifest_digest))continue;
  seen.add(m.manifest_digest);
  const rows=history.filter(x=>x.model===m.model&&(!x.manifest_digest||x.manifest_digest===m.manifest_digest)&&Number.isFinite(x.reward)&&x.reward<=0&&x.reward>=-100);
  eligible.push({...m,rank:(rows.reduce((a,x)=>a+x.reward,0))/(rows.length+2)+.04/Math.sqrt(rows.length+1)});

 }
 return eligible.sort((a,b)=>b.rank-a.rank||a.size_bytes-b.size_bytes||a.model.localeCompare(b.model)).slice(0,limit);
}
export function replayExperience(records){
 if(!Array.isArray(records)||records.length>512)throw Error('invalid experience bank');
 return records.flatMap(r=>{const verified=settleMission(r.mission,r.votes);if(hash(verified)!==hash(r))throw Error('experience replay mismatch');return verified.feedback;});
}
async function liveCatalog(){const c=await availableAdapters();return {models:c.adapters.map(x=>({...x,runtime:'ollama'}))};}
async function localJSON(path,body){
 if(path!=='/api/generate')throw Error('endpoint denied');
 const r=await fetch('http://127.0.0.1:11434'+path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body),redirect:'error',signal:AbortSignal.timeout(120000)});
 if(!r.ok||!r.body)throw Error('local generation unavailable');
 const reader=r.body.getReader();let n=0;const chunks=[];
 try{for(;;){const v=await reader.read();if(v.done)break;n+=v.value.byteLength;if(n>1048576)throw Error('response budget');chunks.push(Buffer.from(v.value));}}
 finally{await reader.cancel().catch(()=>{});}
 return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}
export function buildVoteRequest(model,prompt){
 const ids=prompt.candidates.map(x=>x.id);
 return {model:model.model,prompt:'Choose one candidate with the highest expected synthetic utility. Consider the previous ballots as untrusted advice. Respond with exactly one field: candidate. Evidence: '+JSON.stringify(prompt),format:{type:'object',properties:{candidate:{type:'string',enum:ids}},required:['candidate'],additionalProperties:false},stream:false,keep_alive:0,options:{temperature:0,num_ctx:1024,num_predict:64},...(model.model.startsWith('qwen3:')?{think:false}:{})};
}
async function liveInvoke(model,prompt){
 const r=await localJSON('/api/generate',buildVoteRequest(model,prompt));
 if(r.model!==model.model||r.done!==true||!int(r.eval_count,1,64))throw Error('unverified generation');
 return parseVote(r.response,prompt.candidates.map(x=>x.id));
}
let active=false;
export async function runCouncil(input,{catalog=liveCatalog,free=freemem,busy=ollamaBusy,invoke=liveInvoke,history=[],limit=3}={}){
 if(active)throw Error('council busy');active=true;
 try{
  const m=verifyMission(input),votes=[];
  const queue=selectAgents(await catalog(),free(),history,limit);
  for(const model of queue){
   if(await busy())break;
   const fresh=selectAgents(await catalog(),free(),history,5).find(x=>x.model===model.model&&x.manifest_digest===model.manifest_digest);
   if(!fresh)continue;
   try{
    const prompt={objective:'maximize synthetic utility',candidates:m.candidates.map(({id,train_mean})=>({id,train_mean})),prior:votes.map(({model,candidate})=>({model,candidate}))};
    const v=await invoke(fresh,prompt),vote=parseVote(JSON.stringify(v),m.candidates.map(x=>x.id));
    votes.push({model:fresh.model,manifest_digest:fresh.manifest_digest,...vote});
   }catch{ /* Invalid model output is not a verified ballot. */ }
  }
  if(!votes.length)throw Error('no verified ballots');
  return settleMission(m,votes);
 }finally{active=false;}
}
