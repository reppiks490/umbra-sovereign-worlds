import {join,resolve} from 'node:path';
import {mkdirSync,readFileSync,writeFileSync,existsSync,openSync,closeSync,unlinkSync,renameSync,lstatSync,readdirSync} from 'node:fs';
import {CARDS,DIVISIONS,expandCorpus,verifyKnowledge} from '../mcp/omni_knowledge.mjs';
import {runKnowledge,nextKnowledgeBatch} from '../mcp/omni_worker.mjs';
import {toolCatalog} from '../mcp/external_capabilities.mjs';
import {availableAdapters} from '../mcp/local_model_adapters.mjs';
const [rootArg,mode='audit']=process.argv.slice(2);
if(!rootArg||!['audit','cycle'].includes(mode))throw Error('invalid mode');
const root=resolve(rootArg),dir=join(root,'omni-academy'),bank=join(dir,'receipts');
mkdirSync(bank,{recursive:true});const lock=join(dir,'worker.lock');let fd;
try{fd=openSync(lock,'wx');}catch(e){if(e.code==='EEXIST'){console.log(JSON.stringify({status:'busy'}));process.exit(0);}throw e;}
function read(p,max){const s=lstatSync(p);if(!s.isFile()||s.isSymbolicLink()||s.size>max)throw Error('invalid file');return JSON.parse(readFileSync(p,'utf8'));}
function save(p,x){const tmp=p+'.'+process.pid+'.tmp';writeFileSync(tmp,JSON.stringify(x,null,2),{flag:'wx'});renameSync(tmp,p);}
try{
 const names=readdirSync(bank).filter(n=>/^[a-f0-9]{64}\.json$/.test(n)).sort();if(names.length>4096)throw Error('receipt capacity');
 const history=names.map(n=>{const r=verifyKnowledge(read(join(bank,n),32768));if(n!==r.evidence+'.json')throw Error('receipt mismatch');return r;});
 const ids=new Set();for(const r of history)for(const q of r.rows){const k=r.model+':'+r.manifest_digest+':'+q.id;if(ids.has(k))throw Error('duplicate answer');ids.add(k);}
 const models=['qwen3:0.6b','granite4:350m','qwen2.5-coder:7b'],tick=Math.floor(Date.now()/1800000);
 let last={status:'audit_only'};
 if(mode==='cycle'&&history.length<4096){
  const adapters=(await availableAdapters()).adapters;
  const name=models[tick%models.length],m=adapters.find(x=>x.model===name);
  if(!m)last={status:'deferred_inventory',model:name};
  else {const qs=nextKnowledgeBatch(m,history);if(qs.length){const r=await runKnowledge(name,qs);last={status:r.status,model:name};if(r.receipt){const v=verifyKnowledge(r.receipt);writeFileSync(join(bank,v.evidence+'.json'),JSON.stringify(v),{flag:'wx'});history.push(v);last.correct=v.correct;last.questions=v.rows.length;}}else last={status:'fixed_assessment_complete',model:name};}
 }
 const corpora=[];
 for(const model of models.slice(0,2)){
  const f=join(root,'megaswarm','corpora',model.replace(':','-')+'.json');if(!existsSync(f))continue;
  const c=expandCorpus(read(f,2*1024**2),tick);const a=c.training.filter(x=>!x.omni_task_id),b=c.training.filter(x=>x.omni_task_id),mixed=[];
  for(let i=0;i<Math.max(a.length,b.length);i++){if(b[i])mixed.push(b[i]);if(a[i])mixed.push(a[i]);}c.training=mixed;save(f,c);
  corpora.push({model,training:c.training.length,retention:c.retention.length,transfer:c.transfer.length});
 }
 const stats={status:'completed',mode,divisions:DIVISIONS,cards:CARDS.length,assessment_cards:CARDS.filter(c=>c.assessment).length,answered:history.reduce((n,r)=>n+r.rows.length,0),correct:history.reduce((n,r)=>n+r.correct,0),last,corpora,external_tools:toolCatalog(),production_authority:false};
 save(join(dir,'status.json'),stats);console.log(JSON.stringify(stats));
}finally{closeSync(fd);unlinkSync(lock);}
