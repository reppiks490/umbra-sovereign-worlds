import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// Dependency-free, intentionally narrow workflow contract: catches accidental
// removal of finite job budgets, least-privilege permissions, or smoke coverage.
const workflow = readFileSync(new URL('../.github/workflows/unit.yml', import.meta.url), 'utf8').replace(/\r\n/g, '\n');
const jobBlock = (name) => {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = workflow.match(new RegExp('^  ' + escaped + ':\\n([\\s\\S]*?)(?=^  [a-z][a-z0-9_-]*:\\n|(?![\\s\\S]))', 'm'));
  assert.ok(match, 'missing job: ' + name);
  return match[1];
};

test('CI uses explicit read-only GitHub permissions and noncancelling evidence', () => {
  assert.match(workflow, /^permissions:\n  contents: read$/m);
  assert.match(workflow, /^concurrency:\n  group: [^\n]+\n  cancel-in-progress: false$/m);
  assert.doesNotMatch(workflow, /^\s*(?:contents|actions|packages|deployments): write\s*$/m);
});

test('each required verification job has a finite nonzero timeout', () => {
  for (const [name, max] of [['unit', 20], ['browser', 30]]) {
    const body = jobBlock(name);
    const match = body.match(/^    timeout-minutes: (\d+)$/m);
    assert.ok(match, name + ' lacks a timeout');
    assert.ok(Number(match[1]) > 0 && Number(match[1]) <= max, name + ' timeout exceeds budget');
    assert.match(body, /runs-on: ubuntu-latest/);
  }
});

test('verification still executes model tests and all viewport smoke tests', () => {
  assert.match(jobBlock('unit'), /^        run: npm test$/m);
  assert.match(jobBlock('browser'), /^        run: python tests\/smoke\.py$/m);
  const smoke = readFileSync(new URL('./smoke.py', import.meta.url), 'utf8');
  for (const size of ['1440,900', '390,844', '768,1024']) {
    assert.ok(smoke.includes(size), 'missing viewport ' + size);
  }
});

test('existing scheduled and 300-case verification is preserved', () => {
  assert.match(workflow, /^  schedule:\n    - cron: '17 5,17 \* \* \*'$/m);
  assert.match(jobBlock('unit'), /^        run: python3 scripts\/validate_umbra_workflows\.py$/m);
  assert.match(jobBlock('unit'), /^        run: node scripts\/umbra_lab\.mjs --audit-all$/m);
});
