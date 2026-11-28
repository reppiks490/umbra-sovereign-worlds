/** Bounded local model probe execution; no arbitrary prompts or external tools. */
import {freemem} from 'node:os';
import {availableAdapters,ollamaBusy} from './local_model_adapters.mjs';
import {battery,publicQuestions,grade,selectProbe} from './intelligence_gaps.mjs';
export function buildProbeRequest(model,questions){
 if(!Array.isArray(questions)||questions.length<1||questions.length>4)throw Error('batch budget');
 const properties=Object.fromEntries(questions.map(q=>[q.id,{type:'object',properties:{answer:{type:'string',enum:q.options},confidence:{type:'integer',enum:[50,75,95]}},required:['answer','confidence'],additionalProperties:false}]));
 return {model:model.model,prompt:'Answer each independent multiple-choice question using only its listed options. Confidence is 50, 75 or 95 percent probability of correctness. Return JSON keyed by question id with answer and confidence. Questions: '+JSON.stringify(questions),format:{type:'object',properties,required:questions.map(q=>q.id),additionalProperties:false},stream:false,keep_alive:0,options:{temperature:0,num_ctx:2048,num_predict:240},...(model.model.startsWith('qwen3:')?{think:false}:{})};
}
export function parseProbeBatch(raw,questions){
 if(typeof raw!=='string'||raw.length>12000)throw Error('invalid response');
 const x=JSON.parse(raw);
 if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).length!==questions.length)throw Error('batch shape');
 return questions.map(q=>{const a=x[q.id];if(!a||Object.keys(a).sort().join(',')!=='answer,confidence'||!q.options.includes(a.answer)||![50,75,95].includes(a.confidence))throw Error('invalid probe answer');return {id:q.id,answer:a.answer,confidence:a.confidence};});
}
async function liveInvoke(model,questions){
 const r=await fetch('http://127.0.0.1:11434/api/generate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(buildProbeRequest(model,questions)),redirect:'error',signal:AbortSignal.timeout(60000)});
 if(!r.ok||!r.body)throw Error('runtime unavailable');
 const reader=r.body.getReader(),chunks=[];let n=0;
 try{for(;;){const x=await reader.read();if(x.done)break;n+=x.value.byteLength;if(n>1024**2)throw Error('response budget');chunks.push(Buffer.from(x.value));}}finally{await reader.cancel().catch(()=>{});}
 const out=JSON.parse(Buffer.concat(chunks).toString('utf8'));
 if(out.model!==model.model||out.done!==true||!Number.isSafeInteger(out.eval_count)||out.eval_count<1||out.eval_count>240)throw Error('unverified output');
 return parseProbeBatch(out.response,questions);
}
export async function runProbe(seed,history,{catalog=availableAdapters,free=freemem,busy=ollamaBusy,invoke=liveInvoke}={}){
 if(await busy())return {status:'deferred_busy'};
 const model=selectProbe((await catalog()).adapters,history,free(),seed);
 if(!model)return {status:'deferred_memory_or_inventory'};
 const questions=publicQuestions(battery(seed)),answers=[];
 for(let i=0;i<questions.length;i+=4){
  if(await busy())return {status:'deferred_busy',completed_questions:answers.length,model:model.model};
  const fresh=(await catalog()).adapters.find(x=>x.model===model.model&&x.manifest_digest===model.manifest_digest);
  if(!fresh||!selectProbe([fresh],history,free(),seed))return {status:'deferred_memory_or_identity',completed_questions:answers.length,model:model.model};
  try{const batch=questions.slice(i,i+4),a=await invoke(fresh,batch);if(!Array.isArray(a)||a.length!==batch.length)throw Error('incomplete batch');answers.push(...a);}
  catch(e){return {status:'probe_failed',completed_questions:answers.length,model:model.model,reason:e.name};}
 }
 const final=(await catalog()).adapters.find(x=>x.model===model.model&&x.manifest_digest===model.manifest_digest);
 if(!final)return {status:'deferred_identity'};
 return {status:'completed',receipt:grade(seed,model,answers)};
}
