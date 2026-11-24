import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import evolution_research_protocol_v67 as m

KEY = b'local-test-fixture-not-a-real-secret-000'
def signed(record):
    r = copy.deepcopy(record)
    r.pop('hmac_sha256', None)
    r['hmac_sha256'] = m.ev.sign(r, KEY)
    return r

def fixture():
    seed = 992
    cases = m.cases(seed)
    out = []
    for protocol in ('compact','explicit'):
        raw = json.dumps([c['expected']+c['evidence_id'][1] for c in cases] if protocol=='compact' else
                         [{'n':i+1,'action':c['expected'],'fact':c['evidence_id']} for i,c in enumerate(cases)])
        out.append({'protocol':protocol,'case_sha256':hashlib.sha256(m.ev.canonical(cases)).hexdigest(),
                    'raw':raw,'response_sha256':'a'*64,'seconds':1.0,**m.score(cases,raw,protocol)})
    return {'schema':'myriad.research_protocol.v67','seed':seed,'model':m.MODEL,'digest':m.PINS[m.MODEL],
            'results':out,'errors':[],'production_authority':False,'status':'completed',
            'comparison':m.compare(*out)}

class ReceiptIntegrityTests(unittest.TestCase):
    def test_complete_and_failure_receipts_replay(self):
        r=fixture()
        self.assertTrue(m.verify(signed(r),KEY))
        r['status']='failed'; r.pop('comparison'); r['results'].pop()
        r['errors']=[{'protocol':'explicit','error_class':'TimeoutError'}]
        self.assertTrue(m.verify(signed(r),KEY))
        r['results'].clear(); r['errors'].insert(0,{'protocol':'compact','error_class':'ValueError'})
        self.assertTrue(m.verify(signed(r),KEY))

    def test_reject_wrong_model_and_unknown_state(self):
        for field,value in [('model','wrong-model'),('status','unknown'),('seed',True)]:
            with self.subTest(field=field):
                r=fixture(); r[field]=value
                with self.assertRaises(ValueError): m.verify(signed(r),KEY)

    def test_reject_inconsistent_failure_coverage(self):
        for mode in ('no-error','duplicate-success','duplicate-error','overlap','failed-comparison','unknown-protocol'):
            with self.subTest(mode=mode):
                r=fixture(); r['status']='failed'; r.pop('comparison')
                r['results'].pop()
                r['errors']=[{'protocol':'explicit','error_class':'TimeoutError'}]
                if mode=='no-error': r['errors']=[]
                if mode=='duplicate-success': r['results']*=2
                if mode=='duplicate-error': r['errors']*=2
                if mode=='overlap': r['errors'][0]['protocol']='compact'
                if mode=='failed-comparison': r['comparison']={}
                if mode=='unknown-protocol': r['errors'][0]['protocol']='other'
                with self.assertRaises(ValueError): m.verify(signed(r),KEY)

    def test_reject_extra_error_on_complete(self):
        r=fixture(); r['errors']=[{'protocol':'explicit','error_class':'TimeoutError'}]
        with self.assertRaises(ValueError): m.verify(signed(r),KEY)

    def test_reject_malformed_metadata_and_type_coercion(self):
        for field,value in [('response_sha256','not-a-digest'),('seconds',-1),('seconds',True),('total',4.0)]:
            with self.subTest(field=field):
                r=fixture(); r['results'][0][field]=value
                with self.assertRaises(ValueError): m.verify(signed(r),KEY)

    def test_reject_unauthenticated_or_extra_fields(self):
        r=signed(fixture()); r['model']='changed'
        with self.assertRaises(ValueError): m.verify(r,KEY)
        r=fixture(); r['unrecognized']=True
        with self.assertRaises(ValueError): m.verify(signed(r),KEY)

    def test_invalid_candidate_not_persisted(self):
        items={v['protocol']:v for v in fixture()['results']}; items['compact']['response_sha256']='broken'
        with patch.object(m.scale,'free_mb',return_value=4000), patch.object(m.teacher,'request',return_value=({'models':[]},b'')), patch.object(m.ev,'secret',return_value=KEY), patch.object(m,'infer',side_effect=lambda cases,protocol: {**items[protocol],'case_sha256':hashlib.sha256(m.ev.canonical(cases)).hexdigest(),'raw':json.dumps([c['expected']+c['evidence_id'][1] for c in cases] if protocol=='compact' else [{'n':i+1,'action':c['expected'],'fact':c['evidence_id']} for i,c in enumerate(cases)])}), patch.object(m.teacher,'save') as save, patch.object(m.orch,'atomic') as aggregate:
            with self.assertRaises(ValueError): m.run(Path('unused'),7000)
            save.assert_not_called()
            aggregate.assert_not_called()

if __name__=='__main__': unittest.main()
