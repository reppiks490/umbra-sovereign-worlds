import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorld,advanceWorld,DEFAULT_POLICY} from '../engine.mjs';
import {ARCHIVE_SCHEMA,MAX_ARCHIVE_BYTES,MAX_CHECKPOINTS,canonicalize,sha256Text,
  createArchive,appendCheckpoint,verifyArchive,replayFromCheckpoint,importArchive,exportArchive} from '../archive.mjs';

const copy = x => JSON.parse(JSON.stringify(x));
const make = async (seed=49021, policy=DEFAULT_POLICY) => {
  const world = createWorld(seed, policy);
  let archive = await createArchive(world);
  advanceWorld(world, 18); archive = await appendCheckpoint(archive, world);
  advanceWorld(world, 25); archive = await appendCheckpoint(archive, world);
  return {world,archive};
};
const reject = async (archive, fragment) =>
  assert.rejects(verifyArchive(archive), new RegExp(fragment));

test('archive genesis has versioned schema, SHA-256 digest and independent replay', async () => {
  const archive = await createArchive(createWorld(7));
  const checked = await verifyArchive(archive);
  assert.equal(archive.schema, ARCHIVE_SCHEMA);
  assert.equal(archive.checkpoints[0].previous, 'GENESIS');
  assert.match(checked.head, /^[0-9a-f]{64}$/);
  assert.deepEqual({valid:checked.valid,checked:checked.checked,tick:checked.tick},
    {valid:true,checked:1,tick:0});
});

test('multiple checkpoints verify and original records remain immutable after append', async () => {
  const world = createWorld(12);
  const a = await createArchive(world), original = JSON.stringify(a);
  advanceWorld(world, 25);
  const b = await appendCheckpoint(a, world);
  assert.equal(JSON.stringify(a), original);
  assert.notStrictEqual(b.checkpoints[0], a.checkpoints[0]);
  assert.equal((await verifyArchive(b)).tick, 25);
  assert.equal(b.checkpoints[1].previous, b.checkpoints[0].digest);
});

test('same seed, policy and tick produce identical archive digests', async () => {
  const a = await make(99), b = await make(99);
  assert.equal(await exportArchive(a.archive), await exportArchive(b.archive));
  const c = await make(100);
  assert.notEqual(c.archive.checkpoints.at(-1).digest, a.archive.checkpoints.at(-1).digest);
});

test('verified checkpoint hydration and forward replay match independent genesis replay', async () => {
  const {archive} = await make(34);
  const resumed = await replayFromCheckpoint(archive, {index:1,steps:29});
  const expected = advanceWorld(createWorld(34), 47);
  assert.equal(canonicalize(resumed), canonicalize(expected));
  assert.equal(resumed.tick,47);
});

test('archive roundtrip validates every checkpoint before returning any state', async () => {
  const {archive} = await make(1001);
  const restored = await importArchive(await exportArchive(archive));
  assert.equal((await verifyArchive(restored)).checked,3);
  assert.equal((await replayFromCheckpoint(restored)).tick,43);
});

test('tampered snapshot bytes fail the SHA-256 digest check', async () => {
  const {archive} = await make();
  const corrupt = copy(archive);
  corrupt.checkpoints[1].state.population += 4;
  await reject(corrupt, 'snapshot digest mismatch');
});

test('forged self-consistent hashes still fail independent genesis replay', async () => {
  const {archive} = await make();
  const forged = copy(archive);
  const entry = forged.checkpoints.at(-1);
  entry.state.population += 12;
  entry.stateDigest = await sha256Text(canonicalize(entry.state));
  entry.digest = await sha256Text(canonicalize({
    tick:entry.tick,previous:entry.previous,stateDigest:entry.stateDigest}));
  await reject(forged, 'independent genesis replay mismatch');
});

test('broken previous link, duplicate tick and out-of-order tick are rejected', async () => {
  const {archive} = await make();
  const broken = copy(archive);
  broken.checkpoints[2].previous = '0'.repeat(64);
  await reject(broken,'broken hash chain');
  const duplicate = copy(archive);
  duplicate.checkpoints[2].tick = duplicate.checkpoints[1].tick;
  await reject(duplicate,'duplicate or unordered');
  const reversed = copy(archive);
  reversed.checkpoints.reverse();
  await reject(reversed,'broken hash chain');
});

test('version, policy, schema and unexpected keys fail closed', async () => {
  const {archive} = await make();
  for (const mutation of [
    a => {a.engine='0.0.0';},
    a => {a.society='unknown';},
    a => {a.schema='umbra.archive.v999';},
    a => {a.policy.trade=Infinity;},
    a => {a.untrusted='surprise';},
    a => {a.checkpoints[0].extra=true;}
  ]) {
    const bad = copy(archive);
    mutation(bad);
    await assert.rejects(verifyArchive(bad));
  }
});

test('a manually corrupted candidate world cannot be appended', async () => {
  const world = createWorld(45), archive = await createArchive(world);
  advanceWorld(world,15);
  world.towns[0].food += 99;
  await assert.rejects(appendCheckpoint(archive,world),/fails independent replay/);
});

test('import limits and invalid JSON are rejected atomically', async () => {
  await assert.rejects(importArchive('{"invalid":'),/invalid JSON/);
  await assert.rejects(importArchive(' '.repeat(MAX_ARCHIVE_BYTES+1)),/oversized/);
  const {archive} = await make();
  const tooMany = copy(archive);
  while (tooMany.checkpoints.length <= MAX_CHECKPOINTS)
    tooMany.checkpoints.push(copy(tooMany.checkpoints.at(-1)));
  await assert.rejects(importArchive(JSON.stringify(tooMany)),/checkpoint count/);
});

test('invalid replay horizon and checkpoint index are rejected', async () => {
  const {archive} = await make();
  await assert.rejects(replayFromCheckpoint(archive,{index:-1}),/invalid checkpoint index/);
  await assert.rejects(replayFromCheckpoint(archive,{steps:-1}),/invalid replay horizon/);
  await assert.rejects(replayFromCheckpoint(archive,{steps:3000}),/invalid replay horizon/);
});

test('canonical serialization is key-order independent and rejects non-JSON input', () => {
  assert.equal(canonicalize({z:1,a:{b:2,a:1}}),canonicalize({a:{a:1,b:2},z:1}));
  assert.throws(()=>canonicalize({x:NaN}),/nonfinite/);
  const loop={};loop.self=loop;assert.throws(()=>canonicalize(loop),/cyclic/);
});
