/** Owner-local repository index: source data, never executable instructions. */
import {createHash} from 'node:crypto';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const valid=(x,n)=>typeof x==='string'&&x.length>0&&x.length<=n&&!/[\x00-\x1f]/.test(x);
function normalize(x){
 if(!valid(x?.name,256)||!valid(x.path,2048)||!['git','source_candidate','archive_candidate'].includes(x.kind)||!(x.repo===null||typeof x.repo==='string'&&/^[\w.-]+\/[\w.-]+$/.test(x.repo))||!(x.kind==='git'?typeof x.head==='string'&&/^[a-f0-9]{40,64}$/.test(x.head):x.head===null)||!(x.readme===null||valid(x.readme,80))||!(x.readme_sha256===null||/^[a-f0-9]{64}$/.test(x.readme_sha256))||typeof x.excerpt!=='string'||[...x.excerpt].length>4000||!Array.isArray(x.markers)||x.markers.length>32||!x.markers.every(m=>valid(m,80)))throw Error('invalid local repository evidence');
 return {id:hash(x.path.toLowerCase()),repo:x.repo,name:x.name,path:x.path,head:x.head,kind:x.kind,readme:x.readme,readme_sha256:x.readme_sha256,excerpt:x.excerpt,markers:[...new Set(x.markers)].sort(),status:x.kind==='git'?'local_git_observed':x.kind==='archive_candidate'?'local_archive_candidate':'local_source_candidate',execution_allowed:false};
}
export function buildRegistry(inv){
 if(inv?.schema!=='umbra.local.repo.inventory.v1'||!Array.isArray(inv.repositories)||inv.repositories.length>4096)throw Error('inventory schema');
 const repositories=inv.repositories.map(normalize);
 if(new Set(repositories.map(x=>x.id)).size!==repositories.length)throw Error('duplicate source path');
 const r={schema:'umbra.local.repo.registry.v1',repositories,execution_allowed:false,production_authority:false};
 return {...r,digest:hash(r)};
}
export function verifyRegistry(r){
 const v=buildRegistry({schema:'umbra.local.repo.inventory.v1',repositories:r?.repositories});
 if(hash(r)!==hash(v))throw Error('registry mismatch');return v;
}
export function attachRegistry(state,registry){
 const r=verifyRegistry(registry);
 if(!Array.isArray(state?.agents)||state.agents.length>10000||new Set(state.agents.map(a=>a.id)).size!==state.agents.length)throw Error('invalid swarm state');
 return {...state,agents:state.agents.map(a=>({...a,repository_registry:r.digest,repository_count:r.repositories.length})),repository_registry:r.digest};
}
const terms=x=>[...new Set(x.toLowerCase().match(/[a-z0-9_-]{2,}/g)??[])];
export function searchRepositories(registry,state,agentId,query,limit=4){
 const r=verifyRegistry(registry);
 if(!state?.agents?.some(a=>a.id===agentId&&a.repository_registry===r.digest)||!valid(query,256)||!Number.isSafeInteger(limit)||limit<1||limit>12)throw Error('repository query rejected');
 const ts=terms(query);
 const results=r.repositories.map(x=>{const name=terms(x.name+' '+(x.repo??'')),body=terms(x.excerpt);return {x,score:ts.reduce((s,t)=>s+Number(name.includes(t))*4+Number(body.includes(t)),0)};}).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||a.x.id.localeCompare(b.x.id)).slice(0,limit).map(({x,score})=>({id:x.id,repo:x.repo,name:x.name,head:x.head,readme_sha256:x.readme_sha256,status:x.status,excerpt:x.excerpt.slice(0,1200),score,trust:'untrusted_source_data'}));
 return {agent:agentId,registry:r.digest,results,execution_allowed:false,production_authority:false};
}

export function mergeInventories(windows,wsl=null,archives=null){
 const inventories=[windows,...(wsl?[wsl]:[])];
 if(inventories.some(x=>x?.schema!=='umbra.local.repo.inventory.v1'||!Array.isArray(x.repositories)))throw Error('inventory schema');
 const repositories=inventories.flatMap(x=>x.repositories);
 if(archives){
  if(archives.schema!=='umbra.local.archive.candidates.v1'||!Array.isArray(archives.archives))throw Error('archive schema');
  for(const a of archives.archives){
   if(!valid(a.name,256)||!valid(a.path,2048)||!Number.isSafeInteger(a.bytes)||a.bytes<0||!Number.isSafeInteger(a.marker_count)||a.marker_count<1||!Array.isArray(a.marker_examples)||a.marker_examples.length>5||!a.marker_examples.every(m=>typeof m==='string'&&m.length<=2048))throw Error('archive evidence');
   repositories.push({repo:null,name:a.name,path:a.path,head:null,kind:'archive_candidate',readme:null,readme_sha256:null,excerpt:'Archive project markers: '+a.marker_examples.map(x=>x.slice(0,300)).join(', '),markers:[]});
  }
 }
 return {schema:'umbra.local.repo.inventory.v1',repositories};
}
