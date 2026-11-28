/** Independent bounded parser for generated curriculum tasks. Never executes supplied code. */
import {solveProbe} from './gap_tools.mjs';
const nums=s=>s.split(', ').map(x=>x.split('/').map(Number));
const sum=a=>a.reduce((x,y)=>x+y,0);
export function solveAdvanced(q){
 if(!q||typeof q.prompt!=='string'||q.prompt.length>2048||!Array.isArray(q.options)||q.options.length!==4)return null;
 const p=q.prompt;let m,a;
 if(m=p.match(/^Compute \((\d+) \* (\d+) - (\d+)\) \* (\d+) \+ (\d+)\.$/)){const [x,y,z,w,k]=m.slice(1).map(Number);a=(x*y-z)*w+k;}
 else if(m=p.match(/^Compute the least nonnegative remainder of \(\((\d+) \* (\d+) - (\d+)\) \* (\d+) \+ (\d+)\) divided by (\d+)\.$/)){const [x,y,z,w,k,n]=m.slice(1).map(Number);if(!n)return null;a=((x*y*w-z*w+k)%n+n)%n;}
 else if(m=p.match(/^Facts: (P\d+) is true(?:; Z is false)?\. Rules: (.+)\. Which is necessarily true\?$|^Facts: (P\d+) is true; Z is false\. Rules: (.+)\. Under forward chaining, which is derivable\?$/)){
  const known=new Set([m[1]||m[3]]),rules=(m[2]||m[4]).split('; ').map(x=>x.split(' implies '));
  for(let i=0;i<rules.length;i++)for(const [left,right] of rules)if(left&&right&&left.split(' AND ').every(x=>known.has(x)))known.add(right);
  const valid=q.options.filter(x=>x.endsWith(' is true')&&known.has(x.slice(0,-8)));if(valid.length===1)a=valid[0];
 }
 else if(m=p.match(/^Schedule these tasks subject to every constraint: (.+)\. Select a valid order\.$/)){
  const edges=m[1].split('; ').map(x=>x.split(' before ')),nodes=new Set(edges.flat());
  const valid=q.options.filter(x=>x.length===nodes.size&&new Set(x).size===nodes.size&&[...x].every(v=>nodes.has(v))&&edges.every(([u,v])=>x.indexOf(u)<x.indexOf(v)));if(valid.length===1)a=valid[0];
 }
 else if(m=p.match(/^One worker, no overlap or idle time\. Precedence: (.+)\. Durations: (.+)\. Earliest finish time of the last task if time starts at 0\?$/)){
  const edges=m[1].split('; ').map(x=>x.split(' before ')),duration=new Map(m[2].split(', ').map(x=>{const [n,v]=x.split('=');return [n,Number(v)];}));const done=new Set();for(let i=0;i<duration.size;i++){const n=[...duration.keys()].find(x=>!done.has(x)&&edges.filter(e=>e[1]===x).every(e=>done.has(e[0])));if(n===undefined)return null;done.add(n);}a=sum([...duration.values()]);
 }
 else if(m=p.match(/^Equal-sized randomized strata have treated\/control means (.+)\. What is the sum of within-stratum treatment-minus-control differences\?$/))a=sum(nums(m[1]).map(([t,c])=>t-c));
 else if(m=p.match(/^Randomized strata \(weight, treated mean, control mean\): (.+)\. Calculate the numerator of the weighted average treatment effect, sum\(weight\*\(treated-control\)\)\.$/))a=sum(nums(m[1]).map(([w,t,c])=>w*(t-c)));
 else if(m=p.match(/^Pseudocode: x=(\d+); for j=1 through (\d+): if j is even add j\*(\d+) to x, otherwise subtract j\. Return x\.$/)){const [x,n,k]=m.slice(1).map(Number);if(n>1000)return null;const e=Math.floor(n/2),o=Math.ceil(n/2);a=x+k*e*(e+1)-o*o;}
 else if(m=p.match(/^Pseudocode: x=(\d+); for j=1 through (\d+): x=\(x\*(\d+)\+j\) mod (\d+)\. Return x\.$/)){let [x,n,k,mod]=m.slice(1).map(Number);if(n>1000||mod===0)return null;for(let i=0;i<n;i++)x=(k*x+i+1)%mod;a=x;}
 else if(m=p.match(/^Records indexed from 1, available\/reserved: (.+)\. Sum reserved values for odd-numbered records\.$/))a=sum(nums(m[1]).filter((_,i)=>i%2===0).map(x=>x[1]));
 else if(m=p.match(/^Records indexed from 1, available\/reserved: (.+)\. For odd records with available > reserved, sum available minus reserved\.$/))a=sum(nums(m[1]).filter((x,i)=>i%2===0&&x[0]>x[1]).map(([x,y])=>x-y));
 else if(m=p.match(/^Repeat XY exactly (\d+) times then append (\d+) without spaces\.$/)){if(+m[1]>100)return null;a='XY'.repeat(+m[1])+m[2];}
 else if(m=p.match(/^Write (\d+), then reverse each XY pair in (\d+) repeated pairs, then append Z\. No spaces\.$/)){if(+m[2]>100)return null;a=m[1]+'YX'.repeat(+m[2])+'Z';}
 else if(m=p.match(/^There are (\d+) items split across (\d+) labeled boxes\. Each box has at least one item\. No counts per box are supplied\. What is the exact count in box (\d+)\?$/)){const [n,k,b]=m.slice(1).map(Number);if(b<1||b>k||n<k)return null;a=n===k?1:'insufficient evidence';}
 else if(m=p.match(/^There are (\d+) items across (\d+) boxes\. All boxes except box (\d+) contain (\d+) items in total\. What is the exact count in that box\?$/)){const [n,k,b,o]=m.slice(1).map(Number);if(b<1||b>k||o>n)return null;a=n-o;}
 else return solveProbe(q);
 return q.options.includes(String(a))?String(a):null;
}
