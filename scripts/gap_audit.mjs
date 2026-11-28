/** Owner-local persistent evidence audit. No weight acquisition or deletion. */
import {resolve,join} from 'node:path';
import {existsSync,mkdirSync,readFileSync,writeFileSync,renameSync,statSync,lstatSync,openSync,closeSync,unlinkSync} from 'node:fs';
import {readExperience} from '../mcp/agentic_memory.mjs';
import {assessGaps,rankDiscovery,verifyReceipt,battery,publicQuestions} from '../mcp/intelligence_gaps.mjs';
import {compareCouncil} from '../mcp/gap_strategy.mjs';
import {solveProbe} from '../mcp/gap_tools.mjs';
import {runProbe} from '../mcp/gap_probe.mjs';
import {readProbeWindow} from '../mcp/gap_evidence.mjs';
function json(path,fallback,max=8*1024**2){
 if(!existsSync(path))return fallback;
 if(lstatSync(path).isSymbolicLink()||statSync(path).size>max)throw Error('invalid audit input');
 return JSON.parse(readFileSync(path,'utf8'));
}
function atomic(path,data){
 const temp=path+'.'+process.pid+'.tmp';
 writeFileSync(temp,JSON.stringify(data,null,2),{flag:'wx'});renameSync(temp,path);
}
const [arg,mode='audit',seedArg]=process.argv.slice(2);
if(!arg||!['audit','probe'].includes(mode)||process.argv.length>5)throw Error('usage: gap_audit.mjs ROOT [audit|probe] [SEED]');
const root=resolve(arg),dir=join(root,'infinity','gaps'),bank=join(dir,'receipts');
mkdirSync(bank,{recursive:true});
const lock=join(dir,'audit.lock');
let fd;
try{fd=openSync(lock,'wx');}catch(e){if(e.code==='EEXIST'){console.log(JSON.stringify({status:'audit_busy'}));process.exit(0);}throw e;}
try{
 const archive=join(dir,'archive');
 const receipts=readProbeWindow(bank,archive,256);
 let probe={status:'audit_only'};
 if(mode==='probe'){
  const seed=seedArg===undefined?Math.floor(Date.now()/1800000):Number(seedArg);
  probe=await runProbe(seed,receipts);
  if(probe.receipt){
   const r=verifyReceipt(probe.receipt),name='probe-'+r.manifest_digest+'-'+r.seed+'.json';
   if(existsSync(join(bank,name))||existsSync(join(archive,name)))throw Error('receipt already recorded');
   atomic(join(bank,name),r);
   receipts.splice(0,receipts.length,...readProbeWindow(bank,archive,256));
  }
 }
 const records=readExperience(join(root,'experience','council.json')).slice(-64);
 const strategy=compareCouncil(records);
 const native=json(join(root,'infinity','state.json'),{profiles:{}});
 const discovery=json(join(root,'infinity','discovery.json'),{models:[]});
 const gaps=assessGaps({receipts,policy:records.map(r=>({mission_id:r.mission_id,regret:r.regret})),nativeProfiles:Object.values(native.profiles??{})});
 const candidates=rankDiscovery(gaps,discovery.models??[]);
 const uniqueSeeds=[...new Set(receipts.map(r=>r.seed))];
 const baseline=uniqueSeeds.map(seed=>{const qs=battery(seed),answers=publicQuestions(qs).map(solveProbe);return {seed,correct:answers.filter((x,i)=>x===qs[i].correct).length,questions:qs.length};});
 const report={...gaps,symbolic_baseline:{scope:'known generated templates only; not general reasoning',seeds:baseline,correct:baseline.reduce((a,x)=>a+x.correct,0),questions:baseline.reduce((a,x)=>a+x.questions,0)},timestamp:new Date().toISOString(),probe_status:probe.status,probe_detail:probe.receipt?{model:probe.receipt.model,correct:probe.receipt.correct,questions:probe.receipt.rows.length,high_confidence_errors:probe.receipt.high_confidence_errors}:probe,policy_strategy:strategy,discovered_candidates:candidates.length,candidates,qualification_scope:'local synthetic probes, not independently authenticated research',automated_acquisition_scope:'existing retrieval adapters only',general_intelligence_qualified:false,active_receipt_limit:256,archive_policy:'retain original receipts; active window ordered by seed'};
 atomic(join(dir,'report.json'),report);
 console.log(JSON.stringify({status:'completed',probe_status:probe.status,probe_detail:report.probe_detail,domains:gaps.domains.map(({id,status,accuracy,observations,priority})=>({id,status,accuracy,observations,priority})),policy_strategy:strategy,discovered_candidates:candidates.length,symbolic_baseline:report.symbolic_baseline,total_probes:gaps.total_probes,high_confidence_errors:gaps.high_confidence_errors}));
}finally{closeSync(fd);unlinkSync(lock);}
