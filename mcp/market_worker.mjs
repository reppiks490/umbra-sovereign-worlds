import {freemem} from 'node:os';
import {availableAdapters,ollamaBusy} from './local_model_adapters.mjs';
import {requiredBytes} from './polymind_admission.mjs';
import {buildProbeRequest,parseProbeBatch} from './gap_probe.mjs';
import {gradeMarket,verifyMarket} from './market_academy.mjs';
export const REFERENCE='qwen2.5-coder:7b';
export const STUDENTS=['qwen3:0.6b','granite4:350m'];
async function liveInvoke(model,qs){
 const body=buildProbeRequest(model,qs);
 const r=await fetch('http://127.0.0.1:11434/api/generate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body),redirect:'error',signal:AbortSignal.timeout(60000)});
 if(!r.ok||!r.body)throw Error('runtime unavailable');
 const reader=r.body.getReader(),chunks=[];let n=0;
 try{for(;;){const x=await reader.read();if(x.done)break;n+=x.value.byteLength;if(n>1024**2)throw Error('response budget');chunks.push(Buffer.from(x.value));}}finally{await reader.cancel().catch(()=>{});}
 const out=JSON.parse(Buffer.concat(chunks).toString('utf8'));
 if(out.model!==model.model||out.done!==true||!Number.isSafeInteger(out.eval_count)||out.eval_count<1||out.eval_count>240)throw Error('unverified response');
 return parseProbeBatch(out.response,qs);
}
export async function runMarketBatch(name,questions,{catalog=availableAdapters,busy=ollamaBusy,free=freemem,invoke=liveInvoke}={}){
 if(![REFERENCE,...STUDENTS].includes(name))throw Error('unsupported model');
 if(!Array.isArray(questions)||!questions.length||questions.length>4)throw Error('batch budget');
 if(await busy())return {status:'deferred_busy'};
 const model=(await catalog()).adapters.find(x=>x.model===name);
 if(!model)return {status:'deferred_inventory'};
 if(free()<requiredBytes('ollama',model.size_bytes)+512*1024**2)return {status:'deferred_memory'};
 try{
  const answers=await invoke(model,questions.map(({id,prompt,options})=>({id,prompt,options})));
  if(!(await catalog()).adapters.some(x=>x.model===name&&x.manifest_digest===model.manifest_digest))return {status:'deferred_identity'};
  return {status:'completed',receipt:gradeMarket(model,questions,answers)};
 }catch(e){return {status:'failed',reason:e.name};}
}
export function compareMarket(history){
 if(!Array.isArray(history)||history.length>16384)throw Error('history budget');
 const rows=history.map(verifyMarket),by=new Map(),students=new Map(),seen=new Set();
 for(const r of rows)for(const q of r.rows){
  const k=r.model+':'+r.manifest_digest+':'+q.id;if(seen.has(k))throw Error('duplicate observation');seen.add(k);
  if(q.seed<800001)continue;
  if(r.model===REFERENCE){if(!by.has(q.id))by.set(q.id,[]);by.get(q.id).push({q,digest:r.manifest_digest});}
  else{const key=r.model+':'+r.manifest_digest;if(!students.has(key))students.set(key,[]);students.get(key).push({q,model:r.model,digest:r.manifest_digest});}
 }
 const pairs=[];
 for(const group of students.values()){
  const matches=new Map();
  for(const row of group)for(const ref of by.get(row.q.id)??[]){const key=ref.digest;if(!matches.has(key))matches.set(key,[]);matches.get(key).push([row.q,ref.q]);}
  for(const [digest,rs] of matches){const n=rs.length,delta=rs.reduce((a,[s,t])=>a+Number(s.correct)-Number(t.correct),0)/n;pairs.push({model:group[0].model,digest:group[0].digest,reference_digest:digest,matched:n,mean_paired_delta:delta,scope:'descriptive synthetic paired tasks only'});}
 }
 return {pairs,general_reasoning_verified:false,production_authority:false};
}
