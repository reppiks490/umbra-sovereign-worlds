/** Numerical teaching from pinned repository outputs, independently replayed. */
import {createHash} from 'node:crypto';
const sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const ph=x=>createHash('sha256').update(x).digest('hex');
const pins={
 forecast_metrics:['Nixtla/neuralforecast','24dd828c12d966ba5d41566d91735c996e488db7','6151fd16e8d1ee200cb24d87f1bbd21f74a1f715aa6edee5368e49f25317bc5e'],
 simulation_latency:['abides-sim/abides','c4bf157678928934417aba6073eb0651aeaf6d15','85e0824d8a90a7510b4322b96d263b7bd884df382ea447984ce3370142a23a42'],
 timeseries_windows:['yuezhihan/ts2vec','b0088e14a99706c05451316dc6db8d3da9351163','85ca67e8e84cad09933d2f3ba60de3bc18bafda78706bd5c4c4a509f577dea90'],
 forecast_crosscheck:['thuml/Time-Series-Library','4e938a1767106324dd753b2a44832bf870a0252e','0a565c3f64d7cd29d9a87dee0c22d48f4a6a329476f893458cc18a35fa46a5df'],
 sparse_regularization:['dynamicslab/pysindy','c4421fcec275c8f4cc5c1e93bebb961b212067ae','be5fad3f6cd5b62f06dd51bc94d027f4b86f5228f8ef3097a0b5f7b77a7e59e5']};
const sum=a=>a.reduce((x,y)=>x+y,0),mean=a=>sum(a)/a.length;
const vector=a=>{if(!Array.isArray(a)||a.length<1||a.length>12||a.some(x=>typeof x!=='number'||!Number.isFinite(x)||Math.abs(x)>1e8))throw Error('lesson vector');return a;};
function near(a,b){if(Array.isArray(b)){if(!Array.isArray(a)||a.length!==b.length)throw Error('result shape');b.forEach((x,i)=>near(a[i],x));}else if(b===null){if(a!==null)throw Error('padding mismatch');}else if(typeof a!=='number'||!Number.isFinite(a)||Math.abs(a-b)>1e-9*Math.max(1,Math.abs(b)))throw Error('numerical disagreement');}
export function lessonFromReceipt(r){
 const pin=pins[r?.capability],a=r?.arguments??r?.request?.arguments;
 if(r?.schema!=='umbra.repository.execution.v1'||!pin||pin.some((x,i)=>x!==[r.repository,r.revision,r.source_sha256][i])||r.independently_checked!==true||!a||!r.result)throw Error('receipt identity');
 let v,prompt,explanation;
 if(r.capability==='forecast_metrics'||r.capability==='forecast_crosscheck'){
  const y=vector(a.actual),p=vector(a.predicted);if(y.length!==p.length)throw Error('shape');
  const d=y.map((x,i)=>x-p[i]),mae=mean(d.map(Math.abs)),mse=mean(d.map(x=>x*x));
  near(r.result.mae,mae);near(r.result.mse,mse);near(r.result.rmse,Math.sqrt(mse));
  if(r.capability==='forecast_metrics'){near(r.result.quantile_loss,mae/2);v=mae;prompt='Actual '+JSON.stringify(y)+', predictions '+JSON.stringify(p)+'. Compute mean absolute error, rounded to six decimal places.';explanation='Average the absolute forecast errors.';}
  else{if(y.some(x=>Math.abs(x)<1e-9))throw Error('percentage denominator');near(r.result.mape,mean(d.map((x,i)=>Math.abs(x/y[i]))));near(r.result.mspe,mean(d.map((x,i)=>(x/y[i])**2)));v=Math.sqrt(mse);prompt='Actual '+JSON.stringify(y)+', predictions '+JSON.stringify(p)+'. Compute root mean squared error, rounded to six decimal places.';explanation='Square the errors, average them, and take the square root.';}
 }else if(r.capability==='simulation_latency'){
  const m=vector(a.meters);if(m.some(x=>x<0)||!Number.isFinite(a.signal)||!Number.isFinite(a.beta)||Math.abs(a.signal)>100||a.beta<0||a.beta>100)throw Error('latency inputs');
  const z=a.signal*a.beta,logistic=z>=0?1/(1+Math.exp(-z)):Math.exp(z)/(1+Math.exp(z));
  near(r.result.light_nanoseconds,m.map(x=>Math.trunc(x/.299792458)));near(r.result.sigmoid,logistic);
  v=logistic;prompt='Evaluate logistic sigmoid 1/(1+exp(-signal*beta)) for signal '+a.signal+' and beta '+a.beta+', rounded to six decimal places.';explanation='Apply the logistic transformation to the scaled signal.';
 }else if(r.capability==='timeseries_windows'){
  const x=vector(a.values),n=a.sections;if(!Number.isInteger(n)||n<1||n>x.length)throw Error('section count');
  const width=Math.ceil(x.length/n),q=Math.floor(x.length/n),rem=x.length%n;let start=0;
  const expected=Array.from({length:n},(_,i)=>{const count=q+Number(i<rem),part=x.slice(start,start+count);start+=count;return [...part,...Array(width-count).fill(null)];});
  near(r.result.windows,expected);v=width*n-x.length;prompt='Split '+JSON.stringify(x)+' into '+n+' nearly equal consecutive sections and right-pad each to the longest section. How many padding values are needed? Give six decimal places.';explanation='Total padded capacity minus original sequence length.';
 }else{
  const x=vector(a.coefficients),w=a.weight;if(!Number.isFinite(w)||w<0||w>1000)throw Error('penalty weight');
  near(r.result.l1_prox,x.map(v=>Math.sign(v)*Math.max(0,Math.abs(v)-w)));near(r.result.l2_prox,x.map(v=>v/(1+2*w)));
  near(r.result.l1_penalty,w*sum(x.map(Math.abs)));near(r.result.l2_penalty,w*sum(x.map(v=>v*v)));
  v=w*sum(x.map(Math.abs));prompt='For coefficients '+JSON.stringify(x)+' and L1 penalty weight '+w+', compute the weighted L1 norm to six decimal places.';explanation='Multiply the sum of absolute coefficients by the weight.';
 }
 const answer=v.toFixed(6),options=[answer,(v+1).toFixed(6),(v-1).toFixed(6),(v+2).toFixed(6)];
 if(new Set(options).size!==4||prompt.length>512)throw Error('lesson budget');
 const evidence=sha({capability:r.capability,pin,arguments:a,result:r.result});
 const shift=parseInt(evidence.slice(0,2),16)%4;return {prompt,answer,options:[...options.slice(shift),...options.slice(0,shift)],domain:'repository_'+r.capability,seed:0,level:1,prompt_sha256:ph(prompt),source:'repository_verified',repository_lesson_id:evidence,repository:r.repository,revision:r.revision,source_sha256:r.source_sha256,explanation};
}
export function augmentRepositoryCorpus(base,receipts){
 if(!base||!['training','retention','transfer'].every(k=>Array.isArray(base[k]))||!Array.isArray(receipts)||receipts.length>128)throw Error('corpus input');
 const out=structuredClone(base);out.training=out.training.filter(x=>!x.repository_lesson_id);
 if(out.training.length>128)throw Error('corpus budget');
 const original=out.training.slice(),added=[];
 const seen=new Set([...out.training,...out.retention,...out.transfer].map(x=>x.prompt));
 for(const r of receipts){const l=lessonFromReceipt(r);if(seen.has(l.prompt)||out.training.length>=128)continue;seen.add(l.prompt);out.training.push(l);added.push(l);}
 out.training=[];for(let i=0;i<Math.max(original.length,added.length);i++){if(added[i])out.training.push(added[i]);if(original[i])out.training.push(original[i]);}
 return {...out,repository_examples:added.length};
}

