/** Shared-weight specialist population and bounded replay learning. */
import {DOMAINS} from './intelligence_gaps.mjs';
import {trainNetwork,evaluateNetwork} from './autogenesis_neural.mjs';
import {createHash} from 'node:crypto';
const int=(n,a,b)=>Number.isSafeInteger(n)&&n>=a&&n<=b;
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const models=['qwen3:0.6b','granite4:350m'];
const domains=DOMAINS.map(x=>x.id);
const strategies=['direct','decompose','constraint_check','counterexample','retrieve','abstain','compare','verify'];
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
export function createSwarm(perFamily=2048){
 if(!int(perFamily,1,5000))throw Error('population budget');
 return {schema:'umbra.megaswarm.v1',per_family:perFamily,agents:models.flatMap((model,f)=>Array.from({length:perFamily},(_,i)=>({id:'F'+f+'-'+String(i).padStart(4,'0'),model,domain:domains[i%domains.length],strategy:strategies[Math.floor(i/domains.length)%strategies.length],wins:0,attempts:0}))),evidence:[],independent_llm_weights:false,production_authority:false};
}
function validate(s){
 if(s?.schema!=='umbra.megaswarm.v1'||!int(s.per_family,1,5000)||!Array.isArray(s.agents)||s.agents.length!==2*s.per_family||!Array.isArray(s.evidence)||s.evidence.length>16384||s.independent_llm_weights!==false)throw Error('invalid swarm');
 for(const [i,a] of s.agents.entries()){const f=Math.floor(i/s.per_family),j=i%s.per_family;if(a.id!=='F'+f+'-'+String(j).padStart(4,'0')||a.model!==models[f]||a.domain!==domains[j%domains.length]||a.strategy!==strategies[Math.floor(j/domains.length)%strategies.length]||!int(a.attempts,0,1e9)||!int(a.wins,0,a.attempts))throw Error('agent identity mismatch');}
}
export function assignSwarm(s,domain,count=4){
 validate(s);if(!domains.includes(domain)||!int(count,1,16))throw Error('invalid dispatch');
 const score=a=>(a.wins+1)/(a.attempts+2)+.2/Math.sqrt(a.attempts+1);
 const eligible=s.agents.filter(a=>a.domain===domain).sort((a,b)=>score(b)-score(a)||a.attempts-b.attempts||a.id.localeCompare(b.id));
 const out=[],used=new Set();
 for(const a of eligible){const key=a.model+':'+a.strategy;if(!used.has(key)){out.push(a);used.add(key);}if(out.length===count)return out;}
 return out.concat(eligible.filter(a=>!out.includes(a)).slice(0,count-out.length));
}
export function recordOutcome(s,r){
 validate(s);if(!r||!hex(r.evidence)||typeof r.success!=='boolean'||s.evidence.includes(r.evidence)||s.evidence.length===16384)throw Error('invalid or duplicate outcome');
 const i=s.agents.findIndex(a=>a.id===r.agent&&a.domain===r.domain);if(i<0)throw Error('invalid agent');
 const next=structuredClone(s);next.agents[i].attempts++;next.agents[i].wins+=Number(r.success);next.evidence.push(r.evidence);return next;
}
export function buildCurriculum(gaps,seed,count=64){
 if(!Array.isArray(gaps)||!int(seed,1,1000000)||!int(count,1,256))throw Error('curriculum budget');
 const rows=gaps.filter(x=>domains.includes(x.id)&&Number.isFinite(x.priority)&&x.priority>=0&&x.priority<=1);if(!rows.length||new Set(rows.map(x=>x.id)).size!==rows.length)throw Error('invalid gaps');
 const weights=rows.map(x=>.05+x.priority),total=weights.reduce((a,b)=>a+b,0);
 const served=rows.map(()=>0),out=[];
 for(let i=0;i<count;i++){const j=rows.map((_,j)=>j).sort((a,b)=>((i+1)*weights[b]/total-served[b])-((i+1)*weights[a]/total-served[a])||a-b)[0];served[j]++;out.push({domain:rows[j].id,train_seed:seed*512+i,eval_seed:600000000+seed*512+i,difficulty:1+Math.min(4,Math.floor(served[j]/8)),status:'planned'});}
 return out;
}
export function distillExamples(rows,verify){
 if(!Array.isArray(rows)||rows.length>4096||typeof verify!=='function')throw Error('distillation budget');
 const seen=new Set(),out=[];
 for(const r of rows){if(typeof r?.id!=='string'||seen.has(r.id)||typeof r.prompt!=='string'||r.prompt.length>4096||typeof r.answer!=='string'||r.answer.length>4096||typeof r.expected!=='string'||typeof r.teacher!=='string'||!hex(r.teacher_digest))throw Error('invalid teacher example');seen.add(r.id);if(r.answer===r.expected&&verify(r)===true)out.push({id:r.id,prompt:r.prompt,answer:r.answer,teacher:r.teacher,teacher_digest:r.teacher_digest,evidence:hash(r),verification:'independently_checked'});}
 return out;
}
export function trainContinual({old,newRows,retention,transfer,seed=1}){
 if(![old,newRows,retention,transfer].every(x=>Array.isArray(x)&&x.length>=2&&x.length<=256))throw Error('invalid replay datasets');
 const held=new Set([...retention,...transfer].map(hash));const a=old.filter(x=>!held.has(hash(x))),b=newRows.filter(x=>!held.has(hash(x)));
 if(a.length<2||b.length<2)throw Error('held-out separation');
 const baselineNet=trainNetwork(a,{seed,width:8,epochs:150});
 const describe=(name,network)=>({name,network,retention_mse:evaluateNetwork(network,retention),transfer_mse:evaluateNetwork(network,transfer)});
 const baseline=describe('incumbent',baselineNet);
 const candidates=[describe('new_only',trainNetwork(b,{seed,width:8,epochs:150})),describe('replay',trainNetwork([...a,...b],{seed,width:8,epochs:150})),describe('replay_wide',trainNetwork([...a,...b],{seed,width:16,epochs:150}))];
 const eligible=candidates.filter(c=>c.retention_mse<=baseline.retention_mse+.01&&c.transfer_mse<baseline.transfer_mse).sort((a,b)=>a.transfer_mse-b.transfer_mse||a.retention_mse-b.retention_mse);
 return {schema:'umbra.continual.v1',baseline,candidates,selected:eligible[0]??baseline,train_examples:a.length+b.length,retention_examples:retention.length,transfer_examples:transfer.length,external_model_weights_trained:false,synthetic:true,production_authority:false};
}
