import os,sys,subprocess,unittest
from local_process import capture,settlement
class ProcessTests(unittest.TestCase):
 def test_real_process_lifecycle(self):
  p=subprocess.Popen([sys.executable,'-c','import sys; sys.stdin.read()'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
   identity=capture(p.pid)
   self.assertEqual(identity['pid'],p.pid)
   self.assertEqual(settlement(identity)['state'],'running')
   p.stdin.close();p.wait(timeout=10)
   self.assertEqual(settlement(identity)['state'],'settled')
  finally:
   if p.poll() is None:p.terminate();p.wait(timeout=10)
 def test_current_process_never_released(self):
  self.assertEqual(settlement(capture(os.getpid()))['state'],'running')
 def test_wrong_identity_fails_closed(self):
  a=capture(os.getpid());a['birth']+='-wrong'
  self.assertEqual(settlement(a)['state'],'unknown')
 def test_invalid_identity(self):
  for a in ({},{'pid':0,'birth':'x','platform':sys.platform},{'pid':True,'birth':'x','platform':sys.platform}):
   with self.assertRaises(ValueError):settlement(a)
 def test_wrong_platform_fails_closed(self):
  a=capture(os.getpid());a['platform']='unrecognized'
  self.assertEqual(settlement(a)['state'],'unknown')
