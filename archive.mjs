/**
 * UMBRA Ω / UM-101: bounded, local-only, content-addressed world archives.
 * SHA-256 proves byte consistency, NOT authorship, authenticity, or external truth.
 * Imported snapshots are NEVER trusted until independently replayed from genesis.
 * No server, database, persistence, account access, or network calls are made here.
 */
import {createWorld, advanceWorld, DEFAULT_POLICY, ENGINE_VERSION} from './engine.mjs';
import {SOCIETY_VERSION} from './society.mjs';

export const ARCHIVE_SCHEMA = 'umbra.archive.v1';
export const MAX_ARCHIVE_BYTES = 8_000_000;
export const MAX_CHECKPOINTS = 12;
export const MAX_ARCHIVE_TICK = 2000;
const HEX = /^[0-9a-f]{64}$/;
const KEYS = Object.keys(DEFAULT_POLICY).sort();
const fail = message => {throw new Error('UMBRA archive: ' + message);};
const plain = x => x !== null && typeof x === 'object' && !Array.isArray(x) &&
  (Object.getPrototypeOf(x) === Object.prototype || Object.getPrototypeOf(x) === null);
const sameKeys = (x, keys) => plain(x) &&
  JSON.stringify(Object.keys(x).sort()) === JSON.stringify([...keys].sort());
const clone = x => JSON.parse(canonicalize(x));
const byteLength = x => new TextEncoder().encode(x).length;

/** Deterministic JSON serialization with sorted keys; rejects non-JSON values and cycles. */
export function canonicalize(value) {
  const seen = new WeakSet();
  function encode(v, depth) {
    if (depth > 24) fail('nesting limit exceeded');
    if (v === null || typeof v === 'string' || typeof v === 'boolean') return JSON.stringify(v);
    if (typeof v === 'number') {
      if (!Number.isFinite(v)) fail('nonfinite number');
      return JSON.stringify(v);
    }
    if (typeof v !== 'object' || (!Array.isArray(v) && !plain(v))) fail('non-JSON value');
    if (seen.has(v)) fail('cyclic data');
    seen.add(v);
    const result = Array.isArray(v)
      ? '[' + v.map(x => encode(x, depth + 1)).join(',') + ']'
      : '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + encode(v[k], depth + 1)).join(',') + '}';
    seen.delete(v);
    return result;
  }
  return encode(value, 0);
}

export async function sha256Text(text) {
  if (typeof text !== 'string') fail('digest input must be text');
  if (!globalThis.crypto?.subtle) fail('WebCrypto SHA-256 unavailable; use HTTPS/localhost or Node 20+');
  const bytes = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, '0')).join('');
}

function header(archive, allowEmpty = false) {
  if (!sameKeys(archive, ['schema','engine','society','seed','policy','checkpoints'])) fail('invalid archive header');
  if (archive.schema !== ARCHIVE_SCHEMA || archive.engine !== ENGINE_VERSION ||
      archive.society !== SOCIETY_VERSION) fail('unsupported archive or engine version');
  if (!Number.isSafeInteger(archive.seed) || archive.seed < 1 || archive.seed > 0xffffffff)
    fail('invalid seed');
  if (!sameKeys(archive.policy, KEYS) ||
      KEYS.some(k => typeof archive.policy[k] !== 'number' ||
        !Number.isFinite(archive.policy[k]) || archive.policy[k] < 0 || archive.policy[k] > 1))
    fail('invalid policy');
  if (!Array.isArray(archive.checkpoints) ||
      archive.checkpoints.length > MAX_CHECKPOINTS ||
      (!allowEmpty && archive.checkpoints.length === 0)) fail('invalid checkpoint count');
  if (byteLength(JSON.stringify(archive)) > MAX_ARCHIVE_BYTES) fail('archive exceeds byte limit');
}

function checkpointShape(entry) {
  if (!sameKeys(entry, ['tick','previous','state','stateDigest','digest'])) fail('invalid checkpoint shape');
  if (!Number.isSafeInteger(entry.tick) || entry.tick < 0 || entry.tick > MAX_ARCHIVE_TICK)
    fail('invalid checkpoint tick');
  if (!(entry.previous === 'GENESIS' || HEX.test(entry.previous)) ||
      !HEX.test(entry.stateDigest) || !HEX.test(entry.digest)) fail('invalid digest syntax');
  if (!plain(entry.state)) fail('invalid snapshot');
}
function chainPayload(entry) {
  return {tick:entry.tick, previous:entry.previous, stateDigest:entry.stateDigest};
}
function assertWorldMatchesHeader(world, archive) {
  if (!plain(world) || world.engine !== archive.engine || world.seed !== archive.seed ||
      !Number.isSafeInteger(world.tick) || world.tick < 0 || world.tick > MAX_ARCHIVE_TICK ||
      canonicalize(world.policy) !== canonicalize(archive.policy) ||
      world.society?.version !== archive.society) fail('world/header mismatch');
}

