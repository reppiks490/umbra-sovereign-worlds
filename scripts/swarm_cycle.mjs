/** Durable bounded worker dispatch; private state and immutable task receipts. */
import {join,resolve} from 'node:path';
import {mkdirSync,readFileSync,writeFileSync,existsSync,openSync,closeSync,unlinkSync,renameSync,lstatSync,readdirSync} from 'node:fs';
import {createSwarm,buildCurriculum} from '../mcp/megaswarm.mjs';
import {executeAgentTask,verifyTask,supportedDomains} from '../mcp/swarm_worker.mjs';
import {nextLevel,encodeLevel,levelOf} from '../mcp/swarm_difficulty.mjs';
import {REFERENCE,nextReferenceTask,referenceReport,runReference} from '../mcp/swarm_reference.mjs';
import {emptyLineage,evolveLineage,selectApprentice} from '../mcp/swarm_lineage.mjs';
import {teach,verifyLesson,makeLesson} from '../mcp/swarm_teachers.mjs';
import {makeCorpus} from '../mcp/swarm_corpus.mjs';
import {learnSwarmPolicy} from '../mcp/swarm_policy.mjs';
import {runResearch} from '../mcp/research_learning.mjs';
import {buildRegistry,attachRegistry,mergeInventories} from '../mcp/repository_fabric.mjs';
import {DOMAINS} from '../mcp/intelligence_gaps.mjs';
const [rootArg,mode='cycle']=process.argv.slice(2);
if(!rootArg||!['cycle','init','status'].includes(mode))throw Error('usage: swarm_cycle.mjs ROOT [init|cycle|status]');
const root=resolve(rootArg),dir=join(root,'megaswarm'),bank=join(dir,'receipts');
mkdirSync(bank,{recursive:true});
const lessonBank=join(dir,'lessons');mkdirSync(lessonBank,{recursive:true});
const refBank=join(dir,'reference-7b');mkdirSync(refBank,{recursive:true});
const lock=join(dir,'worker.lock');let fd;
try{fd=openSync(lock,'wx');}catch(e){if(e.code==='EEXIST'){console.log(JSON.stringify({status:'busy'}));process.exit(0);}throw e;}
function read(p,max){const st=lstatSync(p);if(!st.isFile()||st.isSymbolicLink()||st.size>max)throw Error('invalid file');return JSON.parse(readFileSync(p,'utf8'));}
function save(p,x){const tmp=p+'.'+process.pid+'.tmp';writeFileSync(tmp,JSON.stringify(x),{flag:'wx'});renameSync(tmp,p);}
try{
 const lineageFile=join(dir,'lineage.json');
 let lineage=existsSync(lineageFile)?read(lineageFile,2*1024**2):emptyLineage(2048);
 let state=createSwarm(lineage.per_family);
 const names=readdirSync(bank).filter(x=>/^[a-f0-9]{64}\.json$/.test(x)).sort();
 if(names.length>16384)throw Error('receipt capacity');
 const lessonNames=readdirSync(lessonBank).filter(x=>/^[a-f0-9]{64}\.json$/.test(x)).sort();
 if(lessonNames.length>4096)throw Error('lesson capacity');
 const lessons=lessonNames.map(n=>{const r=verifyLesson(read(join(lessonBank,n),32768));if(n!==r.evidence+'.json')throw Error('lesson identity');return r;});
 const lessonIds=new Set(lessons.map(l=>l.evidence));
 const refNames=readdirSync(refBank).filter(n=>/^[a-f0-9]{64}\.json$/.test(n));
 if(refNames.length>16384)throw Error('reference capacity');
 const refs=refNames.map(n=>{const r=verifyLesson(read(join(refBank,n),32768));if(n!==r.evidence+'.json'||r.teacher!==REFERENCE)throw Error('reference identity');return r;});
 const tasks=new Set(),observations=[];
 for(const n of names){const r=verifyTask(read(join(bank,n),32768)),a=state.agents.find(x=>x.id===r.agent.id);if(n!==r.evidence+'.json'||!a||a.model!==r.agent.model||a.strategy!==r.agent.strategy||a.domain!==r.agent.domain)throw Error('identity mismatch');if((r.lesson_evidence??[]).some(id=>!lessonIds.has(id)))throw Error('missing teaching evidence');const k=r.agent.id+':'+r.seed;if(tasks.has(k))throw Error('duplicate task');tasks.add(k);observations.push(r);a.attempts++;a.wins+=Number(r.success);state.evidence.push(r.evidence);}
 lineage=evolveLineage(lineage,state,observations);
 if(lineage.per_family!==state.per_family){const old=state;state=createSwarm(lineage.per_family);const history=new Map(old.agents.map(a=>[a.id,a]));for(const a of state.agents){const b=history.get(a.id);if(b){a.wins=b.wins;a.attempts=b.attempts;}}state.evidence=old.evidence;}
 save(lineageFile,lineage);
 const reportPath=join(root,'infinity','gaps','report.json');
 const gaps=existsSync(reportPath)?read(reportPath,8*1024**2).domains:DOMAINS.map(x=>({id:x.id,priority:x.weight}));
 const curriculum=buildCurriculum(gaps,Math.floor(Date.now()/1800000)%1000000||1,64);
 save(join(dir,'curriculum.json'),curriculum);
 const results=[];let teacher={status:'not_requested'},reference={status:'audit_only',model:REFERENCE};
 if(mode==='cycle'){
  const seed=Math.floor(Date.now()/1800000);

  const lanes=[...new Set(curriculum.map(c=>c.domain).filter(d=>supportedDomains.includes(d)))];
  const domain=lanes[seed%lanes.length];
  const apprentices=['qwen3:0.6b','granite4:350m'].map(f=>selectApprentice(state,observations,f,domain,seed,lineage.teachers,lineage.births)).filter(Boolean);
  const currentLevel=a=>nextLevel(observations.filter(r=>r.agent.id===a.id));
  const trainLevel=Math.max(1,...apprentices.map(currentLevel));
  const trainSeed=700000000+encodeLevel(seed,trainLevel);
  if(domain&&lessonNames.length<4096&&!lessons.some(l=>l.seed===trainSeed&&l.domain===domain)){
   const mentor=lineage.teachers.find(t=>t.domain===domain&&t.level>=trainLevel&&!tasks.has(t.agent+':'+trainSeed));
   let t;
   if(mentor&&state.evidence.length<16384){
    const r=await executeAgentTask(state,mentor.agent,trainSeed);
    if(r.receipt){
     writeFileSync(join(bank,r.receipt.evidence+'.json'),JSON.stringify(r.receipt),{flag:'wx'});
     state=r.state;tasks.add(mentor.agent+':'+trainSeed);observations.push(r.receipt);
     if(r.receipt.model_digest===mentor.model_digest)t={status:'completed',mentor:mentor.agent,lesson:makeLesson({model:mentor.model,manifest_digest:mentor.model_digest},domain,trainSeed,r.receipt.rows)};
     else t={status:'deferred_teacher_identity'};
    }else t={status:r.status};
   }else t=await teach(domain,trainSeed);
   teacher={status:t.status,...(t.mentor?{mentor:t.mentor}:{})};
   if(t.lesson){const l=verifyLesson(t.lesson);writeFileSync(join(lessonBank,l.evidence+'.json'),JSON.stringify(l),{flag:'wx'});lessons.push(l);teacher={status:t.status,model:l.teacher,examples:l.examples.length,domain:l.domain,...(t.mentor?{mentor:t.mentor}:{})};}
  }
  for(const family of ['qwen3:0.6b','granite4:350m']){
   if(state.evidence.length>=16384)break;
   const a=apprentices.find(a=>a.model===family);
   if(!a)continue;
   // Two unassisted assessment cycles per guided cycle; the same slot remains in focus.
   const guided=Math.floor(seed/Math.max(1,lanes.length))%3===0;
   const r=await executeAgentTask(state,a.id,encodeLevel(seed,currentLevel(a)),{lessons:guided?lessons.filter(l=>levelOf(l.seed)===currentLevel(a)):[]});
   results.push({agent:a.id,model:a.model,domain:a.domain,level:currentLevel(a),status:r.status,correct:r.receipt?.correct,questions:r.receipt?.questions});
   if(r.receipt){const path=join(bank,r.receipt.evidence+'.json');writeFileSync(path,JSON.stringify(r.receipt),{flag:'wx'});state=r.state;tasks.add(a.id+':'+r.receipt.seed);observations.push(r.receipt);}
  }
  if(!existsSync(join(root,'active.lock'))){
   const pending=nextReferenceTask(observations,refs);
   if(pending&&refs.length<16384){
    const r=await runReference(pending);reference={status:r.status,model:REFERENCE,seed:pending.seed,domain:pending.agent.domain};
    if(r.lesson){const l=verifyLesson(r.lesson);if(l.teacher!==REFERENCE)throw Error('reference substitution');writeFileSync(join(refBank,l.evidence+'.json'),JSON.stringify(l),{flag:'wx'});refs.push(l);}
   }else reference={status:'no_pending_pairs',model:REFERENCE};
  }else reference={status:'deferred_acquisition',model:REFERENCE};
 }
 const referenceSummary=referenceReport(observations,refs),parity=referenceSummary.agents;
 save(join(dir,'reference-report.json'),referenceSummary);
 const roundSeed=Math.floor(Date.now()/1800000)%1000000||1;
 const corpusDir=join(dir,'corpora');mkdirSync(corpusDir,{recursive:true});
 for(const family of ['qwen3:0.6b','granite4:350m'])save(join(corpusDir,family.replace(':','-')+'.json'),makeCorpus(family,lessons,roundSeed,Math.max(1,...state.agents.filter(a=>a.model===family&&a.attempts>0).map(a=>nextLevel(observations.filter(r=>r.agent.id===a.id))))));
 const learning=learnSwarmPolicy(observations.sort((a,b)=>a.seed-b.seed).slice(-512));
 save(join(dir,'neural-policy.json'),learning);
 const research=runResearch(roundSeed);
 save(join(dir,'research.json'),research);
 const localInventory=join(root,'local-source-inventory.json');
 if(existsSync(localInventory)){
  const wsl=join(root,'wsl-source-inventory.json'),archives=join(root,'local-source-archives.json');
  state=attachRegistry(state,buildRegistry(mergeInventories(read(localInventory,32*1024**2),existsSync(wsl)?read(wsl,32*1024**2):null,existsSync(archives)?read(archives,32*1024**2):null)));
 }
 save(join(dir,'population.json'),state);
 const status={status:'completed',mode,agents:state.agents.length,agents_per_family:state.per_family,executable_agents:state.agents.filter(a=>supportedDomains.includes(a.domain)).length,agents_with_outcomes:state.agents.filter(a=>a.attempts>0).length,verified_tasks:state.evidence.length,successful_tasks:state.agents.reduce((n,a)=>n+a.wins,0),results,teacher,reference:{...reference,receipts:refs.length,specialist_matches:parity.filter(x=>x.status==='matched_on_specialist_probes').length,general_reasoning_verified:false},lineage:{teachers:lineage.teachers.length,births:lineage.births.length,max_observed_level:Math.max(1,...observations.filter(r=>r.seed<200000000).map(r=>levelOf(r.seed))),capacity_reached:lineage.capacity_reached,parity_7b_general_verified:false},neural_policy:learning.status,research:{continual_selected:research.continual.selected.name,retention_mse:research.continual.selected.retention_mse,transfer_mse:research.continual.selected.transfer_mse,forecast:research.forecast.selected,causal_effect:research.causal.effect,hypothesis:research.hypothesis.selected},verified_lessons:lessons.length,verified_examples:lessons.reduce((n,l)=>n+l.examples.length,0),repository_registry:state.repository_registry??null,repository_locations:state.agents[0]?.repository_count??0,independent_llm_weights:false,production_authority:false};
 save(join(dir,'status.json'),status);console.log(JSON.stringify(status));
}finally{closeSync(fd);unlinkSync(lock);}
