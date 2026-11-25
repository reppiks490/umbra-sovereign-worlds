import sys,pathlib,unittest,tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from source_knowledge import Knowledge,split_chunks,license_id,learning_policy
class KnowledgeTest(unittest.TestCase):
 def test_license_conservative(self):
  self.assertEqual(license_id('MIT License\nPermission is hereby granted, free of charge, to any person obtaining a copy'), 'MIT')
  self.assertEqual(license_id('Apache License\nVersion 2.0, January 2004'), 'Apache-2.0')
  self.assertIsNone(license_id('research only; no commercial use'))
 def test_pinned_source_retrieval(self):
  with tempfile.TemporaryDirectory() as d:
   with Knowledge(pathlib.Path(d)) as k:
    k.ingest('example/repo','a'*40,'README.md','MIT','Forecasting uses chronological holdouts.\nAvoid future observations.')
    out=k.search('chronological holdouts')
    self.assertEqual(out[0]['repo'],'example/repo')
    self.assertEqual(out[0]['revision'],'a'*40)
    self.assertIn('chronological',out[0]['text'])
    self.assertEqual(k.search(''),[])
    self.assertEqual(k.stats()['sources'],1)
    k.ingest('example/repo','a'*40,'README.md','MIT','Forecasting uses chronological holdouts.\nAvoid future observations.')
    self.assertEqual(k.stats()['sources'],1)
    with self.assertRaises(ValueError):k.ingest('example/repo','a'*40,'README.md','MIT','changed source')
 def test_synthetic_training_disabled(self):
  p=learning_policy()
  self.assertFalse(p['synthetic_training'])
  self.assertFalse(p['legacy_llm_optimizer'])
  self.assertTrue(p['source_retrieval'])
 def test_chunk_bounds(self):
  self.assertTrue(all(len(x['text'])<=1600 for x in split_chunks('a '*5000)))

 def test_mit_without_title(self):
  self.assertEqual(license_id('Copyright (c) 2024 Author\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the Software without restriction. The above copyright notice and this permission notice shall be included in all copies. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.'),'MIT')
