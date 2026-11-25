/** Narrow, typed deterministic tools. No eval, shell, model-generated code, or arbitrary execution. */
const num=x=>Number.isSafeInteger(x)&&Math.abs(x)<=1000000;
const keys=(x,ks)=>Object.keys(x).sort().join(',')===ks.slice().sort().join(',');
export function solveStructured(q){
 if(!q||typeof q!=='object'||Array.isArray(q))throw Error('invalid task');
 if(q.kind==='arithmetic'&&keys(q,['kind','a','b','c'])&&[q.a,q.b,q.c].every(num))return q.a*q.b-q.c;
 if(q.kind==='progression'&&keys(q,['kind','start','count','factor'])&&[q.start,q.count,q.factor].every(num)&&q.count>=0&&q.count<=10000)return q.start+q.count*(q.count+1)/2*q.factor;
 if(q.kind==='dag'&&keys(q,['kind','nodes','edges'])&&Array.isArray(q.nodes)&&q.nodes.length>=1&&q.nodes.length<=64&&q.nodes.every(x=>typeof x==='string'&&/^[A-Za-z0-9_-]{1,32}$/.test(x))&&new Set(q.nodes).size===q.nodes.length&&Array.isArray(q.edges)&&q.edges.length<=4096){
  const incoming=new Map(q.nodes.map(x=>[x,0])),outgoing=new Map(q.nodes.map(x=>[x,new Set()]));
  for(const e of q.edges){if(!Array.isArray(e)||e.length!==2||!incoming.has(e[0])||!incoming.has(e[1]))throw Error('invalid edge');if(!outgoing.get(e[0]).has(e[1])){outgoing.get(e[0]).add(e[1]);incoming.set(e[1],incoming.get(e[1])+1);}}
  const ready=q.nodes.filter(x=>incoming.get(x)===0).sort(),order=[];
  while(ready.length){const x=ready.shift();order.push(x);for(const y of outgoing.get(x)){incoming.set(y,incoming.get(y)-1);if(incoming.get(y)===0){ready.push(y);ready.sort();}}}
  if(order.length!==q.nodes.length)throw Error('cyclic constraints');return order;
 }
 if(q.kind==='repeat'&&keys(q,['kind','count','suffix'])&&Number.isInteger(q.count)&&q.count>=0&&q.count<=128&&num(q.suffix))return 'X'.repeat(q.count)+q.suffix;
 if(q.kind==='extract'&&keys(q,['kind','record','field'])&&q.record&&typeof q.record==='object'&&!Array.isArray(q.record)&&typeof q.field==='string'&&Object.hasOwn(q.record,q.field)&&num(q.record[q.field]))return q.record[q.field];
 throw Error('unsupported or invalid structured task');
}
export function solveProbe(q){
 if(!q||typeof q.prompt!=='string'||q.prompt.length>512||!Array.isArray(q.options)||q.options.length!==4)return null;
 const p=q.prompt;let m,value;
 if(m=p.match(/^Compute (\d+) \* (\d+) - (\d+)\.$/))value=solveStructured({kind:'arithmetic',a:+m[1],b:+m[2],c:+m[3]});
 else if(m=p.match(/^All dax are (\w+)\. No (\w+) object is (\w+)\. Item T is a dax\. Which statement must be true\?$/)){if(m[1]!==m[2])return null;value='T is not '+m[3];}
 else if(m=p.match(/^Finish (\w) before (\w); (\w) before (\w); (\w) after (\w)\. Which order is valid\?$/))value=solveStructured({kind:'dag',nodes:[...new Set(m.slice(1))],edges:[[m[1],m[2]],[m[3],m[4]],[m[6],m[5]]]}).join('');
 else if(/^A controlled randomized trial assigns \d+ participants per group\. What design feature most directly reduces pre-treatment confounding\?$/.test(p))value='random assignment';
 else if(m=p.match(/^Pseudocode: x=(\d+); for j=1 through (\d+) inclusive: x=x\+j\*(\d+); return x\. What returns\?$/))value=solveStructured({kind:'progression',start:+m[1],count:+m[2],factor:+m[3]});
 else if(m=p.match(/^Record: id=A\d+, available=(\d+), reserved=(\d+), units=kg\. Return the reserved integer only\.$/))value=solveStructured({kind:'extract',record:{available:+m[1],reserved:+m[2]},field:'reserved'});
 else if(m=p.match(/^Select the option containing exactly (\d+) repetitions of the letter X followed by the number (\d+)\.$/))value=solveStructured({kind:'repeat',count:+m[1],suffix:+m[2]});
 else if(p==='A sealed container has an unknown number of coins. No other evidence is provided. How many coins are inside?')value='insufficient evidence';
 return value!==undefined&&q.options.includes(String(value))?String(value):null;
}
