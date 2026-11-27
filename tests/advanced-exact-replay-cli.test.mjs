import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const root=new URL('../',import.meta.url);
test('exact replay receipt proves two independent full states', {timeout:30000},()=>{
 const output=mkdtempSync(join(tmpdir(),'umbra-exact-'));
 execFileSync(process.execPath,['scripts/umbra_advanced_lab.mjs','--id','U4301','--out-dir',output],{cwd:root,timeout:25000,env:{...process.env,GITHUB_STEP_SUMMARY:''}});
 const r=JSON.parse(readFileSync(join(output,'U4301.json'),'utf8')).results;
 assert.equal(r.uniqueWorldStates,1);
 assert.equal(r.simulationExecutions,2);
 assert.equal(r.data.independentExecutions,2);
 assert.match(r.data.firstStateDigest,/^[a-f0-9]{64}$/);
 assert.equal(r.data.firstStateDigest,r.data.secondStateDigest);
 assert.equal(r.data.pass,true);
 assert.equal(r.productionAuthorized,false);
});
