"""Adversarial tests for read-only independently pinned ledger recovery."""
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_archive_recovery_v20 as recovery

class ArchiveRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        db=self.root/'fixture.sqlite3'
        c=sqlite3.connect(db)
        c.execute('CREATE TABLE runs(workflow TEXT)')
        c.execute('INSERT INTO runs VALUES (\'E000001\')')
        c.commit();c.close()
        self.db=db.read_bytes()
        self.inner={"schema":recovery.INNER_SCHEMA,"research_only":True,"production_integrations":0,
                    "sqlite":{"path":recovery.LEDGER,"size_bytes":len(self.db),"sha256":hashlib.sha256(self.db).hexdigest()},"completed_occurrences":1}
        self.build()

    def build(self,extra=None):
        self.archive=self.root/'fixture.zip'
        with zipfile.ZipFile(self.archive,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr(recovery.LEDGER,self.db)
            z.writestr(recovery.MANIFEST,json.dumps(self.inner))
            if extra:z.writestr(extra[0],extra[1])
        data=self.archive.read_bytes();chunks=[data[:len(data)//2],data[len(data)//2:]]
        self.spec={"schema":recovery.SCHEMA,"archive_name":"fixture.zip","archive_bytes":len(data),"archive_sha256":hashlib.sha256(data).hexdigest(),
                   "source_database_bytes":len(self.db),"source_database_sha256":hashlib.sha256(self.db).hexdigest(),"verified_receipt_records":1,
                   "segments":[]}
        for i,chunk in enumerate(chunks,1):
            name=f'fixture.zip.part{i:02d}';(self.root/name).write_bytes(chunk)
            self.spec['segments'].append({'path':name,'bytes':len(chunk),'sha256':hashlib.sha256(chunk).hexdigest()})
        self.manifest=self.root/'parts.json';self.manifest.write_text(json.dumps(self.spec))

    def test_streaming_integrity_and_read_only_sqlite(self):
        out=recovery.recover(self.manifest,check_sqlite=True)
        self.assertEqual(out['sqlite']['integrity_check'],'ok')
        self.assertEqual(out['sqlite']['recorded_occurrences'],1)
        self.assertIsNone(out['restored_database'])

    def test_restore_requires_empty_destination_and_sets_readonly(self):
        target=self.root/'recovered'
        out=recovery.recover(self.manifest,output_directory=target)
        self.assertTrue(Path(out['restored_database']).exists())
        self.assertEqual(Path(out['restored_database']).stat().st_mode&0o222,0)
        with self.assertRaises(FileExistsError):recovery.recover(self.manifest,output_directory=target)

    def test_part_tampering_rejected(self):
        p=self.root/'fixture.zip.part01';b=bytearray(p.read_bytes());b[5]^=3;p.write_bytes(b)
        with self.assertRaisesRegex(ValueError,'Part checksum'):recovery.recover(self.manifest)

    def test_path_traversal_rejected_even_if_checksum_recomputed(self):
        self.build(('../escape.txt',b'bad'))
        with self.assertRaisesRegex(ValueError,'Unsafe archived path'):recovery.recover(self.manifest)
        self.assertFalse((self.root.parent/'escape.txt').exists())

    def test_manifest_denylist_and_order(self):
        self.spec['segments'].reverse();self.manifest.write_text(json.dumps(self.spec))
        with self.assertRaisesRegex(ValueError,'unordered'):recovery.read_manifest(self.manifest)

    def test_inner_metadata_tamper_rejected_after_rehash(self):
        self.inner['production_integrations']=1;self.build()
        with self.assertRaisesRegex(ValueError,'Unqualified'):recovery.recover(self.manifest)

    def test_no_overwrite_of_user_directory(self):
        target=self.root/'other';target.mkdir();(target/'keep.txt').write_text('unchanged')
        with self.assertRaises(FileExistsError):recovery.recover(self.manifest,output_directory=target)
        self.assertEqual((target/'keep.txt').read_text(),'unchanged')

if __name__=='__main__':unittest.main()
