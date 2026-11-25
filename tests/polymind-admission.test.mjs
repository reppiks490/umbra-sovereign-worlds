import test from 'node:test';
import assert from 'node:assert/strict';
import {availableAdapters} from '../mcp/local_model_adapters.mjs';
import {planAdmission,requiredBytes} from '../mcp/polymind_admission.mjs';
const G=1024**3,sha='a'.repeat(64);
const model=(name,size)=>({name,size,digest:sha});
test('recognizes Mistral senior candidates without claiming training',async()=>{
 const r=await availableAdapters({request:async()=>({models:[model('mistral-nemo:12b',7*G),model('mistral-nemo:12b-instruct-2407-q3_K_M',5*G),model('mistral:latest',4*G)]})});
 assert.equal(r.adapters.length,3);assert.ok(r.adapters.every(m=>m.roles.includes('reasoning')));assert.equal(r.research_qualified,false);
});
test('large models need additional memory margin',()=>{assert.equal(requiredBytes('ollama',7*G),9*G);assert.equal(requiredBytes('onnxruntime',G/4),2*G);});
test('plan is role-specific, memory-aware, stable, and does not certify capability',()=>{
 const models=[{runtime:'ollama',model:'large',size_bytes:7*G,roles:['reasoning']},{runtime:'ollama',model:'small',size_bytes:G,roles:['reasoning']},{runtime:'onnxruntime',model:'other',size_bytes:G/8,roles:['retrieval']}];
 const r=planAdmission({models},'reasoning',4*G);assert.deepEqual(r.eligible.map(x=>x.model),['small']);assert.deepEqual(r.blocked.map(x=>x.model),['large']);assert.equal(r.research_qualified,false);assert.equal(r.production_authority,false);
});
test('busy Ollama is excluded and untrusted sizes fail closed',()=>{
 const m={runtime:'ollama',model:'x',size_bytes:G,roles:['reasoning']};
 assert.equal(planAdmission({models:[m]},'reasoning',8*G,true).eligible.length,0);
 assert.throws(()=>planAdmission({models:[{...m,size_bytes:-1}]},'reasoning',8*G));
 assert.throws(()=>planAdmission({models:[m]},'reasoning',NaN));
});

import {polymindPlan} from '../mcp/polymind_router.mjs';
test('live plan uses injected runtime and memory readings without executing models',async()=>{const p=await polymindPlan({role:'reasoning'},{list:async()=>({models:[{runtime:'ollama',model:'mistral:latest',roles:['reasoning'],size_bytes:G}]}),free:()=>3*G,busy:async()=>false});assert.equal(p.eligible[0].model,'mistral:latest');await assert.rejects(polymindPlan({role:'reasoning',free:99}));});
