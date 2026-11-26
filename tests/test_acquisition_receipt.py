import json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import acquisition_receipt as q

class QueueReceiptTests(unittest.TestCase):
 def test_missing_or_later_stop_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)
   self.assertEqual(q.queue_status(p,lambda:[]),'initial_queue_not_verified')
   (p/'acquisition.log').write_text('2026-11-25 13:06:15 DONE 12871577600\n2026-11-25 14:00:00 STOP_STORAGE 0\n')
   self.assertEqual(q.queue_status(p,lambda:[q.expected_tag()]),'initial_queue_not_verified')
 def test_verified_completion_survives_model_absence_but_not_new_failure(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'acquisition.log').write_text('2026-11-25 13:06:15 DONE 12871577600\n')
   layers=q.expected_layers()
   with patch.object(q,'inspect_installed_manifest',return_value={'manifest_sha256':'c'*64,'layers':layers}):
    receipt=q.record_completion(p,[q.expected_tag()],p)
   self.assertTrue(q.completed_receipt(p))
   self.assertEqual(q.queue_status(p,lambda:[]),'ready')
   self.assertEqual(q.queue_status(p,lambda:(_ for _ in ()).throw(OSError())),'ollama_unavailable')
   self.assertEqual(receipt['scope'],'historical acquisition metadata; not model capability or training evidence')
   (p/'acquisition.log').write_text('2026-11-25 13:06:15 DONE 12871577600\n2026-11-25 14:00:00 STOP_STORAGE 0\n')
   self.assertFalse(q.completed_receipt(p))
 def test_wrong_tag_and_active_lock_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'acquisition.log').write_text('2026-11-25 13:06:15 DONE 12871577600\n')
   with self.assertRaises(ValueError):q.record_completion(p,[{**q.expected_tag(),'digest':'f'*64}],p)
   (p/'active.lock').write_text('123')
   with self.assertRaises(ValueError):q.record_completion(p,[q.expected_tag()],p)
   self.assertEqual(q.queue_status(p,lambda:[q.expected_tag()]),'deferred_acquisition')
 def test_metadata_tamper_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'acquisition.log').write_text('2026-11-25 13:06:15 DONE 12871577600\n')
   with patch.object(q,'inspect_installed_manifest',return_value={'manifest_sha256':'c'*64,'layers':q.expected_layers()}):q.record_completion(p,[q.expected_tag()],p)
   r=json.loads((p/q.RECEIPT).read_text());r['tag']['size']=1;(p/q.RECEIPT).write_text(json.dumps(r))
   self.assertFalse(q.completed_receipt(p))
   self.assertEqual(q.queue_status(p,lambda:[]),'q8_not_installed')
 def test_historical_complete_prevents_reacquisition(self):
  from acquisition_recovery import plan_recovery
  self.assertEqual(plan_recovery(False,False,False,True,40000000000,None,completed_proof=True)['status'],'complete')
  self.assertEqual(plan_recovery(False,False,True,True,40000000000,None,completed_proof=True)['status'],'queue_running')
  self.assertEqual(plan_recovery(False,False,False,False,40000000000,None,completed_proof=True)['status'],'deferred_partial_identity')
if __name__=='__main__':unittest.main()
