/** Owner-local market curriculum worker; one admitted model batch per cycle. */
import {join,resolve} from 'node:path';
import {mkdirSync,readFileSync,writeFileSync,existsSync,openSync,closeSync,unlinkSync,renameSync,lstatSync,readdirSync} from 'node:fs';
import {question,verifyMarket,marketCorpus,selectMarketTask,LANES,SPACE} from '../mcp/market_academy.mjs';
import {runMarketBatch,compareMarket,REFERENCE,STUDENTS} from '../mcp/market_worker.mjs';
import {availableAdapters} from '../mcp/local_model_adapters.mjs';
const [rootArg,mode='audit']=process.argv.slice(2);
if(!rootArg||!['audit','cycle'].includes(mode))throw Error('invalid mode');
const root=resolve(rootArg),dir=join(root,'market-academy'),bank=join(dir,'receipts');
mkdirSync(bank,{recursive:true});let fd;const lock=join(dir,'worker.lock');
try{fd=openSync(lock,'wx');}catch(e){if(e.code==='EEXIST'){console.log(JSON.stringify({status:'busy'}));process.exit(0);}throw e;}
function read(p,max){const s=lstatSync(p);if(!s.isFile()||s.isSymbolicLink()||s.size>max)throw Error('invalid file');return JSON.parse(readFileSync(p,'utf8'));}
function save(p,x){const tmp=p+'.'+process.pid+'.tmp';writeFileSync(tmp,JSON.stringify(x,null,2),{flag:'wx'});renameSync(tmp,p);}
try{
 const names=readdirSync(bank).filter(x=>/^[a-f0-9]{64}\.json$/.test(x)).sort();if(names.length>16384)throw Error('market receipt capacity');
 const history=names.map(n=>{const r=verifyMarket(read(join(bank,n),32768));if(n!==r.evidence+'.json')throw Error('receipt identity');return r;});
 // Validate history before dispatch; use time-slot seed, never duplicate exact identity/task.
 compareMarket(history);
 const tick=Math.floor(Date.now()/1800000),seed=800001+tick%200000,trainSeed=600001+tick%200000;
 let result={status:'audit_only'};
 if(mode==='cycle'&&history.length<16384){
  const catalog=(await availableAdapters()).adapters;
  const slot=tick%4,name=slot===0||slot===1?STUDENTS[slot]:REFERENCE,model=catalog.find(x=>x.model===name);
  if(!model)result={status:'deferred_inventory',model:name};
  else{
   const observed=new Set(history.filter(r=>r.model===name&&r.manifest_digest===model.manifest_digest).flatMap(r=>r.rows.map(q=>q.id)));
   const start=(Math.floor(tick/4)*4)%LANES.length;
   let qs;
   if(slot===2){
    const seen=new Set();qs=history.filter(r=>STUDENTS.includes(r.model)).flatMap(r=>r.rows).filter(q=>q.seed>=800001&&!observed.has(q.id)&&!seen.has(q.id)&&seen.add(q.id)).sort((a,b)=>a.seed-b.seed||a.lane-b.lane).slice(0,4).map(q=>question(q.lane,q.level,q.seed));
   }else qs=Array.from({length:4},(_,i)=>slot===3?question((start+i)%LANES.length,1,trainSeed):selectMarketTask(model,(start+i)%LANES.length,history,seed)).filter(q=>!observed.has(q.id));
   if(qs.length){const r=await runMarketBatch(name,qs);result={status:r.status,model:name,requested:qs.length};if(r.receipt){const v=verifyMarket(r.receipt);writeFileSync(join(bank,v.evidence+'.json'),JSON.stringify(v),{flag:'wx'});history.push(v);result.correct=v.correct;result.questions=v.rows.length;}}
   else result={status:'no_pending_questions',model:name};
  }
 }
 // Extend general family curricula without overwriting existing nonmarket examples.
 const corpusDir=join(root,'megaswarm','corpora'),generated=[];
 for(const name of STUDENTS){
  const file=join(corpusDir,name.replace(':','-')+'.json');if(!existsSync(file))continue;
  const prior=read(file,2*1024**2),base=structuredClone(prior);
  for(const k of ['training','retention','transfer'])base[k]=base[k].filter(r=>!r.market_task_id);
  const liveModel=history.filter(r=>r.model===name).at(-1);const level=liveModel?Math.max(1,...LANES.map((_,k)=>selectMarketTask(liveModel,k,history,seed).level)):1;
  const combined=marketCorpus(base,tick%1000000||1,level,history);
  // Include a verified market example in the first replay minibatches while retaining general exercises.
  const general=combined.training.filter(r=>!r.market_task_id),market=combined.training.filter(r=>r.market_task_id),mixed=[];
  for(let i=0;i<Math.max(general.length,market.length);i++){if(market[i])mixed.push(market[i]);if(general[i])mixed.push(general[i]);}
  combined.training=mixed;save(file,combined);generated.push({model:name,market_examples:48,teacher_examples:combined.market_teacher_examples,level});
 }
 const stats={status:'completed',mode,lanes:LANES.length,tiers:10,address_space:SPACE,receipts:history.length,answered:history.reduce((n,r)=>n+r.rows.length,0),correct:history.reduce((n,r)=>n+r.correct,0),last:result,corpora:generated,comparison:compareMarket(history),production_authority:false};
 save(join(dir,'status.json'),stats);console.log(JSON.stringify(stats));
}finally{closeSync(fd);unlinkSync(lock);}
