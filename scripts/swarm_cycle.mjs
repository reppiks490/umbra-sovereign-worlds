/** Durable bounded worker dispatch; private state and immutable task receipts. */
import {join,resolve} from 'node:path';
import {mkdirSync,readFileSync,writeFileSync,existsSync,openSync,closeSync,unlinkSync,renameSync,lstatSync,readdirSync} from 'node:fs';
import {createSwarm,assignSwarm,recordOutcome,buildCurriculum} from '../mcp/megaswarm.mjs';
import {executeAgentTask,verifyTask,supportedDomains} from '../mcp/swarm_worker.mjs';
import {teach,verifyLesson} from '../mcp/swarm_teachers.mjs';
import {makeCorpus} from '../mcp/swarm_corpus.mjs';
import {learnSwarmPolicy,predictSwarmPolicy} from '../mcp/swarm_policy.mjs';
import {runResearch} from '../mcp/research_learning.mjs';
import {DOMAINS} from '../mcp/intelligence_gaps.mjs';
const [rootArg,mode='cycle']=process.argv.slice(2);
if(!rootArg||!['cycle','init','status'].includes(mode))throw Error('usage: swarm_cycle.mjs ROOT [init|cycle|status]');
const root=resolve(rootArg),dir=join(root,'megaswarm'),bank=join(dir,'receipts');
mkdirSync(bank,{recursive:true});
const lessonBank=join(dir,'lessons');mkdirSync(lessonBank,{recursive:true});
const lock=join(dir,'worker.lock');let fd;
try{fd=openSync(lock,'wx');}catch(e){if(e.code==='EEXIST'){console.log(JSON.stringify({status:'busy'}));process.exit(0);}throw e;}
function read(p,max){const st=lstatSync(p);if(!st.isFile()||st.isSymbolicLink()||st.size>max)throw Error('invalid file');return JSON.parse(readFileSync(p,'utf8'));}
function save(p,x){const tmp=p+'.'+process.pid+'.tmp';writeFileSync(tmp,JSON.stringify(x),{flag:'wx'});renameSync(tmp,p);}
try{
 let state=createSwarm(2048);
 const names=readdirSync(bank).filter(x=>/^[a-f0-9]{64}\.json$/.test(x)).sort();
 if(names.length>16384)throw Error('receipt capacity');
 const lessonNames=readdirSync(lessonBank).filter(x=>/^[a-f0-9]{64}\.json$/.test(x)).sort();
 if(lessonNames.length>4096)throw Error('lesson capacity');
 const lessons=lessonNames.map(n=>{const r=verifyLesson(read(join(lessonBank,n),32768));if(n!==r.evidence+'.json')throw Error('lesson identity');return r;});
 const lessonIds=new Set(lessons.map(l=>l.evidence));
 const tasks=new Set(),observations=[];
 for(const n of names){const r=verifyTask(read(join(bank,n),32768)),a=state.agents.find(x=>x.id===r.agent.id);if(n!==r.evidence+'.json'||!a||a.model!==r.agent.model||a.strategy!==r.agent.strategy||a.domain!==r.agent.domain)throw Error('identity mismatch');if((r.lesson_evidence??[]).some(id=>!lessonIds.has(id)))throw Error('missing teaching evidence');const k=r.agent.id+':'+r.seed;if(tasks.has(k))throw Error('duplicate task');tasks.add(k);observations.push(r);a.attempts++;a.wins+=Number(r.success);state.evidence.push(r.evidence);}
 const reportPath=join(root,'infinity','gaps','report.json');
 const gaps=existsSync(reportPath)?read(reportPath,8*1024**2).domains:DOMAINS.map(x=>({id:x.id,priority:x.weight}));
 const curriculum=buildCurriculum(gaps,Math.floor(Date.now()/1800000)%1000000||1,64);
 save(join(dir,'curriculum.json'),curriculum);
 const results=[];let teacher={status:'not_requested'};
 const policy=learnSwarmPolicy(observations.sort((a,b)=>a.seed-b.seed).slice(-512));
 if(mode==='cycle'){
  const seed=Math.floor(Date.now()/1800000);
  const trainSeed=700000000+seed;
  const domain=curriculum.find(c=>supportedDomains.includes(c.domain))?.domain;
  if(domain&&lessonNames.length<4096&&!lessons.some(l=>l.seed===trainSeed&&l.domain===domain)){
   const t=await teach(domain,trainSeed);teacher={status:t.status};
   if(t.lesson){const l=verifyLesson(t.lesson);writeFileSync(join(lessonBank,l.evidence+'.json'),JSON.stringify(l),{flag:'wx'});lessons.push(l);teacher={status:t.status,model:l.teacher,examples:l.examples.length,domain:l.domain};}
  }
  for(const family of ['qwen3:0.6b','granite4:350m']){
   const eligible=state.agents.filter(a=>a.model===family&&supportedDomains.includes(a.domain)&&!tasks.has(a.id+':'+seed));
   if(!eligible.length||state.evidence.length>=16384)break;
   const min=Math.min(...eligible.map(a=>a.attempts)),pool=eligible.filter(a=>a.attempts===min);
   const order=[...new Set(curriculum.map(c=>c.domain))];
   const a=pool.sort((a,b)=>order.indexOf(a.domain)-order.indexOf(b.domain)||((predictSwarmPolicy(policy,b,lessons.some(l=>l.domain===b.domain&&l.teacher!==b.model))??0)-(predictSwarmPolicy(policy,a,lessons.some(l=>l.domain===a.domain&&l.teacher!==a.model))??0))||a.id.localeCompare(b.id))[0];
   const r=await executeAgentTask(state,a.id,seed,{lessons});
   results.push({agent:a.id,model:a.model,domain:a.domain,status:r.status,correct:r.receipt?.correct,questions:r.receipt?.questions});
   if(r.receipt){const path=join(bank,r.receipt.evidence+'.json');writeFileSync(path,JSON.stringify(r.receipt),{flag:'wx'});state=r.state;tasks.add(a.id+':'+seed);observations.push(r.receipt);}
  }
 }
 const roundSeed=Math.floor(Date.now()/1800000)%1000000||1;
 const corpusDir=join(dir,'corpora');mkdirSync(corpusDir,{recursive:true});
 for(const family of ['qwen3:0.6b','granite4:350m'])save(join(corpusDir,family.replace(':','-')+'.json'),makeCorpus(family,lessons,roundSeed));
 const learning=learnSwarmPolicy(observations.sort((a,b)=>a.seed-b.seed).slice(-512));
 save(join(dir,'neural-policy.json'),learning);
 const research=runResearch(roundSeed);
 save(join(dir,'research.json'),research);
 save(join(dir,'population.json'),state);
 const status={status:'completed',mode,agents:state.agents.length,agents_per_family:state.per_family,executable_agents:state.agents.filter(a=>supportedDomains.includes(a.domain)).length,agents_with_outcomes:state.agents.filter(a=>a.attempts>0).length,verified_tasks:state.evidence.length,successful_tasks:state.agents.reduce((n,a)=>n+a.wins,0),results,teacher,neural_policy:learning.status,research:{continual_selected:research.continual.selected.name,retention_mse:research.continual.selected.retention_mse,transfer_mse:research.continual.selected.transfer_mse,forecast:research.forecast.selected,causal_effect:research.causal.effect,hypothesis:research.hypothesis.selected},verified_lessons:lessons.length,verified_examples:lessons.reduce((n,l)=>n+l.examples.length,0),independent_llm_weights:false,production_authority:false};
 save(join(dir,'status.json'),status);console.log(JSON.stringify(status));
}finally{closeSync(fd);unlinkSync(lock);}
