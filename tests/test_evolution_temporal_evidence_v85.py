import unittest
import evolution_temporal_evidence_v85 as m

H='a'*64

def record(event, available, revision, value, series='macro', entity='x'):
    return dict(source='example',series=series,entity=entity,event_time=event,available_time=available,revision=revision,value=value,source_sha256=H)

class Tests(unittest.TestCase):
    def test_revisions_never_leak(self):
        data=[record(100,120,0,1),record(100,180,1,9),record(130,140,0,2)]
        self.assertEqual(m.snapshot(data,119),[])
        self.assertEqual([r['value'] for r in m.snapshot(data,150)],[1,2])
        self.assertEqual([r['value'] for r in m.snapshot(data,180)],[9,2])
        self.assertEqual(m.snapshot(data[::-1],180),m.snapshot(data,180))
    def test_equal_revision_conflict_and_invalid_time(self):
        a=record(100,120,0,1)
        self.assertEqual(len(m.snapshot([a,a],200)),1)
        for b in [{**a,'value':2},{**a,'available_time':99},{**a,'event_time':True},{**a,'source_sha256':'invalid'},{**a,'value':float('nan')},{**a,'revision':True},{**a,'extra':1}]:
            with self.subTest(b=b),self.assertRaises(ValueError):m.snapshot([a,b],200)
    def test_stale_policy_and_latest_known(self):
        data=[record(100,120,0,1),record(130,140,0,2),record(180,190,0,3),record(110,150,0,5,'environment')]
        result=m.latest(data,160,50)
        self.assertEqual({r['series']:r['value'] for r in result},{'macro':2,'environment':5})
        self.assertEqual(m.latest(data,160,20),[])
    def test_purged_split_respects_label_availability(self):
        rows=[dict(id='a',decision_time=10,label_end=20,label_available=22),dict(id='b',decision_time=20,label_end=35,label_available=40),dict(id='c',decision_time=30,label_end=31,label_available=55),dict(id='d',decision_time=45,label_end=48,label_available=50),dict(id='e',decision_time=50,label_end=60,label_available=62),dict(id='f',decision_time=70,label_end=90,label_available=100),dict(id='g',decision_time=80,label_end=81,label_available=82)]
        p=m.purged_split(rows,50,80,5,90)
        self.assertEqual(p['train'],['a','b']);self.assertEqual(p['test'],['e']);self.assertEqual(p['purged_train'],['c','d']);self.assertEqual(p['unmatured_test'],['f'])
        self.assertEqual(p,m.purged_split(rows[::-1],50,80,5,90))
        with self.assertRaises(ValueError):m.purged_split(rows+[rows[0]],50,80,5,90)
    def test_cross_domain_revision_identity(self):
        a=record(100,120,0,1);b=record(100,120,0,8,'energy');c=record(100,120,0,9,entity='y')
        self.assertEqual(len(m.snapshot([a,b,c],120)),3)
        with self.assertRaises(ValueError):m.snapshot([a,record(100,110,1,2)],150)
if __name__=='__main__':unittest.main()
