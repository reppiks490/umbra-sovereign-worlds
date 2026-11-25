import {homedir,freemem} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {readFileSync,lstatSync,existsSync,writeFileSync,renameSync,openSync,closeSync,unlinkSync,mkdirSync,readdirSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {verifyRegistry} from './repository_fabric.mjs';
export const CAPABILITIES=Object.freeze(['forecast_metrics','simulation_latency','timeseries_windows','forecast_crosscheck','sparse_regularization']);
const root=()=>join(homedir(),'projects','umbra-agentic-native-20261124');
const plain=x=>x&&typeof x==='object'&&!Array.isArray(x);
function read(p){const s=lstatSync(p);if(!s.isFile()||s.isSymbolicLink()||s.size>32*1024**2)throw Error('local state budget');return JSON.parse(readFileSync(p,'utf8'));}
export function admitRepositoryRequest(state,q){
 if(!plain(q)||Object.keys(q).some(k=>!['agent','capability','arguments'].includes(k))||!state?.agents?.some(a=>a.id===q.agent&&a.repository_registry===state.repository_registry)||!CAPABILITIES.includes(q.capability)||!plain(q.arguments)||JSON.stringify(q.arguments).length>32768)throw Error('repository request rejected');
 return {operation:'execute',capability:q.capability,arguments:q.arguments};
}
export function qualifiedCapabilities(r){return [...new Set((r?.results??[]).filter(x=>x.status==='operational'&&x.receipt?.independently_checked===true&&CAPABILITIES.includes(x.receipt.capability)).map(x=>x.receipt.capability))];}
function invoke(q){
 const py=join(homedir(),'projects','umbra-polymind-runtime','Scripts','python.exe');
 const script=fileURLToPath(new URL('../scripts/repository_runtime.py',import.meta.url));
 if(!existsSync(py))throw Error('repository runtime missing');
 if(freemem()<1024**3)throw Error('repository memory gate');
 const lock=join(root(),'repository-fabric','execution.lock');let fd;
 try{fd=openSync(lock,'wx');}catch{throw Error('repository runtime busy');}
 try{
 const env={};for(const k of ['PATH','SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','HOMEDRIVE','HOMEPATH','LOCALAPPDATA','APPDATA'])if(process.env[k])env[k]=process.env[k];
 Object.assign(env,{OMP_NUM_THREADS:'1',OPENBLAS_NUM_THREADS:'1',MKL_NUM_THREADS:'1',GIT_TERMINAL_PROMPT:'0',PYTHONDONTWRITEBYTECODE:'1'});
 const r=spawnSync(py,['-I',script],{input:JSON.stringify(q),encoding:'utf8',timeout:90000,maxBuffer:1024**2,windowsHide:true,env});
 if(r.status!==0||r.error)throw Error('repository operation failed');
 return JSON.parse(r.stdout);
 }finally{closeSync(fd);unlinkSync(lock);}
}
function state(){
 const r=verifyRegistry(read(join(root(),'repository-fabric','registry.json'))),s=read(join(root(),'megaswarm','population.json'));
 if(s.repository_registry!==r.digest)throw Error('registry version mismatch');
 return {r,s};
}
export function repositoryCatalog(){const {r,s}=state();const p=join(root(),'repository-fabric','qualification.json');const q=existsSync(p)?read(p):null;return {registry:r.digest,agents:s.agents.length,source_locations:r.repositories.length,capabilities:q?.registry===r.digest?qualifiedCapabilities(q):[],production_authority:false};}
export function qualifyRepositories(){
 const {r}=state();const q={...invoke({operation:'qualify'}),registry:r.digest};const p=join(root(),'repository-fabric','qualification.json'),tmp=p+'.'+process.pid+'.tmp';writeFileSync(tmp,JSON.stringify(q),{flag:'wx'});renameSync(tmp,p);return q;
}
export function repositoryExecute(q){
 const {s}=state(),request=admitRepositoryRequest(s,q);
 if(!repositoryCatalog().capabilities.includes(request.capability))throw Error('capability not qualified');
 return {...invoke(request),agent:q.agent,registry:s.repository_registry};
}
export function repositorySource(q){
 const {r,s}=state();
 if(!plain(q)||Object.keys(q).some(k=>!['agent','repo_id','path'].includes(k))||!s.agents.some(a=>a.id===q.agent&&a.repository_registry===r.digest)||!r.repositories.some(x=>x.id===q.repo_id)||typeof q.path!=='string'||q.path.length>240)throw Error('source request rejected');
 return {...invoke({operation:'source',repo_id:q.repo_id,path:q.path}),agent:q.agent,registry:r.digest};
}

export function planRepositoryMission(s,capabilities,tick){
 if(!Number.isSafeInteger(tick)||tick<0||!Array.isArray(capabilities)||!Array.isArray(s?.agents))throw Error('mission request');
 const caps=CAPABILITIES.filter(x=>capabilities.includes(x));if(!caps.length)return null;
 const family=s.agents.filter(a=>a.id.startsWith('F'+(tick%2)+'-'));if(!family.length)return null;
 const agent=family[Math.floor(tick/2)%family.length].id,capability=caps[tick%caps.length],n=1+tick%31;
 const args={
 forecast_metrics:{actual:[n,n+2,n+4],predicted:[n+1,n+2,n+1]},
 simulation_latency:{meters:[0,n,300+n],signal:n/10,beta:1},
 timeseries_windows:{values:[n,n+1,n+2,n+3,n+4],sections:2},
 forecast_crosscheck:{actual:[n,n+2,n+4],predicted:[n+1,n+2,n+1]},
 sparse_regularization:{coefficients:[-n,0,n+1],weight:.5}
 };
 return {agent,capability,arguments:args[capability]};
}
export function runRepositoryMission(tick=Math.floor(Date.now()/1800000)){
 const {r,s}=state(),catalog=repositoryCatalog();
 const request=planRepositoryMission(s,catalog.capabilities,tick);
 if(!request)return {status:'no_qualified_capabilities'};
 const dir=join(root(),'repository-fabric','missions');mkdirSync(dir,{recursive:true});
 const target=join(dir,String(tick)+'.json');
 if(existsSync(target)){const x=read(target);if(x.registry===r.digest&&x.tick===tick)return {status:'already_completed',agent:x.agent,capability:x.capability};return {status:'deferred_registry_change'};}
 if(readdirSync(dir).length>=4096)return {status:'deferred_evidence_capacity'};
 const receipt=repositoryExecute(request);
 const x={...receipt,tick,request,synthetic:true};
 const temp=target+'.'+process.pid+'.tmp';writeFileSync(temp,JSON.stringify(x),{flag:'wx'});renameSync(temp,target);
 return {status:'completed',agent:receipt.agent,capability:receipt.capability,independently_checked:receipt.independently_checked,tick};
}

export function repositorySourceList(q){
 const {r,s}=state();
 if(!plain(q)||Object.keys(q).some(k=>!['agent','repo_id'].includes(k))||!s.agents.some(a=>a.id===q.agent&&a.repository_registry===r.digest)||!r.repositories.some(x=>x.id===q.repo_id))throw Error('source request rejected');
 return {...invoke({operation:'source_list',repo_id:q.repo_id}),agent:q.agent,registry:r.digest};
}
