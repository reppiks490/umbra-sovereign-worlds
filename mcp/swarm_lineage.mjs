/** Evidence-gated specialist lineage. A promotion is narrow synthetic competence, not AGI. */
import {createHash} from 'node:crypto';
import {createSwarm} from './megaswarm.mjs';
import {verifyTask,supportedDomains} from './swarm_worker.mjs';
import {swarmBattery as battery,levelOf,nextLevel,encodeLevel} from './swarm_difficulty.mjs';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const int=(x,a,b)=>Number.isSafeInteger(x)&&x>=a&&x<=b;
const assessment=r=>r.seed<200000000&&!r.lesson_evidence?.length;
const baseIdentity=a=>({id:a.id,model:a.model,domain:a.domain,strategy:a.strategy});
function checked(state,receipts){
 if(!Array.isArray(receipts)||receipts.length>16384)throw Error('lineage evidence budget');
 const byId=new Map(state.agents.map(a=>[a.id,a])),seen=new Set();
 return receipts.map(verifyTask).map(r=>{
  const a=byId.get(r.agent.id),k=r.agent.id+':'+r.seed;
  if(!a||hash(baseIdentity(a))!==hash(r.agent)||seen.has(k))throw Error('lineage evidence identity');
  seen.add(k);return r;
 });
}
function quality(rows){
 if(rows.length<24)return null;
 const highest=Math.max(...rows.map(r=>levelOf(r.seed)));
 const recent=rows.filter(r=>levelOf(r.seed)===highest).sort((a,b)=>a.seed-b.seed).slice(-24);
 if(recent.length<24)return null;
 if(new Set(recent.map(r=>r.model_digest)).size!==1)return null;
 const prompts=new Map();
 for(const r of recent)for(const a of r.rows){
  const q=battery(r.seed).find(q=>q.id===a.id);
  const h=hash(q.prompt);
  if(!prompts.has(h))prompts.set(h,a.correct);
  else if(!a.correct)prompts.set(h,false);
 }
 const successes=[...prompts.values()].filter(Boolean).length,n=prompts.size;
 const highErrors=recent.flatMap(r=>r.rows).filter(x=>!x.correct&&x.confidence===95).length;
 if(n<32||successes/n<.9||recent.filter(r=>r.success).length<22||highErrors>2)return null;
 return {agent:recent[0].agent.id,model:recent[0].agent.model,domain:recent[0].agent.domain,strategy:recent[0].agent.strategy,model_digest:recent[0].model_digest,level:highest,assessments:recent.length,unique_prompts:n,accuracy:successes/n,proof:recent.map(r=>r.evidence),scope:'generated specialist tasks only'};
}
export function qualifyTeachers(state,receipts){
 const groups=new Map();
 for(const r of checked(state,receipts).filter(assessment)){if(!groups.has(r.agent.id))groups.set(r.agent.id,[]);groups.get(r.agent.id).push(r);}
 return [...groups.values()].map(rows=>{for(let l=10;l>=1;l--){const q=quality(rows.filter(r=>levelOf(r.seed)===l));if(q)return q;}return null;}).filter(Boolean).sort((a,b)=>a.agent.localeCompare(b.agent));
}
export function emptyLineage(perFamily=2048){
 if(!int(perFamily,128,5000)||perFamily%128!==0)throw Error('invalid starting cohort');
 return {schema:'umbra.swarm.lineage.v1',initial_per_family:perFamily,per_family:perFamily,births:[],teachers:[],production_authority:false,parity_7b_general_verified:false};
}
export function evolveLineage(previous,state,receipts,cap=4992){
 if(previous?.schema!=='umbra.swarm.lineage.v1'||!int(previous.initial_per_family,128,5000)||previous.initial_per_family%128||!int(cap,previous.initial_per_family,5000)||!Array.isArray(previous.births)||previous.births.length>40||previous.per_family!==previous.initial_per_family+128*previous.births.length||state.per_family!==previous.per_family)throw Error('invalid lineage ledger');
 const rows=checked(state,receipts),byProof=new Map(rows.map(r=>[r.evidence,r])),parents=new Set(),children=new Set();
 for(const [i,b] of previous.births.entries()){
  const limit=previous.initial_per_family+128*i,parent=state.agents.find(a=>a.id===b.parent);
  if(!parent||Number(parent.id.slice(3))>=limit||parents.has(b.parent)||children.has(b.child)||!Array.isArray(b.proof)||b.proof.length!==24||new Set(b.proof).size!==24)throw Error('invalid birth history');
  const evidence=b.proof.map(x=>byProof.get(x));
  if(evidence.some(r=>!r||r.agent.id!==b.parent||!assessment(r))||!quality(evidence))throw Error('unverified birth');
  const childId='F'+(parent.id[1]==='0'?1:0)+'-'+String(limit+Number(parent.id.slice(3))%128).padStart(4,'0');
  if(b.child!==childId||b.generation!==(previous.births.find(x=>x.child===b.parent)?.generation??0)+1)throw Error('invalid descendant');
  parents.add(b.parent);children.add(b.child);
 }
 const teachers=qualifyTeachers(state,rows),births=structuredClone(previous.births);
 const mentor=teachers.find(t=>!parents.has(t.agent));
 let count=previous.per_family;
 if(mentor&&count+128<=cap){
  const child='F'+(mentor.agent[1]==='0'?1:0)+'-'+String(count+Number(mentor.agent.slice(3))%128).padStart(4,'0');
  births.push({parent:mentor.agent,child,generation:(births.find(x=>x.child===mentor.agent)?.generation??0)+1,proof:mentor.proof});
  count+=128;
 }
 return {...emptyLineage(previous.initial_per_family),per_family:count,births,teachers,capacity_reached:count+128>cap};
}
export function selectApprentice(state,receipts,family,domain,seed,teachers=[],births=[]){
 if(!supportedDomains.includes(domain)||!int(seed,1,19999999))throw Error('invalid assessment lane');
 const groups=new Map(),tasks=new Set(),children=new Set(births.map(b=>b.child));
 for(const r of receipts){tasks.add(r.agent.id+':'+r.seed);if(assessment(r)){const rows=groups.get(r.agent.id)??[];rows.push(r);groups.set(r.agent.id,rows);}}
 const candidates=state.agents.filter(a=>a.model===family&&a.domain===domain).map(a=>{
  const history=groups.get(a.id)??[],level=nextLevel(history),rows=history.filter(r=>levelOf(r.seed)===level);
  return {a,level,attempts:rows.length,success:rows.filter(r=>r.success).length,seed:encodeLevel(seed,level)};
 }).filter(x=>!tasks.has(x.a.id+':'+x.seed)&&x.attempts<32);
 candidates.sort((a,b)=>Number(children.has(b.a.id))-Number(children.has(a.a.id))||Number(b.attempts>0)-Number(a.attempts>0)||b.level-a.level||b.attempts-a.attempts||b.success-a.success||a.a.id.localeCompare(b.a.id));
 return candidates[0]?.a??null;
}
export function trainingBoost(last){
 const ok=last?.status==='evaluated'&&last.accepted===true&&last.adapter_weight_training===true&&[4,8,16].includes(last.steps);
 return {steps:ok?Math.min(16,last.steps*2):4,rank:4,scope:'optimizer step budget only; base parameter count unchanged'};
}
