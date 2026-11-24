import unittest
from unittest.mock import patch
import evolution_observatory_live_v52 as m
import evolution_telemetry_v48 as t
class Tests(unittest.TestCase):
 def test_missing_data_is_not_zero(self):
  with patch.object(m,'fetch_snapshot',side_effect=OSError('offline')):
   self.assertEqual(m.live_data()['freshness'],'unavailable')
   self.assertNotIn('counts',m.live_data())
 def test_valid_snapshot(self):
  v=t.snapshot(1000,{k:0 for k in t.FIELDS})
  with patch.object(m,'fetch_snapshot',return_value=v),patch.object(m.time,'time',return_value=1050):
   self.assertEqual(m.live_data()['freshness'],'fresh')
 def test_tamper_rejected(self):
  v=t.snapshot(1000,{k:0 for k in t.FIELDS});v['counts']['legacy_completed']=999
  with patch.object(m,'fetch_snapshot',return_value=v):
   self.assertEqual(m.live_data()['freshness'],'unavailable')
 def test_browser_document_has_live_link(self):
  self.assertIn(b'/live.js',m.PAGE)
  self.assertIn(b'Live aggregate',m.PAGE)
if __name__=='__main__':unittest.main()
