import test from 'node:test';
import assert from 'node:assert/strict';
import {inventoryReceipt} from '../mcp/local_model_inventory.mjs';
const model=(name,size=100,digest='a'.repeat(64))=>({name,size,digest,details:{parameter_size:'1B',quantization_level:'Q4_K_M'}});
test('inventory is stable under reorder and never claims qualification',()=>{
 const a=inventoryReceipt({models:[model('qwen3:8b'),model('qwen3:0.6b')]});
 const b=inventoryReceipt({models:[model('qwen3:0.6b'),model('qwen3:8b')]});
 assert.deepEqual(a,b); assert.equal(a.models.length,2); assert.equal(a.inference_verified,false); assert.equal(a.production_authority,false);
});
test('rejects malformed sizes, digest, duplicate name and oversized inventory',()=>{
 for(const models of [[model('x',-1)],[model('x',1,'bad')],[model('x'),model('x')],Array.from({length:257},(_,i)=>model(`m:${i}`))]) assert.throws(()=>inventoryReceipt({models}));
});
test('does not export unknown input or invent digest-distinct weights',()=>{
 const r=inventoryReceipt({models:[{...model('a:1'),secret:'private'},model('b:1')]});
 assert.equal(r.distinct_manifest_digests,1); assert.equal(r.logical_manifest_bytes,200); assert.equal(r.physical_disk_bytes,null); assert.ok(!JSON.stringify(r).includes('private'));
});
test('rejects invalid and nonlocal path-like names',()=>{
 for(const n of ['', 'C:\\private', 'https://example.com/model','a\nsecret']) assert.throws(()=>inventoryReceipt({models:[model(n)]}));
});
