import {replayExperience} from './agentic_swarm.mjs';
const mean=x=>x.length?x.reduce((a,b)=>a+b,0)/x.length:null;
export function compareCouncil(records){
 replayExperience(records);
 const ids=new Set();
 const rows=records.map(r=>{
  if(ids.has(r.mission.seed))throw Error('duplicate mission seed');ids.add(r.mission.seed);
  const baseline=[...r.mission.candidates].sort((a,b)=>b.train_mean-a.train_mean||a.id.localeCompare(b.id))[0];
  const best=Math.max(...r.candidate_scores.map(x=>x.mean)),base=best-r.candidate_scores.find(x=>x.id===baseline.id).mean;
  return {seed:r.mission.seed,council_regret:r.regret,baseline_regret:base,council_gain:base-r.regret};
 });
 const gains=rows.map(x=>x.council_gain),wins=gains.filter(x=>x>1e-9).length,losses=gains.filter(x=>x< -1e-9).length;
 const gain=mean(gains),promote=rows.length>=12&&wins>=Math.ceil(rows.length*.75)&&gain>0.01&&losses<=Math.floor(rows.length*.15);
 return {schema:'umbra.gap.strategy.v1',missions:rows.length,council_mean_regret:mean(rows.map(x=>x.council_regret)),baseline_mean_regret:mean(rows.map(x=>x.baseline_regret)),council_wins:wins,council_losses:losses,ties:rows.length-wins-losses,mean_paired_gain:gain,selected:promote?'council':'training_evidence',reason:promote?'bounded paired evidence gate passed':'insufficient evidence of council superiority',rows,synthetic:true,production_authority:false};
}

import {requiredBytes} from './polymind_admission.mjs';
export function routeCapability(report,domain,adapters,free,busy=false){
 if(!report||report.schema!=='umbra.intelligence.gaps.v1'||!Array.isArray(adapters)||!Number.isSafeInteger(free)||free<0||typeof busy!=='boolean')throw Error('invalid capability routing request');
 const gap=report.domains.find(x=>x.id===domain);
 if(!gap)throw Error('unknown capability');
 const experimental=[],blocked=[];
 for(const m of adapters){
  if(!m||typeof m.model!=='string'||!Array.isArray(m.roles)||!m.roles.some(r=>['reasoning','triage','critique','research','coding'].includes(r)))continue;
  const evidence=gap.model_results.find(x=>x.digest===m.manifest_digest);
  if(!evidence)continue;
  const required=requiredBytes('ollama',m.size_bytes)+256*1024**2;
  const row={model:m.model,digest:m.manifest_digest,observations:evidence.observations,lower95:evidence.lower95,required_bytes:required,probe_qualified:evidence.status==='strong_probe_evidence'&&evidence.observations>=32};
  if(busy||required>free)blocked.push({...row,reason:busy?'busy':'memory'});
  else experimental.push(row);
 }
 experimental.sort((a,b)=>b.lower95-a.lower95||a.required_bytes-b.required_bytes||a.model.localeCompare(b.model));
 return {schema:'umbra.gap.route.v1',domain,selected:experimental.find(x=>x.probe_qualified)?.model??'deterministic_or_abstain',experimental,blocked,scope:'advisory for generated probes only; no general capability certificate',production_authority:false};
}
