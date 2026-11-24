import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
const validName=/^[A-Za-z0-9][A-Za-z0-9._-]*(?:\/[A-Za-z0-9][A-Za-z0-9._-]*)*(?::[A-Za-z0-9][A-Za-z0-9._-]*)?$/;
const digestPattern=/^(?:sha256:)?[a-f0-9]{64}$/;
export function inventoryReceipt(input){
 if(!Array.isArray(input?.models)||input.models.length>256)throw Error('invalid inventory');
 const seen=new Set();let bytes=0;
 const models=input.models.map(m=>{
  if(typeof m?.name!=='string'||m.name.length>200||!validName.test(m.name)||seen.has(m.name)||!Number.isSafeInteger(m.size)||m.size<1||typeof m.digest!=='string'||!digestPattern.test(m.digest))throw Error('invalid model metadata');
  seen.add(m.name);bytes+=m.size;if(!Number.isSafeInteger(bytes))throw Error('inventory size overflow');
  return {name:m.name,size_bytes:m.size,manifest_digest:m.digest.replace(/^sha256:/,'')};
 }).sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0);
 const result={schema:'umbra.local_model_inventory.v1',source:'operator_supplied_ollama_tags',models,distinct_manifest_digests:new Set(models.map(m=>m.manifest_digest)).size,logical_manifest_bytes:bytes,physical_disk_bytes:null,inference_verified:false,research_qualified:false,production_authority:false};
 return {...result,receipt_sha256:createHash('sha256').update(JSON.stringify(result)).digest('hex')};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{let total=0;const chunks=[];for await(const chunk of process.stdin){total+=chunk.length;if(total>1048576)throw Error('inventory exceeds 1 MiB');chunks.push(chunk);}console.log(JSON.stringify(inventoryReceipt(JSON.parse(Buffer.concat(chunks).toString('utf8')))));}catch{process.stderr.write('Invalid or oversized model inventory\n');process.exitCode=1;}
}
