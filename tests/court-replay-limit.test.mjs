import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorld,advanceWorld} from '../engine.mjs';
import {runCourt} from '../court.mjs';

const gate=(result,id)=>result.rows.find(row=>row.id===id);
const shortWorld=()=>advanceWorld(createWorld(41),10);
const check=(world,options,shape,replay)=>{
 const result=runCourt(world,options);
 assert.equal(gate(result,'G01').status,shape);
 assert.equal(gate(result,'G07').status,replay);
 assert.equal(gate(result,'G08').status,'pass');
 assert.equal(result.rows.length,13);
 return result;
};

test('normal world passes and caller can reduce replay budget',()=>{
 const w=shortWorld();
 check(w,{},'pass','pass');
 check(w,{replayLimit:0},'pass','blocked');
});

test('genuine long world stays structurally valid and cannot exceed engine replay bound',()=>{
 const w=advanceWorld(advanceWorld(createWorld(41),5000),1);
 assert.equal(w.tick,5001);
 for(const options of [{},{replayLimit:6000}]){
  const r=check(w,options,'pass','blocked');
  assert.match(gate(r,'G07').evidence,/5000/);
 }
});

for(const tick of [-1,0.5,NaN,Infinity])test(`malformed tick ${tick} fails structure and blocks replay`,()=>{
 const w=shortWorld();w.tick=tick;
 check(w,{},'fail','blocked');
});

for(const replayLimit of [-1,0.5,NaN,Infinity,'20',null])test(`invalid replay limit ${String(replayLimit)} blocks replay, not world validity`,()=>{
 const r=check(shortWorld(),{replayLimit},'pass','blocked');
 assert.match(gate(r,'G07').evidence,/Invalid replay limit/);
});

test('zero-turn replay and exact lower boundary are allowed',()=>{
 check(createWorld(41),{replayLimit:0},'pass','pass');
 check(shortWorld(),{replayLimit:10},'pass','pass');
});
