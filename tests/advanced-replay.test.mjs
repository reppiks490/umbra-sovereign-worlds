import test from 'node:test';
import assert from 'node:assert/strict';
import {createSimulationRunner} from '../scripts/umbra_independent_replay.mjs';

const keyFor = (seed, policy, steps) => JSON.stringify([seed, policy, steps]);
const validate = (w, steps) => {
  assert.equal(w.tick, steps);
  assert.ok(Number.isFinite(w.population));
  assert.equal(w.civicValid, true);
};
const policy = {trade: 0.5};

test('cached reads and independent placebo executions have distinct accounting', () => {
  let calls = 0;
  const r = createSimulationRunner({keyFor, validate, simulate: (seed, p, tick) => {
    calls++;
    return {seed, tick, policy: {...p}, population: 42, civicValid: true};
  }});
  const original = r.world(1, policy, 10);
  assert.strictEqual(r.world(1, policy, 10), original);
  assert.deepEqual(r.stats(), {simulationExecutions: 1, distinctParameterKeys: 1});
  const replay = r.independentReplay(1, policy, 10);
  assert.notStrictEqual(replay.first, replay.second);
  assert.notStrictEqual(replay.first, original);
  assert.equal(replay.firstDigest, replay.secondDigest);
  assert.equal(replay.executions, 2);
  assert.equal(calls, 3);
  assert.deepEqual(r.stats(), {simulationExecutions: 3, distinctParameterKeys: 1});
});

test('divergent independent simulations fail rather than report a placebo pass', () => {
  let calls = 0;
  const r = createSimulationRunner({keyFor, validate, simulate: (seed, p, tick) =>
    ({seed, tick, population: ++calls, civicValid: true})});
  assert.throws(() => r.independentReplay(1, policy, 10), /Independent simulation mismatch/);
  assert.deepEqual(r.stats(), {simulationExecutions: 2, distinctParameterKeys: 1});
});

test('second simulation receives the same validation as the first', () => {
  let calls = 0;
  const r = createSimulationRunner({keyFor, validate, simulate: (seed, p, tick) =>
    ({seed, tick, population: 42, civicValid: ++calls === 1})});
  assert.throws(() => r.independentReplay(1, policy, 10));
  assert.equal(r.stats().simulationExecutions, 2);
});

test('reusing the same world object cannot establish independent replay', () => {
  const shared = {tick: 10, population: 42, civicValid: true};
  const r = createSimulationRunner({keyFor, validate, simulate: () => shared});
  assert.throws(() => r.independentReplay(1, policy, 10), /Independent simulation reused an object/);
});
