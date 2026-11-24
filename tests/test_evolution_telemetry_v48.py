import unittest
import evolution_telemetry_v48 as m
class Tests(unittest.TestCase):
 def test_freshness_and_privacy(self):
  v=m.snapshot(1000,{'legacy_enrolled':128,'legacy_completed':243,'fleet_enrolled':195000,'fleet_distinct_completed':8,'fleet_completed_items':8,'fleet_model_calls':2,'fleet_peer_linked':0,'specialist_completed':68,'source_completed':22,'ability_rows':8192,'ability_bytes':8192000,'ability_updates':196608,'agent_checkpoints':16,'agent_bytes':13152000,'teacher_labels':28,'student_updates':4480,'algorithm_implementations_added':0})
  self.assertEqual(m.validate(v,1100)['freshness'],'fresh')
  self.assertEqual(m.validate(v,3000)['freshness'],'stale')
  v['token']='secret'
  with self.assertRaises(ValueError):m.validate(v,1100)
 def test_false_count_rejected(self):
  counts={k:0 for k in m.FIELDS}
  counts['fleet_distinct_completed']=1
  with self.assertRaises(ValueError):m.snapshot(1000,counts)
 def test_future_rejected(self):
  v=m.snapshot(1000,{k:0 for k in m.FIELDS})
  with self.assertRaises(ValueError):m.validate(v,1)
if __name__=='__main__':unittest.main()
