/** Shared owner-local dispatch; no remote endpoints or model-controlled commands. */
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {isAbsolute,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {simulate,DEFAULT_POLICY,ENGINE_VERSION} from '../engine.mjs';
import {civicAudit} from '../society.mjs';
import {availableAdapters,runModelAdapter} from './local_model_adapters.mjs';
const ROOT=fileURLToPath(new URL('../',import.meta.url));
const hex=/^[a-f0-9]{64}$/, rev=/^[a-f0-9]{40}$/, repo=/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const tasks={'feature-extraction':'retrieval','sentence-similarity':'retrieval','text-classification':'classification','token-classification':'classification','text-ranking':'ranking','question-answering':'research','zero-shot-classification':'classification'};
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.getPrototypeOf(x)===Object.prototype;
function config(){
 const python=process.env.UMBRA_POLYMIND_PYTHON,root=process.env.UMBRA_POLYMIND_ROOT;
 if(!python&&!root)return null;
 if(!python||!root||!isAbsolute(python)||!isAbsolute(root)||!existsSync(python)||!existsSync(root))throw Error('POLYMIND owner configuration invalid');
 return {python,root};
}
function invoke(c,script,args=[],input){
 const env={};for(const k of ['SystemRoot','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR','LANG','PATH','Path'])if(process.env[k]!==undefined)env[k]=process.env[k];
 const p=spawnSync(c.python,[join(ROOT,'scripts',script),'--root',c.root,...args],{input:input===undefined?undefined:JSON.stringify(input),encoding:'utf8',cwd:ROOT,env,timeout:120000,maxBuffer:2097152,windowsHide:true});
 if(p.error||p.status!==0)throw Error('POLYMIND local subprocess failed');return JSON.parse(p.stdout);
}
const external=async()=>{const c=config();return c?invoke(c,'polymind_acquire.py',['--inventory']):{external:[]};};
const infer=async(model,world)=>{const c=config();if(!c)throw Error('POLYMIND not configured');return invoke(c,'polymind_infer.py',['--model',model],world);};
function modelsFrom(r){
 if(!Array.isArray(r?.external)||r.external.length>100)throw Error('invalid external catalog');
 const seen=new Set();return r.external.map(x=>{
  if(!repo.test(x?.repo)||!rev.test(x.revision)||!hex.test(x.weight_sha256)||!Number.isSafeInteger(x.total_bytes)||x.total_bytes<1||seen.has(x.repo))throw Error('invalid external entry');
  seen.add(x.repo);
  return {runtime:'onnxruntime',model:x.repo,roles:Object.hasOwn(tasks,x.task)?[tasks[x.task]]:[],task:x.task,revision:x.revision,weight_sha256:x.weight_sha256,size_bytes:x.total_bytes,inference_verified:false,research_qualified:false};
 });
}
export async function polymindList({ollama=availableAdapters,external:ext=external}={}){
 const o=await ollama(),e=await ext();
 if(!Array.isArray(o.adapters))throw Error('invalid Ollama inventory');
 return {schema:'umbra.polymind.catalog.v1',models:[...o.adapters.map(x=>({...x,runtime:'ollama',inference_verified:false})),...modelsFrom(e)],research_qualified:false,production_authority:false};
}
function evidence(seed,steps){
 const w=simulate(seed,DEFAULT_POLICY,steps);if(!civicAudit(w).valid)throw Error('world integrity');
 const numeric={seed:w.seed,tick:w.tick};
 for(const k of ['population','food','water','energy','wealth','knowledge','infected','carbon','biodiversity','inequality']){if(!Number.isFinite(w[k]))throw Error('nonfinite evidence');numeric[k]=w[k];}
 return numeric;
}
export async function polymindRun(a,{ollama=availableAdapters,external:ext=external,infer:run=infer,runOllama=runModelAdapter}={}){
 if(!plain(a)||Object.keys(a).length!==5||!Object.keys(a).every(k=>['runtime','model','role','seed','steps'].includes(k))||!['ollama','onnxruntime'].includes(a.runtime)||typeof a.model!=='string'||a.model.length>200||typeof a.role!=='string'||!Number.isSafeInteger(a.seed)||a.seed<1||a.seed>4294967295||!Number.isSafeInteger(a.steps)||a.steps<1||a.steps>120)throw Error('invalid request');
 const chosen=(await polymindList({ollama,external:ext})).models.find(x=>x.runtime===a.runtime&&x.model===a.model&&x.roles.includes(a.role));if(!chosen)throw Error('model or role unavailable');
 const world=evidence(a.seed,a.steps);
 const r=a.runtime==='ollama'?await runOllama({model:a.model,role:a.role,seed:a.seed,steps:a.steps}):await run(a.model,world);
 if(r?.model!==a.model||r.synthetic!==true||r.inference_verified!==true||r.production_authority!==false||r.research_qualified!==false)throw Error('unverified adapter receipt');
 if(a.runtime==='onnxruntime'&&(r.schema!=='umbra.polymind.inference.v1'||r.revision!==chosen.revision||r.weight_sha256!==chosen.weight_sha256||!Array.isArray(r.outputs)||!r.outputs.length||r.outputs.length>16||r.outputs.some(x=>!hex.test(x.sha256)||!Array.isArray(x.shape)||x.shape.length>8||x.shape.some(n=>!Number.isSafeInteger(n)||n<0))))throw Error('invalid external receipt');
 if(a.runtime==='ollama'&&(r.schema!=='umbra.local_adapter_receipt.v1'||r.world?.seed!==a.seed||r.world?.tick!==a.steps))throw Error('invalid Ollama receipt');
 return {schema:'umbra.polymind.dispatch.v1',engine:ENGINE_VERSION,synthetic:true,production_authority:false,research_qualified:false,runtime:a.runtime,role:a.role,world,world_sha256:hash(world),result:r};
}
