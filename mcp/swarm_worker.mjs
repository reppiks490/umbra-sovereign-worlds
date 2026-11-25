import {solveAdvanced} from './swarm_verifier.mjs';
/** Small-model worker; one admitted inference at a time, independently graded. */
import {createHash} from 'node:crypto';
import {freemem} from 'node:os';
import {availableAdapters,ollamaBusy} from './local_model_adapters.mjs';
import {requiredBytes} from './polymind_admission.mjs';
import {publicQuestions} from './intelligence_gaps.mjs';
import {swarmBattery as battery} from './swarm_difficulty.mjs';
import {buildProbeRequest,parseProbeBatch} from './gap_probe.mjs';
import {verifyLesson,lessonContext} from './swarm_teachers.mjs';
import {recordOutcome} from './megaswarm.mjs';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const tactics={direct:'Answer directly.',decompose:'Break the problem into small steps internally.',constraint_check:'Check all constraints before answering.',counterexample:'Test alternatives for counterexamples.',retrieve:'Recall relevant rules before answering.',abstain:'Check whether information is sufficient.',compare:'Compare every listed option.',verify:'Recheck the calculation or logic.'};
export const supportedDomains=Object.freeze([...new Set(battery(1).map(x=>x.domain))]);
function taskQuestions(seed,domain){const q=battery(seed).filter(x=>x.domain===domain);if(!q.length)throw Error('unimplemented task domain');return q;}
function receiptFor(agent,model,seed,answers,lessonIds=[]){
 if(!agent||!/^F[01]-\d{4}$/.test(agent.id)||!Object.hasOwn(tactics,agent.strategy)||!['qwen3:0.6b','granite4:350m'].includes(agent.model)||model.model!==agent.model||!hex(model.manifest_digest))throw Error('invalid worker identity');
 const questions=taskQuestions(seed,agent.domain);
 if(!Array.isArray(answers)||answers.length!==questions.length||new Set(answers.map(x=>x.id)).size!==questions.length)throw Error('invalid answers');
 const rows=questions.map(q=>{if(solveAdvanced({id:q.id,prompt:q.prompt,options:q.options})!==q.correct)throw Error('independent verifier disagreement');const a=answers.find(x=>x.id===q.id);if(!a||!q.options.includes(a.answer)||![50,75,95].includes(a.confidence))throw Error('invalid answer');return {id:q.id,answer:a.answer,confidence:a.confidence,correct:a.answer===q.correct};});
 if(!Array.isArray(lessonIds)||lessonIds.length>2||new Set(lessonIds).size!==lessonIds.length||!lessonIds.every(hex))throw Error('invalid lesson references');
 const r={schema:'umbra.swarm.task.v1',agent:{id:agent.id,model:agent.model,domain:agent.domain,strategy:agent.strategy},model_digest:model.manifest_digest,seed,rows,success:rows.every(x=>x.correct),correct:rows.filter(x=>x.correct).length,questions:rows.length,...(lessonIds.length?{lesson_evidence:lessonIds}:{}),production_authority:false,synthetic:true};return {...r,evidence:hash(r)};
}
export function verifyTask(r){const b=receiptFor(r?.agent,{model:r?.agent?.model,manifest_digest:r?.model_digest},r?.seed,r?.rows,r?.lesson_evidence??[]);if(hash(b)!==hash(r))throw Error('task receipt mismatch');return b;}
async function liveInvoke(model,qs,agent,context){
 const body=buildProbeRequest(model,qs);body.prompt=tactics[agent.strategy]+' '+(context.length?'Verified prior examples (not current answers): '+JSON.stringify(context)+' ':'')+body.prompt;
 const r=await fetch('http://127.0.0.1:11434/api/generate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body),redirect:'error',signal:AbortSignal.timeout(60000)});
 if(!r.ok||!r.body)throw Error('runtime unavailable');
 const reader=r.body.getReader(),chunks=[];let n=0;
 try{for(;;){const x=await reader.read();if(x.done)break;n+=x.value.byteLength;if(n>1024**2)throw Error('response budget');chunks.push(Buffer.from(x.value));}}finally{await reader.cancel().catch(()=>{});}
 const out=JSON.parse(Buffer.concat(chunks).toString('utf8'));if(out.model!==model.model||out.done!==true||!Number.isSafeInteger(out.eval_count)||out.eval_count<1||out.eval_count>240)throw Error('unverified generation');
 return parseProbeBatch(out.response,qs);
}
export async function executeAgentTask(state,id,seed,{catalog=availableAdapters,free=freemem,busy=ollamaBusy,invoke=liveInvoke,lessons=[]}={}){
 const agent=state.agents.find(x=>x.id===id);if(!agent)throw Error('unknown agent');
 const qs=taskQuestions(seed,agent.domain);
 if(await busy())return {status:'deferred_busy',state};
 const model=(await catalog()).adapters.find(x=>x.model===agent.model);if(!model)return {status:'deferred_inventory',state};
 if(requiredBytes('ollama',model.size_bytes)+256*1024**2>free())return {status:'deferred_memory',state};
 const selected=lessons.map(verifyLesson).filter(x=>x.teacher!==agent.model&&x.teacher_digest!==model.manifest_digest&&x.domain===agent.domain&&x.seed!==seed&&x.examples.length).slice(-2);
 const context=lessonContext(selected,{...agent,model_digest:model.manifest_digest},seed).filter(x=>!qs.some(q=>q.prompt===x.prompt));
 let answers;try{answers=await invoke(model,publicQuestions(qs),agent,context);}catch(e){return {status:'inference_failed',reason:e.name,state};}
 if(!(await catalog()).adapters.some(x=>x.model===model.model&&x.manifest_digest===model.manifest_digest))return {status:'deferred_identity',state};
 const receipt=receiptFor(agent,model,seed,answers,context.length?selected.filter(l=>l.examples.some(e=>context.some(c=>c.prompt===e.prompt&&c.answer===e.answer))).map(l=>l.evidence):[]);
 return {status:'completed',receipt,state:recordOutcome(state,{agent:id,domain:agent.domain,success:receipt.success,evidence:receipt.evidence})};
}
