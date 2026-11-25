/** Dependency-free bounded neural regression, ensemble uncertainty and distillation. */
const int=(n,a,b)=>Number.isSafeInteger(n)&&n>=a&&n<=b;
const finite=(v)=>Number.isFinite(v)&&Math.abs(v)<=100;
function rng(seed){let s=seed>>>0;return ()=>{s=(Math.imul(1664525,s)+1013904223)>>>0;return s/4294967296;};}
function examples(rows){
 if(!Array.isArray(rows)||!int(rows.length,2,512))throw Error('invalid examples');
 const dim=rows[0]?.features?.length;
 if(!int(dim,1,32)||rows.some(r=>!Array.isArray(r.features)||r.features.length!==dim||!r.features.every(x=>finite(x)&&Math.abs(x)<=10)||!finite(r.reward)))throw Error('invalid examples');
 return dim;
}
function forward(l,x){
 const h=l.hidden.map((r)=>Math.tanh(r[0]+x.reduce((s,v,i)=>s+r[i+1]*v,0)));
 return {h,y:l.output[0]+h.reduce((s,v,j)=>s+v*l.output[j+1],0)};
}
function valid(n,x){
 if(n?.schema!=='umbra.autogenesis.neural.v1'||!int(n.dim,1,32)||!int(n.width,2,32)||!Array.isArray(x)||x.length!==n.dim||!x.every(v=>finite(v)&&Math.abs(v)<=10))throw Error('invalid input');
 const {hidden,output}=n.layers||{};
 if(!Array.isArray(hidden)||hidden.length!==n.width||hidden.some(r=>!Array.isArray(r)||r.length!==n.dim+1||!r.every(finite))||!Array.isArray(output)||output.length!==n.width+1||!output.every(finite))throw Error('invalid network');
}
export function inferNetwork(n,x){valid(n,x);return forward(n.layers,x).y;}
export function evaluateNetwork(n,rows){examples(rows);return rows.reduce((s,r)=>s+(inferNetwork(n,r.features)-r.reward)**2,0)/rows.length;}
export function trainNetwork(rows,{seed=1,epochs=100,width=8,rate=.08}={}){
 const dim=examples(rows);
 if(!int(seed,1,4294967295)||!int(epochs,1,250)||!int(width,2,32)||!Number.isFinite(rate)||rate<=0||rate>.2)throw Error('invalid training budget');
 const r=rng(seed),l={hidden:Array.from({length:width},()=>Array.from({length:dim+1},()=>((r()-.5)*2)/Math.sqrt(dim))),output:Array.from({length:width+1},()=>((r()-.5)*2)/Math.sqrt(width))};
 const n={schema:'umbra.autogenesis.neural.v1',dim,width,layers:l,synthetic:true};
 const initial=evaluateNetwork(n,rows);
 for(let e=0;e<epochs;e++){
  const gh=l.hidden.map(v=>v.map(()=>0)),go=l.output.map(()=>0);
  for(const row of rows){
   const {h,y}=forward(l,row.features),err=y-row.reward;
   go[0]+=err;
   for(let j=0;j<width;j++){go[j+1]+=err*h[j];const delta=err*l.output[j+1]*(1-h[j]**2);gh[j][0]+=delta;for(let i=0;i<dim;i++)gh[j][i+1]+=delta*row.features[i];}
  }
  for(let j=0;j<width;j++)for(let i=0;i<=dim;i++)l.hidden[j][i]-=rate*gh[j][i]/rows.length;
  for(let j=0;j<=width;j++)l.output[j]-=rate*go[j]/rows.length;
 }
 n.training={examples:rows.length,epochs,initial_mse:initial,final_mse:evaluateNetwork(n,rows),parameters:width*(dim+2)+1};
 return n;
}
export function trainCommittee(rows,{seed=1,epochs=100,width=8,members=3}={}){
 examples(rows);
 if(!int(members,2,5)||!int(seed,1,4294967290))throw Error('invalid committee budget');
 // Independent initializations and bootstraps, deterministic from seed.
 const r=rng(seed),models=[];
 for(let i=0;i<members;i++)models.push(trainNetwork(Array.from({length:rows.length},()=>rows[Math.floor(r()*rows.length)]),{seed:seed+i,epochs,width}));
 return {schema:'umbra.autogenesis.committee.v1',members:models,synthetic:true};
}
export function committeePredict(c,x){
 if(c?.schema!=='umbra.autogenesis.committee.v1'||!Array.isArray(c.members)||!int(c.members.length,2,5))throw Error('invalid committee');
 const predictions=c.members.map(n=>inferNetwork(n,x)),mean=predictions.reduce((s,v)=>s+v,0)/predictions.length,sd=Math.sqrt(predictions.reduce((s,v)=>s+(v-mean)**2,0)/predictions.length);
 return {mean,sd,predictions};
}
export function distillCommittee(c,features,options={}){
 if(!Array.isArray(features)||!int(features.length,2,512))throw Error('invalid distillation examples');
 return trainNetwork(features.map(x=>({features:x,reward:committeePredict(c,x).mean})),options);
}
