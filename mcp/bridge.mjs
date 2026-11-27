/** Bounded MCP stdio subset. No listener, shell, external service or dynamic tools. */
import {TextDecoder} from 'node:util';
export const MAX_FRAME=65536;
const MAX_RESULT=262144;
const VERSIONS=new Set(['2025-11-25','2025-06-18','2025-03-26']);
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.getPrototypeOf(x)===Object.prototype;
const validId=x=>Number.isSafeInteger(x)||(typeof x==='string'&&x.length>0&&x.length<=128);
const result=(id,value)=>({jsonrpc:'2.0',id,result:value});
const error=(id,code,message)=>({jsonrpc:'2.0',id,error:{code,message}});
const keys=(x,allowed)=>plain(x)&&Object.keys(x).every(k=>allowed.includes(k));
export function validate(schema,value){
 if(schema.enum&&!schema.enum.includes(value))return false;
 switch(schema.type){
  case 'object':return plain(value)&&Object.keys(value).every(k=>Object.hasOwn(schema.properties??{},k)&&validate(schema.properties[k],value[k]))&&(schema.required??[]).every(k=>Object.hasOwn(value,k));
  case 'array':return Array.isArray(value)&&value.length>=(schema.minItems??0)&&value.length<=(schema.maxItems??64)&&value.every(x=>validate(schema.items,x));
  case 'integer':return Number.isSafeInteger(value)&&value>=(schema.minimum??-Number.MAX_SAFE_INTEGER)&&value<=(schema.maximum??Number.MAX_SAFE_INTEGER);
  case 'number':return typeof value==='number'&&Number.isFinite(value)&&value>=(schema.minimum??-Number.MAX_VALUE)&&value<=(schema.maximum??Number.MAX_VALUE);
  case 'string':return typeof value==='string'&&value.length>=(schema.minLength??0)&&value.length<=(schema.maxLength??256)&&(!schema.pattern||new RegExp(schema.pattern).test(value));
  case 'boolean':return typeof value==='boolean';
  default:return false;
 }
}
const toolResult=(value,failed=false)=>({content:[{type:'text',text:JSON.stringify(value)}],isError:failed});
export function createBridge(tools,{maxCalls=64}={}){
 if(!Array.isArray(tools)||tools.length<1||tools.length>24||!Number.isSafeInteger(maxCalls)||maxCalls<1||maxCalls>128)throw Error('invalid bridge configuration');
 const byName=new Map();
 for(const t of tools){if(!/^[a-z][a-z0-9_]{0,63}$/.test(t.name)||byName.has(t.name)||typeof t.invoke!=='function'||t.inputSchema?.type!=='object')throw Error('invalid tool');byName.set(t.name,t);}
 let state='new',calls=0;
 return {handle(r){
  if(!keys(r,['jsonrpc','id','method','params'])||r.jsonrpc!=='2.0'||typeof r.method!=='string'||(Object.hasOwn(r,'id')&&!validId(r.id)))return error(validId(r?.id)?r.id:null,-32600,'Invalid request');
  const p=r.params??{};const id=r.id;
  if(!Object.hasOwn(r,'id')){if(r.method==='notifications/initialized'&&state==='initializing'&&plain(p))state='ready';return null;}
  if(!plain(p))return error(id,-32602,'Invalid params');
  if(r.method==='initialize'){
   if(state!=='new'||typeof p.protocolVersion!=='string'||!plain(p.capabilities)||!plain(p.clientInfo)||typeof p.clientInfo.name!=='string'||typeof p.clientInfo.version!=='string')return error(id,-32602,'Invalid initialization');
   state='initializing';return result(id,{protocolVersion:VERSIONS.has(p.protocolVersion)?p.protocolVersion:'2025-11-25',capabilities:{tools:{listChanged:false}},serverInfo:{name:'umbra-compute',version:'1.1.0'}});
  }
  if(r.method==='ping')return result(id,{});
  if(!['tools/list','tools/call'].includes(r.method))return error(id,-32601,'Method not found');
  if(state!=='ready')return error(id,-32002,'Not initialized');
  if(r.method==='tools/list'){
   if(!keys(p,['_meta','cursor'])||(p.cursor!==undefined&&p.cursor!==null))return error(id,-32602,'Invalid cursor');
   return result(id,{tools:[...byName.values()].map(t=>({name:t.name,description:t.description,inputSchema:t.inputSchema,annotations:{readOnlyHint:true,destructiveHint:false,openWorldHint:false}}))});
  }
  if(!keys(p,['name','arguments','_meta'])||typeof p.name!=='string'||!byName.has(p.name))return error(id,-32602,'Unknown tool');
  const t=byName.get(p.name),a=p.arguments??{};
  if(!validate(t.inputSchema,a))return error(id,-32602,'Invalid tool arguments');
  if(calls>=maxCalls)return result(id,toolResult({error:'Session computation budget exhausted'},true));
  calls++;
  try{
   const value=t.invoke(a);const response=toolResult(value);
   if(Buffer.byteLength(response.content[0].text,'utf8')>MAX_RESULT)throw Error('response exceeds limit');
   return result(id,response);
  }catch{return result(id,toolResult({error:'Computation failed or unavailable'},true));}
 }};
}
export async function serve(bridge,source,sink){
 const decoder=new TextDecoder('utf-8',{fatal:true});let pending=Buffer.alloc(0);
 const send=async value=>{if(value!==null)await new Promise((resolve,reject)=>sink.write(JSON.stringify(value)+'\n',e=>e?reject(e):resolve()));};
 const invalid=()=>error(null,-32700,'Invalid JSON frame');
 for await(const item of source){const chunk=Buffer.isBuffer(item)?item:Buffer.from(item);let start=0;
  while(start<chunk.length){const i=chunk.indexOf(10,start),end=i<0?chunk.length:i;
   if(pending.length+end-start>MAX_FRAME){await send(invalid());return;}
   pending=Buffer.concat([pending,chunk.subarray(start,end)]);start=i<0?chunk.length:i+1;
   if(i<0)break;
   let message;try{message=JSON.parse(decoder.decode(pending));}catch{await send(invalid());pending=Buffer.alloc(0);continue;}
   pending=Buffer.alloc(0);await send(bridge.handle(message));
  }
 }
 if(pending.length)await send(invalid());
}
