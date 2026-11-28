/** MNEMOSYNE: owner-local, bounded, hash-chained experiment memory. */
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,renameSync,unlinkSync,openSync,closeSync,statSync,existsSync} from 'node:fs';
import {replayExperience} from './agentic_swarm.mjs';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const genesis='0'.repeat(64),maxBytes=8*1024*1024,maxEntries=512;
function read(path){
 if(!existsSync(path))return [];
 if(statSync(path).size>maxBytes)throw Error('memory budget');
 const envelope=JSON.parse(readFileSync(path,'utf8'));
 if(envelope?.schema!=='umbra.swarm.memory.v1'||!Array.isArray(envelope.entries)||envelope.entries.length>maxEntries)throw Error('invalid memory');
 let prev=genesis;const ids=new Set(),seeds=new Set();
 for(const [i,e] of envelope.entries.entries()){
  if(e?.index!==i||e.prev!==prev||e.sha256!==hash({index:i,prev,record:e.record})||e.record?.schema!=='umbra.swarm.result.v1'||e.record.synthetic!==true||e.record.production_authority!==false||typeof e.record.mission_id!=='string'||ids.has(e.record.mission_id)||!Number.isSafeInteger(e.record.mission?.seed)||seeds.has(e.record.mission.seed))throw Error('memory integrity');
  ids.add(e.record.mission_id);seeds.add(e.record.mission.seed);prev=e.sha256;
 }
 return envelope.entries;
}
export function readExperience(path){return read(path).map(x=>x.record);}
export function appendExperience(path,record){
 replayExperience([record]);
 const lock=path+'.lock',fd=openSync(lock,'wx'),tmp=path+'.'+process.pid+'.tmp';
 try{
  const entries=read(path);
  const old=entries.find(e=>e.record.mission_id===record.mission_id);
  if(old){if(hash(old.record)!==hash(record))throw Error('mission already recorded');return {count:entries.length,duplicate:true};}
  if(entries.some(e=>e.record.mission.seed===record.mission.seed))throw Error('seed already recorded');
  if(entries.length>=maxEntries)throw Error('memory capacity');
  const item={index:entries.length,prev:entries.at(-1)?.sha256??genesis,record};
  entries.push({...item,sha256:hash(item)});
  const payload=JSON.stringify({schema:'umbra.swarm.memory.v1',entries});
  if(Buffer.byteLength(payload)>maxBytes)throw Error('memory budget');
  writeFileSync(tmp,payload,{flag:'wx'});renameSync(tmp,path);
  return {count:entries.length,duplicate:false};
 }finally{closeSync(fd);try{unlinkSync(tmp);}catch(e){if(e.code!=='ENOENT')throw e;}unlinkSync(lock);}
}
export function recallExperience(records,{model,candidate,limit=32}={}){
 if(!Array.isArray(records)||records.length>maxEntries||!Number.isSafeInteger(limit)||limit<1||limit>128||[model,candidate].some(x=>x!==undefined&&(typeof x!=='string'||x.length>200)))throw Error('invalid recall');
 return records.filter(r=>(model===undefined||r.votes.some(v=>v.model===model))&&(candidate===undefined||r.candidate===candidate)).slice(-limit);
}
