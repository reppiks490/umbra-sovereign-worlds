import test from 'node:test';
import assert from 'node:assert/strict';
import {summarizeMasteryReceipts, RECEIPT_SCHEMA} from '../mastery-receipts.mjs';

const HASH = 'a'.repeat(64);
const SOURCE = 'b'.repeat(64);
const NOW = '2026-11-28T18:00:00.000Z';
function receipt(overrides={}) {
  return {
    schema: RECEIPT_SCHEMA,
    model_id: 'qwen3-0.6b', checkpoint_sha256: HASH,
    source_id: 'umbra-curriculum-v1', source_sha256: SOURCE,
    evaluator_version: 'rubric-v1', skill: 'navigation', difficulty: 2,
    question_id: 'navigation-q1', attempt_id: 'attempt-1',
    split: 'development', grade: 'fail', failure_category: 'constraint',
    observed_at: '2026-11-28T17:30:00.000Z', tokens: 26, latency_ms: 900,
    ...overrides
  };
}
const summarize = (receipts, overrides={}) => summarizeMasteryReceipts(receipts,{asOf: NOW, maxAgeHours: 24, ...overrides});

test('empty batch is explicitly empty and never reports training progress', () => {
  const s=summarize([]);
  assert.equal(s.status,'EMPTY');
  assert.deepEqual(s.models,[]);
  assert.equal(s.weightTraining,'NOT_EVALUATED');
  assert.equal(s.inputTrust,'UNVERIFIED_SANITIZED_DATA');
});

test('counts actual attempts separately from unique questions, grouped by exact checkpoint',()=>{
  const s=summarize([
    receipt(),
    receipt({attempt_id:'attempt-2',grade:'pass',failure_category:null,observed_at:'2026-11-28T17:40:00.000Z'}),
    receipt({checkpoint_sha256:'c'.repeat(64),attempt_id:'attempt-3',grade:'abstain',failure_category:null,question_id:'navigation-q2'}),
  ]);
  assert.equal(s.status,'READY');
  assert.equal(s.models.length,2);
  assert.equal(s.models[0].attempts,2);
  assert.equal(s.models[0].uniqueQuestions,1);
  assert.deepEqual(s.models[0].grades,{pass:1,fail:1,abstain:0});
  assert.equal(s.models[0].skills[0].failures.constraint,1);
  assert.equal(s.models[1].attempts,1);
  assert.equal(s.weightTraining,'NOT_EVALUATED');
});

test('preserves split-specific counts and exposes retention only when observed',()=>{
  const s=summarize([
    receipt({attempt_id:'d1',question_id:'d1',split:'development',grade:'pass',failure_category:null}),
    receipt({attempt_id:'t1',question_id:'t1',split:'transfer',grade:'fail',failure_category:'state'}),
    receipt({attempt_id:'r1',question_id:'r1',split:'retention',grade:'pass',failure_category:null}),
    receipt({attempt_id:'h1',question_id:'h1',split:'final-holdout',grade:'abstain',failure_category:null}),
  ]);
  assert.deepEqual(s.models[0].splits,{'development':1,'transfer':1,'retention':1,'final-holdout':1});
  assert.equal(s.models[0].skills[0].highestPassedDifficulty,2);
});

test('rejects identical attempt IDs within model and checkpoint',()=>{
  assert.throws(()=>summarize([receipt(),receipt({grade:'pass',failure_category:null})]),/DUPLICATE_ATTEMPT/);
});

test('rejects the same question crossing development and final holdout for a checkpoint',()=>{
  assert.throws(()=>summarize([receipt(),receipt({attempt_id:'attempt-2',split:'final-holdout'})]),/CROSS_SPLIT_QUESTION/);
});

test('rejects unknown/private fields rather than forwarding raw prompts, paths or tokens',()=>{
  assert.throws(()=>summarize([receipt({raw_answer:'sensitive answer'})]),/UNKNOWN_FIELD/);
  assert.throws(()=>summarize([receipt({access_token:'private'})]),/UNKNOWN_FIELD/);
  assert.throws(()=>summarize([receipt({weight_training_verified:true})]),/UNKNOWN_FIELD/);
});

test('rejects malformed records, nonfinite values, invalid dates and invented grades',()=>{
  for(const r of [null,[],receipt({latency_ms:Infinity}),receipt({tokens:-1}),receipt({grade:'perfect'}),receipt({observed_at:'2026-02-30T00:00:00.000Z'}),receipt({checkpoint_sha256:'not-a-hash'}),receipt({difficulty:999})]) {
    assert.throws(()=>summarize([r]),/INVALID_/);
  }
});

test('does not execute receipt getters or custom toJSON and rejects non-plain objects',()=>{
  let called=0;
  const getter=receipt();Object.defineProperty(getter,'model_id',{enumerable:true,get(){called++;throw Error('danger')}});
  assert.throws(()=>summarize([getter]),/INVALID_RECORD/);
  const serializer=receipt();serializer.toJSON=()=>{called++;return {}};
  assert.throws(()=>summarize([serializer]),/UNKNOWN_FIELD/);
  assert.throws(()=>summarize([Object.assign(Object.create({inherited:'value'}),receipt())]),/INVALID_RECORD/);
  assert.equal(called,0);
});

test('rejects sparse and accessor arrays without invoking their getters',()=>{
  let called=0;const sparse=new Array(1);
  assert.throws(()=>summarize(sparse),/INVALID_ARRAY/);
  const getter=[receipt()];Object.defineProperty(getter,'0',{get(){called++;throw Error('danger')}});
  assert.throws(()=>summarize(getter),/INVALID_ARRAY/);assert.equal(called,0);
});

test('marks stale evidence, refuses future evidence, and keeps supplied observation clock deterministic',()=>{
  const stale=summarize([receipt({observed_at:'2026-11-20T12:00:00.000Z'})]);
  assert.equal(stale.status,'STALE');assert.equal(stale.models[0].freshness,'STALE');
  assert.throws(()=>summarize([receipt({observed_at:'2026-12-01T12:00:00.000Z'})]),/FUTURE_RECEIPT/);
});

test('rejects overlong batches, nonarrays, absurd timeouts and invalid timestamps',()=>{
  assert.throws(()=>summarize({}),/INVALID_ARRAY/);
  assert.throws(()=>summarize(new Array(1001).fill(receipt())),/INVALID_ARRAY/);
  assert.throws(()=>summarize([],{maxAgeHours:Infinity}),/INVALID_OPTIONS/);
  assert.throws(()=>summarize([],{asOf:'yesterday'}),/INVALID_OPTIONS/);
});
