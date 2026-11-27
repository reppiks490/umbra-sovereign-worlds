import test from 'node:test';
import assert from 'node:assert/strict';
import {EVIDENCE_SCHEMA,validateEvidenceManifest as check} from '../evidence-contract.mjs';
const fixture=()=>({
  schema:EVIDENCE_SCHEMA,provider:'Example Research',dataset:'synthetic-fixture',
  version:'1.0',license:'unverified',rights:'UNVERIFIED',retentionDays:0,
  redistribution:'DENIED',updateCadence:'unspecified',
  observedAt:'2026-01-01T00:00:00Z',capturedAt:'2026-01-02T00:00:00Z',
  validFrom:'2025-01-01T00:00:00Z',validTo:null,units:'synthetic index',
  missingness:'unknown',costUsd:0,authScope:'none',revocation:'unknown',
  sha256:'a'.repeat(64)
});
test('valid strict offline manifest remains blocked for rights and external truth',()=>{
  const result=check(fixture());
  assert.equal(result.ok,true);assert.equal(result.rightsVerified,false);
  assert.equal(result.externalValidation,false);assert.equal(result.checksumVerified,false);
  assert.equal(result.licensedDataFetched,false);assert.equal(result.status,'SCHEMA_VALID_RIGHTS_UNVERIFIED');
  assert.equal(result.validTo,null);assert.equal(Object.isFrozen(result),true);
});
test('valid finite validity interval',()=>assert.equal(check({...fixture(),validTo:'2026-01-01T00:00:00Z'}).ok,true));
test('no prototype or inherited data accepted',()=>{
  assert.equal(check(Object.create({provider:'evil'})).ok,false);
  assert.equal(check(new Date()).ok,false);
  assert.equal(check(null).ok,false);
  assert.equal(check([]).ok,false);
});
test('reject unexpected fields, missing fields and symbols',()=>{
  assert.equal(check({...fixture(),token:'secret'}).ok,false);
  const missing=fixture();delete missing.license;
  assert.equal(check(missing).ok,false);
  const sym=fixture();sym[Symbol('hidden')]='x';
  assert.equal(check(sym).ok,false);
});
test('reject accessor and toJSON without executing either',()=>{
  let invoked=0;
  const getter=fixture();
  Object.defineProperty(getter,'provider',{enumerable:true,get(){invoked++;throw Error('getter executed');}});
  assert.equal(check(getter).ok,false);assert.equal(invoked,0);
  const json=fixture();json.toJSON=()=>{invoked++;throw Error('toJSON executed');};
  assert.equal(check(json).ok,false);assert.equal(invoked,0);
});
test('reject malformed bitemporal order, invalid dates and reversed intervals',()=>{
  for(const x of [
    {capturedAt:'2025-01-01T00:00:00Z'},
    {observedAt:'2026-02-30T00:00:00Z'},
    {capturedAt:'2026-01-02T00:00:00+00:00'},
    {validTo:'2024-12-31T00:00:00Z'},
    {validTo:'2025-01-01T00:00:00Z'},
    {validTo:{}},
  ]) assert.equal(check({...fixture(),...x}).ok,false,JSON.stringify(x));
});
test('reject nonfinite and out-of-bounds costs/retention',()=>{
  for(const x of [{costUsd:NaN},{costUsd:Infinity},{costUsd:-1},
    {costUsd:1000001},{retentionDays:1.5},{retentionDays:-1},
    {retentionDays:36501},{retentionDays:true}])
    assert.equal(check({...fixture(),...x}).ok,false,JSON.stringify(x));
});
test('reject malformed declared digest, rights and redistribution',()=>{
  for(const x of [{sha256:'bad'},{sha256:'A'.repeat(64)},
    {rights:'VERIFIED'}, {redistribution:'OPEN'}, {license:'<script>'}])
    assert.equal(check({...fixture(),...x}).ok,false,JSON.stringify(x));
});
test('does not mutate source or silently claim data access',()=>{
  const f=fixture();const before=structuredClone(f);const result=check(f);
  assert.deepEqual(f,before);assert.equal(Object.hasOwn(result,'rawRows'),false);
  assert.equal(Object.hasOwn(result,'credentials'),false);
});
test('null prototype object accepted only with exact own data keys',()=>{
  const f=Object.assign(Object.create(null),fixture());
  assert.equal(check(f).ok,true);
});

test('uninspectable proxy manifests fail closed without propagating traps',()=>{
  const revoked=Proxy.revocable(fixture(),{});revoked.revoke();
  const samples=[
    new Proxy(fixture(),{getPrototypeOf(){throw Error('prototype trap');}}),
    new Proxy(fixture(),{ownKeys(){throw Error('ownKeys trap');}}),
    revoked.proxy
  ];
  for(const sample of samples){
    const result=check(sample);
    assert.equal(result.ok,false);
    assert.equal(result.status,'BLOCKED');
    assert.equal(result.rightsVerified,false);
    assert.equal(result.externalValidation,false);
    assert.equal(Object.isFrozen(result),true);
  }
  const result=check(new Proxy(fixture(),{}));
  assert.equal(result.ok,true);
  assert.equal(result.rightsVerified,false);
  assert.equal(result.checksumVerified,false);
});
