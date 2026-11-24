import json
import pathlib
import tempfile
import unittest
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from validate_daily_fleet import verify_manual_workflows, verify_evidence, validate_schedule

class FleetGate(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)
        (self.root/'.github/workflows').mkdir(parents=True)
    def add(self, number, cmd=None):
        code=f'U{number:03d}' if number<=300 else f'U{number:04d}'
        name=f'umbra-u{number:03d}-demo.yml' if number<=300 else f'umbra-u{number:04d}-demo.yml'
        content=f'name: {code}\non:\n  workflow_dispatch:\njobs:\n  verify:\n    steps:\n      - run: node scripts/{"umbra_lab.mjs" if number<=300 else "umbra_advanced_lab.mjs"} --id {code}\n'
        (self.root/'.github/workflows'/name).write_text(cmd or content)
    def test_exact_manual_case_coverage(self):
        for n in (1,2,301,302):self.add(n)
        a=verify_manual_workflows(self.root,expected_base=2,expected_advanced=2)
        self.assertEqual(a['count'],4)
    def test_gap_blocks(self):
        for n in (1,301,302):self.add(n)
        with self.assertRaisesRegex(ValueError,'coverage'):
            verify_manual_workflows(self.root,expected_base=2,expected_advanced=2)
    def test_dangerous_command_rejected(self):
        self.add(1,cmd='name: U001\non:\n  workflow_dispatch:\nsteps:\n - run: node scripts/umbra_lab.mjs --id U002')
        self.add(301)
        with self.assertRaises(ValueError):verify_manual_workflows(self.root,expected_base=1,expected_advanced=1)
    def test_implicit_schedule_rejected(self):
        self.add(1,cmd='on:\n  schedule:\n  workflow_dispatch:\n - run: node scripts/umbra_lab.mjs --id U001')
        self.add(301)
        with self.assertRaises(ValueError):verify_manual_workflows(self.root,expected_base=1,expected_advanced=1)
    def test_shard_receipts(self):
        evidence=self.root/'receipts';evidence.mkdir()
        (evidence/'base.json').write_text(json.dumps({'schema':'umbra.synthetic.catalog.audit.v1','passed':2,'failed':0,'total':2}))
        for n in range(2):
            (evidence/f'shard-{n}.json').write_text(json.dumps({'schema':'umbra.synthetic.advanced-shard.v1','shard':n,'totalShards':2,'passed':2,'failed':0,'expected':2,'aggregateDigest':'a'*64,'failures':[]}))
        self.assertEqual(verify_evidence(evidence,base_count=2,advanced_count=4,shards=2)['total_passed'],6)
    def test_shard_duplicate_rejected(self):
        evidence=self.root/'receipts';evidence.mkdir()
        (evidence/'base.json').write_text(json.dumps({'schema':'umbra.synthetic.catalog.audit.v1','passed':2,'failed':0,'total':2}))
        for n in range(2):
            (evidence/f'shard-{n}.json').write_text(json.dumps({'schema':'umbra.synthetic.advanced-shard.v1','shard':0,'totalShards':2,'passed':2,'failed':0,'expected':2,'aggregateDigest':'a'*64,'failures':[]}))
        with self.assertRaises(ValueError):verify_evidence(evidence,base_count=2,advanced_count=4,shards=2)
    def test_no_legacy_300_only_validator(self):
        wf=(pathlib.Path(__file__).resolve().parents[1]/'.github/workflows/umbra-daily-scenario-fleet.yml').read_text()
        self.assertNotIn('python3 scripts/validate_umbra_workflows.py',wf)
    def test_schedule_is_two_daily_utc(self):
        path=pathlib.Path(__file__).resolve().parents[1]/'.github/workflows/umbra-daily-scenario-fleet.yml'
        self.assertTrue(validate_schedule(path)['valid'])

if __name__=='__main__':unittest.main()
