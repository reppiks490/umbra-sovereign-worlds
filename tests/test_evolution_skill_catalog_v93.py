import hashlib,tempfile,unittest
from pathlib import Path
import evolution_skill_catalog_v93 as m

def entry(name,body):
    raw=body.encode()
    return {'path':'skills/'+name+'/SKILL.md','blob':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),'text':body}

class Tests(unittest.TestCase):
    def test_catalog_retrieves_locally_and_replays_provenance(self):
        rows=[entry('scientific-reasoning','Hypothesis generation and statistical reasoning.'),entry('graph-methods','Graph reasoning and connectivity.'),entry('visualization','Plotting and figure design.')]
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=m.build(root,rows,'fixture-license',source='fixture',commit='a'*40)
            self.assertEqual(m.audit(p)['documents'],3)
            result=m.search(p,'graph connectivity')
            self.assertEqual(result[0]['slug'],'graph-methods')
            self.assertEqual(result[0]['blob'],rows[1]['blob'])
            self.assertTrue(result[0]['data_only'])
            self.assertEqual(result[0]['commit'],'a'*40)
            self.assertEqual(m.search(p,'no_matching_term'),[])
    def test_wrong_hash_duplicate_and_traversal_are_rejected(self):
        good=entry('test','some text')
        cases=[[{**good,'blob':'a'*40}],[good,good],[{**good,'path':'skills/../SKILL.md'}],[entry('large','x'*65537)]]
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for rows in cases:
                with self.subTest(rows=len(rows)),self.assertRaises(ValueError):m.build(root,rows,'fixture-license',source='fixture',commit='a'*40)
            self.assertEqual(list(root.iterdir()),[])
    def test_existing_catalog_never_overwritten(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=m.build(root,[entry('a','alpha')],'fixture-license',source='fixture',commit='a'*40)
            old=p.read_bytes()
            with self.assertRaises(FileExistsError):m.build(root,[entry('a','changed')],'fixture-license',source='fixture',commit='a'*40)
            self.assertEqual(old,p.read_bytes())
    def test_fts_query_is_bounded_data_not_sql(self):
        with tempfile.TemporaryDirectory() as t:
            p=m.build(Path(t),[entry('a','hypothesis validation')],'fixture-license',source='fixture',commit='a'*40)
            self.assertEqual(m.search(p,'hypothesis" OR 1=1 --'),[])
            for q in ('', 'x'*161, 'one two three four five six seven eight nine ten eleven twelve thirteen'):
                with self.assertRaises(ValueError):m.search(p,q)
            with self.assertRaises(ValueError):m.search(p,'hypothesis',True)
    def test_tampering_detected(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as t:
            p=m.build(Path(t),[entry('a','alpha beta')],'fixture-license',source='fixture',commit='a'*40)
            c=sqlite3.connect(p)
            try:
                with c:c.execute("UPDATE skills SET body='tampered'")
            finally:c.close()
            with self.assertRaises(ValueError):m.audit(p)
    def test_real_pinned_git_objects_imported_without_checkout(self):
        import subprocess,os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);repo=root/'repo';repo.mkdir();out=root/'out';out.mkdir()
            env=dict(os.environ,GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0')
            def git(*args):
                return subprocess.run(['git','-C',str(repo),*args],env=env,check=True,capture_output=True).stdout
            git('init','--template=')
            (repo/'skills'/'graph').mkdir(parents=True)
            (repo/'skills'/'graph'/'SKILL.md').write_bytes(b'Graph reasoning and verification.\n')
            (repo/'LICENSE.md').write_bytes(b'Fixture license\n')
            git('add','--all')
            git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture')
            commit=git('rev-parse','HEAD').decode().strip();license_blob=git('rev-parse','HEAD:LICENSE.md').decode().strip()
            with patch.object(m,'COMMIT',commit),patch.object(m,'LICENSE_BLOB',license_blob):
                entries,license_text=m.read_pinned(repo)
                self.assertEqual(len(entries),1)
                self.assertEqual(entries[0]['blob'],git('rev-parse','HEAD:skills/graph/SKILL.md').decode().strip())
                p=m.build(out,entries,license_text,source=m.SOURCE,commit=commit)
                self.assertEqual(m.audit(p)['documents'],1)
                self.assertEqual(m.search(p,'graph reasoning')[0]['slug'],'graph')
            with self.assertRaises(ValueError):m.read_pinned(repo)
if __name__=='__main__':unittest.main()
