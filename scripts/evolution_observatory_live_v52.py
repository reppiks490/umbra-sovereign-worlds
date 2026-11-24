"""Read-only hosted live aggregate view. Fixed public snapshot URL, fail-closed freshness."""
import argparse,json,time,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlparse
import evolution_telemetry_v48 as contract
URL='https://raw.githubusercontent.com/reppiks490/umbra-sovereign-worlds/refs/heads/telemetry/myriad-live/telemetry/live.json'
PAGE=b'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MYRIAD Omega live telemetry</title><link rel="stylesheet" href="/live.css"><script defer src="/live.js"></script></head><body><main><header><a href="/">Evolution Observatory</a><span>MYRIAD OMEGA / LIVE EVIDENCE</span></header><h1>Live aggregate telemetry</h1><p id="health" role="status">Reading authenticated repository snapshot...</p><p>Observed research metrics only. Enrollment is not completed inference. Synthetic rows are not mastered skills. No production authority.</p><section id="metrics" aria-label="Operational counters"></section><p id="stamp"></p><footer>Refreshes every 30 seconds; publisher targets 15-minute snapshots. Stale or unavailable evidence is explicitly marked.</footer></main></body></html>'''
STYLE=b'''*{box-sizing:border-box}body{margin:0;color:#f0edf3;background:#0b0911;font:16px system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px 20px}header{display:flex;justify-content:space-between;gap:12px;color:#aeb4c6;font-size:.75rem;letter-spacing:.07em}a{color:#fa8da0}h1{font-size:clamp(2rem,6vw,3.5rem);letter-spacing:-.04em}p,footer{color:#b5bacb;line-height:1.6}#health{color:#f7c8d2;border-left:3px solid #e24d64;padding-left:12px}#metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:28px 0}.metric{padding:18px;background:#16121f;border:1px solid #382737;border-radius:12px;min-height:110px}.label{color:#b8afbf;font-size:.8rem;letter-spacing:.03em}.number{font:600 1.8rem ui-monospace,monospace;margin-top:12px;overflow-wrap:anywhere}footer{font-size:.8rem}'''
JS=b'''(()=>{const names={legacy_enrolled:"Legacy LLM workers enrolled",legacy_completed:"Legacy LLM occurrences",fleet_enrolled:"Full fleet enrolled",fleet_distinct_completed:"Full fleet distinct completed",fleet_completed_items:"Full fleet completed items",fleet_model_calls:"Full fleet inference requests",fleet_peer_linked:"Full fleet peer-linked items",specialist_completed:"Specialist evaluations",source_completed:"Source reviews",ability_rows:"Trained synthetic adapter rows",ability_bytes:"Trained adapter bytes",ability_updates:"Adapter gradient row updates",agent_checkpoints:"Saved neural checkpoints",agent_bytes:"Saved neural checkpoint bytes",teacher_labels:"Accepted teacher labels",student_updates:"Student gradient updates",algorithm_implementations_added:"New executable algorithms"};const metrics=document.getElementById("metrics"),health=document.getElementById("health"),stamp=document.getElementById("stamp");async function refresh(){try{const r=await fetch("/api/live",{cache:"no-store"});if(!r.ok)throw Error("unavailable");const v=await r.json();health.textContent=v.freshness==="fresh"?"FRESH OBSERVATION":v.freshness==="stale"?"STALE OBSERVATION":"TELEMETRY UNAVAILABLE";metrics.replaceChildren();stamp.textContent="";if(!v.counts)return;for(const [k,label] of Object.entries(names)){const box=document.createElement("article"),l=document.createElement("div"),n=document.createElement("div");box.className="metric";l.className="label";n.className="number";l.textContent=label;n.textContent=Number(v.counts[k]).toLocaleString();box.append(l,n);metrics.append(box)}stamp.textContent="Last observed: "+new Date(v.observed_epoch*1000).toLocaleString()+" | Age: "+v.age_seconds+" seconds";}catch(e){health.textContent="TELEMETRY UNAVAILABLE";metrics.replaceChildren();stamp.textContent=""}}refresh();setInterval(refresh,30000)})();'''
def fetch_snapshot():
    req=urllib.request.Request(URL,headers={'User-Agent':'MYRIAD-live-observatory','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=8) as r:
        if r.geturl()!=URL or r.status!=200:raise ValueError('unexpected source')
        raw=r.read(32769)
    if len(raw)>32768:raise ValueError('snapshot too large')
    return json.loads(raw)
def live_data():
    try:return contract.validate(fetch_snapshot(),int(time.time()))
    except (OSError,ValueError,TypeError,KeyError,urllib.error.URLError):return {'schema':contract.SCHEMA,'freshness':'unavailable','research_only':True}
def main():
    import evolution_api as original
    from http.server import ThreadingHTTPServer
    class Handler(original.Handler):
        def do_GET(self):
            path=urlparse(self.path).path
            if path=='/api/live':return self._send(live_data())
            if path=='/live':return self._send(PAGE,mime='text/html; charset=utf-8')
            if path=='/live.js':return self._send(JS,mime='application/javascript; charset=utf-8')
            if path=='/live.css':return self._send(STYLE,mime='text/css; charset=utf-8')
            if path in ('/','/index.html'):
                b=original.INDEX.read_bytes()
                link=b'<section><a href="/live">OPEN LIVE AGGREGATE TELEMETRY</a></section>'
                return self._send(b.replace(b'</body>',link+b'</body>'),mime='text/html; charset=utf-8')
            return super().do_GET()
    p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8797);p.add_argument('--ledger',required=True);a=p.parse_args()
    Handler.db_path=Path(a.ledger)
    server=ThreadingHTTPServer((a.host,a.port),Handler)
    try:server.serve_forever(poll_interval=.1)
    finally:server.server_close()
if __name__=='__main__':main()
