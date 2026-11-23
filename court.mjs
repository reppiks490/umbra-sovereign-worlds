/** Independent, on-demand self-checks. These are ENGINEERING checks, NOT model validation. */
import {createWorld,advanceWorld,pairedExperiment,noise,SITE_COUNT,ENGINE_VERSION} from './engine.mjs';
import {civicAudit} from './society.mjs';
const safe=x=>Number.isFinite(x)&&x>=0;
const round=x=>Math.round(x*1e6)/1e6;
const summary=w=>JSON.stringify({version:w.engine,tick:w.tick,seed:w.seed,policy:w.policy,
 totals:[w.population,w.food,w.water,w.energy,w.knowledge,w.wealth,w.infected,round(w.carbon),round(w.biodiversity)],
 towns:w.towns.map(t=>[round(t.p),round(t.food),round(t.water),round(t.energy),round(t.wealth),round(t.knowledge),round(t.infected),round(t.trait)]),
 civic:[round(w.society.treasury),round(w.society.trust),w.society.elections,w.society.corridors.map(c=>[c.a,c.b,c.pact,round(c.relation)]),w.society.councils.map(c=>[c.faction,round(c.treasury),round(c.support)])]});
export function runCourt(world,{replayLimit=5000}={}){
 if(!world||world.engine!==ENGINE_VERSION)throw Error('Unsupported world');
 const rows=[];const check=(id,label,ok,evidence)=>rows.push({id,label,status:ok?'pass':'fail',evidence});
 const civic=civicAudit(world);
 check('G01','World schema and coordinate topology',world.sites.length===SITE_COUNT&&world.near.length===SITE_COUNT&&world.towns.length===SITE_COUNT,
  `${world.sites.length} regions / ${world.near.length} neighbor maps`);
 check('G02','Nonnegative and finite settlement resources',world.towns.every(t=>['p','food','water','energy','wealth','knowledge','infected','trait'].every(k=>safe(t[k]))),
  'Population, reserves, wealth, knowledge, health and inherited traits');
 check('G03','Civilization headcount reconciles',Math.abs(world.population-world.towns.reduce((a,t)=>a+t.p,0))<1e-6,
  'Regional populations sum to world total');
 check('G04','Fiscal ledger remains balanced',civic.valid&&Math.abs(civic.fiscalResidual)<1e-5,
  `${civic.balancedEntries} double-entry records; residual ${civic.fiscalResidual}`);
 check('G05','Aid transfers preserve food units',civic.valid&&Math.abs(civic.foodResidual)<1e-5,
  `Civic food-transfer residual ${civic.foodResidual}`);
 check('G06','Diplomatic graph is structurally valid',civic.valid&&new Set(world.society.corridors.map(c=>`${c.a}:${c.b}`)).size===world.society.corridors.length,
  `${world.society.corridors.length} unique cross-settlement corridors`);
 // Recreate from seed and policy rather than trusting exported/saved states.
 if(world.tick<=replayLimit){const replay=advanceWorld(createWorld(world.seed,world.policy),world.tick);
  check('G07','Exact seed-based replay',summary(replay)===summary(world),`Two independent runs, ${world.tick} turns, exact canonical state comparison`);
 }else rows.push({id:'G07',label:'Exact seed-based replay',status:'blocked',evidence:`Replay limit ${replayLimit} turns exceeded`});
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
