import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

// Count actual full simulate() calls separately from distinct input keys.
// Fresh calls intentionally neither read nor populate the cache.
export function createSimulationRunner({simulate, validate, keyFor}) {
  const cache = new Map(), keys = new Set();
  let simulationExecutions = 0;
  function world(seed, policy, steps, {fresh = false} = {}) {
    const key = keyFor(seed, policy, steps);
    if (!fresh && cache.has(key)) return cache.get(key);
    simulationExecutions++;
    keys.add(key);
    const result = simulate(seed, policy, steps);
    validate(result, steps);
    if (!fresh) cache.set(key, result);
    return result;
  }
  function independentReplay(seed, policy, steps) {
    const before = simulationExecutions;
    const first = world(seed, policy, steps, {fresh: true});
    const firstDigest = digest(first);
    const second = world(seed, policy, steps, {fresh: true});
    const secondDigest = digest(second);
    assert.notStrictEqual(first, second, 'Independent simulation reused an object');
    assert.equal(firstDigest, secondDigest, 'Independent simulation mismatch');
    assert.equal(digest(first), firstDigest, 'First simulation mutated during replay');
    assert.deepStrictEqual(first, second, 'Independent simulation mismatch');
    return {first, second, firstDigest, secondDigest, executions: simulationExecutions - before};
  }
  return {world, independentReplay, stats: () => ({simulationExecutions, distinctParameterKeys: keys.size})};
}
