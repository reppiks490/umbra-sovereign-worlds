import {join,resolve} from 'node:path';
import {existsSync,lstatSync,readFileSync,mkdirSync,writeFileSync,renameSync,readdirSync} from 'node:fs';
import {buildRegistry,attachRegistry,searchRepositories,mergeInventories} from '../mcp/repository_fabric.mjs';
import {repositoryCatalog,qualifyRepositories,runRepositoryMission} from '../mcp/repository_gateway.mjs';
import {qualificationReceipts,lessonFromReceipt,augmentRepositoryCorpus,compareForecastReceipts} from '../mcp/repository_lessons.mjs';
const [arg,mode='audit',agent,query]=process.argv.slice(2);
if(!arg||!['audit','ready','search'].includes(mode))throw Error('usage: repository_cycle ROOT audit|ready|search [AGENT QUERY]');
const root=resolve(arg),dir=join(root,'repository-fabric');mkdirSync(dir,{recursive:true});
function read(p,max=32*1024**2){const s=lstatSync(p);if(!s.isFile()||s.isSymbolicLink()||s.size>max)throw Error('invalid input');return JSON.parse(readFileSync(p,'utf8'));}
function save(p,x){const t=p+'.'+process.pid+'.tmp';writeFileSync(t,JSON.stringify(x),{flag:'wx'});renameSync(t,p);}
const input=join(root,'local-source-inventory.json');
if(!existsSync(input)){console.log(JSON.stringify({status:'deferred_local_inventory'}));process.exit(0);}
const wsl=join(root,"wsl-source-inventory.json"),archives=join(root,"local-source-archives.json");
const registry=buildRegistry(mergeInventories(read(input),existsSync(wsl)?read(wsl):null,existsSync(archives)?read(archives):null));const pop=join(root,'megaswarm','population.json');
if(!existsSync(pop)){console.log(JSON.stringify({status:'deferred_population'}));process.exit(0);}
const state=attachRegistry(read(pop),registry);
if(mode==='search'){console.log(JSON.stringify(searchRepositories(registry,state,agent,query)));process.exit(0);}
save(join(dir,'registry.json'),registry);
const status={status:'indexed',mode,repository_locations:registry.repositories.length,git_worktrees:registry.repositories.filter(x=>x.kind==='git').length,source_candidates:registry.repositories.filter(x=>x.kind==='source_candidate').length,archive_candidates:registry.repositories.filter(x=>x.kind==='archive_candidate').length,agents_linkable:state.agents.length,digest:registry.digest,post_download_review:mode==='ready'?'eligible_for_adapter_qualification':'deferred_acquisition_or_runtime',execution_allowed:false};
if(mode==='ready'){
 try{
  let c=repositoryCatalog();
  if(c.capabilities.length<5){qualifyRepositories();c=repositoryCatalog();}
  status.qualified_capabilities=c.capabilities;
  status.mission=runRepositoryMission();
 }catch(e){status.mission={status:'deferred_or_failed',reason:e.name};}
}
// Read existing verified evidence in audit mode too; no model or numerical runtime is loaded.
const qualification=join(dir,'qualification.json'),missions=join(dir,'missions');
try{
 const q=existsSync(qualification)?read(qualification):null;
 const receipts=q?.registry===registry.digest?qualificationReceipts(q):[];
 const comparison=compareForecastReceipts(receipts);
 const rejected=[];
 if(existsSync(missions)){
  const names=readdirSync(missions).filter(n=>/^\d+\.json$/.test(n)).sort((a,b)=>Number(b.split('.')[0])-Number(a.split('.')[0])).slice(0,32);
  for(const name of names){try{const r=read(join(missions,name),65536);if(r.registry!==registry.digest||!state.agents.some(a=>a.id===r.agent)||r.request?.agent!==r.agent||r.request?.capability!==r.capability)throw Error('mission identity');lessonFromReceipt(r);receipts.push(r);}catch(e){rejected.push(name);}}
 }
 const corpora=[];
 for(const model of ['qwen3-0.6b','granite4-350m']){
  const f=join(root,'megaswarm','corpora',model+'.json');if(!existsSync(f))continue;
  const out=augmentRepositoryCorpus(read(f,2*1024**2),receipts);
  save(f,out);corpora.push({model,training:out.training.length,retention:out.retention.length,transfer:out.transfer.length,repository_examples:out.repository_examples});
 }
 status.repository_learning={verified_receipts:receipts.length,rejected_receipts:rejected,corpora,comparison,model_weights_trained:false};
}catch(e){status.repository_learning={status:'deferred_or_failed',reason:e.name};}
save(join(dir,'status.json'),status);console.log(JSON.stringify(status));
