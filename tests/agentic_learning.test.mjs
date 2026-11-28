import test from 'node:test';
import assert from 'node:assert/strict';
import {createMission,settleMission} from '../mcp/agentic_swarm.mjs';
import {learnCouncilExperience,forecastMission} from '../mcp/agentic_learning.mjs';
const record=(seed,steps)=>settleMission(createMission({seed,steps}),[{model:'synthetic-test-fixture',candidate:'health'}]);
test('learning separates complete historical missions before evaluating neural predictor',()=>{const records=[record(1,5),record(2,10),record(3,15),record(4,20)];const r=learnCouncilExperience(records);assert.equal(r.training_missions,3);assert.equal(r.validation_missions,1);assert.equal(r.training_rows,15);assert.equal(r.validation_rows,5);assert.ok(Number.isFinite(r.validation_mse));assert.ok(Number.isFinite(r.baseline_mse));assert.equal(r.synthetic,true);assert.equal(r.production_authority,false);assert.throws(()=>forecastMission(r,createMission({seed:4,steps:20})),/already observed/);assert.equal(forecastMission(r,createMission({seed:5,steps:8})).predictions.length,5);});
test('insufficient history and duplicate seed never train',()=>{const a=record(1,5);assert.throws(()=>learnCouncilExperience([a]));assert.throws(()=>learnCouncilExperience([a,a,a,a]));});
