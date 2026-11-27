import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdtempSync, readFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
test('registered U1101 placebo CLI runs two full worlds for one parameter key', {timeout: 30000}, () => {
  const output = mkdtempSync(join(tmpdir(), 'umbra-placebo-'));
  try {
    execFileSync(process.execPath, ['scripts/umbra_advanced_lab.mjs', '--id', 'U1101', '--out-dir', output], {cwd: root, timeout: 25000, env: {...process.env, GITHUB_STEP_SUMMARY: ''}});
    const receipt = JSON.parse(readFileSync(join(output, 'U1101.json'), 'utf8'));
    assert.equal(receipt.method, 'placebo-falsification');
    const result = receipt.results;
    assert.equal(result.uniqueWorldStates, 1);
    assert.equal(result.simulationExecutions, 2);
    assert.equal(result.data.independentExecutions, 2);
    assert.equal(result.data.difference, 0);
    assert.equal(result.data.pass, true);
    assert.match(result.data.firstStateDigest, /^[a-f0-9]{64}$/);
    assert.equal(result.data.firstStateDigest, result.data.secondStateDigest);
    assert.equal(receipt.flags.independentRealWorldValidity, false);
    assert.equal(result.productionAuthorized, false);
  } finally {
    rmSync(output, {recursive: true, force: true});
  }
});
