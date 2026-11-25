/** Owner-authorized, local-only advisory adapters. Never modify world state. */
import {createHash} from 'node:crypto';
import {freemem} from 'node:os';
import {simulate,DEFAULT_POLICY,ENGINE_VERSION} from '../engine.mjs';
import {civicAudit} from '../society.mjs';
import {requiredBytes} from './polymind_admission.mjs';
const registry=Object.freeze({
 'qwen3:8b':['reasoning','research'], 'hf.co/bartowski/Qwen_Qwen3-8B-GGUF:IQ2_M':['reasoning','research'],
 'qwen3:4b':['reasoning','research'], 'qwen3:1.7b':['reasoning','triage'], 'qwen3:0.6b':['triage'],
 'deepseek-r1:1.5b':['reasoning','critique'], 'qwen2.5-coder:1.5b':['coding'], 'qwen2.5-coder:3b':['coding'], 'qwen2.5-coder:7b':['coding'],
 'granite4:350m':['triage'], 'gemma3:1b':['critique','triage'], 'gemma3:4b':['critique','research'], 'gemma3:12b':['reasoning','research','critique'],
 'mistral-nemo:12b':['reasoning','research','critique'], 'mistral-nemo:12b-instruct-2407-q3_K_M':['reasoning','research','critique'], 'mistral:latest':['reasoning','research','critique'],
 'phi4-mini:3.8b':['reasoning','critique'], 'qwen2.5:3b':['research','triage'], 'smollm2:1.7b':['triage'],
 'llama3.2:1b':['triage'], 'granite3.2:2b':['research','critique'],
 'all-minilm:22m':['retrieval'], 'nomic-embed-text:latest':['retrieval'], 'bge-m3:latest':['retrieval'], 'qwen3-embedding:0.6b':['retrieval']
});
const directives={reasoning:'Identify one testable within-model hypothesis and a falsifying experiment.',research:'Propose a bounded paired-seed experiment and identify a confound.',critique:'Identify one limitation of the synthetic evidence and a negative control.',coding:'Suggest one regression test in plain language; do not output executable code.',triage:'Identify the most important next verification check.',retrieval:'Represent the synthetic evidence for retrieval.'};
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.getPrototypeOf(x)===Object.prototype;
const digest=/^(?:sha256:)?[a-f0-9]{64}$/;
const cap=1048576;
let running=false;
async function localRequest(path,body){
 if(!['/api/tags','/api/ps','/api/generate','/api/embed'].includes(path))throw Error('endpoint denied');
 const r=await fetch('http://127.0.0.1:11434'+path,{method:body?'POST':'GET',headers:body?{'content-type':'application/json'}:{},body:body?JSON.stringify(body):undefined,redirect:'error',signal:AbortSignal.timeout(body?180000:10000)});
 if(!r.ok||!r.body)throw Error('Ollama unavailable');
 const reader=r.body.getReader();let total=0;const chunks=[];
 try{for(;;){const {done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>cap)throw Error('response budget');chunks.push(Buffer.from(value));}}
 finally{await reader.cancel().catch(()=>{});}
 return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)));
}
function parseInventory(input){
 if(!Array.isArray(input?.models)||input.models.length>256)throw Error('invalid inventory');
 const seen=new Set(),out=[];
 for(const m of input.models){
  if(typeof m?.name!=='string'||m.name.length>200||seen.has(m.name)||!Number.isSafeInteger(m.size)||m.size<=0||typeof m.digest!=='string'||!digest.test(m.digest))throw Error('invalid inventory metadata');
  seen.add(m.name);if(Object.hasOwn(registry,m.name))out.push({model:m.name,roles:[...registry[m.name]],size_bytes:m.size,manifest_digest:m.digest.replace(/^sha256:/,'')});
 }
 return out.sort((a,b)=>a.model.localeCompare(b.model));
}
export async function ollamaBusy({request=localRequest}={}){const status=await request('/api/ps');if(!Array.isArray(status?.models))throw Error('invalid runtime status');return status.models.length!==0;}
export async function availableAdapters({request=localRequest}={}){
 return {schema:'umbra.local_adapters.v1',adapters:parseInventory(await request('/api/tags')),research_qualified:false,production_authority:false};
}
function worldEvidence(seed,steps){
 const w=simulate(seed,DEFAULT_POLICY,steps);
 if(!civicAudit(w).valid)throw Error('world integrity');
 const result={seed:w.seed,tick:w.tick,engine:ENGINE_VERSION};
 for(const k of ['population','food','water','energy','wealth','knowledge','infected','carbon','biodiversity','inequality']){
  if(!Number.isFinite(w[k]))throw Error('nonfinite world');result[k]=w[k];
 }
 return result;
}
export async function runModelAdapter(args,{request=localRequest,freeMemory=freemem}={}){
 if(!plain(args)||Object.keys(args).length!==4||!Object.keys(args).every(k=>['role','model','seed','steps'].includes(k))||
 !Object.hasOwn(directives,args.role)||!Object.hasOwn(registry,args.model)||!registry[args.model].includes(args.role)||
 !Number.isSafeInteger(args.seed)||args.seed<1||args.seed>4294967295||!Number.isSafeInteger(args.steps)||args.steps<1||args.steps>120)throw Error('invalid adapter request');
 if(running)throw Error('adapter busy');running=true;
 try{
 const {adapters}=await availableAdapters({request});const selected=adapters.find(x=>x.model===args.model);if(!selected)throw Error('model not installed');
 const free=freeMemory();if(!Number.isFinite(free)||free<requiredBytes('ollama',selected.size_bytes))throw Error('memory admission denied');
 const busy=await request('/api/ps');if(!Array.isArray(busy?.models)||busy.models.length!==0)throw Error('Ollama already busy');
 const world=worldEvidence(args.seed,args.steps);
 const prompt='UMBRA synthetic model evidence only. No empirical validity, commands, personal data or production authority. '+directives[args.role]+' Evidence: '+JSON.stringify(world);
 const begin=performance.now();let result;
 if(args.role==='retrieval'){
  const r=await request('/api/embed',{model:args.model,input:prompt,truncate:false,keep_alive:0});
  const v=r?.embeddings?.[0];if(r?.model!==args.model||r.embeddings.length!==1||!Array.isArray(v)||v.length<1||v.length>8192||!v.every(Number.isFinite))throw Error('invalid embedding');
  result={embedding_dimensions:v.length,embedding_sha256:hash(v)};
 }else{
  const r=await request('/api/generate',{model:args.model,prompt,stream:false,keep_alive:0,options:{temperature:0,num_ctx:1024,num_predict:128},...(args.model.startsWith('qwen3:')?{think:false}:{})});
  if(r?.model!==args.model||r.done!==true||typeof r.response!=='string'||!r.response.trim()||r.response.length>8192||!Number.isSafeInteger(r.eval_count)||r.eval_count<1||r.eval_count>128)throw Error('invalid generation');
  result={advice:r.response,generated_tokens:r.eval_count,advice_sha256:hash(r.response)};
 }
 return {schema:'umbra.local_adapter_receipt.v1',synthetic:true,production_authority:false,research_qualified:false,inference_verified:true,model:args.model,role:args.role,manifest_digest:selected.manifest_digest,world,world_sha256:hash(world),elapsed_ms:Math.round(performance.now()-begin),...result};
 }finally{running=false;}
}
