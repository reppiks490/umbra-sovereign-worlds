/** NEURAL NEXUS: local native catalog, bounded synthetic embedding and semantic recall. */
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {isAbsolute,join} from 'node:path';
import {existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {availableAdapters} from './local_model_adapters.mjs';
import {createMission} from './agentic_swarm.mjs';
const ROOT=fileURLToPath(new URL('../',import.meta.url));
const sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x),rev=x=>typeof x==='string'&&/^[a-f0-9]{40}$/.test(x);
const supported=new Set(['sentence-transformers/all-MiniLM-L6-v2','BAAI/bge-small-en-v1.5']);
function config(){
 const python=process.env.UMBRA_AGENTIC_NATIVE_PYTHON,root=process.env.UMBRA_AGENTIC_NATIVE_ROOT;
 if(!python&&!root)return null;
 if(!python||!root||!isAbsolute(python)||!isAbsolute(root)||!existsSync(python)||!existsSync(root))throw Error('native owner configuration invalid');
 return {python,root};
}
function nativeInvoke(model,text){
 const c=config();if(!c){if(model)throw Error('native runtime not configured');return {models:[]};}
 const env={};for(const k of ['SystemRoot','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR','LANG','PATH','Path'])if(process.env[k]!==undefined)env[k]=process.env[k];
 Object.assign(env,{OPENBLAS_NUM_THREADS:'1',OMP_NUM_THREADS:'1',MKL_NUM_THREADS:'1',TOKENIZERS_PARALLELISM:'false',PYTHONNOUSERSITE:'1'});
 const args=[join(ROOT,'scripts','agentic_native.py'),'--root',c.root];
 if(model){args.push('--model',model);if(process.env.UMBRA_AGENTIC_AUTO_RESTORE==='1')args.push('--restore');}
 const p=spawnSync(c.python,args,{input:text,encoding:'utf8',cwd:ROOT,env,timeout:120000,maxBuffer:2097152,windowsHide:true});
 if(p.error||p.status!==0)throw Error('native inference or catalog unavailable');
 return JSON.parse(p.stdout);
}
export function missionText(m){
 if(sha(m)!==sha(createMission({seed:m?.seed,steps:m?.steps})))throw Error('invalid synthetic mission');
 return 'Synthetic policy optimization: '+JSON.stringify({steps:m.steps,candidates:m.candidates.map(c=>({id:c.id,policy:c.policy,train_mean:c.train_mean}))});
}
const vec=v=>Array.isArray(v)&&v.length>=1&&v.length<=768&&v.every(Number.isFinite)&&Math.abs(Math.sqrt(v.reduce((a,x)=>a+x*x,0))-1)<.005;
export function validateEmbedding(r,m){
 if(r?.schema!=='umbra.native.embedding.v1'||r.model!==m.repo||r.revision!==m.revision||r.weight_sha256!==m.digest||r.inference_verified!==true||r.synthetic!==true||r.production_authority!==false||r.research_qualified!==false||!vec(r.embedding)||r.dimensions!==r.embedding.length)throw Error('invalid native embedding receipt');
 return r.embedding;
}
export function semanticRank(query,rows){
 if(!vec(query)||!Array.isArray(rows)||rows.length>32||rows.some(r=>typeof r.id!=='string'||!vec(r.embedding)||r.embedding.length!==query.length))throw Error('invalid semantic vectors');
 return rows.map(r=>({id:r.id,similarity:Math.max(-1,Math.min(1,r.embedding.reduce((a,v,i)=>a+v*query[i],0)))})).sort((a,b)=>b.similarity-a.similarity||a.id.localeCompare(b.id));
}
export async function nexusCatalog({ollama=availableAdapters,native=()=>nativeInvoke()}={}){
 const o=await ollama(),n=native();
 if(!Array.isArray(o?.adapters)||!Array.isArray(n?.models)||n.models.length>200)throw Error('invalid nexus inventory');
 const seen=new Set();
 const ext=n.models.map(x=>{
  if(typeof x.repo!=='string'||!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(x.repo)||!hex(x.digest)||!rev(x.revision)||seen.has(x.digest)||!Number.isSafeInteger(x.size_bytes)||x.size_bytes<=0||x.weights_verified!==true||x.inference_verified!==false||!['numpy-bert','catalog-only'].includes(x.runtime)||(x.runtime==='numpy-bert'&&!supported.has(x.repo)))throw Error('invalid native entry');
  seen.add(x.digest);
  return {model:x.repo,runtime:x.runtime,revision:x.revision,weight_sha256:x.digest,size_bytes:x.size_bytes,roles:x.runtime==='numpy-bert'?['retrieval']:[],weights_verified:true,inference_verified:false};
 });
 const archives=n.archived??[];
 if(!Array.isArray(archives)||archives.length>200)throw Error('invalid archive inventory');
 const remote=archives.map(x=>{
  if(typeof x.repo!=='string'||!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(x.repo)||!hex(x.digest)||!rev(x.revision)||seen.has(x.digest)||!Number.isSafeInteger(x.size_bytes)||x.size_bytes<=0||x.status!=='remote'||x.source!=='https://huggingface.co/'+x.repo+'/tree/'+x.revision)throw Error('invalid archive entry');
  seen.add(x.digest);
  return {model:x.repo,runtime:supported.has(x.repo)?'numpy-bert':'catalog-only',revision:x.revision,weight_sha256:x.digest,size_bytes:x.size_bytes,roles:supported.has(x.repo)?['retrieval']:[],availability:'remote',source:x.source,weights_verified:false,inference_verified:false};
 });
 return {schema:'umbra.nexus.catalog.v1',models:[...o.adapters.map(x=>({...x,runtime:'ollama',inference_verified:false})),...ext,...remote],research_qualified:false,production_authority:false};
}
export function nativeMissionEmbedding(model,mission,{native=nativeInvoke}={}){
 if(!supported.has(model))throw Error('unsupported native model');
 const c=native(),matches=c.models.filter(x=>x.repo===model&&x.runtime==='numpy-bert'&&x.weights_verified===true);
 if(matches.length===0&&process.env.UMBRA_AGENTIC_AUTO_RESTORE==='1'){
  const archived=(c.archived??[]).filter(x=>x.repo===model&&x.status==='remote'&&hex(x.digest)&&rev(x.revision)&&x.source==='https://huggingface.co/'+x.repo+'/tree/'+x.revision);
  if(archived.length===1)matches.push(archived[0]);
 }
 if(matches.length!==1)throw Error('verified native bundle unavailable');
 const r=native(model,missionText(mission));validateEmbedding(r,matches[0]);return r;
}
export function semanticRecall(model,mission,records,{embed=nativeMissionEmbedding}={}){
 if(!Array.isArray(records)||records.length>8)throw Error('recall budget');
 const q=embed(model,mission);
 const rows=records.map(r=>{const e=embed(model,r.mission);if(e.weight_sha256!==q.weight_sha256||e.revision!==q.revision)throw Error('embedding revision mismatch');return {id:r.mission_id,embedding:e.embedding};});
 return semanticRank(q.embedding,rows);
}