const fixtures=Object.freeze({forecast_metrics:{actual:[1,3,5],predicted:[2,3,2]},forecast_crosscheck:{actual:[1,3,5],predicted:[2,3,2]},simulation_latency:{meters:[0,1,300],signal:2,beta:1},timeseries_windows:{values:[1,2,3,4,5],sections:2},sparse_regularization:{coefficients:[-2,0,3],weight:.5}});
export function qualificationReceipts(q){
 if(!Array.isArray(q?.results)||q.results.length>5)throw Error('qualification schema');
 const seen=new Set(),out=[];
 for(const x of q.results){if(x.status!=='operational')continue;const r=x.receipt,a=fixtures[r?.capability];if(!a||seen.has(r.capability)||r.arguments&&sha(r.arguments)!==sha(a))throw Error('qualification inputs');seen.add(r.capability);const v={...r,arguments:a};lessonFromReceipt(v);out.push(v);}
 return out;
}
export function qualificationLessons(q){return qualificationReceipts(q).map(lessonFromReceipt);}
export function compareForecastReceipts(receipts){
 const a=receipts.find(x=>x.capability==='forecast_metrics'),b=receipts.find(x=>x.capability==='forecast_crosscheck');
 if(!a||!b)return {status:'insufficient_evidence'};
 lessonFromReceipt(a);lessonFromReceipt(b);
 if(sha(a.arguments)!==sha(b.arguments))return {status:'different_inputs'};
 for(const k of ['mae','mse','rmse'])near(a.result[k],b.result[k]);
 return {status:'agreed',metrics:['mae','mse','rmse'],source_revisions:[a.revision,b.revision],synthetic:true};
}
