/** Receipt window with lossless archive rotation; caller holds the audit lock. */
import {join} from 'node:path';
import {existsSync,mkdirSync,lstatSync,readFileSync,readdirSync,renameSync} from 'node:fs';
import {verifyReceipt} from './intelligence_gaps.mjs';
const pattern=/^probe-([a-f0-9]{64})-([0-9]+)\.json$/;
export function readProbeWindow(bank,archive,limit=256){
 if(!Number.isSafeInteger(limit)||limit<1||limit>256)throw Error('invalid window');
 mkdirSync(archive,{recursive:true});
 if(lstatSync(archive).isSymbolicLink()||lstatSync(bank).isSymbolicLink())throw Error('invalid evidence directory');
 const entries=readdirSync(bank).filter(n=>pattern.test(n));
 if(entries.length>4096)throw Error('evidence scan budget exceeded');
 const rows=entries.map(n=>{
  const p=join(bank,n),st=lstatSync(p),m=n.match(pattern);
  if(!st.isFile()||st.isSymbolicLink()||st.size>65536)throw Error('invalid receipt path');
  const r=verifyReceipt(JSON.parse(readFileSync(p,'utf8')));
  if(r.manifest_digest!==m[1]||String(r.seed)!==m[2])throw Error('receipt identity mismatch');
  return {name:n,r};
 }).sort((a,b)=>a.r.seed-b.r.seed||a.name.localeCompare(b.name));
 const old=rows.slice(0,Math.max(0,rows.length-limit));
 for(const x of old)if(existsSync(join(archive,x.name)))throw Error('archive identity collision');
 for(const x of old)renameSync(join(bank,x.name),join(archive,x.name));
 return rows.slice(-limit).map(x=>x.r);
}
