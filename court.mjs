/** Independent, on-demand self-checks. These are ENGINEERING checks, NOT model validation. */
import {createWorld,advanceWorld,pairedExperiment,noise,SITE_COUNT,ENGINE_VERSION} from './engine.mjs';
import {civicAudit} from './society.mjs';
const safe=x=>Number.isFinite(x)&&x>=0;
const settlementKeys=['p','food','water','energy','wealth','knowledge','infected','trait'];
// Array iteration helpers skip holes; require each expected settlement to exist.
const denseSettlements=(towns,validate=safe)=>Array.isArray(towns)&&towns.length===SITE_COUNT&&
 Array.from({length:SITE_COUNT},(_,i)=>Object.hasOwn(towns,i)&&towns[i]!==null&&
 typeof towns[i]==='object'&&!Array.isArray(towns[i])&&
 settlementKeys.every(k=>Object.hasOwn(towns[i],k)&&validate(towns[i][k]))).every(Boolean);
// Topology is immutable seeded model data, not merely a pair of array lengths.
const dense=(xs,n,valid)=>Array.isArray(xs)&&xs.length===n&&
 Array.from({length:n},(_,i)=>Object.hasOwn(xs,i)&&valid(xs[i],i)).every(Boolean);
const siteFields=['lat','lon','fertility','water','mineral','vulnerability'];
const topologyValid=w=>dense(w.sites,SITE_COUNT,(s,i)=>s!==null&&typeof s==='object'&&!Array.isArray(s)&&
 s.id===i&&typeof s.name==='string'&&s.name.length>0&&
 dense(s.pos,3,x=>Number.isFinite(x)&&Math.abs(x)<=1)&&
 Math.abs(Math.hypot(...s.pos)-1)<1e-9&&
 siteFields.every(k=>Object.hasOwn(s,k)&&Number.isFinite(s[k]))&&
 Number.isInteger(s.group)&&s.group>=0&&s.group<7)&&
 dense(w.near,SITE_COUNT,(row,i)=>dense(row,6,j=>Number.isInteger(j)&&j>=0&&j<SITE_COUNT&&j!==i)&&new Set(row).size===6);
const topologySummary=w=>[w.sites.map(s=>[s.id,s.name,s.pos,...siteFields.map(k=>s[k]),s.group]),w.near];
const round=x=>Math.round(x*1e6)/1e6;
const summary=w=>JSON.stringify({version:w.engine,tick:w.tick,seed:w.seed,policy:Object.fromEntries(Object.keys(w.policy).sort().map(k=>[k,w.policy[k]])),
 topology:topologySummary(w),
 totals:[w.population,w.food,w.water,w.energy,w.knowledge,w.wealth,w.infected,round(w.carbon),round(w.biodiversity)],
 towns:w.towns.map(t=>[round(t.p),round(t.food),round(t.water),round(t.energy),round(t.wealth),round(t.knowledge),round(t.infected),round(t.trait)]),
 civic:[round(w.society.treasury),round(w.society.trust),w.society.elections,w.society.corridors.map(c=>[c.a,c.b,c.pact,round(c.relation)]),w.society.councils.map(c=>[c.faction,round(c.treasury),round(c.support)])]});
export function runCourt(world,{replayLimit=5000}={}){
 if(!world||world.engine!==ENGINE_VERSION)throw Error('Unsupported world');
 const rows=[];const check=(id,label,ok,evidence)=>rows.push({id,label,status:ok?'pass':'fail',evidence});
 const civic=civicAudit(world);
 const turnValid=Number.isSafeInteger(world.tick)&&world.tick>=0;
 const settlementShape=Array.isArray(world.towns)&&world.towns.length===SITE_COUNT&&
  Array.from({length:SITE_COUNT},(_,i)=>Object.hasOwn(world.towns,i)&&
   world.towns[i]!==null&&typeof world.towns[i]==='object'&&!Array.isArray(world.towns[i])).every(Boolean);
 const topology=topologyValid(world);
 check('G01','World schema and coordinate topology',topology&&settlementShape&&turnValid,
  `${Array.isArray(world.sites)?world.sites.length:'invalid'} regions / ${Array.isArray(world.near)?world.near.length:'invalid'} neighbor maps; turn ${turnValid?world.tick:'invalid'}`);
 check('G02','Nonnegative and finite settlement resources',denseSettlements(world.towns),
  'Population, reserves, wealth, knowledge, health and inherited traits');
 check('G03','Civilization headcount reconciles',denseSettlements(world.towns)&&Number.isFinite(world.population)&&Math.abs(world.population-world.towns.reduce((a,t)=>a+t.p,0))<1e-6,
  'Regional populations sum to world total');
 check('G04','Fiscal ledger remains balanced',civic.valid&&Math.abs(civic.fiscalResidual)<1e-5,
  `${civic.balancedEntries} double-entry records; residual ${civic.fiscalResidual}`);
 check('G05','Aid transfers preserve food units',civic.valid&&Math.abs(civic.foodResidual)<1e-5,
  `Civic food-transfer residual ${civic.foodResidual}`);
 const corridors=world.society?.corridors;
 check('G06','Diplomatic graph is structurally valid',civic.valid&&Array.isArray(corridors)&&new Set(corridors.map(c=>`${c.a}:${c.b}`)).size===corridors.length,
  `${Array.isArray(corridors)?corridors.length:'invalid'} cross-settlement corridor records`);
 // Recreate from seed and policy rather than trusting exported/saved states.
 const replayable=civic.valid&&topology&&denseSettlements(world.towns,Number.isFinite)&&turnValid;
 const limitValid=Number.isSafeInteger(replayLimit)&&replayLimit>=0;
 const effectiveReplayLimit=limitValid?Math.min(replayLimit,5000):0;
 if(limitValid&&replayable&&world.tick<=effectiveReplayLimit){const replay=advanceWorld(createWorld(world.seed,world.policy),world.tick);
  check('G07','Seed-based selected-state replay',summary(replay)===summary(world),`Two independent runs, ${world.tick} turns, selected rounded state comparison`);
 }else rows.push({id:'G07',label:'Seed-based selected-state replay',status:'blocked',evidence:!limitValid?'Invalid replay limit':!replayable?'Malformed civic, topology, settlement or turn data prevents safe replay':`Replay limit ${effectiveReplayLimit} turns exceeded`});
 const seed=world.seed;const keyA=noise(seed,25,3,7),keyB=noise(seed,25,3,7);
 check('G08','Keyed exogenous signals reproduce',keyA===keyB,'Identical seed / time / region / channel produce identical draws');
 // Source access and data rights are absent. Do not promote uncalibrated outputs.
 for(const [id,label,evidence] of [
  ['V01','External scientific calibration','No external calibration dataset or fitted ecological mechanisms'],
  ['V02','Empirical causal validity','Policy forks identify only differences within the synthetic rules'],
  ['V03','Persistent shared-world authority','Local browser simulation; no authoritative durable backend'],
  ['V04','Real independent AI citizens','Aggregated settlements and councils, not person-level cognitive agents'],
  ['V05','Production-capable public deployment','This portable build has not been deployed or production-hardened']])
 rows.push({id,label,status:'blocked',evidence});
 const counts={pass:rows.filter(r=>r.status==='pass').length,fail:rows.filter(r=>r.status==='fail').length,blocked:rows.filter(r=>r.status==='blocked').length};
 return {engine:ENGINE_VERSION,seed,tick:world.tick,counts,rows,conclusion:counts.fail?'ENGINEERING VALIDATION FAILED':'ENGINEERING CHECKS ONLY; REAL-WORLD VALIDATION STILL BLOCKED'};
}
