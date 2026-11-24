"""Adversarial proof that a partial manifest cannot validate an intact weight blob."""
import copy
import json
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import myriad_bank_fabric as bank

# The CI fixture has to be a portable minimal bank, not a private real checkpoint.
# Use a deterministic, correctly hashed fixture when the actual sample is absent.


def synthetic_fixture():
    import hashlib
    agents = bytes(10 * bank.BASE_AGENT_WIDTH * 2)
    abilities = bytes(10_000 * bank.BASE_ABILITY_WIDTH * 2)
    steps = bytes([1]) * 10_000
    manifest = {
        'schema':'myriad.portable_joint_bank.v1', 'agent_parameters':bank.BASE_AGENT_WIDTH,
        'ability_parameters':bank.BASE_ABILITY_WIDTH, 'auto_promote':False,
        'agent_weight_sha256':hashlib.sha256(agents).hexdigest(),
        'ability_weight_sha256':hashlib.sha256(abilities).hexdigest(),
        'agent_rows':[{'agent':j,'sha256':hashlib.sha256(agents[(j-1)*bank.BASE_AGENT_WIDTH*2:j*bank.BASE_AGENT_WIDTH*2]).hexdigest(),'steps':1} for j in range(1,11)],
        'ability_ranges':[{'start':j*1000+1,'end':(j+1)*1000,
            'sha256':hashlib.sha256(abilities[j*1000*bank.BASE_ABILITY_WIDTH*2:(j+1)*1000*bank.BASE_ABILITY_WIDTH*2]).hexdigest(),
            'steps_sha256':hashlib.sha256(steps[j*1000:(j+1)*1000]).hexdigest()}
            for j in range(10)],
    }
    return manifest, {'agent_weights.fp16':agents,'ability_weights.fp16':abilities,'ability_steps.u8':steps}


class CheckpointVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.payload = synthetic_fixture()
        cls.temp = tempfile.TemporaryDirectory()
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()
    def archive(self, manifest=None, payload=None, extras=None, duplicate=None):
        manifest = copy.deepcopy(manifest if manifest is not None else self.manifest)
        payload = payload if payload is not None else self.payload
        target = Path(self.temp.name) / f'{self._testMethodName}.zip'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:
                z.writestr('manifest.json',json.dumps(manifest))
                for k,v in payload.items():z.writestr(k,v)
                if extras:
                    for k,v in extras.items():z.writestr(k,v)
                if duplicate:z.writestr(duplicate,payload[duplicate])
        return target
    def reject(self, manifest=None, payload=None, extras=None, duplicate=None):
        with self.assertRaises((ValueError,TypeError,KeyError,zipfile.BadZipFile)):
            bank.verify_sample(self.archive(manifest,payload,extras,duplicate))
    def test_valid_checkpoint_is_accepted(self):
        r=bank.verify_sample(self.archive())
        self.assertEqual((r['verified_agents'],r['verified_ability_adapters']),(10,10_000))
    def test_partial_agent_manifest_rejected(self):
        m=copy.deepcopy(self.manifest);m['agent_rows']=m['agent_rows'][:3];self.reject(m)
    def test_duplicate_agent_id_rejected(self):
        m=copy.deepcopy(self.manifest);m['agent_rows'][9]=copy.deepcopy(m['agent_rows'][0]);self.reject(m)
    def test_agent_index_boolean_rejected(self):
        m=copy.deepcopy(self.manifest);m['agent_rows'][0]['agent']=True;self.reject(m)
    def test_agent_steps_zero_rejected(self):
        m=copy.deepcopy(self.manifest);m['agent_rows'][0]['steps']=0;self.reject(m)
    def test_agent_rows_unsorted_rejected(self):
        m=copy.deepcopy(self.manifest);m['agent_rows'][0],m['agent_rows'][1]=m['agent_rows'][1],m['agent_rows'][0];self.reject(m)
    def test_partial_ability_manifest_rejected(self):
        m=copy.deepcopy(self.manifest);m['ability_ranges']=m['ability_ranges'][:2];self.reject(m)
    def test_ability_range_gap_rejected(self):
        m=copy.deepcopy(self.manifest);m['ability_ranges'][1]['start']=2002;self.reject(m)
    def test_ability_range_overlap_rejected(self):
        m=copy.deepcopy(self.manifest);m['ability_ranges'][1]['start']=900;self.reject(m)
    def test_ability_range_reordered_rejected(self):
        m=copy.deepcopy(self.manifest);m['ability_ranges'].reverse();self.reject(m)
    def test_ability_range_boolean_rejected(self):
        m=copy.deepcopy(self.manifest);m['ability_ranges'][0]['start']=True;self.reject(m)
    def test_ability_step_zero_rejected(self):
        p=dict(self.payload);s=bytearray(p['ability_steps.u8']);s[0]=0;p['ability_steps.u8']=bytes(s)
        m=copy.deepcopy(self.manifest)
        import hashlib
        m['ability_ranges'][0]['steps_sha256']=hashlib.sha256(p['ability_steps.u8'][:1000]).hexdigest()
        self.reject(m,p)
    def test_duplicate_zip_member_rejected(self):
        self.reject(duplicate='agent_weights.fp16')
    def test_undeclared_extra_zip_member_rejected(self):
        self.reject(extras={'other-weights.fp16':b'1234'})
    def test_wrong_dimensions_rejected(self):
        m=copy.deepcopy(self.manifest);m['agent_parameters']=411001;self.reject(m)
    def test_auto_promote_rejected(self):
        m=copy.deepcopy(self.manifest);m['auto_promote']=True;self.reject(m)
    def test_checkpoint_does_not_attest_training(self):
        result = bank.verify_sample(self.archive())
        self.assertTrue(result['sample_receipt_coverage_verified'])
        self.assertFalse(result['training_provenance_independently_attested'])
        self.assertFalse(result['complete_original_10k_agent_bank_verified'])
        self.assertFalse(result['complete_original_10m_ability_bank_verified'])
    def test_missing_agent_step_receipt_rejected(self):
        m=copy.deepcopy(self.manifest);del m['agent_rows'][5]['steps'];self.reject(m)
    def test_invalid_sha256_format_rejected(self):
        m=copy.deepcopy(self.manifest);m['agent_rows'][2]['sha256']='xyz';self.reject(m)
    def test_duplicate_json_field_rejected(self):
        target=Path(self.temp.name)/f'{self._testMethodName}.zip'
        source=json.dumps(self.manifest)
        source=source.replace('"schema":', '"schema":"duplicate", "schema":', 1)
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:
            z.writestr('manifest.json',source)
            for name, data in self.payload.items():z.writestr(name,data)
        with self.assertRaises(ValueError):bank.verify_sample(target)
    def test_ability_ranges_missing_rejected(self):
        m=copy.deepcopy(self.manifest);del m['ability_ranges'];self.reject(m)

if __name__=='__main__':unittest.main()
