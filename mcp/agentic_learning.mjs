/** PROMETHEUS/METAMIND: replay-verified learning across whole prior missions. */
import {createHash} from 'node:crypto';
import {DEFAULT_POLICY} from '../engine.mjs';
import {createMission,replayExperience} from './agentic_swarm.mjs';
import {trainNetwork,inferNetwork,evaluateNetwork} from './autogenesis_neural.mjs';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const features=(m,c)=>[...Object.keys(DEFAULT_POLICY).map(k=>c.policy[k]),m.steps/120,c.train_mean];
function verify(m){if(hash(m)!==hash(createMission({seed:m?.seed,steps:m?.steps})))throw Error('invalid mission');}
export function learnCouncilExperience(records){
 if(!Array.isArray(records)||records.length<4||records.length>64||new Set(records.map(x=>x?.mission?.seed)).size!==records.length)throw Error('need four to sixty-four distinct missions');
 replayExperience(records);
 const cut=Math.floor(records.length*.75),rows=rs=>rs.flatMap(r=>r.mission.candidates.map(c=>({features:features(r.mission,c),reward:r.candidate_scores.find(x=>x.id===c.id).mean})));
 const train=rows(records.slice(0,cut)),valid=rows(records.slice(cut));
 const network=trainNetwork(train,{seed:records[0].mission.seed,width:8,epochs:150});
 const validation_mse=evaluateNetwork(network,valid);
 const baseline_mse=mean(valid.map(r=>(r.features.at(-1)-r.reward)**2));
 return {schema:'umbra.agentic.learner.v1',observed_seeds:records.map(r=>r.mission.seed),training_missions:cut,validation_missions:records.length-cut,training_rows:train.length,validation_rows:valid.length,network,validation_mse,baseline_mse,selected:validation_mse<baseline_mse?'neural':'training_evidence',synthetic:true,research_qualified:false,production_authority:false};
}
export function forecastMission(learner,mission){
 verify(mission);
 if(learner?.schema!=='umbra.agentic.learner.v1'||!Array.isArray(learner.observed_seeds)||!['neural','training_evidence'].includes(learner.selected))throw Error('invalid learner');
 if(learner.observed_seeds.includes(mission.seed))throw Error('mission seed already observed');
 return {synthetic:true,production_authority:false,selected:learner.selected,predictions:mission.candidates.map(c=>({candidate:c.id,score:learner.selected==='neural'?inferNetwork(learner.network,features(mission,c)):c.train_mean})).sort((a,b)=>b.score-a.score||a.candidate.localeCompare(b.candidate))};
}
