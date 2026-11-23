#!/usr/bin/env python3
"""MYRIAD × UMBRA Evolution Observatory (local research-only HTTP service).

Read-only by design, no credentials in requests, no remote user exposure, no
broker tools, model prompts or system command execution. The mesh can run in a
separate authorized process with persistent on-host SQLite evidence.
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))
import umbra_evolution_mesh as mesh
import evolution_source_registry as sources
import myriad_bank_fabric as banks

INDEX=(ROOT/'evolution'/'index.html')
JS=(ROOT/'evolution'/'app.js')
CSS=(ROOT/'evolution'/'style.css')


def overview(db_path):
    result={'schema':'umbra.evolution.observatory.v1','algorithm_configuration_space':mesh.ALGORITHM_COUNT,
            'implemented_operator_optimizer_combinations':25,
            'sourced_method_metadata_records':len(list(sources.entries())),
            'logical_worker_identities':mesh.WORKFLOW_COUNT,
            'live_dedicated_worker_processes':0,
            'full_fleet_hourly_training_certified':False,
            'historical_full_neural_banks_available_here':False,
            'research_only':True,'production_writes_authorized':False,
            'bank_expansion_targets':{'agent_bytes':banks.TARGET_AGENT_BYTES,'ability_bytes':banks.TARGET_ABILITY_BYTES},
            'timestamp_utc':datetime.now(timezone.utc).isoformat()}
    if db_path.exists():
        with sqlite3.connect(f'file:{db_path}?mode=ro',uri=True) as db:
            result['recorded_research_runs']=db.execute('SELECT COUNT(*) FROM runs').fetchone()[0]
            result['recorded_hours']=db.execute('SELECT COUNT(DISTINCT hour) FROM runs').fetchone()[0]
            result['recorded_workflows']=db.execute('SELECT COUNT(DISTINCT workflow) FROM runs').fetchone()[0]
            result['latest_hour']=db.execute('SELECT MAX(hour) FROM runs').fetchone()[0]
            result['reviewable_candidates']=db.execute("SELECT COUNT(*) FROM runs WHERE record LIKE '%candidate_for_manual_review%'").fetchone()[0]
    else:result.update(recorded_research_runs=0,recorded_hours=0,recorded_workflows=0,latest_hour=None,reviewable_candidates=0)
    return result


def worker_status(db_path,worker_id):
    obj=mesh.workflow(worker_id)
    obj['mode']='logical_identity_only'
    obj['recorded_runs']=0
    if db_path.exists():
        with sqlite3.connect(f'file:{db_path}?mode=ro',uri=True) as db:
            row=db.execute('SELECT hour,record FROM runs WHERE workflow=? ORDER BY hour DESC LIMIT 1',(obj['id'],)).fetchone()
            if row:
                p=json.loads(row[1]);digest=p.pop('receipt_sha256')
                if mesh.digest(p)!=digest:raise ValueError('Corrupted worker record')
                obj['last_observed_hour']=row[0];obj['last_proposal']=p
                obj['recorded_runs']=db.execute('SELECT COUNT(*) FROM runs WHERE workflow=?',(obj['id'],)).fetchone()[0]
    return obj


class Handler(BaseHTTPRequestHandler):
    db_path=Path('/tmp/myriad-umbra-evolution.sqlite3')
    def _send(self,body,status=200,mime='application/json; charset=utf-8'):
        blob=(json.dumps(body,separators=(',',':'),allow_nan=False)+'\n').encode() if not isinstance(body,bytes) else body
        self.send_response(status);self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(blob)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers();self.wfile.write(blob)
    def do_GET(self):
        parsed=urlparse(self.path);path=parsed.path
        try:
            if path in ('/','/index.html'):
                return self._send(INDEX.read_bytes(),mime='text/html; charset=utf-8')
            if path=='/app.js':return self._send(JS.read_bytes(),mime='application/javascript; charset=utf-8')
            if path=='/style.css':return self._send(CSS.read_bytes(),mime='text/css; charset=utf-8')
            if path=='/api/health':return self._send({'ok':True,'read_only':True,'schema':'evolution.health.v1'})
            if path=='/api/metrics':return self._send(overview(self.db_path))
            if path=='/api/banks':return self._send(banks.plan())
            if path=='/api/sources':return self._send({'schema':sources.SCHEMA,'metrics':sources.validate(),'items':list(sources.entries())})
            if path=='/api/algorithms':
                param=parse_qs(parsed.query);idx=int(param.get('id',['1'])[0]);return self._send(mesh.recipe(idx))
            if path=='/api/workers':
                param=parse_qs(parsed.query);idx=int(param.get('id',['1'])[0]);return self._send(worker_status(self.db_path,idx))
            if path=='/api/events':
                if not self.db_path.is_file():return self._send({'events':[],'kind':'recorded_only'})
                with sqlite3.connect(f'file:{self.db_path}?mode=ro',uri=True) as db:
                    rows=db.execute('SELECT hour,workflow,domain,receipt FROM runs ORDER BY rowid DESC LIMIT 24').fetchall()
                return self._send({'events':[{'hour':h,'workflow':w,'domain':d,'receipt_sha256':r} for h,w,d,r in rows], 'kind':'recorded_only'})
            return self._send({'error':'not_found'},404)
        except (ValueError,TypeError,OverflowError):return self._send({'error':'invalid_request'},400)
        except (sqlite3.Error, OSError) as e:return self._send({'error':'source_unavailable','detail':type(e).__name__},503)
    def do_POST(self):return self._send({'error':'read_only_research_observatory'},403)
    def do_PUT(self):return self.do_POST()
    def do_DELETE(self):return self.do_POST()
    def log_message(self,fmt,*args):
        # Do not echo URLs, paths, or tokens to stdout by default.
        pass


def main():
    p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8797)
    p.add_argument('--ledger',default='/tmp/myriad-umbra-evolution.sqlite3');a=p.parse_args()
    # Users may explicitly bind externally only behind their own auth proxy.
    Handler.db_path=Path(a.ledger)
    httpd=ThreadingHTTPServer((a.host,a.port),Handler)
    print(json.dumps({'serving':f'http://{a.host}:{a.port}', 'read_only':True,'ledger':str(a.ledger)}),flush=True)
    try:httpd.serve_forever(poll_interval=.1)
    except KeyboardInterrupt:pass
    finally:httpd.server_close()
if __name__=='__main__':main()