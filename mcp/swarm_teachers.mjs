/** Cross-model lessons with independently verified generated-task answers. */
import {createHash} from 'node:crypto';
import {freemem} from 'node:os';
import {battery,publicQuestions} from './intelligence_gaps.mjs';
import {availableAdapters,ollamaBusy} from './local_model_adapters.mjs';
import {requiredBytes} from './polymind_admission.mjs';
import {buildProbeRequest,parseProbeBatch} from './gap_probe.mjs';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const validModel=x=>typeof x==='string'&&/^[A-Za-z0-9_.:/-]{1,200}$/.test(x);
export function makeLesson(teacher,domain,seed,answers){
 if(!validModel(teacher?.model)||!hex(teacher.manifest_digest))throw Error('teacher identity');
 const qs=battery(seed).filter(x=>x.domain===domain);
 if(!qs.length||!Array.isArray(answers)||answers.length!==qs.length||new Set(answers.map(x=>x.id)).size!==qs.length)throw Error('lesson answers');
 const rows=qs.map(q=>{const a=answers.find(x=>x.id===q.id);if(!a||!q.options.includes(a.answer)||![50,75,95].includes(a.confidence))throw Error('invalid teacher answer');return {id:q.id,answer:a.answer,confidence:a.confidence,correct:a.answer===q.correct};});
 const examples=qs.filter(q=>rows.find(a=>a.id===q.id).correct).map(q=>({prompt:q.prompt,answer:q.correct}));
 const r={schema:'umbra.swarm.lesson.v1',teacher:teacher.model,teacher_digest:teacher.manifest_digest,domain,seed,rows,examples,synthetic:true,production_authority:false};
 return {...r,evidence:hash(r)};
}
export function verifyLesson(r){const v=makeLesson({model:r?.teacher,manifest_digest:r?.teacher_digest},r?.domain,r?.seed,r?.rows);if(hash(v)!==hash(r))throw Error('lesson receipt mismatch');return v;}
export function lessonContext(lessons,agent,seed){
 if(!Array.isArray(lessons)||lessons.length>4096)throw Error('lesson bank');
 return lessons.map(verifyLesson).filter(x=>x.teacher!==agent.model&&x.domain===agent.domain&&x.seed!==seed&&(!agent.model_digest||agent.model_digest!==x.teacher_digest)).flatMap(x=>x.examples).slice(-2);
}
async function liveInvoke(model,qs){
 const body=buildProbeRequest(model,qs);
 const r=await fetch('http://127.0.0.1:11434/api/generate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body),redirect:'error',signal:AbortSignal.timeout(60000)});
 if(!r.ok||!r.body)throw Error('runtime unavailable');
 const reader=r.body.getReader(),chunks=[];let n=0;
 try{for(;;){const x=await reader.read();if(x.done)break;n+=x.value.byteLength;if(n>1024**2)throw Error('response budget');chunks.push(Buffer.from(x.value));}}finally{await reader.cancel().catch(()=>{});}
 const out=JSON.parse(Buffer.concat(chunks).toString('utf8'));if(out.model!==model.model||out.done!==true||!Number.isSafeInteger(out.eval_count)||out.eval_count<1||out.eval_count>240)throw Error('unverified generation');
 return parseProbeBatch(out.response,qs);
}
export async function teach(domain,seed,{catalog=availableAdapters,free=freemem,busy=ollamaBusy,invoke=liveInvoke,student=null}={}){
 if(await busy())return {status:'deferred_busy'};
 const qs=battery(seed).filter(q=>q.domain===domain);if(!qs.length)throw Error('unsupported domain');
 const eligible=(await catalog()).adapters.filter(m=>m.model!==student&&m.roles.some(r=>['reasoning','research','critique','triage','coding'].includes(r))&&requiredBytes('ollama',m.size_bytes)+256*1024**2<=free()).sort((a,b)=>Number(['qwen3:0.6b','granite4:350m'].includes(a.model))-Number(['qwen3:0.6b','granite4:350m'].includes(b.model))||b.size_bytes-a.size_bytes);
 const model=eligible[0];if(!model)return {status:'deferred_memory'};
 try{const answers=await invoke(model,publicQuestions(qs));if(!(await catalog()).adapters.some(x=>x.model===model.model&&x.manifest_digest===model.manifest_digest))return {status:'deferred_identity'};return {status:'completed',lesson:makeLesson(model,domain,seed,answers)};}catch(e){return {status:'teacher_failed',reason:e.name};}
}
