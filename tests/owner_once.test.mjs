import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const entry=fileURLToPath(new URL('../mcp/owner_once.mjs',import.meta.url));
const call=input=>spawnSync(process.execPath,[entry],{input,encoding:'utf8',timeout:45000,maxBuffer:1048576,env:{...process.env,UMBRA_MYRIAD_PYTHON:'',UMBRA_MYRIAD_BANK:''}});
test('owner CLI lists actual available tools',()=>{const p=call('{"operation":"list"}');assert.equal(p.status,0,p.stderr);const r=JSON.parse(p.stdout);assert.ok(r.tools.some(x=>x.name==='umbra_simulate'));assert.ok(!r.tools.some(x=>x.name==='myriad_checkpoint_evaluate'));});
test('owner CLI executes an actual seeded world',()=>{const p=call('{"operation":"call","name":"umbra_simulate","arguments":{"seed":42,"steps":2}}');assert.equal(p.status,0,p.stderr);const r=JSON.parse(p.stdout);assert.equal(r.synthetic,true);assert.equal(r.production_authority,false);assert.equal(r.result.seed,42);assert.equal(r.result.tick,2);});
test('owner CLI refuses unregistered tools, extra keys and oversized frames',()=>{for(const q of ['{"operation":"call","name":"shell","arguments":{}}','{"operation":"list","path":"x"}',' '.repeat(65537)]){const p=call(q);assert.notEqual(p.status,0);assert.equal(p.stdout,'');assert.match(p.stderr,/UMBRA owner request failed/);}});
