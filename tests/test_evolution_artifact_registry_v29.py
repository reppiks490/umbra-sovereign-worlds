"""Strict v2.9 immutable binary model artifact registry test contract."""
import hashlib
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_artifact_registry_v29 as reg

class ArtifactRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'models';self.root.mkdir()
        self.manifest=Path(self.tmp.name)/'manifest.json'
        self.key='s'*48
        self.patcher=patch.dict(os.environ,{'MYRIAD_ARTIFACT_REGISTRY_KEY':self.key})
        self.patcher.start();self.addCleanup(self.patcher.stop)
        (self.root/'AG-00001.fp16').write_bytes(b'\0\x3c'*32)
    def register(self,**kwargs):
        a={'root':self.root,'out':self.manifest,'model_id':'myriad-v25-private','source':'imported_unverified','license_id':'unknown','authorize':True}
        a.update(kwargs)
        return reg.register(**a)
    def test_explicit_optin_and_absent_secret(self):
        with self.assertRaises(PermissionError):self.register(authorize=False)
        self.assertFalse(self.manifest.exists())
        with patch.dict(os.environ,{'MYRIAD_ARTIFACT_REGISTRY_KEY':''}):
            with self.assertRaises(PermissionError):self.register()
        self.assertFalse(self.manifest.exists())
    def test_signed_manifest_roundtrip_and_no_promotion(self):
        row=self.register()
        self.assertEqual(row['artifacts'][0]['size_bytes'],64)
        self.assertFalse(row['model_origin_authenticated'])
        self.assertFalse(row['production_authority'])
        report=reg.verify(self.root,self.manifest)
        self.assertTrue(report['all_bytes_verified'])
        self.assertFalse(report['model_origin_authenticated'])
        self.assertEqual(report['file_count'],1)
    def test_overwrite_refused_even_with_authorization(self):
        self.manifest.write_text('old')
        with self.assertRaises(FileExistsError):self.register()
        self.assertEqual(self.manifest.read_text(),'old')
    def test_modified_artifact_rejected(self):
        self.register()
        (self.root/'AG-00001.fp16').write_bytes(b'\xff\xff'*32)
        with self.assertRaises(ValueError):reg.verify(self.root,self.manifest)
    def test_resigned_manifest_cannot_mark_external_authority(self):
        d=self.register()
        d['production_authority']=True
        d=reg.seal(d,self.key)
        self.manifest.write_text(json.dumps(d))
        with self.assertRaises(ValueError):reg.verify(self.root,self.manifest)
    def test_unmanifested_extra_binary_is_rejected(self):
        self.register()
        (self.root/'AG-00002.fp16').write_bytes(b'\0\0'*10)
        with self.assertRaises(ValueError):reg.verify(self.root,self.manifest)
    def test_symlink_and_parent_escape_rejected(self):
        self.root.joinpath('AG-00001.fp16').unlink()
        outside=Path(self.tmp.name)/'outside.fp16';outside.write_bytes(b'\0'*64)
        (self.root/'AG-00001.fp16').symlink_to(outside)
        with self.assertRaises(ValueError):self.register()
    def test_pinned_revision_required_but_not_attested(self):
        with self.assertRaises(ValueError):self.register(source='huggingface_pinned',revision='main')
        row=self.register(source='huggingface_pinned',revision='e'*40,license_id='apache-2.0')
        self.assertEqual(row['pinned_revision'],'e'*40)
        self.assertFalse(row['model_origin_authenticated'])
    def test_safetensors_header_duplicate_and_gap_rejected(self):
        name=self.root/'model.safetensors'
        body=b'\x00\x3c'*2
        header=json.dumps({'a':{'dtype':'F16','shape':[2],'data_offsets':[0,4]}}).encode()
        name.write_bytes(struct.pack('<Q',len(header))+header+body)
        self.assertTrue(reg.validate_safetensors(name))
        header=b'{"a":{"dtype":"F16","shape":[2],"data_offsets":[0,4]},"a":{"dtype":"F16","shape":[2],"data_offsets":[0,4]}}'
        name.write_bytes(struct.pack('<Q',len(header))+header+body)
        with self.assertRaises(ValueError):reg.validate_safetensors(name)
        header=json.dumps({'a':{'dtype':'F16','shape':[1],'data_offsets':[2,4]}}).encode()
        name.write_bytes(struct.pack('<Q',len(header))+header+body)
        with self.assertRaises(ValueError):reg.validate_safetensors(name)
    def test_disallow_unknown_artifact_formats(self):
        (self.root/'payload.pkl').write_bytes(b'pickle')
        with self.assertRaises(ValueError):self.register()
if __name__=='__main__':unittest.main()
