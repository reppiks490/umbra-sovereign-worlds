import test from 'node:test';
import assert from 'node:assert/strict';
import {simulate,DEFAULT_POLICY} from '../engine.mjs';
import {civicAudit} from '../society.mjs';
import {runCourt} from '../court.mjs';
const gate=(world,id)=>runCourt(world).rows.find(row=>row.id===id).status;

test('malformed civic collections produce structured Court failures without throwing',()=>{
 for(const field of ['councils','corridors','ledger'])for(const value of [undefined,null,{}]){
  const w=simulate(41,DEFAULT_POLICY,20);w.society[field]=value;
  const r=runCourt(w);
  for(const id of ['G04','G05','G06'])assert.equal(r.rows.find(x=>x.id===id).status,'fail',field+": "+id);
  assert.equal(r.rows.find(x=>x.id==='G07').status,'blocked');
 }
});
test('sparse civic collections are not accepted as valid',()=>{
 for(const field of ['councils','corridors','ledger']){
  const w=simulate(42,DEFAULT_POLICY,20);const items=w.society[field];
  if(!items.length)items.length=1;else delete items[0];
  assert.equal(civicAudit(w).valid,false,field);
  assert.equal(gate(w,'G07'),'blocked',field);
 }
});
test('finite negative resource is invalid but permits replay divergence detection',()=>{
 const w=simulate(43,DEFAULT_POLICY,20);w.towns[0].water=-0.5;
 assert.equal(gate(w,'G02'),'fail');assert.equal(gate(w,'G07'),'fail');
});
test('nonfinite settlement values block replay',()=>{
 const w=simulate(44,DEFAULT_POLICY,20);w.towns[0].water=Infinity;
 assert.equal(gate(w,'G02'),'fail');assert.equal(gate(w,'G07'),'blocked');
});
test('ordinary deterministic world retains all eight engineering checks',()=>{
 const w=simulate(45,DEFAULT_POLICY,20);
 assert.deepEqual(runCourt(w).counts,{pass:8,fail:0,blocked:5});
});
