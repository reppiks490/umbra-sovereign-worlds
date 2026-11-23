import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorld,stepWorld,simulate,pairedExperiment,sensitivityExperiment,DEFAULT_POLICY,noise,buildPassport} from '../engine.mjs';
import {advanceSociety,civicAudit,FACTIONS,SOCIETY_VERSION} from '../society.mjs';
const stable = w => JSON.stringify({turn:w.tick,gov:w.society,world:w.towns.map(t=>[t.p,t.food,t.water,t.energy,t.wealth,t.knowledge,t.infected]),series:w.series});
test('civic replay is deterministic across the same seed and policy',()=>{
 const a=simulate(73,DEFAULT_POLICY,340),b=simulate(73,DEFAULT_POLICY,340);
 assert.equal(stable(a),stable(b));assert.equal(a.society.version,SOCIETY_VERSION);});
test('civic factions cover every region and electoral transitions occur',()=>{
 const a=createWorld(2026);assert.equal(a.society.councils.length,a.sites.length);
 assert.ok(a.society.councils.every(c=>FACTIONS.some(f=>f.id===c.faction)));
 for(let n=0;n<75;n++)stepWorld(a);assert.ok(a.society.elections>0);
 assert.ok(a.society.councils.some(c=>c.mandate>0));});
test('diplomatic corridors have unique undirected keys and stable semantics',()=>{
 const a=createWorld(13),roads=a.society.corridors;assert.ok(roads.length>=a.sites.length);
 assert.equal(new Set(roads.map(r=>r.a+':'+r.b)).size,roads.length);
 assert.ok(roads.every(r=>r.a<r.b&&r.relation>=-1&&r.relation<=1));});
test('food aid is exactly conserved inside the civic step',()=>{
 const a=createWorld(17);const edge=a.society.corridors[0],left=a.towns[edge.a],right=a.towns[edge.b];
 left.p=70;right.p=50;left.food=100;right.food=4;left.wealth=80;right.wealth=20;
 a.tick=3;edge.pact=true;const initial=a.towns.reduce((v,t)=>v+t.food,0);
 advanceSociety(a,noise);const final=a.towns.reduce((v,t)=>v+t.food,0);
 assert.ok(a.society.aid>0,'aid should move units');assert.ok(Math.abs(initial-final)<1e-7);
 assert.equal(a.society.foodResidual,0);assert.ok(civicAudit(a).valid);});
test('fiscal transfers are double-entry within a civic step',()=>{
 const a=simulate(49,{...DEFAULT_POLICY,climate:.8},240);
 assert.ok(a.society.taxes>0&&a.society.grants>0);
 assert.ok(a.society.councils.every(c=>c.treasury>=0));
 assert.equal(a.society.fiscalResidual,0);assert.ok(civicAudit(a).valid);});
test('many seeds and policies do not break civic accounting or resource bounds',()=>{
 for(const seed of [1,4,74,49021,4294967295])for(const policy of [DEFAULT_POLICY,{trade:0,climate:1,medicine:0,innovation:1,conflict:1},{trade:1,climate:0,medicine:1,innovation:0,conservation:1}]){
  const a=simulate(seed,policy,260);const result=civicAudit(a);
  assert.ok(result.valid, `${seed}: ${result.issues.join(', ')}`);
  assert.ok(a.society.corridors.every(c=>c.relation>=-1&&c.relation<=1));
  assert.ok(a.towns.every(t=>t.food>=0&&t.water>=0&&t.wealth>=0&&t.infected>=0));
 }});
test('civic ledger entries preserve positive values, transaction kinds, and monotonic ids',()=>{
 const a=simulate(193,DEFAULT_POLICY,150),entries=a.society.ledger;
 assert.ok(entries.length>0);assert.ok(entries.length<=240);
 assert.ok(entries.every(e=>e.amount>0&&['tax','grant','aid'].includes(e.kind)&&['credit','food'].includes(e.unit)));
 assert.ok(entries.every((e,i)=>i===0||e.id<entries[i-1].id));});
test('induced corruption is detectable by civic audit',()=>{
 const a=simulate(77,DEFAULT_POLICY,45);
 assert.ok(civicAudit(a).valid);a.society.councils[0].support=NaN;
 assert.equal(civicAudit(a).valid,false);
 a.society.councils[0].support=.5;a.society.foodResidual=.0009;assert.equal(civicAudit(a).valid,false);});
test('single-axis sensitivity sweep repeats exactly and preserves configured inputs',()=>{
 const args={seed:927,trials:4,steps:60,delta:.2,base:DEFAULT_POLICY};
 const x=sensitivityExperiment(args),y=sensitivityExperiment(args);
 assert.deepEqual(x,y);assert.equal(x.results.length,7);
 for(const row of x.results){assert.ok(row.low>=0&&row.high<=1&&row.span>0);assert.equal(row.trials,4);}
});
test('zero or malformed sensitivity designs are rejected',()=>{
 for(const args of [{trials:1},{trials:33},{steps:-1},{delta:0},{delta:2},{trials:2.1}])assert.throws(()=>sensitivityExperiment(args));});
test('same policies yield zero model-internal treatment effect after civic integration',()=>{
 const a=pairedExperiment({seed:947,trials:4,steps:120,baseline:DEFAULT_POLICY,treatment:DEFAULT_POLICY});
 assert.equal(a.mean,0);assert.equal(a.sd,0);});
test('world passport includes readable fiscal audit, ledger and explicit synthetic mode',()=>{
 const a=simulate(258,DEFAULT_POLICY,80),passport=buildPassport(a);
 assert.equal(passport.version,'5.0.0');assert.equal(passport.mode,'synthetic model experiment');
 assert.ok(passport.totals.society.accounting.valid);assert.ok(passport.totals.society.ledger.length>0);
 assert.ok(passport.assumptions.some(x=>x.includes('synthetic')));});
