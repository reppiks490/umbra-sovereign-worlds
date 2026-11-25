/** Verified supervised examples from teachers and the generated benchmark engine. */
import {createHash} from 'node:crypto';
import {battery} from './intelligence_gaps.mjs';
import {verifyLesson} from './swarm_teachers.mjs';
import {solveProbe} from './gap_tools.mjs';
const hash=x=>createHash('sha256').update(x,'utf8').digest('hex');
const known=['arithmetic','logic','instruction_following','data_extraction'];
const transfer=['planning','code_tracing'];
export function makeCorpus(model,lessons,seed){
 if(!['qwen3:0.6b','granite4:350m'].includes(model)||!Array.isArray(lessons)||lessons.length>4096||!Number.isSafeInteger(seed)||seed<1||seed>1000000)throw Error('invalid corpus request');
 const seen=new Set(),training=[],retention=[],test=[];
 const add=(out,q,s,source,extra={})=>{
  if(solveProbe({id:q.id,prompt:q.prompt,options:q.options})!==q.correct)throw Error('independent symbolic verifier mismatch');
  const prompt_sha256=hash(q.prompt);if(seen.has(prompt_sha256))return;
  seen.add(prompt_sha256);out.push({prompt:q.prompt,answer:q.correct,options:q.options,domain:q.domain,seed:s,prompt_sha256,source,...extra});
 };
 for(const l of lessons.map(verifyLesson).filter(x=>x.teacher!==model).slice(-32)){
  for(const q of battery(l.seed).filter(q=>q.domain===l.domain&&l.examples.some(e=>e.prompt===q.prompt&&e.answer===q.correct))){if(training.length>=32)break;add(training,q,l.seed,'teacher',{teacher:l.teacher,teacher_digest:l.teacher_digest,lesson_evidence:l.evidence});}
 }
 const teacher_examples=training.length;
 for(let j=0;j<128&&training.length<64;j++){const s=seed*128+j;for(const q of battery(s).filter(q=>known.includes(q.domain)))if(training.length<64)add(training,q,s,'symbolic_verified');}
 for(let j=0;j<128&&retention.length<16;j++){const s=200000000+seed*128+j;for(const q of battery(s).filter(q=>known.includes(q.domain)))if(retention.length<16)add(retention,q,s,'held_out');}
 for(let j=0;j<128&&test.length<16;j++){const s=400000000+seed*128+j;for(const q of battery(s).filter(q=>transfer.includes(q.domain)))if(test.length<16)add(test,q,s,'held_out');}
 if(training.length<32||retention.length<8||test.length<8)throw Error('insufficient unique examples');
 return {schema:'umbra.swarm.corpus.v1',model,seed,training,retention,transfer:test,teacher_examples,synthetic:true,production_authority:false};
}
