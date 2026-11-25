import {freemem} from 'node:os';
import {availableAdapters,ollamaBusy} from './local_model_adapters.mjs';
import {requiredBytes} from './polymind_admission.mjs';
import {buildProbeRequest,parseProbeBatch} from './gap_probe.mjs';
import {gradeKnowledge} from './omni_knowledge.mjs';
const MODELS=['qwen3:0.6b','granite4:350m','qwen2.5-coder:7b'];
async function live(model,qs){
 const r=await fetch('http://127.0.0.1:11434/api/generate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(buildProbeRequest(model,qs)),redirect:'error',signal:AbortSignal.timeout(60000)});
 if(!r.ok||!r.body)throw Error('runtime unavailable');
 const reader=r.body.getReader(),chunks=[];let n=0;
 try{for(;;){const x=await reader.read();if(x.done)break;n+=x.value.byteLength;if(n>1048576)throw Error('response budget');chunks.push(Buffer.from(x.value));}}finally{await reader.cancel().catch(()=>{});}
 const out=JSON.parse(Buffer.concat(chunks).toString('utf8'));
 if(out.model!==model.model||out.done!==true||!Number.isSafeInteger(out.eval_count)||out.eval_count<1||out.eval_count>240)throw Error('unverified output');
 return parseProbeBatch(out.response,qs);
}
export async function runKnowledge(name,qs,{catalog=availableAdapters,busy=ollamaBusy,free=freemem,invoke=live}={}){
 if(!MODELS.includes(name)||!Array.isArray(qs)||qs.length!==4)throw Error('knowledge request');
 if(await busy())return {status:'deferred_busy'};
 const model=(await catalog()).adapters.find(x=>x.model===name);
 if(!model)return {status:'deferred_inventory'};
 if(free()<requiredBytes('ollama',model.size_bytes)+512*1024**2)return {status:'deferred_memory'};
 try{const answers=await invoke(model,qs.map(({id,prompt,options})=>({id,prompt,options})));
 if(!(await catalog()).adapters.some(x=>x.model===name&&x.manifest_digest===model.manifest_digest))return {status:'deferred_identity'};
 return {status:'completed',receipt:gradeKnowledge(model,qs,answers)};}catch(e){return {status:'failed',reason:e.name};}
}

import {knowledgeBatch,verifyKnowledge} from './omni_knowledge.mjs';
export function nextKnowledgeBatch(model,history){if(!Array.isArray(history)||history.length>4096)throw Error('history budget');const seen=new Set(history.map(verifyKnowledge).filter(r=>r.model===model.model&&r.manifest_digest===model.manifest_digest).flatMap(r=>r.rows.map(q=>q.id)));for(let d=0;d<6;d++){const qs=knowledgeBatch(d,0);if(qs.every(q=>!seen.has(q.id)))return qs;if(qs.some(q=>!seen.has(q.id)))throw Error('partial batch history');}return [];}
