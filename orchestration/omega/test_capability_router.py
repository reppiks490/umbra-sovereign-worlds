import unittest
from capability_router import select,validate_registry
def registry():
 return {'connectorNamespaces':[{'name':'GitHub','actions':['mcp__GitHub__fetch_file','mcp__GitHub__update_file']},{'name':'Remote_Desktop_Commander','actions':['mcp__Remote_Desktop_Commander__read_file']}],'routing':[{'lane':'ICARUS','connectors':['GitHub','Remote_Desktop_Commander']}]}
def policy():
 return {'mcp__GitHub__fetch_file':{'lane':'ICARUS','intent':'source-read','effect':'read','rank':1},'mcp__GitHub__update_file':{'lane':'ICARUS','intent':'source-read','effect':'write','rank':9},'mcp__Remote_Desktop_Commander__read_file':{'lane':'ICARUS','intent':'source-read','effect':'read','rank':2}}
def evidence(action,**kw):
 return {'action':action,'observed_at':100,'status':'verified-read','receipt_sha256':'a'*64,**kw}
class RouteTests(unittest.TestCase):
 def test_discovery_is_not_verified_execution(self):
  self.assertIsNone(select(registry(),policy(),[],'ICARUS','source-read',101))
 def test_verified_read_and_rank(self):
  p=policy();a='mcp__GitHub__fetch_file';b='mcp__Remote_Desktop_Commander__read_file'
  self.assertEqual(select(registry(),p,[evidence(a),evidence(b)],'ICARUS','source-read',101)['action'],b)
 def test_stale_future_and_failed_receipts(self):
  a='mcp__GitHub__fetch_file'
  for e in (evidence(a,observed_at=0),evidence(a,observed_at=102),evidence(a,status='failed'),evidence(a,receipt_sha256='x')):
   self.assertIsNone(select(registry(),policy(),[e],'ICARUS','source-read',101,max_age=50))
 def test_mutation_never_selected(self):
  a='mcp__GitHub__update_file'
  self.assertIsNone(select(registry(),policy(),[evidence(a)],'ICARUS','source-read',101))
 def test_lane_and_intent_boundaries(self):
  a='mcp__GitHub__fetch_file'
  for lane,intent in [('UMBRA','source-read'),('ICARUS','execute')]:
   self.assertIsNone(select(registry(),policy(),[evidence(a)],lane,intent,101))
 def test_duplicate_action_registry_rejected(self):
  r=registry();r['connectorNamespaces'][0]['actions'].append('mcp__GitHub__fetch_file')
  with self.assertRaises(ValueError):validate_registry(r)
 def test_latest_failure_revokes_prior_success(self):
  a='mcp__GitHub__fetch_file';e=[evidence(a),evidence(a,observed_at=101,status='failed')]
  self.assertIsNone(select(registry(),policy(),e,'ICARUS','source-read',102))
 def test_conflicting_same_time_fails_closed(self):
  a='mcp__GitHub__fetch_file';e=[evidence(a),evidence(a,status='failed')]
  self.assertIsNone(select(registry(),policy(),e,'ICARUS','source-read',101))
