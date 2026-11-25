import {join,resolve} from 'node:path';
import {existsSync,lstatSync,readFileSync,mkdirSync,writeFileSync,renameSync} from 'node:fs';
import {buildRegistry,attachRegistry,searchRepositories,mergeInventories} from '../mcp/repository_fabric.mjs';
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
save(join(dir,'status.json'),status);console.log(JSON.stringify(status));