export function infinityInvoke(action,mission){
 const c=config();
 if(!c){if(['status','gaps'].includes(action))return {status:'unconfigured',production_authority:false};throw Error('infinity not configured');}
 if(!['status','embed','gaps'].includes(action))throw Error('invalid infinity operation');
 const env={};for(const k of ['SystemRoot','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR','LANG','PATH','Path'])if(process.env[k]!==undefined)env[k]=process.env[k];
 Object.assign(env,{OPENBLAS_NUM_THREADS:'1',OMP_NUM_THREADS:'1',MKL_NUM_THREADS:'1',TOKENIZERS_PARALLELISM:'false',PYTHONNOUSERSITE:'1'});
 const p=spawnSync(c.python,[join(ROOT,'scripts','infinity.py'),'--root',c.root,action],{input:action==='embed'?missionText(mission):undefined,encoding:'utf8',cwd:ROOT,env,timeout:120000,maxBuffer:2097152,windowsHide:true});
 if(p.error||p.status!==0)throw Error('infinity operation unavailable');
 const r=JSON.parse(p.stdout);
 if(action==='embed'){
  const s=infinityInvoke('status'),m=s.champion;
  if(!m||m.status!=='qualified')throw Error('no qualified champion');
  validateEmbedding(r,{repo:m.repo,revision:m.revision,digest:m.digest});
 }
 return {...r,production_authority:false};
}
