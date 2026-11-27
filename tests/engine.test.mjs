import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorld,advanceWorld,stepWorld,simulate,pairedExperiment,policyOf,DEFAULT_POLICY,buildPassport,validateImport,SITE_COUNT,noise} from '../engine.mjs';
const snapshot = w => JSON.stringify({tick:w.tick,sites:w.towns,totals:w.series,events:w.events,carbon:w.carbon,bio:w.biodiversity});
test('same seed + policy + turns generate exact same world',()=>{let a=simulate(123,DEFAULT_POLICY,430),b=simulate(123,DEFAULT_POLICY,430);assert.equal(snapshot(a),snapshot(b))});
test('chunked stepping equals direct stepping',()=>{let a=createWorld(9),b=createWorld(9);advanceWorld(a,120);advanceWorld(a,85);advanceWorld(b,205);assert.equal(snapshot(a),snapshot(b))});
test('seed-locked weather is independent from policy',()=>{const a=createWorld(14,{trade:0}),b=createWorld(14,{trade:1});for(let t=1;t<=120;t++){stepWorld(a);stepWorld(b);assert.equal(a.climate,b.climate);assert.equal(a.season,b.season);}});
test('distinct seeds produce distinct realities',()=>assert.notEqual(snapshot(simulate(101,DEFAULT_POLICY,20)),snapshot(simulate(102,DEFAULT_POLICY,20))));
test('universe has 42 stable regions and localized neighbors',()=>{const a=createWorld(12);assert.equal(a.towns.length,SITE_COUNT);assert.equal(a.sites.length,SITE_COUNT);assert.equal(a.near.length,SITE_COUNT);assert.equal(new Set(a.sites.map(s=>s.name)).size,SITE_COUNT)});
test('policy is clamped, never NaN',()=>{const p=policyOf({trade:99,climate:-22,medicine:NaN,conflict:'xyz'});assert.equal(p.trade,1);assert.equal(p.climate,0);assert.equal(p.medicine,DEFAULT_POLICY.medicine);assert.equal(p.conflict,DEFAULT_POLICY.conflict)});
test('matched policies yield zero paired difference',()=>{const e=pairedExperiment({seed:12,trials:8,steps:100,baseline:DEFAULT_POLICY,treatment:DEFAULT_POLICY});assert.equal(e.mean,0);assert.equal(e.sd,0);assert.ok(e.paths.every(x=>x.diff===0))});
test('paired ensemble reproducible',()=>{const p={seed:1962,trials:16,steps:240,baseline:DEFAULT_POLICY,treatment:{...DEFAULT_POLICY,trade:0}};assert.deepEqual(pairedExperiment(p),pairedExperiment(p))});
test('every resource remains finite and nonnegative in long stress',()=>{for(const p of [{trade:0,climate:1,medicine:0,conservation:0,conflict:1},{trade:1,climate:0,medicine:1,innovation:1}]){
  const a=simulate(999,p,1000);assert.equal(a.tick,1000);assert.ok(a.population>=0);for(const t of a.towns){for(const key of ['p','food','water','energy','knowledge','wealth','infected','trait','health'])assert.ok(Number.isFinite(t[key])&&t[key]>=0,`bad ${key}`)}for(const x of a.series)assert.ok(Number.isFinite(x.pop));}}
);
test('passport import reconstructs seed, policy and turn; rejects corrupted input',()=>{const w=simulate(1976,{trade:0,climate:.75},18),data=buildPassport(w);assert.deepEqual(validateImport(data),{seed:1976,tick:18,policy:w.policy});assert.throws(()=>validateImport({...data,version:'0.1'}));assert.throws(()=>validateImport({...data,tick:-1}));assert.throws(()=>validateImport({...data,policy:{...data.policy,trade:Infinity}}));});
test('environmental random draws do not depend on state mutation',()=>{assert.equal(noise(122,42,10,4),noise(122,42,10,4));assert.ok(noise(122,42,10,4)>=0&&noise(122,42,10,4)<1)});
test('bad step count rejected, and cannot silently overflow',()=>{assert.throws(()=>advanceWorld(createWorld(1),-1));assert.throws(()=>advanceWorld(createWorld(1),9999999));});


test('paired experiment rejects NaN, infinite and fractional dimensions before running',()=>{
 for(const trials of [NaN,Infinity,-Infinity,2.5,'8',null]){
   assert.throws(()=>pairedExperiment({seed:13,trials,steps:2}),RangeError);
 }
 for(const steps of [NaN,Infinity,-Infinity,2.5,'20',null]){
   assert.throws(()=>pairedExperiment({seed:13,trials:2,steps}),RangeError);
 }
});
test('paired experiment preserves finite integer boundary clamps and reproducibility',()=>{
 const a=pairedExperiment({seed:7,trials:1,steps:0});
 assert.equal(a.trials,2);
 assert.equal(a.steps,1);
 assert.ok(Number.isFinite(a.mean)&&Number.isFinite(a.sd));
 assert.deepEqual(a,pairedExperiment({seed:7,trials:2,steps:1}));
 const upper=pairedExperiment({seed:7,trials:2,steps:2});
 assert.equal(upper.paths.length,2);
 assert.ok(upper.paths.every(row=>Number.isFinite(row.diff)));
});


test('paired experiment rejects noncanonical seed identities before simulation',()=>{
 for(const seed of [NaN,Infinity,-Infinity,1.5,'7',null,true,0,-1,4294967296,Number.MAX_SAFE_INTEGER]){
  assert.throws(()=>pairedExperiment({seed,trials:2,steps:1}),/seed/);
 }
 for(const seed of [1,4294967295]){
  const args={seed,trials:2,steps:1};
  const result=pairedExperiment(args);
  assert.equal(result.seed,seed);
  assert.deepEqual(result,pairedExperiment(args));
 }
});
