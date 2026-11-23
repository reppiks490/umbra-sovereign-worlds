"""UMBRA UM-103: real HTTP-served ES modules and real module-worker integration.

Unlike tests/smoke.py, this test does NOT inline JS for the primary path.
Run in CI after Playwright Chromium installation: python tests/served_smoke.py
"""
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from shutil import which
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

class Handler(SimpleHTTPRequestHandler):
    def guess_type(self, path):
        if path.endswith(".mjs"):
            return "text/javascript"
        return super().guess_type(path)

    def log_message(self, fmt, *args):
        pass

@contextmanager
def serve():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(ROOT)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/index.html"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

WORKER_AUDIT = """
(() => {
  const NativeWorker = window.Worker;
  window.__workerAudit = {created:0, responses:[], errors:[]};
  window.Worker = class extends NativeWorker {
    constructor(url, options) {
      super(url, options);
      window.__workerAudit.created++;
      this.addEventListener('message', e => {
        window.__workerAudit.responses.push({ok:e.data?.ok, id:e.data?.id});
      });
      this.addEventListener('error', e => {
        window.__workerAudit.errors.push(String(e.message));
      });
    }
  };
})();
"""

def ready(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_function(
        "window.__UMBRA && document.querySelector('#stat-pop').textContent.trim() !== '0'",
        timeout=20000
    )
    assert page.title() == "UMBRA Ω · Sovereign Worlds Observatory"
    assert page.evaluate("window.__UMBRA.getStatus().civic.valid")

def experiment(page):
    page.locator("#pause").click()
    page.locator("#experiment").click()
    page.wait_for_function(
        "() => !document.querySelector('#experiment').disabled",
        timeout=45000
    )
    status = page.locator("#exp-status").inner_text()
    assert status.startswith("COMPLETE"), status
    assert page.locator("#exp-mean").inner_text() != "—"
    return status

def run():
    with serve() as url, sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=which("chromium") or which("chromium-browser"),
            args=["--no-sandbox"]
        )
        try:
            # Actual ESM import graph and successful module Worker roundtrip.
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors, assets = [], []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("response", lambda r: assets.append((r.url.split("/")[-1], r.status)))
            page.add_init_script(WORKER_AUDIT)
            ready(page, url)
            result = experiment(page)
            page.wait_for_function("window.__workerAudit.responses.length > 0", timeout=10000)
            audit = page.evaluate("window.__workerAudit")
            assert audit["created"] >= 1, audit
            assert any(x["ok"] is True for x in audit["responses"]), audit
            assert not audit["errors"], audit
            for module in ["observatory.mjs", "engine.mjs", "society.mjs", "court.mjs"]:
                assert (module, 200) in assets, (module, assets)
            assert not errors, errors
            assert page.evaluate("document.documentElement.scrollWidth") <= 1441
            print(f"PASS served ESM + real Worker: {result}, workers={audit['created']}")

            # Negative protocol check must be answered by a real worker, not fallback.
            bad = page.evaluate("""() => new Promise(resolve => {
              const worker = new Worker('./lab.worker.mjs', {type:'module'});
              worker.onmessage = event => {worker.terminate(); resolve(event.data);};
              worker.onerror = event => {worker.terminate(); resolve({ok:false,error:String(event.message)});};
              worker.postMessage({version:'invalid-protocol',id:'negative-probe'});
            })""")
            assert bad.get("ok") is False and "protocol mismatch" in bad.get("error", ""), bad
            print("PASS real Worker negative protocol response")
            page.close()

            # Explicit no-Worker fallback on a phone viewport, still served over HTTP.
            phone = browser.new_page(viewport={"width": 390, "height": 844})
            fallback_errors = []
            phone.on("pageerror", lambda e: fallback_errors.append(str(e)))
            phone.add_init_script("window.Worker = undefined;")
            ready(phone, url)
            fallback_status = experiment(phone)
            assert not fallback_errors, fallback_errors
            assert phone.evaluate("document.documentElement.scrollWidth") <= 391
            print(f"PASS served ESM + forced fallback phone: {fallback_status}")
            phone.close()
        finally:
            browser.close()

if __name__ == "__main__":
    run()
