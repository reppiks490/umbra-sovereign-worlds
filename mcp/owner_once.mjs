/** One bounded local request; no listener, shell, dynamic imports or tool-controlled paths. */
import {TextDecoder} from 'node:util';
import {createBridge,MAX_FRAME} from './bridge.mjs';
import {createUmbraTools} from './umbra_server.mjs';
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.getPrototypeOf(x)===Object.prototype;
const ownKeys=(x,allowed)=>plain(x)&&Object.keys(x).every(k=>allowed.includes(k));
async function readRequest(){
 let size=0;const chunks=[];
 for await(const chunk of process.stdin){size+=chunk.length;if(size>MAX_FRAME)throw Error('input budget');chunks.push(chunk);}
 return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)));
}
function request(bridge,id,method,params){
 const r=bridge.handle({jsonrpc:'2.0',id,method,params});
 if(!r||r.error||!r.result)throw Error('protocol failure');
 return r.result;
}
try{
 const q=await readRequest();
 if(!ownKeys(q,['operation','name','arguments'])||!['list','call'].includes(q.operation))throw Error('invalid request');
 if(q.operation==='list'&&Object.keys(q).length!==1)throw Error('invalid list');
 if(q.operation==='call'&&(typeof q.name!=='string'||!plain(q.arguments)))throw Error('invalid call');
 const bridge=createBridge(createUmbraTools(),{maxCalls:1});
 request(bridge,1,'initialize',{protocolVersion:'2025-11-25',capabilities:{},clientInfo:{name:'umbra-owner-once',version:'1.0.0'}});
 bridge.handle({jsonrpc:'2.0',method:'notifications/initialized',params:{}});
 const listed=request(bridge,2,'tools/list',{});
 let output=listed;
 if(q.operation==='call'){
  if(!listed.tools.some(t=>t.name===q.name))throw Error('tool unavailable');
  const r=request(bridge,3,'tools/call',{name:q.name,arguments:q.arguments});
  if(r.isError||r.content?.length!==1||r.content[0].type!=='text')throw Error('computation failed');
  output=JSON.parse(r.content[0].text);
 }
 process.stdout.write(JSON.stringify(output)+'\n');
}catch{process.stderr.write('UMBRA owner request failed\n');process.exitCode=1;}
