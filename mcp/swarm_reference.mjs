/** Paired specialist benchmark against an installed 7B coding model; not general reasoning equivalence. */
import {verifyTask} from './swarm_worker.mjs';
import {verifyLesson,teach} from './swarm_teachers.mjs';
import {swarmBattery as battery,levelOf,nextLevel,encodeLevel} from './swarm_difficulty.mjs';
export const REFERENCE='qwen2.5-coder:7b';
function inputs(tasks,refs){
 if(!Array.isArray(tasks)||tasks.length>16384||!Array.isArray(refs)||refs.length>16384)throw Error('reference evidence budget');
 const rows=tasks.map(verifyTask),seen=new Set();
 for(const r of rows){const k=r.agent.id+':'+r.seed;if(seen.has(k))throw Error('duplicate assessment');seen.add(k);}
 const map=new Map();
 for(const raw of refs){const r=verifyLesson(raw),k=r.domain+':'+r.seed;if(r.teacher!==REFERENCE||map.has(k))throw Error('invalid reference identity');map.set(k,r);}
 return {rows:rows.filter(r=>r.seed<200000000&&!r.lesson_evidence?.length),map};
}
export function nextReferenceTask(tasks,refs){
 const {rows,map}=inputs(tasks,refs);return rows.filter(r=>!map.has(r.agent.domain+':'+r.seed)).sort((a,b)=>a.seed-b.seed||a.agent.id.localeCompare(b.agent.id))[0]??null;
}
function summarize(rows,map,agent){
 const pairs=rows.filter(r=>r.agent.id===agent&&map.has(r.agent.domain+':'+r.seed)).map(r=>({student:r,reference:map.get(r.agent.domain+':'+r.seed)})).sort((a,b)=>a.student.seed-b.student.seed).slice(-24);
 const highest=pairs.length?Math.max(...pairs.map(x=>levelOf(x.student.seed))):1;
 const same=pairs.filter(x=>levelOf(x.student.seed)===highest);
 const out={agent,reference:REFERENCE,level:highest,pairs:same.length,general_reasoning_verified:false,production_authority:false};
 if(!same.length)return {...out,status:'unmeasured'};
 if(new Set(same.map(x=>x.student.model_digest)).size!==1||new Set(same.map(x=>x.reference.teacher_digest)).size!==1)return {...out,status:'identity_changed'};
 const prompts=new Set(),diff=[];
 for(const {student,reference} of same){for(const q of battery(student.seed).filter(q=>q.domain===student.agent.domain))prompts.add(q.prompt);diff.push((student.correct-reference.rows.filter(r=>r.correct).length)/student.questions);}
 const delta=diff.reduce((s,x)=>s+x,0)/diff.length;
 const status=same.length<24||prompts.size<32?'insufficient_pairs':delta>=0?'matched_on_specialist_probes':'below_reference';
 return {...out,status,domain:same[0].student.agent.domain,unique_prompts:prompts.size,mean_paired_delta:delta,student_digest:same[0].student.model_digest,reference_digest:same[0].reference.teacher_digest,scope:'exact paired synthetic multiple-choice probes; descriptive comparison only'};
}
export function referenceParity(tasks,refs,agent){const {rows,map}=inputs(tasks,refs);return summarize(rows,map,agent);}
export function referenceReport(tasks,refs){
 const {rows,map}=inputs(tasks,refs),groups=new Map();
 for(const r of rows){if(!groups.has(r.agent.id))groups.set(r.agent.id,[]);groups.get(r.agent.id).push(r);}
 const agents=[...groups].map(([id,rs])=>summarize(rs,map,id));
 return {target:REFERENCE,reference_receipts:refs.length,agents,general_reasoning_verified:false,production_authority:false};
}
export async function runReference(task){
 const t=verifyTask(task);if(t.seed>=200000000||t.lesson_evidence?.length)throw Error('not independent assessment');
 return teach(t.agent.domain,t.seed,{reference:REFERENCE});
}
