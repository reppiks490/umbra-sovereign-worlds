/** Bounded synthetic policy learning; never real-world decisions or model weight training. */
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,renameSync,unlinkSync,statSync} from 'node:fs';
import {simulate,DEFAULT_POLICY,ENGINE_VERSION} from '../engine.mjs';
import {civicAudit} from '../society.mjs';
import {planAdmission} from './polymind_admission.mjs';
import {trainCommittee,committeePredict,distillCommittee,inferNetwork} from './autogenesis_neural.mjs';
const keys=Object.keys(DEFAULT_POLICY), clip=x=>Math.max(0,Math.min(1,x)), mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const digest=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const divisions=['planning','reinforcement','continual','collective','memory','evolution','world-model','meta-learning','distillation','optimization'];
const specialties=['explore','exploit','conserve','recover','forecast','critique','balance','stress-test','transfer','verify'];
const freezePolicy=p=>Object.freeze(p);
export const ROLES=Object.freeze(divisions.flatMap((division,d)=>specialties.map((specialty,s)=>{
 const policy=Object.fromEntries(keys.map((k,i)=>[k,clip(DEFAULT_POLICY[k]+(((d*7+s*3+i*5)%19)-9)/40)]));
 policy.trade=(d*10+s+1)/101;
 return Object.freeze({id:division+':'+specialty,division,specialty,policy:freezePolicy(policy)});
})));
const integer=(x,l,h)=>Number.isSafeInteger(x)&&x>=l&&x<=h;
const features=p=>keys.map(k=>p[k]);
const validPolicy=p=>p&&Object.keys(p).length===keys.length&&keys.every(k=>Number.isFinite(p[k])&&p[k]>=0&&p[k]<=1);
export function trainPredictor(rows){
 if(!Array.isArray(rows)||!rows.length||rows.length>512)throw Error('invalid examples');
 const n=rows[0]?.features?.length;
 if(!integer(n,1,32)||rows.some(r=>r.features?.length!==n||!r.features.every(x=>Number.isFinite(x)&&Math.abs(x)<=10)||!Number.isFinite(r.reward)||Math.abs(r.reward)>100))throw Error('invalid features');
 const w=Array(n+1).fill(0);
 for(let epoch=0;epoch<250;epoch++){
  const grad=Array(n+1).fill(0);
  for(const r of rows){const x=[1,...r.features],err=x.reduce((s,v,i)=>s+v*w[i],0)-r.reward;for(let i=0;i<x.length;i++)grad[i]+=err*x[i];}
  for(let i=0;i<w.length;i++)w[i]-=.08/(n+1)*(grad[i]/rows.length+.001*w[i]);
 }
 return w;
}
export function predict(w,x){if(!Array.isArray(w)||!Array.isArray(x)||w.length!==x.length+1||![...w,...x].every(Number.isFinite))throw Error('invalid prediction');return w[0]+x.reduce((s,v,i)=>s+v*w[i+1],0);}
export const routeRoles=(catalog,role,free,busy=false)=>planAdmission(catalog,role,free,busy);
function score(w){
 if(!civicAudit(w).valid)throw Error('world audit failed');
 const x=[w.population,w.food,w.water,w.knowledge,w.infected,w.carbon,w.biodiversity,w.inequality];
 if(!x.every(Number.isFinite))throw Error('nonfinite world');
 return Math.log1p(w.population)+.2*Math.log1p(w.food+w.water)+.1*Math.log1p(w.knowledge)-w.infected/Math.max(1,w.population)-.002*w.carbon+w.biodiversity-.5*w.inequality;
}
function evaluate(policy,seed,steps){return score(simulate(seed,policy,steps))-score(simulate(seed,DEFAULT_POLICY,steps));}
function mutate(p,i){const q={...p};const key=keys[i%keys.length];q[key]=clip(q[key]+(i%2===0?.08:-.08));return q;}
function validateState(s){
 if(s?.schema!=='umbra.autogenesis.v1'||s.engine!==ENGINE_VERSION||s.synthetic!==true||s.production_authority!==false||!integer(s.seed,1,1e6)||!integer(s.steps,1,120)||!Array.isArray(s.memory)||s.memory.length>512||!validPolicy(s.champion?.policy))throw Error('invalid checkpoint state');
 const seen=new Set();
 for(const r of s.memory){if(!integer(r.seed,1,4294967295)||seen.has(r.seed)||typeof r.role!=='string'||!validPolicy(r.policy)||!Number.isFinite(r.reward)||Math.abs(r.reward)>100||r.audit!==true)throw Error('invalid memory');seen.add(r.seed);}
 return s;
}
export function runEvolution(q={}){
 if(!q||typeof q!=='object'||Array.isArray(q)||Object.keys(q).some(k=>!['seed','rounds','steps','previous'].includes(k)))throw Error('invalid request');
 const {seed=49021,rounds=16,steps=12,previous}=q;
 if(!integer(seed,1,1e6)||!integer(rounds,1,100)||!integer(steps,1,120))throw Error('invalid experiment budget');
 if(previous){validateState(previous);if(previous.seed!==seed||previous.steps!==steps||previous.memory.length+rounds>512)throw Error('incompatible checkpoint');}
 const memory=previous?structuredClone(previous.memory):[], offset=memory.length, incumbent=previous?structuredClone(previous.champion.policy):{...DEFAULT_POLICY};
 const stats=new Map();
 for(const r of memory){const s=stats.get(r.role)||{n:0,sum:0};s.n++;s.sum+=r.reward;stats.set(r.role,s);}
 const trainSeed=i=>seed*1024+i+1;
 for(let i=0;i<rounds;i++){
  const index=offset+i, pool=ROLES.map(r=>({r,value:stats.has(r.id)?stats.get(r.id).sum/stats.get(r.id).n+Math.sqrt(2*Math.log(index+2)/stats.get(r.id).n):Infinity}));
  pool.sort((a,b)=>a.value===b.value?0:b.value-a.value);
  const r=pool[0].r,policy=index%5===4?mutate(incumbent,index):r.policy,role=index%5===4?'mutation:'+index:r.id;
  const reward=evaluate(policy,trainSeed(index),steps);
  memory.push({seed:trainSeed(index),role,policy:{...policy},reward,audit:true});
  const s=stats.get(role)||{n:0,sum:0};s.n++;s.sum+=reward;stats.set(role,s);
 }
 const rows=memory.map(r=>({features:features(r.policy),reward:r.reward}));
 const predictor=trainPredictor(rows);
 let neural=null,rankPrediction=x=>predict(predictor,x);
 if(rows.length>=8){
  const cut=Math.floor(rows.length*.75),training=rows.slice(0,cut),validation=rows.slice(cut);
  const linear=trainPredictor(training);
  const committee=trainCommittee(training,{seed:seed+offset,epochs:80,width:8,members:3});
  const student=distillCommittee(committee,training.map(r=>r.features),{seed:seed+offset+1,epochs:80,width:4});
  const linear_mse=mean(validation.map(r=>(predict(linear,r.features)-r.reward)**2));
  const validation_mse=mean(validation.map(r=>(committeePredict(committee,r.features).mean-r.reward)**2));
  const student_teacher_mse=mean(validation.map(r=>(inferNetwork(student,r.features)-committeePredict(committee,r.features).mean)**2));
  const selected=validation_mse<linear_mse?'committee':'linear';
  rankPrediction=selected==='committee'?x=>{const p=committeePredict(committee,x);return p.mean-p.sd;}:x=>predict(linear,x);
  neural={training_count:training.length,validation_count:validation.length,committee,student,linear_mse,validation_mse,student_teacher_mse,selected};
 }
 // Ranking uses only training/validation observations, never promotion holdout.
 const candidates=[...memory].sort((a,b)=>(b.reward+rankPrediction(features(b.policy)))-(a.reward+rankPrediction(features(a.policy))));
 const candidate=candidates[0].policy;
 const holdSeeds=Array.from({length:8},(_,i)=>3000000000+seed*1024+offset*8+i);
 const paired=holdSeeds.map(s=>{const a=evaluate(incumbent,s,steps),b=evaluate(candidate,s,steps);return {seed:s,incumbent:a,candidate:b,delta:b-a};});
 const delta=mean(paired.map(x=>x.delta)),positive=paired.filter(x=>x.delta>0).length;
 const promoted=delta>1e-6&&positive>=6;
 const champion={policy:promoted?{...candidate}:incumbent,source:promoted?'heldout-challenger':'incumbent'};
 return {schema:'umbra.autogenesis.v1',engine:ENGINE_VERSION,seed,steps,synthetic:true,production_authority:false,research_qualified:false,external_model_weight_training:false,neural_weight_training:neural!==null,memory,predictor,neural,champion,holdout:{seeds:holdSeeds,paired,delta,positive,promoted},metrics:{observations:memory.length,roles_observed:new Set(memory.filter(x=>!x.role.startsWith('mutation:')).map(x=>x.role)).size,mutations_observed:memory.filter(x=>x.role.startsWith('mutation:')).length,train_mean:mean(memory.map(x=>x.reward))}};
}
export function saveCheckpoint(path,state){
 validateState(state);
 const envelope={state,sha256:digest(state)},tmp=path+'.'+process.pid+'.tmp';
 try{writeFileSync(tmp,JSON.stringify(envelope),{flag:'wx'});renameSync(tmp,path);}finally{try{unlinkSync(tmp);}catch(e){if(e.code!=='ENOENT')throw e;}}
}
export function loadCheckpoint(path){
 if(statSync(path).size>2e6)throw Error('checkpoint budget');
 const e=JSON.parse(readFileSync(path,'utf8'));
 if(e.sha256!==digest(e.state))throw Error('checkpoint checksum mismatch');
 return validateState(e.state);
}
