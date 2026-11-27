import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorld,advanceWorld,DEFAULT_POLICY} from '../engine.mjs';
import {createArchive,appendCheckpoint,exportArchive,importArchive,replayFromCheckpoint} from '../archive.mjs';
import {defineResearchPlan,evaluateResearchPlan,inspectResearchWorld} from '../research.mjs';
import {runCourt} from '../court.mjs';
test('archived replay remains compatible with integrated Court and research guards',async()=>{
 const world=createWorld(914,{...DEFAULT_POLICY,trade:.31});
 let archive=await createArchive(world);
 advanceWorld(world,12);
 archive=await appendCheckpoint(archive,world);
 const restored=await replayFromCheckpoint(await importArchive(await exportArchive(archive)),{steps:3});
 assert.equal(restored.tick,15);
 assert.equal(inspectResearchWorld(restored).passed,true);
 assert.equal(runCourt(restored).counts.fail,0);
 restored.society.foodResidual=NaN;
 assert.equal(inspectResearchWorld(restored).passed,false);
 assert.equal(runCourt(restored).rows.find(r=>r.id==='G05').status,'fail');
});
test('research grid on integrated engine preserves exact declared seeds and null controls',()=>{
 const plan=defineResearchPlan({seed:914,trials:20,steps:4,baseline:DEFAULT_POLICY,treatment:DEFAULT_POLICY});
 const out=evaluateResearchPlan(plan);
 assert.deepEqual(out.rows.map(row=>row.seed),plan.replicateSeeds);
 assert.ok(out.rows.every(row=>row.diff===0));
 assert.equal(out.checks.realWorldPrediction,'blocked');
});
