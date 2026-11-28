/** Lightweight scientific and temporal learning experiments, independent of LLM downloads. */
import {trainContinual} from './megaswarm.mjs';
const int=(x,a,b)=>Number.isSafeInteger(x)&&x>=a&&x<=b;
const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
function rng(seed){if(!int(seed,1,4294967295))throw Error('seed');let x=seed>>>0;return ()=>{x=(Math.imul(1664525,x)+1013904223)>>>0;return x/4294967296;};}
export function generateSeries(seed,n=96){
 if(!int(n,32,512))throw Error('series size');const r=rng(seed);
 return Array.from({length:n},(_,i)=>10+.05*i+2*Math.sin(2*Math.PI*i/12)+(r()-.5)*.5);
}
function fitLinear(x,y){
 const mx=mean(x),my=mean(y),den=x.reduce((s,v)=>s+(v-mx)**2,0);
 const b=den?x.reduce((s,v,i)=>s+(v-mx)*(y[i]-my),0)/den:0;return {a:my-b*mx,b};
}
export function forecastAudit(y,cut){
 if(!Array.isArray(y)||y.length>512||!y.every(Number.isFinite)||!int(cut,24,y.length-8))throw Error('invalid forecast data');
 const train=y.slice(0,cut),trend=fitLinear(train.map((_,i)=>i),train);
 const season=Array.from({length:12},(_,k)=>mean(train.map((v,i)=>({v,i})).filter(x=>x.i%12===k).map(x=>x.v-trend.a-trend.b*x.i)));
 const definitions=[['last_value',i=>y[i-1]],['seasonal_naive',i=>y[i-12]],['trend_seasonal',i=>trend.a+trend.b*i+season[i%12]]];
 // Select on internal training-only validation, not the final holdout.
 const inner=cut-12,innerTrain=y.slice(0,inner),t=fitLinear(innerTrain.map((_,i)=>i),innerTrain);
 const s=Array.from({length:12},(_,k)=>mean(innerTrain.map((v,i)=>({v,i})).filter(x=>x.i%12===k).map(x=>x.v-t.a-t.b*x.i)));
 const validation=[mean(y.slice(inner,cut).map((v,i)=>Math.abs(v-y[inner+i-1]))),mean(y.slice(inner,cut).map((v,i)=>Math.abs(v-y[inner+i-12]))),mean(y.slice(inner,cut).map((v,i)=>Math.abs(v-t.a-t.b*(inner+i)-s[(inner+i)%12])))];
 const chosen=validation.indexOf(Math.min(...validation));
 const models=definitions.map(([name,p],j)=>({name,validation_mae:validation[j],mae:mean(y.slice(cut).map((v,i)=>Math.abs(v-p(cut+i))))}));
 return {schema:'umbra.research.forecast.v1',train_count:cut,test_count:y.length-cut,selected:models[chosen].name,models,predictions:y.slice(cut).map((actual,i)=>({index:cut+i,actual,predicted:definitions[chosen][1](cut+i)})),protocol:'one-step rolling-origin; fixed fitted coefficients',synthetic:true,production_authority:false};
}
export function causalTrial(seed,n,effect){
 if(!int(n,32,512)||!Number.isFinite(effect)||Math.abs(effect)>10)throw Error('causal budget');
 const r=rng(seed),rows=Array.from({length:n},(_,i)=>{const confound=i%2,base=5+3*confound+r(),treated=confound===1;return {base,treated,observed:base+(treated?effect:0),counterfactual:base+effect};});
 return {schema:'umbra.research.causal.v1',pairs:n,effect:mean(rows.map(x=>x.counterfactual-x.base)),placebo:mean(rows.map(x=>x.base-x.base)),naive_observational_difference:mean(rows.filter(x=>x.treated).map(x=>x.observed))-mean(rows.filter(x=>!x.treated).map(x=>x.observed)),empirical_validity:false,synthetic:true,production_authority:false};
}
export function hypothesisSearch(seed){
 const r=rng(seed),train_seeds=Array.from({length:24},(_,i)=>seed*64+i),test_seeds=Array.from({length:12},(_,i)=>300000000+seed*64+i);
 const sample=s=>{const rr=rng(s),x=rr()*2-1;return {x,y:.3+.6*x*x+(rr()-.5)*.02};};
 const a=train_seeds.map(sample),b=test_seeds.map(sample),fns=[['constant',x=>0],['linear',x=>x],['quadratic',x=>x*x],['absolute',x=>Math.abs(x)]];
 const hypotheses=fns.map(([name,f])=>{const fit=fitLinear(a.map(r=>f(r.x)),a.map(r=>r.y));return {name,...fit,train_mse:mean(a.map(r=>(r.y-fit.a-fit.b*f(r.x))**2))};}).sort((a,b)=>a.train_mse-b.train_mse||a.name.localeCompare(b.name));
 const best=hypotheses[0],fn=fns.find(x=>x[0]===best.name)[1];
 return {schema:'umbra.research.hypothesis.v1',train_seeds,test_seeds,hypotheses,selected:best.name,test_mse:mean(b.map(r=>(r.y-best.a-best.b*fn(r.x))**2)),synthetic:true,production_authority:false};
}
export function runResearch(seed){
 const r=rng(seed),rows=(domain,n)=>Array.from({length:n},()=>{const x=r()*2-1;return {features:[x,domain],reward:domain===0?.5*x+.2:.5*x*x+.1};});
 const old=rows(0,48),newRows=rows(1,48),retention=rows(0,24),transfer=rows(1,24);
 return {schema:'umbra.research.learning.v1',seed,continual:trainContinual({old,newRows,retention,transfer,seed}),forecast:forecastAudit(generateSeries(seed),72),causal:causalTrial(seed,128,2),hypothesis:hypothesisSearch(seed),synthetic:true,production_authority:false};
}
