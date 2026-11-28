/** Learn a numerical strategy predictor only from independently graded worker receipts. */
import {verifyTask} from './swarm_worker.mjs';
import {DOMAINS} from './intelligence_gaps.mjs';
import {trainNetwork,evaluateNetwork,inferNetwork} from './autogenesis_neural.mjs';
const domains=DOMAINS.map(x=>x.id),strategies=['direct','decompose','constraint_check','counterexample','retrieve','abstain','compare','verify'];
const feat=(a,teacher=false)=>[...domains.map(x=>Number(x===a.domain)),...strategies.map(x=>Number(x===a.strategy)),Number(a.model==='qwen3:0.6b'),Number(teacher)];
const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
export function learnSwarmPolicy(receipts){
 if(!Array.isArray(receipts)||receipts.length>512)throw Error('policy budget');
 const rows=receipts.map(verifyTask),ids=new Set();for(const r of rows){const k=r.agent.id+':'+r.seed;if(ids.has(k))throw Error('duplicate task');ids.add(k);}
 const seeds=[...new Set(rows.map(r=>r.seed))].sort((a,b)=>a-b);
 if(rows.length<16||seeds.length<4)return {status:'insufficient_evidence',observations:rows.length,external_model_weights_trained:false};
 const train_seeds=seeds.slice(0,Math.floor(seeds.length*.75)),test_seeds=seeds.slice(train_seeds.length);
 const examples=rs=>rs.map(r=>({features:feat(r.agent,!!r.lesson_evidence?.length),reward:r.correct/r.questions}));
 const train=examples(rows.filter(r=>train_seeds.includes(r.seed))),test=examples(rows.filter(r=>test_seeds.includes(r.seed)));
 if(train.length<2||test.length<2)return {status:'insufficient_evidence',observations:rows.length,external_model_weights_trained:false};
 const n=trainNetwork(train,{seed:7,width:8,epochs:150}),baseline=mean(train.map(x=>x.reward)),validation_mse=evaluateNetwork(n,test),baseline_mse=mean(test.map(x=>(x.reward-baseline)**2));
 return {schema:'umbra.swarm.policy.v1',status:'evaluated',train_seeds,test_seeds,observations:rows.length,network:n,baseline,validation_mse,baseline_mse,selected:validation_mse+1e-6<baseline_mse?'neural':'historical',model_digests:[...new Set(rows.map(r=>r.model_digest))],external_model_weights_trained:false,synthetic:true,production_authority:false};
}
export function predictSwarmPolicy(policy,agent,teacher=false){
 if(policy?.schema!=='umbra.swarm.policy.v1'||policy.selected!=='neural')return null;
 return Math.max(0,Math.min(1,inferNetwork(policy.network,feat(agent,teacher))));
}
