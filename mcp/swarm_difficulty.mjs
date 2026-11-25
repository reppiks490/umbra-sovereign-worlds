/** Versioned seed bands preserve all legacy receipts; levels 1-10 extend eight domains. */
import {battery} from './intelligence_gaps.mjs';
const BAND=20000000,OFFSET=700000000;
export function levelOf(seed){
 const s=seed>=OFFSET&&seed<OFFSET+10*BAND?seed-OFFSET:seed;
 return s>=BAND&&s<10*BAND?1+Math.floor(s/BAND):1;
}
export function encodeLevel(seed,level){
 if(!Number.isSafeInteger(seed)||seed<1||seed>=10000000||!Number.isSafeInteger(level)||level<1||level>10)throw Error('difficulty seed');
 return seed+(level===1?10000000:(level-1)*BAND);
}
function rng(seed){let x=seed>>>0;return n=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)%n;};}
export function swarmBattery(seed){
 const level=levelOf(seed),base=seed>=OFFSET&&seed<OFFSET+10*BAND?seed-OFFSET:seed;
 if(level===1&&!(base>=10000000&&base<BAND))return battery(seed);
 const next=rng(seed),out=[];
 function add(domain,prompt,answer,wrong){
  const options=[answer,...wrong].map(String);
  if(new Set(options).size!==4)throw Error('duplicate options');
  for(let i=3;i>0;i--){const j=next(i+1);[options[i],options[j]]=[options[j],options[i]];}
  out.push({id:'q'+(out.length+1),domain,prompt,options,correct:String(answer)});
 }
 for(let round=0;round<2;round++){
  const a=next(30*level)+12,b=next(9*level)+3,c=next(20)+2,d=next(8)+2,e=next(19)+1;
  const v=(a*b-c)*d+e;
  if(level<6)add('arithmetic','Compute ('+a+' * '+b+' - '+c+') * '+d+' + '+e+'.',v,[v+1,v+c,v-e]);
  else {const mod=next(91)+101,ans=((v%mod)+mod)%mod;add('arithmetic','Compute the least nonnegative remainder of (('+a+' * '+b+' - '+c+') * '+d+' + '+e+') divided by '+mod+'.',ans,[ans+mod,ans+1,ans-1]);}
  const n=level+3,start=next(10000)+10,labels=Array.from({length:n},(_,j)=>'P'+(start+j));
  const rules=labels.slice(1).map((x,i)=>labels[i]+' implies '+x).reverse().join('; ');
  if(level<6)add('logic','Facts: '+labels[0]+' is true. Rules: '+rules+'. Which is necessarily true?',labels[n-1]+' is true',[labels[n-1]+' is false','No rule can fire','The first fact is false']);
  else add('logic','Facts: '+labels[0]+' is true; Z is false. Rules: '+rules+'; '+labels[n-1]+' AND Z implies W. Under forward chaining, which is derivable?',labels[n-1]+' is true',['W is true','Z is true',labels[0]+' is false']);
  const offset=next(26-n),order=Array.from({length:n},(_,j)=>String.fromCharCode(65+offset+j));
  for(let i=n-1;i>0;i--){const j=next(i+1);[order[i],order[j]]=[order[j],order[i]];}
  const edges=order.slice(1).map((x,i)=>order[i]+' before '+x).reverse().join('; ');
  const bad=i=>{const x=order.slice();[x[i],x[i+1]]=[x[i+1],x[i]];return x.join('');};
  if(level<6)add('planning','Schedule these tasks subject to every constraint: '+edges+'. Select a valid order.',order.join(''),[bad(0),bad(1),bad(2)]);
  else {const durations=order.map(()=>next(9)+1),sum=durations.reduce((x,y)=>x+y,0);add('planning','One worker, no overlap or idle time. Precedence: '+edges+'. Durations: '+order.map((x,i)=>x+'='+durations[i]).join(', ')+'. Earliest finish time of the last task if time starts at 0?',sum,[sum-1,sum+1,sum+durations[0]+1]);}
  const strata=Array.from({length:level},()=>{const control=next(20)+5;return [control+next(8)+1,control];});
  const effect=strata.reduce((s,[t,c])=>s+t-c,0);
  if(level<6)add('causality','Equal-sized randomized strata have treated/control means '+strata.map(x=>x.join('/')).join(', ')+'. What is the sum of within-stratum treatment-minus-control differences?',effect,[effect+1,effect+2,-effect]);
  else {const w=strata.map(()=>next(8)+1),weighted=strata.reduce((s,[t,c],i)=>s+w[i]*(t-c),0);add('causality','Randomized strata (weight, treated mean, control mean): '+strata.map(([t,c],i)=>[w[i],t,c].join('/')).join(', ')+'. Calculate the numerator of the weighted average treatment effect, sum(weight*(treated-control)).',weighted,[weighted+1,weighted+2,-weighted]);}
  const k=next(9)+1,m=next(7)+1,loops=level*2+next(5);let val=k;
  for(let j=1;j<=loops;j++)val+=j%2===0?j*m:-j;
  if(level<6)add('code_tracing','Pseudocode: x='+k+'; for j=1 through '+loops+': if j is even add j*'+m+' to x, otherwise subtract j. Return x.',val,[val+1,val-1,val+loops]);
  else {let x=k;const mod=next(71)+31;for(let j=1;j<=loops;j++)x=(x*m+j)%mod;add('code_tracing','Pseudocode: x='+k+'; for j=1 through '+loops+': x=(x*'+m+'+j) mod '+mod+'. Return x.',x,[x+1,x+mod,x-1]);}
  const records=Array.from({length:level+1},()=>[next(50)+1,next(30)+1]);
  const total=records.reduce((s,[x,y],i)=>s+(i%2===0?y:0),0);
  if(level<6)add('data_extraction','Records indexed from 1, available/reserved: '+records.map(x=>x.join('/')).join(', ')+'. Sum reserved values for odd-numbered records.',total,[total+1,total+2,total-1]);
  else {const ans=records.reduce((s,[x,y],i)=>s+(i%2===0&&x>y?x-y:0),0);add('data_extraction','Records indexed from 1, available/reserved: '+records.map(x=>x.join('/')).join(', ')+'. For odd records with available > reserved, sum available minus reserved.',ans,[ans+1,ans+2,ans-1]);}
  const count=level+next(5),suffix=next(900)+100,pat='XY'.repeat(count)+suffix;
  if(level<6)add('instruction_following','Repeat XY exactly '+count+' times then append '+suffix+' without spaces.',pat,['XY'.repeat(count+1)+suffix,'YX'.repeat(count)+suffix,'XY'.repeat(count)+(suffix+1)]);
  else {const ans=suffix+'YX'.repeat(count)+'Z';add('instruction_following','Write '+suffix+', then reverse each XY pair in '+count+' repeated pairs, then append Z. No spaces.',ans,[suffix+'XY'.repeat(count)+'Z',suffix+'YX'.repeat(count+1)+'Z',suffix+'YX'.repeat(count)+'X']);}
  const known=next(1000)+20;
  const box=1+next(level+2);
  if(level>=6&&round===1){const others=known-level-2;add('abstention','There are '+known+' items across '+(level+2)+' boxes. All boxes except box '+box+' contain '+others+' items in total. What is the exact count in that box?',known-others,[known-others+1,known-others-1,'insufficient evidence']);}
  else add('abstention','There are '+known+' items split across '+(level+2)+' labeled boxes. Each box has at least one item. No counts per box are supplied. What is the exact count in box '+box+'?','insufficient evidence',['1',String(known-level-1),String(known)]);
 }
 return out;
}
// Assessment receipts must already have been independently replayed by caller.
export function nextLevel(receipts){
 let level=1;
 for(;level<10;level++){
  const rows=receipts.filter(r=>levelOf(r.seed)===level&&r.seed<200000000&&!r.lesson_evidence?.length).sort((a,b)=>a.seed-b.seed).slice(-24);
  if(rows.length<24||new Set(rows.map(r=>r.model_digest)).size!==1||rows.filter(r=>r.success).length<22||new Set(rows.flatMap(r=>swarmBattery(r.seed).filter(q=>q.domain===r.agent.domain).map(q=>q.prompt))).size<32)break;
 }
 return level;
}
