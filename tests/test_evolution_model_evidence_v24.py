"""Fail-closed, independently replayable private model-evaluation evidence."""
import hashlib
import hmac
import importlib
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
# The public CI run has the real v2.2 adapter; the local source reconstruction
# may only contain v1.8. Stub only the transport, never the evidence logic.
try:
    import evolution_local_model_v22 as base
except ImportError:
    base=types.ModuleType('evolution_local_model_v22')
    def tasks(seed,count):
        import random
        rng=random.Random(seed); result=[]
        for i in range(count):
            a,b=rng.randint(11,99),rng.randint(11,99);op=('+','-','*')[i%3]
            result.append((f'Return only the integer result of {a} {op} {b}.',str({'+':a+b,'-':a-b,'*':a*b}[op])))
        return result
    def config(port,model,seed,count,max_tokens,budget,timeout):
        if count*max_tokens>budget or not 1<=count<=8:raise ValueError('Invalid budget')
    base.tasks=tasks;base.config=config;base.request=lambda *args: (_ for _ in ()).throw(AssertionError('No network expected'))
    sys.modules['evolution_local_model_v22']=base
import evolution_model_evidence_v24 as evidence

class ModelEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name)/'raw_private.json'
        self.key='research-only-secret-key-32-characters-minimum'
        self.original=patch.dict(os.environ,{'MYRIAD_LOCAL_MODEL_TOKEN':'fixture-only','MYRIAD_EVIDENCE_HMAC_KEY':self.key})
        self.original.start();self.addCleanup(self.original.stop)
    def run_model(self,**override):
        kw={'port':8765,'model':'deterministic-fixture','seed':41,'count':3,'max_tokens':16,'budget':48,'timeout':2,
            'deadline_seconds':20,'out':self.out,'authorize':True}
        kw.update(override)
        def fake_request(port,model,prompt,token,max_tokens,timeout):
            expected={p:a for p,a in base.tasks(41,3)}[prompt]
            return expected,2,hashlib.sha256(expected.encode()).hexdigest()
        with patch.object(base,'request',side_effect=fake_request) as request:
            result=evidence.run(**kw)
            return result,request.call_count
    def test_exact_outputs_saved_and_independently_replayed(self):
        result,calls=self.run_model()
        self.assertEqual(calls,3)
        self.assertEqual(result['correct'],3)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(len(result['rows']),3)
        self.assertEqual(result['rows'][0]['content'],base.tasks(41,3)[0][1])
        self.assertTrue(evidence.verify(json.loads(self.out.read_text()))['score_replayed'])
        self.assertFalse(evidence.verify(result)['model_identity_authenticated'])
        self.assertEqual(self.out.stat().st_mode & 0o777,0o600)
        self.assertNotIn(self.key,self.out.read_text())
        self.assertNotIn('fixture-only',self.out.read_text())
    def test_no_requests_without_explicit_authority(self):
        with self.assertRaises(PermissionError):self.run_model(authorize=False)
        self.assertFalse(self.out.exists())
    def test_reject_budget_before_creating_output(self):
        with self.assertRaises(ValueError):self.run_model(budget=47)
        self.assertFalse(self.out.exists())
    def test_no_existing_evidence_overwrite(self):
        self.out.write_bytes(b'original')
        with self.assertRaises(FileExistsError):self.run_model()
        self.assertEqual(self.out.read_bytes(),b'original')
    def test_hmac_tampering_rejected(self):
        self.run_model();r=json.loads(self.out.read_text());r['rows'][0]['content']='999'
        with self.assertRaises(ValueError):evidence.verify(r)
    def test_modified_answer_with_recomputed_hmac_still_rejected(self):
        self.run_model();r=json.loads(self.out.read_text());r['rows'][0]['content']='999'
        r['correct']=2;r['rows'][0]['exact_match']=False
        r.pop('hmac_sha256');r['hmac_sha256']=hmac.new(self.key.encode(),evidence.canonical(r),hashlib.sha256).hexdigest()
        with self.assertRaises(ValueError):evidence.verify(r)
    def test_wrong_key_rejected(self):
        self.run_model();r=json.loads(self.out.read_text())
        with patch.dict(os.environ,{'MYRIAD_EVIDENCE_HMAC_KEY':'different-secret-key-32-characters-minimum'}):
            with self.assertRaises(ValueError):evidence.verify(r)
    def test_private_raw_output_limit(self):
        def huge(*args):return 'x'*50000,2,hashlib.sha256(b'x').hexdigest()
        with patch.object(base,'request',side_effect=huge):
            with self.assertRaises(ValueError):
                evidence.run(port=8765,model='fixture',seed=41,count=1,max_tokens=16,budget=16,
                             timeout=2,deadline_seconds=20,out=self.out,authorize=True)
        self.assertEqual(json.loads(self.out.read_text())['status'],'incomplete')
    def test_incomplete_report_never_authorized(self):
        def broken(*args):raise ConnectionError('local model failed')
        with patch.object(base,'request',side_effect=broken):
            with self.assertRaises(ConnectionError):
                evidence.run(port=8765,model='fixture',seed=41,count=1,max_tokens=16,budget=16,
                             timeout=2,deadline_seconds=20,out=self.out,authorize=True)
        report=json.loads(self.out.read_text())
        self.assertEqual(report['status'],'incomplete')
        self.assertFalse(evidence.verify(report)['completed'])
    def test_deadline_preempts_expensive_endpoint(self):
        # Cheap deterministic wall-clock check before first network call.
        with patch.object(evidence.time,'monotonic',side_effect=[1.0,100.0]):
            with self.assertRaises(TimeoutError):self.run_model(deadline_seconds=0.5)
        self.assertEqual(json.loads(self.out.read_text())['status'],'incomplete')

if __name__=='__main__':unittest.main()
