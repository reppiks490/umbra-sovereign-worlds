import {join,resolve} from 'node:path';
import {readFileSync,lstatSync,writeFileSync,renameSync,existsSync} from 'node:fs';
import {verifyPair} from '../mcp/market_symbolic.mjs';
const root=resolve(process.argv[2]);const dir=join(root,'market-academy','campaign-paired');
function read(p,max){const s=lstatSync(p);if(!s.isFile()||s.isSymbolicLink()||s.size>max)throw Error('invalid receipt file');return JSON.parse(readFileSync(p,'utf8'));}
if(!existsSync(join(dir,'latest.json'))){console.log(JSON.stringify({status:'unavailable',production_authority:false}));process.exit(0);}
const latest=read(join(dir,'latest.json'),32768);if(!Array.isArray(latest.out)||latest.out.length!==2||latest.out.some(x=>x.status!=='completed'||!(/^[a-f0-9]{64}$/).test(x.evidence??''))){console.log(JSON.stringify({status:'incomplete',production_authority:false}));process.exit(0);}
const rs=latest.out.map(x=>{const r=read(join(dir,x.evidence+'.json'),32768);if(r.evidence!==x.evidence||r.model!==x.model)throw Error('receipt identity');return r;});
const result={status:'completed',...verifyPair(rs),receipt_ids:rs.map(r=>r.evidence)};
const target=join(dir,'symbolic-verification.json'),temp=target+'.'+process.pid+'.tmp';writeFileSync(temp,JSON.stringify(result,null,2),{flag:'wx'});renameSync(temp,target);console.log(JSON.stringify(result));
