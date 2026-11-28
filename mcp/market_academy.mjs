/** Market academy v1: deterministic hypothetical exercises, not actual market predictions. */
import {createHash} from 'node:crypto';
import {MARKET_KNOWLEDGE} from './market_knowledge.mjs';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const ph=x=>createHash('sha256').update(x,'utf8').digest('hex');
const int=(x,a,b)=>Number.isSafeInteger(x)&&x>=a&&x<=b;
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
export const LANES=Object.freeze(['equities','equity_valuation','index_etf','futures','options','sovereign_bonds','credit','fx','commodity_curves','crypto_derivatives','order_book','execution_cost','macro_surprises','inflation','portfolio','drawdown','leverage','swaps','yield_curve','volatility','corporate_fundamentals','causal_attribution','backtest_integrity','forecasting']);
export const SPACE=LANES.length*10*1000000;
const ASSETS=['equity index','energy future','currency','government bond','equity','digital asset'];
function rng(s){let x=s>>>0;return n=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)%n;};}
export function question(lane,level,seed){
 if(!int(lane,0,23)||!int(level,1,10)||!int(seed,1,1000000))throw Error('market address');
 const r=rng(seed+level*1000003+lane*100003),a=10+r(80*level),b=1+r(9*level),c=2+r(8*level),d=1+r(10),e=1+r(8),sign=r(2)?1:-1;
 const hard=level>=6,n=level>=9?3:hard?2:1;
 let prompt,correct,wrong,explanation;
 const numeric=(p,v,why)=>{prompt=p;correct=String(v);wrong=[v+1,v-1,v+Math.max(2,b)].map(String);explanation=why;};
 const concept=(p,v,w,why)=>{prompt=p;correct=v;wrong=w;explanation=why;};
 switch(lane){
 case 0:numeric('A stock position has '+a+' shares. Price changes by '+(sign*b)+' dollars per share and pays '+c+' dollars per share in dividends. Total dollar gain before tax?',a*(sign*b+c),'Total gain includes price change and cash distributions.');break;
 case 1:numeric('A hypothetical company has '+a+' million shares, price '+b+' dollars, cash '+c+' million and debt '+d+' million. Enterprise value in millions, ignoring other adjustments?',a*b-c+d,'Enterprise value approximates equity market value plus debt minus cash.');break;
 case 2:numeric('An ETF holds '+a+' units of asset A and '+b+' units of B at prices '+c+' and '+d+' dollars. Liabilities '+e+' dollars. Total net asset value?',a*c+b*d-e,'NAV is asset value less liabilities, not necessarily the traded price.');break;
 case 3:numeric('A '+(sign===1?'long':'short')+' futures position has '+a+' contracts, multiplier '+c+' dollars per point, price rises '+b+' points. Round-trip fees '+d+' dollars per contract. Net P&L in dollars?',a*(sign*b*c-d),'Futures P&L follows signed price change times multiplier less fees.');break;
 case 4:{const k=a,spot=a+sign*b,put=r(2);numeric('At expiration, '+c+' long '+(put?'put':'call')+' options have strike '+k+', underlying '+spot+', premium '+d+' per unit, multiplier '+e+'. Net P&L?',c*e*(Math.max(0,put?k-spot:spot-k)-d),'Intrinsic value at expiration less premium; this is not pre-expiration pricing.');break;}
 case 5:numeric('A bond portfolio has modified duration '+c+' years. Yield changes '+sign*b+' basis points. First-order price change in basis points, ignoring convexity?',-c*sign*b,'Duration gives a local approximation, holding other factors constant.');break;
 case 6:numeric('Corporate yield is '+(a+b)+' bp and matched Treasury yield '+a+' bp. The corporate yield then rises '+c+' bp while Treasury rises '+d+' bp. New credit spread in bp?',b+c-d,'Credit spread is a yield difference, not a pure default probability.');break;
 case 7:numeric('Exchange rate is quoted as quote currency per base. You hold '+a+' base units. Rate moves '+sign*b+' quote units per base. Change in quote-currency value?',a*sign*b,'Currency exposure depends on quote convention and position direction.');break;
 case 8:numeric('Cash commodity price '+a+' and futures price '+(a+sign*b)+'. Cash-minus-futures basis?',-sign*b,'Basis here means cash minus futures. Curve shape can reflect storage, financing and scarcity.');break;
 case 9:numeric('A crypto perpetual has '+a+' dollars notional. Longs pay shorts '+b+' basis points funding per interval for '+n+' intervals. Long funding cash flow in units of 0.0001 dollars, assuming constant notional?',-a*b*n,'Funding is a transfer under the stated convention; it is not a price forecast.');break;
 case 10:numeric('A buy order consumes '+a+' shares at '+b+' dollars and '+c+' shares at '+(b+d)+' dollars. Total execution cost in dollars?',a*b+c*(b+d),'Execution depends on available depth; quoted best ask is not the full fill price.');break;
 case 11:numeric('A buyer expected '+a+' dollars per unit, fills '+c+' units at '+(a+b)+' dollars, and pays '+d+' total fees. Dollar implementation shortfall?',b*c+d,'Shortfall includes adverse execution difference and explicit costs.');break;
 case 12:concept('A data release is '+(a+b)+' versus consensus '+a+'. A market falls despite this positive surprise. Which explanation is defensible?','Other expectations or risk channels may dominate',['A positive surprise guarantees a rally','The price move proves the release was false','Markets never respond to surprises'],'Price moves reflect surprises relative to expectations, positioning and multiple channels.');break;
 case 13:numeric('Nominal return '+sign*b+' bp; inflation '+c+' bp. Approximate real return in bp using subtraction (not exact compounding)?',sign*b-c,'Real return is approximately nominal return minus inflation for small rates.');break;
 case 14:numeric('A portfolio invests '+a+' dollars in A and '+c+' dollars in B. Their dollar returns per invested dollar are '+sign*b+' and '+d+' basis points. Combined gain in units of 0.0001 dollars?',a*sign*b+c*d,'Portfolio returns depend on weights and component returns; correlation affects risk.');break;
 case 15:numeric('Portfolio peak '+(a+b+c)+' dollars, later value '+(a+c)+' dollars. Dollar drawdown from that peak?',b,'Drawdown measures loss from a preceding peak; dollar and percentage drawdown differ.');break;
 case 16:numeric('An account has '+a+' dollars equity and '+c+' times gross exposure. All exposure is long; assets fall '+b+' bp. Equity loss in units of 0.0001 dollars before financing?',a*c*b,'Leverage magnifies exposure; actual liquidation depends on collateral rules.');break;
 case 17:numeric('A hypothetical interest-rate swap has '+a+' dollars notional, receives floating '+(b+c)+' bp, pays fixed '+b+' bp for a unit year fraction. Net cash flow in units of 0.0001 dollars?',a*c,'Net payment follows the contractual rate difference and accrual convention.');break;
 case 18:numeric('Two-year yield '+(a+b)+' bp; ten-year yield '+(a+c)+' bp. Ten-year rises '+d+' bp; two-year rises '+e+' bp. New 10y-minus-2y slope in bp?',c+d-b-e,'Slope describes curve shape, not a guaranteed recession signal.');break;
 case 19:numeric('A hypothetical linear vega exposure is '+a+' dollars per volatility point. Implied volatility changes '+sign*b+' points. First-order dollar P&L with other inputs fixed?',a*sign*b,'Vega approximation ignores nonlinear and other Greek effects.');break;
 case 20:numeric('A company records revenue '+(a+b+c)+' million, cost of goods '+b+' million and operating expenses '+c+' million. Operating profit before other items?',a,'Operating profit excludes financing and tax under stated assumptions.');break;
 case 21:concept('On hypothetical event '+seed+', a rate announcement and an earnings shock coincide; an index falls '+b+' bp. Can the observed move alone establish the isolated causal effect of the rate announcement?','No, concurrent shocks confound attribution',['Yes, the rate announcement caused all of it','Yes, every index fall has one cause','Yes, correlation establishes causality'],'Causal attribution needs a credible identification strategy or counterfactual.');break;
 case 22:concept('A strategy fitted at time T uses a macroeconomic value revised '+b+' days after T. Is the value available for a point-in-time backtest at T?','No, use the vintage available at T',['Yes, later revisions are always known','Yes, future revisions cannot bias results','Yes, use the final revised history'],'Using later revisions creates potential look-ahead bias.');break;
 case 23:numeric('A one-step forecast predicts '+a+' while actual is '+(a+sign*b)+'. A second forecast error is '+c+' dollars in absolute value. Sum of absolute errors?',b+c,'Absolute errors evaluate forecasts; independent chronological holdouts matter.');break;
 }
 // Higher tiers impose multi-leg reconciliation on numeric problems, using the stated original result.
 if(hard&&wrong.every(x=>/^-?\d+$/.test(x))&&/^-?\d+$/.test(correct)){
  const v=Number(correct),adjustments=Array.from({length:level-4},()=>r(21)-10),total=v+adjustments.reduce((x,y)=>x+y,0);
  prompt+=' Then add the following signed adjustments in the same result units: '+adjustments.join(', ')+'. Report final adjusted result.';
  correct=String(total);wrong=[total+1,total-1,total+Math.max(2,b)].map(String);
  explanation+=' Reconcile each signed adjustment in the stated units.';
 }
 const options=[correct,...wrong];if(new Set(options).size!==4||prompt.length>512)throw Error('invalid market question');
 for(let i=3;i>0;i--){const j=r(i+1);[options[i],options[j]]=[options[j],options[i]];}
 return {id:'m'+lane+'_'+level+'_'+seed,lane:LANES[lane],lane_index:lane,level,seed,prompt,options,correct,explanation};
}
export function gradeMarket(model,questions,answers){
 if(!model||typeof model.model!=='string'||!hex(model.manifest_digest)||!Array.isArray(questions)||questions.length<1||questions.length>4||!Array.isArray(answers)||answers.length!==questions.length||new Set(questions.map(q=>q.id)).size!==questions.length||new Set(answers.map(a=>a.id)).size!==answers.length)throw Error('market receipt schema');
 const rows=questions.map(q=>{const k=question(q.lane_index,q.level,q.seed);if(hash(q)!==hash(k))throw Error('task mismatch');const a=answers.find(x=>x.id===q.id);if(!a||!q.options.includes(a.answer)||![50,75,95].includes(a.confidence))throw Error('answer schema');return {id:q.id,lane:q.lane_index,level:q.level,seed:q.seed,answer:a.answer,confidence:a.confidence,correct:a.answer===q.correct};});
 const v={schema:'umbra.market.receipt.v1',model:model.model,manifest_digest:model.manifest_digest,rows,correct:rows.filter(r=>r.correct).length,high_confidence_errors:rows.filter(r=>!r.correct&&r.confidence===95).length,synthetic:true,production_authority:false};return {...v,evidence:hash(v)};
}
export function verifyMarket(r){const v=gradeMarket(r,r.rows.map(x=>question(x.lane,x.level,x.seed)),r.rows);if(hash(v)!==hash(r))throw Error('receipt mismatch');return v;}
export function selectMarketTask(model,lane,history,seed){
 const rows=history.map(verifyMarket).filter(r=>r.model===model.model&&r.manifest_digest===model.manifest_digest).flatMap(r=>r.rows).filter(r=>r.lane===lane);
 let level=1;
 for(;level<10;level++){const recent=rows.filter(r=>r.level===level).sort((a,b)=>a.seed-b.seed).slice(-12);if(recent.length<12||new Set(recent.map(r=>r.seed)).size<12||recent.filter(r=>r.correct).length<11)break;}
 return question(lane,level,seed);
}
export function marketCorpus(base,seed,level=1,history=[]){
 if(!int(seed,1,1000000)||!int(level,1,10))throw Error('market corpus request');
 if(!base||!['training','retention','transfer'].every(k=>Array.isArray(base[k]))||base.training.length>96||base.retention.length>24||base.transfer.length>24)throw Error('base corpus budget');
 const out=structuredClone(base),seen=new Set([...out.training,...out.retention,...out.transfer].map(r=>r.prompt));
 let teacherCount=0;
 for(const receipt of history.map(verifyMarket).filter(r=>r.model==='qwen2.5-coder:7b').slice(-64))for(const row of receipt.rows){
  if(teacherCount>=8||!row.correct||row.seed<600001||row.seed>800000||row.level>level)continue;
  const q=question(row.lane,row.level,row.seed);if(seen.has(q.prompt))continue;seen.add(q.prompt);
  out.training.push({prompt:q.prompt,answer:q.correct,options:q.options,domain:'market_'+q.lane,seed:q.seed,level:q.level,prompt_sha256:ph(q.prompt),source:'teacher',teacher:receipt.model,teacher_digest:receipt.manifest_digest,lesson_evidence:receipt.evidence,market_task_id:q.id});teacherCount++;
 }
 let factCount=0;
 for(const card of MARKET_KNOWLEDGE){
  if(seen.has(card.prompt))continue;
  seen.add(card.prompt);const {id,...fact}=card;const opts=[...fact.options];const random=rng(seed+factCount*997);for(let j=3;j>0;j--){const k=random(j+1);[opts[j],opts[k]]=[opts[k],opts[j]];}
  out.training.push({...fact,options:opts,prompt_sha256:ph(fact.prompt),market_task_id:id,seed:0});factCount++;
 }
 for(const [key,count,offset] of [['training',32-teacherCount-factCount,0],['retention',8,200000],['transfer',8,400000]]){
  let added=0;
  for(let i=0;i<500&&added<count;i++){
   // Disjoint deterministic seed bands by split, lane and cycle; exact prompt deduplication.
   const s=offset+1+((seed*97+i*113)%200000),k=(seed+i)%LANES.length,l=key==='retention'?1:level,q=question(k,l,s);
   if(seen.has(q.prompt))continue;seen.add(q.prompt);out[key].push({prompt:q.prompt,answer:q.correct,options:q.options,domain:'market_'+q.lane,seed:q.seed,level:q.level,prompt_sha256:ph(q.prompt),source:'symbolic_verified',market_task_id:q.id});added++;
  }
  if(added!==count)throw Error('market corpus coverage');
 }
 return {...out,market_scope:'synthetic_not_market_forecast',market_level:level,market_examples:48,market_teacher_examples:teacherCount,market_reviewed_facts:factCount};
}
