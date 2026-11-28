/** Evidence-driven capability audit; bounded generated probes, not a general intelligence certificate. */
import {createHash} from 'node:crypto';
import {requiredBytes} from './polymind_admission.mjs';
const sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const int=(x,a,b)=>Number.isSafeInteger(x)&&x>=a&&x<=b;
const mean=x=>x.length?x.reduce((a,b)=>a+b,0)/x.length:null;
const defs=[
 ['arithmetic',1.0,['text-generation','text2text-generation'],'numeric tool or reasoning adapter'],
 ['logic',1.0,['text-generation','text2text-generation'],'symbolic checker plus reasoning model'],
 ['planning',1.0,['text-generation','text2text-generation'],'constraint planner and independent verifier'],
 ['causality',1.0,['text-generation','question-answering'],'causal experiment design and statistical verifier'],
 ['code_tracing',.9,['text-generation','text2text-generation'],'sandboxed code benchmark and coding adapter'],
 ['data_extraction',.8,['token-classification','question-answering','text-generation'],'structured extraction adapter'],
 ['instruction_following',1.0,['text-generation','text2text-generation'],'strict schemas and independent validation'],
 ['abstention',1.0,['text-generation','question-answering'],'uncertainty calibration and explicit abstention'],
 ['policy_selection',1.0,['text-generation','reinforcement-learning'],'counterfactual simulator and baseline comparator'],
 ['retrieval',.9,['feature-extraction','sentence-similarity','text-ranking'],'native embedding or reranking adapter'],
 ['forecasting',.8,['time-series-forecasting'],'rolling-origin temporal evaluation'],
 ['vision',.7,['image-classification','image-feature-extraction','object-detection'],'image runtime and labeled holdout'],
 ['audio',.6,['automatic-speech-recognition','audio-classification'],'audio runtime and labeled holdout'],
 ['continual_learning',1.0,[],'temporal replay, retention and forgetting evaluation'],
 ['tool_execution',1.0,[],'bounded tool sandbox with outcome verification'],
 ['cross_domain_transfer',.9,[],'disjoint domain and distribution-shift evaluation']
];
export const DOMAINS=Object.freeze(defs.map(([id,weight,tags,remediation])=>Object.freeze({id,weight,tags:Object.freeze(tags),remediation})));
function rng(seed){let x=seed>>>0;return n=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)%n;};}
export function battery(seed){
 if(!int(seed,1,1e9))throw Error('invalid benchmark seed');
 const next=rng(seed),out=[];
 const add=(domain,prompt,correct,distractors)=>{
  const options=[correct,...distractors].map(String);
  if(new Set(options).size!==4)throw Error('invalid generated options');
  for(let i=options.length-1;i>0;i--){const j=next(i+1);[options[i],options[j]]=[options[j],options[i]];}
  out.push({id:'q'+(out.length+1),domain,prompt,options,correct:String(correct)});
 };
 for(let i=0;i<2;i++){
  const a=next(39)+12,b=next(13)+3,c=next(12)+2;
  const answer=a*b-c;
  add('arithmetic','Compute '+a+' * '+b+' - '+c+'.',answer,[answer+1,answer+c,answer-b]);
  const colors=['red','blue','green','gold'],first=colors[next(4)],second=colors[(colors.indexOf(first)+1)%4];
  add('logic','All dax are '+first+'. No '+first+' object is '+second+'. Item T is a dax. Which statement must be true?', 'T is not '+second,['T is '+second,'T is not '+first,'No dax exist']);
  const tasks=['K','M','P','R'];const shift=next(4);const [u,v,w,z]=tasks.slice(shift).concat(tasks.slice(0,shift));
  add('planning','Finish '+u+' before '+v+'; '+v+' before '+w+'; '+z+' after '+w+'. Which order is valid?',u+v+w+z,[v+u+w+z,u+w+v+z,z+u+v+w]);
  const trial=next(40)+30;
  add('causality','A controlled randomized trial assigns '+trial+' participants per group. What design feature most directly reduces pre-treatment confounding?', 'random assignment',['choosing the largest observed effect','using only treated participants','discarding unfavorable outcomes']);
  const k=next(6)+2,l=next(7)+2,m=next(5)+1,val=k+l*(l+1)/2*m;
  add('code_tracing','Pseudocode: x='+k+'; for j=1 through '+l+' inclusive: x=x+j*'+m+'; return x. What returns?',val,[val+1,val-m,val+l*m]);
  const x=next(40)+10,y=next(40)+60;
  add('data_extraction','Record: id=A'+a+', available='+x+', reserved='+y+', units=kg. Return the reserved integer only.',y,[x,y+1,y-1]);
  const n=next(5)+2,base=next(30)+10;
  add('instruction_following','Select the option containing exactly '+n+' repetitions of the letter X followed by the number '+base+'.','X'.repeat(n)+base,['X'.repeat(n+1)+base,'X'.repeat(n)+(base+1),'X'.repeat(n-1)+base]);
  add('abstention','A sealed container has an unknown number of coins. No other evidence is provided. How many coins are inside?','insufficient evidence',[String(next(10)+1),String(next(10)+11),String(next(10)+21)]);
 }
 return out;
}
export const publicQuestions=b=>b.map(({id,prompt,options})=>({id,prompt,options}));
function validateModel(m){
 if(!m||typeof m.model!=='string'||!/^[A-Za-z0-9_.:/-]{1,200}$/.test(m.model)||!hex(m.manifest_digest))throw Error('invalid model identity');
 return {model:m.model,manifest_digest:m.manifest_digest};
}
export function grade(seed,model,answers){
 const m=validateModel(model),b=battery(seed);
 if(!Array.isArray(answers)||answers.length!==b.length||new Set(answers.map(a=>a?.id)).size!==b.length)throw Error('invalid answer count');
 const rows=b.map(q=>{
  const a=answers.find(x=>x?.id===q.id);
  if(!a||Object.keys(a).sort().join(',')!=='answer,confidence,id'||!q.options.includes(a.answer)||![50,75,95].includes(a.confidence))throw Error('invalid answer');
  return {id:q.id,domain:q.domain,answer:a.answer,confidence:a.confidence,correct:a.answer===q.correct};
 });
 const r={schema:'umbra.gaps.probe.v1',seed,...m,rows,correct:rows.filter(x=>x.correct).length,high_confidence_errors:rows.filter(x=>!x.correct&&x.confidence===95).length,brier:mean(rows.map(x=>(x.confidence/100-Number(x.correct))**2)),synthetic:true,production_authority:false};
 return {...r,receipt_sha256:sha(r)};
}
export function verifyReceipt(r){
 const rebuilt=grade(r?.seed,r,r?.rows?.map(({id,answer,confidence})=>({id,answer,confidence})));
 if(sha(rebuilt)!==sha(r))throw Error('probe receipt mismatch');return rebuilt;
}
function interval(k,n){
 if(!n)return [null,null];const p=k/n,z=1.96,den=1+z*z/n,mid=(p+z*z/(2*n))/den,half=z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;
 return [Math.max(0,mid-half),Math.min(1,mid+half)];
}
function summarize(id,items,weight,remediation){
 const n=items.length,k=items.filter(Boolean).length,p=n?k/n:null,[lower,upper]=interval(k,n);
 const status=n===0?'unmeasured':n<8?(p<.8?'tentative_gap':'limited_evidence'):upper<.8?'measured_gap':lower>=.8?'strong_probe_evidence':'uncertain';
 return {id,status,observations:n,successes:k,accuracy:p,lower95:lower,upper95:upper,priority:weight*(n===0?.85:Math.min(1,Math.max(0,.8-p)+.5*(upper-lower))),remediation};
}
export function assessGaps({receipts=[],policy=[],nativeProfiles=[]}={}){
 if(!Array.isArray(receipts)||receipts.length>256||!Array.isArray(policy)||policy.length>512||!Array.isArray(nativeProfiles)||nativeProfiles.length>512)throw Error('audit budget');
 const verified=receipts.map(verifyReceipt),ids=new Set();
 for(const r of verified){const id=r.manifest_digest+':'+r.seed;if(ids.has(id))throw Error('duplicate benchmark seed/model');ids.add(id);}
 const domains=DOMAINS.map(d=>{
  const rows=verified.flatMap(r=>r.rows.filter(x=>x.domain===d.id).map(x=>({digest:r.manifest_digest,correct:x.correct})));
  const groups=new Map();for(const r of rows){if(!groups.has(r.digest))groups.set(r.digest,[]);groups.get(r.digest).push(r.correct);}
  const model_results=[...groups.entries()].map(([digest,items])=>({digest,...summarize(d.id,items,d.weight,d.remediation)})).sort((a,b)=>b.lower95-a.lower95||b.observations-a.observations);
  let items=model_results.length?groups.get(model_results[0].digest):[];
  if(d.id==='policy_selection'){
   const seen=new Set();items=policy.map(p=>{if(!p||!hex(p.mission_id)||seen.has(p.mission_id)||!Number.isFinite(p.regret)||p.regret<0)throw Error('invalid policy evidence');seen.add(p.mission_id);return p.regret<1e-9;});
  }
  if(d.id==='retrieval'){
   const eligible=nativeProfiles.filter(p=>p&&hex(p.digest)&&int(p.cases,1,100)&&Number.isFinite(p.score)&&p.score>=0&&p.score<=1&&Math.abs(p.score*p.cases-Math.round(p.score*p.cases))<1e-8&&['qualified','rejected'].includes(p.status));
   const best=eligible.sort((a,b)=>b.score-a.score||b.cases-a.cases)[0];
   if(best)items=Array.from({length:best.cases},(_,i)=>i<Math.round(best.score*best.cases));
  }
  return {...summarize(d.id,items,d.weight,d.remediation),best_observed_model:model_results[0]?.digest??null,model_results};
 });
 return {schema:'umbra.intelligence.gaps.v1',domains:domains.sort((a,b)=>b.priority-a.priority||a.id.localeCompare(b.id)),total_probes:verified.reduce((a,r)=>a+r.rows.length,0),receipts:verified.length,high_confidence_errors:verified.reduce((a,r)=>a+r.high_confidence_errors,0),mean_brier:mean(verified.map(x=>x.brier)),scope:'generated synthetic probes and replayed simulator outcomes; not general intelligence qualification',production_authority:false};
}
export function rankDiscovery(report,models){
 if(!Array.isArray(models)||models.length>10000)throw Error('catalog budget');
 const seen=new Set(),out=[];
 for(const m of models){
  if(typeof m?.repo!=='string'||!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(m.repo)||seen.has(m.repo))continue;
  seen.add(m.repo);
  const gaps=report.domains.filter(g=>DOMAINS.find(d=>d.id===g.id)?.tags.includes(m.task));
  if(!gaps.length)continue;
  out.push({repo:m.repo,task:m.task,gap_ids:gaps.map(g=>g.id),priority:Math.max(...gaps.map(g=>g.priority)),qualified:false,action:'verify license, exact revision, runtime compatibility and benchmark before acquisition'});
 }
 return out.sort((a,b)=>b.priority-a.priority||a.repo.localeCompare(b.repo));
}
export function selectProbe(models,receipts,free,seed){
 if(!int(seed,1,1e9)||!int(free,0,Number.MAX_SAFE_INTEGER)||!Array.isArray(models)||!Array.isArray(receipts))throw Error('invalid probe selection');
 const history=receipts.map(verifyReceipt),counts=m=>history.filter(r=>r.manifest_digest===m.manifest_digest).length;
 return models.filter(m=>hex(m?.manifest_digest)&&Array.isArray(m.roles)&&m.roles.some(r=>['triage','reasoning','critique','coding','research'].includes(r))&&int(m.size_bytes,1,1500000000)&&requiredBytes('ollama',m.size_bytes)+256*1024**2<=free&&!history.some(r=>r.manifest_digest===m.manifest_digest&&r.seed===seed)).sort((a,b)=>counts(a)-counts(b)||a.size_bytes-b.size_bytes||a.model.localeCompare(b.model))[0]??null;
}
