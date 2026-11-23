#!/usr/bin/env node
/** Read-only qualification of toy proposals against the real deterministic UMBRA v5 engine.
 * Never merges code, trades, deploys, or promotes a trained policy. No I/O besides local files.
 */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {dirname} from 'node:path';
import {createHash} from 'node:crypto';
import {simulate,policyOf,DEFAULT_POLICY,ENGINE_VERSION} from '../engine.mjs';
import {civicAudit} from '../society.mjs';

const args=process.argv.slice(2);
const flag=k=>{const i=args.indexOf(k);return i<0?null:args[i+1]};
const input=flag('--input'),output=flag('--output'),limit=Number(flag('--limit')??4);
if(!input||!output||!Number.isInteger(limit)||limit<1||limit>32)throw Error('Usage: --input evidence.jsonl --output bridge.json --limit [1,32]');
const records=readFileSync(input,'utf8').trim().split('\n').filter(Boolean).slice(0,limit).map(JSON.parse);
const SHA=x=>createHash('sha256').update(x).digest('hex');
const canonical=v=>Array.isArray(v)?'['+v.map(canonical).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':typeof v==='number'?JSON.stringify(v.toFixed(12)):JSON.stringify(v);
const METRICS=['population','food','water','energy','wealth','knowledge','infected','carbon','biodiversity','inequality'];
const negative=new Set(['infected','carbon','inequality']);
function test(record){
 if(record.schema!=='umbra.evolution.mesh.v1'||record.deployment_authorized!==false||record.real_model_weight_training!==false)throw Error('untrusted proposal or elevated authority');
 const receipt=record.receipt_sha256,copy={...record};delete copy.receipt_sha256;
 if(!/^[0-9a-f]{64}$/.test(receipt)||SHA(canonical(copy))!==receipt)throw Error('missing or tampered receipt');
 if(!Array.isArray(record.parameters)||record.parameters.length!==8||record.parameters.some(x=>!Number.isFinite(x)||x<0||x>1))throw Error('bad policy');
 const keys=Object.keys(DEFAULT_POLICY),candidate=policyOf(Object.fromEntries(keys.map((k,i)=>[k,record.parameters[i]])));
 const baseline=policyOf(DEFAULT_POLICY),seeds=[1729,2999,4919];
 const scores={baseline:[],candidate:[]};
 for(const seed of seeds)for(const [name,policy] of [['baseline',baseline],['candidate',candidate]]){
  const w=simulate(seed,policy,24),audit=civicAudit(w);
  if(!audit.valid)throw Error('UMBRA civic invariant failed');
  const metrics=Object.fromEntries(METRICS.map(k=>{const val=w[k];if(!Number.isFinite(val))throw Error('nonfinite '+k);return [k,val]}));
  scores[name].push(metrics);
 }
 const deltas=Object.fromEntries(METRICS.map(k=>[k,Number((scores.candidate.reduce((a,x)=>a+x[k],0)/seeds.length - scores.baseline.reduce((a,x)=>a+x[k],0)/seeds.length).toFixed(7))]));
 return {workflow:record.workflow,source_receipt:receipt,simulator:ENGINE_VERSION,domain:record.domain,
  simulation_only:true,market_data_verified:false,production_promoted:false,paired_seeds:seeds,
  ticks:24,metric_deltas:deltas,candidate_positive_metrics:METRICS.filter(k=>deltas[k]*(negative.has(k)?-1:1)>0)};
}
const report={schema:'umbra.evolution.bridge.v1',fixture_training_source:true,qualified_umbra_replays:records.map(test),auto_promotions:0,live_deployments:0};
report.report_sha256=SHA(canonical(report));
mkdirSync(dirname(output),{recursive:true});writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({qualified:report.qualified_umbra_replays.length,simulator:ENGINE_VERSION,output}));