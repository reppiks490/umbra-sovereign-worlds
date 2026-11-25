/** Independent narrow parser for four reviewed synthetic market question templates. */
const abstain=()=>({status:'abstain',production_authority:false});
const finiteInt=v=>Number.isSafeInteger(v)&&Math.abs(v)<=1e9;
export function solveMarket({prompt,options}={}){
 if(typeof prompt!=='string'||prompt.length>512||!Array.isArray(options)||options.length!==4||options.some(x=>typeof x!=='string')||new Set(options).size!==4)return abstain();
 let base=prompt,adjust=0,answer=null,rule=null;
 const suffix=base.match(/ Then add the following signed adjustments in the same result units: (-?\d+(?:, -?\d+){1,5})\. Report final adjusted result\.$/);
 if(suffix){const values=suffix[1].split(', ').map(Number);if(values.some(x=>!finiteInt(x)||Math.abs(x)>10))return abstain();adjust=values.reduce((a,b)=>a+b,0);base=base.slice(0,suffix.index);}
 let m=base.match(/^A (long|short) futures position has (\d+) contracts, multiplier (\d+) dollars per point, price rises (\d+) points\. Round-trip fees (\d+) dollars per contract\. Net P&L in dollars\?$/);
 if(m){const [n,mult,change,fee]=m.slice(2).map(Number);if(![n,mult,change,fee].every(x=>finiteInt(x)&&x>0))return abstain();answer=String(n*((m[1]==='long'?1:-1)*mult*change-fee)+adjust);rule='signed_futures_pnl';}
 else if(m=base.match(/^A buyer expected (\d+) dollars per unit, fills (\d+) units at (\d+) dollars, and pays (\d+) total fees\. Dollar implementation shortfall\?$/)){
  const [expected,n,fill,fees]=m.slice(1).map(Number);if(![expected,n,fill,fees].every(x=>finiteInt(x)&&x>0))return abstain();answer=String((fill-expected)*n+fees+adjust);rule='implementation_shortfall';
 }else if(!suffix&&/^On hypothetical event \d+, a rate announcement and an earnings shock coincide; an index falls \d+ bp\. Can the observed move alone establish the isolated causal effect of the rate announcement\?$/.test(base)){
  answer='No, concurrent shocks confound attribution';rule='causal_identification';
 }else if(!suffix&&/^A strategy fitted at time T uses a macroeconomic value revised \d+ days after T\. Is the value available for a point-in-time backtest at T\?$/.test(base)){
  answer='No, use the vintage available at T';rule='point_in_time';
 }
 if(answer===null||!options.includes(answer)||(/^-?\d+$/.test(answer)&&!finiteInt(Number(answer))))return abstain();
 return {status:'solved',answer,rule,scope:'reviewed synthetic template only',production_authority:false};
}
export function compareEvidence(task,modelAnswer,truth){
 if(!task?.options?.includes(truth)||!task.options.includes(modelAnswer))throw Error('invalid evaluation evidence');
 const t=solveMarket(task);
 return {model_correct:modelAnswer===truth,tool_correct:t.status==='solved'?t.answer===truth:null,system_correct:t.status==='solved'?t.answer===truth:null,source:t.status==='solved'?'deterministic_tool':'abstention',production_authority:false};
}

import {question,verifyMarket} from './market_academy.mjs';
export function verifyPair(receipts){
 if(!Array.isArray(receipts)||receipts.length!==2)throw Error('exact pair required');
 const rows=receipts.map(verifyMarket);if(new Set(rows.map(r=>r.model)).size!==2||!rows.every(r=>['qwen3:0.6b','granite4:350m'].includes(r.model)))throw Error('distinct student models required');
 const tasks=new Map(),scores=[];let errors=0,correct=0;
 for(const r of rows){
  if(r.rows.length!==4)throw Error('four matched questions required');
  const ids=r.rows.map(x=>x.id).sort().join('|');if(scores.length&&ids!==scores[0].ids)throw Error('unmatched questions');
  let n=0;for(const x of r.rows){const q=question(x.lane,x.level,x.seed),c=compareEvidence({prompt:q.prompt,options:q.options},x.answer,q.correct);n+=Number(c.model_correct);if(!tasks.has(x.id))tasks.set(x.id,c.tool_correct);}
  errors+=r.high_confidence_errors;correct+=n;scores.push({model:r.model,manifest_digest:r.manifest_digest,correct:n,questions:4,ids});
 }
 return {scope:'matched synthetic prompts; deterministic verifier, not model weight gain',model_answers:8,model_correct:correct,high_confidence_errors:errors,unique_questions:tasks.size,tool_correct:[...tasks.values()].filter(x=>x===true).length,tool_abstained:[...tasks.values()].filter(x=>x===null).length,models:scores.map(({ids,...s})=>s),production_authority:false};
}
