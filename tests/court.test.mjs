import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorld,simulate,DEFAULT_POLICY} from '../engine.mjs';
import {runCourt} from '../court.mjs';

test('court passes the eight engineering checks for a normal world and blocks real validation',()=>{
 const w=simulate(460,DEFAULT_POLICY,160);const finding=runCourt(w);
 assert.deepEqual(finding.counts,{pass:8,fail:0,blocked:5});
 assert.ok(finding.rows.some(x=>x.id==='G07'&&x.status==='pass'));
 assert.ok(finding.rows.every(x=>x.id.startsWith('V')?x.status==='blocked':true));
});
test('court catches a corrupted population ledger',()=>{
 const w=simulate(127,DEFAULT_POLICY,40);w.population+=6;
 const r=runCourt(w);assert.ok(r.rows.some(x=>x.id==='G03'&&x.status==='fail'));
});
test('court catches corruption of civic fiscal residual',()=>{
 const w=simulate(124,DEFAULT_POLICY,40);w.society.fiscalResidual=2;
 const r=runCourt(w);assert.ok(r.rows.some(x=>x.id==='G04'&&x.status==='fail'));
});
test('court catches corruption of civic food conservation',()=>{
 const w=simulate(19,DEFAULT_POLICY,45);w.society.foodResidual=.01;
 const r=runCourt(w);assert.ok(r.rows.some(x=>x.id==='G05'&&x.status==='fail'));
});
test('court catches corridor duplication',()=>{
 const w=simulate(11,DEFAULT_POLICY,60);w.society.corridors.push({...w.society.corridors[0]});
 const r=runCourt(w);assert.ok(r.rows.some(x=>x.id==='G06'&&x.status==='fail'));
});
test('court bounds computationally expensive replay without treating missing evidence as pass',()=>{
 const w=simulate(23,DEFAULT_POLICY,80);const r=runCourt(w,{replayLimit:50});
 assert.equal(r.rows.find(x=>x.id==='G07').status,'blocked');
 assert.equal(r.counts.fail,0);assert.equal(r.counts.blocked,6);
});
test('court catches manually corrupted settlement reserves and fails deterministic replay',()=>{
 const w=simulate(42,DEFAULT_POLICY,100);w.towns[0].water=-0.5;
 const r=runCourt(w);assert.equal(r.rows.find(x=>x.id==='G02').status,'fail');
 assert.equal(r.rows.find(x=>x.id==='G07').status,'fail');
});