/**
 * Independently rebuild every checkpoint from seed and policy. A forged checksum
 * alone cannot make an impossible snapshot pass the replay comparison.
 * Return only verification metadata, never an untrusted imported state object.
 */
export async function verifyArchive(archive) {
  header(archive);
  const replay = createWorld(archive.seed, archive.policy);
  let previous = 'GENESIS';
  for (let i = 0; i < archive.checkpoints.length; i++) {
    const entry = archive.checkpoints[i];
    checkpointShape(entry);
    if (entry.previous !== previous) fail('broken hash chain at checkpoint ' + i);
    if (i > 0 && entry.tick <= archive.checkpoints[i - 1].tick)
      fail('duplicate or unordered checkpoint tick');
    if (await sha256Text(canonicalize(chainPayload(entry))) !== entry.digest)
      fail('checkpoint digest mismatch at ' + i);
    const stored = canonicalize(entry.state);
    if (await sha256Text(stored) !== entry.stateDigest)
      fail('snapshot digest mismatch at ' + i);
    assertWorldMatchesHeader(entry.state, archive);
    advanceWorld(replay, entry.tick - replay.tick);
    if (stored !== canonicalize(replay))
      fail('independent genesis replay mismatch at ' + i);
    previous = entry.digest;
  }
  return {valid:true, checked:archive.checkpoints.length, tick:replay.tick,
    head:previous, engine:archive.engine, schema:archive.schema};
}

/** Append without mutating or aliasing the original archive. */
export async function appendCheckpoint(archive, world) {
  header(archive, true);
  if (archive.checkpoints.length) await verifyArchive(archive);
  assertWorldMatchesHeader(world, archive);
  const prior = archive.checkpoints.at(-1);
  if (prior && world.tick <= prior.tick) fail('checkpoint ticks must increase');
  if (archive.checkpoints.length >= MAX_CHECKPOINTS) fail('checkpoint limit reached');
  const expected = advanceWorld(createWorld(archive.seed, archive.policy), world.tick);
  const state = canonicalize(world);
  if (state !== canonicalize(expected)) fail('cannot append a world that fails independent replay');
  const stateDigest = await sha256Text(state);
  const entry = {tick:world.tick, previous:prior?.digest ?? 'GENESIS',
    state:JSON.parse(state), stateDigest, digest:''};
  entry.digest = await sha256Text(canonicalize(chainPayload(entry)));
  const next = clone(archive);
  next.checkpoints.push(entry);
  header(next);
  return next;
}

export async function createArchive(world) {
  if (!plain(world) || !Number.isSafeInteger(world.seed)) fail('invalid source world');
  const archive = {schema:ARCHIVE_SCHEMA,engine:ENGINE_VERSION,society:SOCIETY_VERSION,
    seed:world.seed,policy:clone(world.policy),checkpoints:[]};
  return appendCheckpoint(archive, world);
}

/** Hydrate a VERIFIED snapshot, advance it, and independently cross-check genesis. */
export async function replayFromCheckpoint(archive, {index, steps = 0} = {}) {
  await verifyArchive(archive);
  const chosen = index === undefined ? archive.checkpoints.length - 1 : index;
  if (!Number.isSafeInteger(chosen) || chosen < 0 || chosen >= archive.checkpoints.length)
    fail('invalid checkpoint index');
  const entry = archive.checkpoints[chosen];
  if (!Number.isSafeInteger(steps) || steps < 0 || entry.tick + steps > MAX_ARCHIVE_TICK)
    fail('invalid replay horizon');
  const world = clone(entry.state);
  advanceWorld(world, steps);
  const expected = advanceWorld(createWorld(archive.seed, archive.policy), entry.tick + steps);
  if (canonicalize(world) !== canonicalize(expected)) fail('resumed world diverges from genesis');
  return world;
}

/** Import is atomic: never expose an archive until every checkpoint is verified. */
export async function importArchive(json) {
  if (typeof json !== 'string' || byteLength(json) > MAX_ARCHIVE_BYTES)
    fail('invalid or oversized archive input');
  let parsed;
  try { parsed = JSON.parse(json); } catch { fail('invalid JSON'); }
  await verifyArchive(parsed);
  return parsed;
}
export async function exportArchive(archive) {
  await verifyArchive(archive);
  return JSON.stringify(archive);
}
