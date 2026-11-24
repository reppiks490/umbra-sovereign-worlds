"""MYRIAD v3.1 read-only Dockerfile/Railway startup verification."""
import json
import shutil
import tempfile
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import evolution_railway_preflight_v31 as preflight

class RailwayPreflight(unittest.TestCase):
    def test_detects_actual_railpack_with_no_start_command(self):
        deployment={'builder':'RAILPACK','dockerfilePath':'evolution/Dockerfile','startCommand':None,'healthcheckPath':'/api/health'}
        result=preflight.assess_builder(deployment)
        self.assertEqual(result['status'],'BLOCKED_BUILDER_MISMATCH')
        self.assertFalse(result['production_deployment_authorized'])
        self.assertEqual(result['corrective_action'],'select DOCKERFILE builder and evolution/Dockerfile; verify in preview')
    def test_verified_dockerfile_builder_is_only_preview_candidate(self):
        candidate={'builder':'DOCKERFILE','dockerfilePath':'evolution/Dockerfile','healthcheckPath':'/api/health'}
        result=preflight.assess_builder(candidate)
        self.assertEqual(result['status'],'PREVIEW_CANDIDATE_ONLY')
        self.assertFalse(result['production_deployment_authorized'])
    def test_dockerfile_uses_runtime_assigned_port_for_start_and_health(self):
        d=(ROOT/'evolution'/'Dockerfile').read_text()
        self.assertIn('${PORT:-8797}',d)
        self.assertIn("os.environ.get('PORT','8797')",d)
        self.assertIn('0.0.0.0',d)
        self.assertIn('HEALTHCHECK',d)
    def test_image_contains_runtime_imports_and_tribunal_aggregate(self):
        d=(ROOT/'evolution'/'Dockerfile').read_text()
        self.assertIn('scripts/evolution_algorithms_v19.py',d)
        self.assertIn('research/EVOLUTION_V19_TRIBUNAL_AGGREGATE.json',d)
        for path in ('scripts/evolution_algorithms_v19.py','research/EVOLUTION_V19_TRIBUNAL_AGGREGATE.json'):
            self.assertTrue((ROOT/path).is_file())
    def test_exact_image_copy_manifest_boots_without_hidden_source_files(self):
        # Reconstruct ONLY the files Dockerfile COPY places in /srv.
        # This detects missing runtime imports even when the full repo boots.
        with tempfile.TemporaryDirectory() as temp:
            image_root=Path(temp)/'srv'
            docker=(ROOT/'evolution'/'Dockerfile').read_text().splitlines()
            for line in docker:
                if not line.startswith('COPY '):continue
                parts=line.split()
                self.assertGreaterEqual(len(parts),3)
                destination=Path(parts[-1].lstrip('/'))
                self.assertTrue(str(destination).startswith('srv/'))
                for name in parts[1:-1]:
                    src=ROOT/name
                    self.assertTrue(src.is_file(),f'Missing Docker build source {name}')
                    target=Path(temp)/destination/src.name
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(src,target)
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
            proc=subprocess.Popen([sys.executable,'scripts/evolution_api.py','--host','127.0.0.1','--port',str(port)],cwd=image_root,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            try:
                for _ in range(80):
                    try:
                        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/methods',timeout=.5) as handle:
                            methods=json.load(handle)
                        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/tribunal',timeout=.5) as handle:
                            tribunal=json.load(handle)
                        break
                    except (OSError,urllib.error.URLError):time.sleep(.05)
                else:self.fail('Minimal Docker image file subset failed to boot')
                self.assertGreaterEqual(methods['count'],12)
                self.assertNotEqual(tribunal.get('status'),'not_installed')
            finally:
                proc.terminate()
                try:proc.communicate(timeout=3)
                except subprocess.TimeoutExpired:proc.kill();proc.communicate(timeout=3)
    def test_rejects_unsupported_builder_and_unbounded_release(self):
        for value in (None,'AUTO','',{'builder':'DOCKERFILE','dockerfilePath':'../../attack'}):
            with self.subTest(value=value),self.assertRaises(ValueError):preflight.assess_builder(value)
    def test_actual_local_health_and_write_prohibition(self):
        with socket.socket() as s:
            s.bind(('127.0.0.1',0))
            port=s.getsockname()[1]
        process=subprocess.Popen([sys.executable,'scripts/evolution_api.py','--host','127.0.0.1','--port',str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: process.wait(timeout=3) if process.poll() is not None else (process.terminate(),process.wait(timeout=3)))
        base=f'http://127.0.0.1:{port}'
        for _ in range(80):
            try:
                with urllib.request.urlopen(base+'/api/health',timeout=.5) as f:
                    status=f.status;body=json.load(f)
                break
            except (OSError,urllib.error.URLError):time.sleep(.05)
        else:self.fail('No local startup health endpoint')
        self.assertEqual(status,200)
        self.assertTrue(body['ok'])
        self.assertTrue(body['read_only'])
        with urllib.request.urlopen(base+'/api/metrics',timeout=2) as f:
            metrics=json.load(f)
        self.assertEqual(metrics['live_dedicated_worker_processes'],0)
        self.assertFalse(metrics['production_writes_authorized'])
        req=urllib.request.Request(base+'/api/health',data=b'x',method='POST')
        with self.assertRaises(urllib.error.HTTPError) as exc:urllib.request.urlopen(req,timeout=2)
        self.assertEqual(exc.exception.code,403)
if __name__=='__main__':unittest.main()
