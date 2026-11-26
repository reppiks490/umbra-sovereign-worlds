import os,pathlib,tempfile,unittest,concurrent.futures
from resource_reservation import Reservation
class ReservationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_pid_markers_and_release(self):
  with Reservation(self.root,['model-compute.lock','cache-use.lock']):
   for n in ('model-compute.lock','cache-use.lock'):self.assertEqual((self.root/n).read_text(),str(os.getpid()))
  self.assertEqual(list(self.root.iterdir()),[])
 def test_partial_acquisition_rolls_back_only_owned(self):
  foreign=self.root/'z.lock';foreign.write_text('99999')
  with self.assertRaises(FileExistsError):
   with Reservation(self.root,['a.lock','z.lock']):pass
  self.assertFalse((self.root/'a.lock').exists());self.assertEqual(foreign.read_text(),'99999')
 def test_stale_marker_is_never_reclaimed(self):
  f=self.root/'compute.lock';f.write_text('99999999')
  with self.assertRaises(FileExistsError):
   with Reservation(self.root,['compute.lock']):pass
  self.assertEqual(f.read_text(),'99999999')
 def test_nested_competitor_refused(self):
  with Reservation(self.root,['a.lock','b.lock']):
   with self.assertRaises(FileExistsError):
    with Reservation(self.root,['b.lock']):pass
   self.assertTrue((self.root/'b.lock').exists())
 def test_modified_marker_preserved(self):
  r=Reservation(self.root,['a.lock']);r.__enter__();(self.root/'a.lock').write_text('foreign')
  with self.assertRaises(ValueError):r.__exit__(None,None,None)
  self.assertEqual((self.root/'a.lock').read_text(),'foreign')
 def test_missing_marker_not_recreated(self):
  r=Reservation(self.root,['a.lock']);r.__enter__();(self.root/'a.lock').unlink()
  with self.assertRaises(ValueError):r.__exit__(None,None,None)
  self.assertFalse((self.root/'a.lock').exists())
 def test_invalid_names_and_missing_root(self):
  for names in ([],['a.lock','a.lock'],['../a.lock'],['a/b.lock'],['a\\b.lock'],['a:stream'],['CON.lock']):
   with self.assertRaises(ValueError):Reservation(self.root,names)
  with self.assertRaises(ValueError):Reservation(self.root/'missing',['a.lock'])
 def test_release_on_body_failure(self):
  with self.assertRaisesRegex(RuntimeError,'body'):
   with Reservation(self.root,['a.lock','b.lock']):raise RuntimeError('body')
  self.assertEqual(list(self.root.iterdir()),[])
 def test_single_use(self):
  r=Reservation(self.root,['a.lock'])
  with r:pass
  with self.assertRaises(ValueError):
   with r:pass
 def test_parallel_competitors(self):
  import threading
  barrier=threading.Barrier(8)
  def work(i):
   try:
    with Reservation(self.root,['a.lock']):
     barrier.wait(timeout=10)
     return 1
   except FileExistsError:
    barrier.wait(timeout=10);return 0
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:r=list(ex.map(work,range(8)))
  self.assertEqual(sum(r),1)
