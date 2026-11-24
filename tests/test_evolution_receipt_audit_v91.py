import json,tempfile,unittest
from pathlib import Path
import evolution_receipt_audit_v91 as m
import evolution_tool_research_v64 as tool
import evolution_reasoning_runtime_v82 as reasoning
import evolution_model_evidence_v24 as ev
KEY=b'x'*32
class Tests(unittest.TestCase):
    def setup_history(self,d):
        root=Path(d);h=root/'teacher-v40';h.mkdir();return root,h
    def tool_record(self,seed):
        return {'schema':'myriad.tool_research.v64','seed':seed,'model':'qwen3:1.7b','digest':tool.PINS['qwen3:1.7b'],'case_sha256':tool.hashlib.sha256(ev.canonical(tool.cases(seed))).hexdigest(),'production_authority':False,'arbitrary_code_execution':False,'status':'failed','error_class':'TimeoutError'}
    def write(self,path,r):
        path.write_bytes(ev.canonical({**r,'hmac_sha256':ev.sign(r,KEY)}))
    def test_both_families_authenticated_and_scores_replayed(self):
        with tempfile.TemporaryDirectory() as d:
            root,h=self.setup_history(d)
            self.write(h/'tool-research-v64-1.json',self.tool_record(4))
            self.write(h/'reasoning-v82-1.json',reasoning.failed(5,'request','TimeoutError'))
            r=m.audit(root,KEY)
            self.assertEqual(r['status'],'qualified')
            self.assertEqual(r['families']['tool']['verified'],1)
            self.assertEqual(r['families']['reasoning']['verified'],1)
            self.assertEqual(r['families']['tool']['failed_outcome'],1)
            self.assertEqual(r['families']['reasoning']['failed_outcome'],1)
            self.assertEqual(r['actual_model_calls'],0)
            self.assertNotIn('hmac_sha256',str(r))
    def test_tamper_duplicates_and_malformed_data(self):
        with tempfile.TemporaryDirectory() as d:
            root,h=self.setup_history(d)
            for i in (1,2):self.write(h/f'tool-research-v64-{i}.json',self.tool_record(4))
            self.write(h/'reasoning-v82-1.json',reasoning.failed(5,'request','TimeoutError'))
            p=h/'reasoning-v82-1.json'
            r=json.loads(p.read_bytes());r['seed']=6;p.write_text(json.dumps(r))
            (h/'reasoning-v82-2.json').write_text('{"seed":1,"seed":2}')
            report=m.audit(root,KEY)
            self.assertEqual(report['status'],'issues_detected')
            self.assertEqual(report['families']['tool']['duplicate_seed_records'],1)
            self.assertEqual(report['families']['reasoning']['rejected'],2)
    def test_empty_missing_and_bound(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            self.assertEqual(m.audit(root,KEY)['status'],'no_evidence')
            h=root/'teacher-v40';h.mkdir()
            (h/'tool-research-v64-1.json').write_bytes(b'x'*65537)
            self.assertEqual(m.audit(root,KEY)['families']['tool']['rejected'],1)
    def test_actual_completed_score_replay(self):
        with tempfile.TemporaryDirectory() as d:
            root,h=self.setup_history(d);r=self.tool_record(9)
            r.pop('error_class');c=tool.cases(9)
            r.update(status='completed',raw=json.dumps(list(tool.EXPECTED)),response_sha256='a'*64,results=[tool.evaluate(q,k) for q,k in zip(c,tool.EXPECTED)])
            self.write(h/'tool-research-v64-1.json',r)
            out=m.audit(root,KEY)
            self.assertEqual(out['families']['tool']['qualified_tasks'],8)
            self.assertEqual(out['families']['tool']['completed_outcome'],1)
    def test_duplicate_seeds_never_contribute_qualified_task_counts(self):
        with tempfile.TemporaryDirectory() as d:
            root,h=self.setup_history(d);r=self.tool_record(9)
            r.pop('error_class');c=tool.cases(9)
            r.update(status='completed',raw=json.dumps(list(tool.EXPECTED)),response_sha256='a'*64,results=[tool.evaluate(q,k) for q,k in zip(c,tool.EXPECTED)])
            self.write(h/'tool-research-v64-1.json',r)
            self.write(h/'tool-research-v64-2.json',r)
            out=m.audit(root,KEY)
            self.assertEqual(out['families']['tool']['qualified_tasks'],0)
            self.assertEqual(out['families']['tool']['duplicate_seed_records'],1)
if __name__=='__main__':unittest.main()
