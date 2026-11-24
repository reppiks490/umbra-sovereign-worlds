import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import evolution_local_model_v22 as m

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_POST(self):
        self.server.calls += 1
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.last = (self.path, self.headers.get("Authorization"), data)
        if self.server.mode == "redirect":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:1/")
            self.end_headers()
            return
        prompt = data["messages"][0]["content"]
        a, op, b = prompt.rstrip(".").split()[-3:]
        a, b = int(a), int(b)
        answer = str({"+": a+b, "-": a-b, "*": a*b}[op])
        response = {"model": data["model"], "choices": [{"message": {"content": answer}}],
                    "usage": {"completion_tokens": 2}}
        if self.server.mode == "overbudget":
            response["usage"]["completion_tokens"] = 999
        if self.server.mode == "wrong_model":
            response["model"] = "other"
        if self.server.mode == "missing_usage":
            del response["usage"]
        raw = json.dumps(response).encode()
        if self.server.mode == "oversize":
            raw = b"x"*(m.MAX_RESPONSE_BYTES+1)
        self.send_response(200)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.calls = 0
        self.server.mode = "ok"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.thread.join, 2)
        self.addCleanup(self.server.shutdown)
        self.env = patch.dict(os.environ, {"MYRIAD_LOCAL_MODEL_TOKEN": "test-token"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.out = Path(self.tmp.name)/"receipt.json"
    def run_model(self, **kw):
        args = dict(port=self.server.server_port, model="test-model", seed=17, count=3,
                    max_tokens=8, budget=24, timeout=3, out=self.out, authorize=True)
        args.update(kw)
        return m.run(**args)
    def test_bounded_authenticated_transport(self):
        r = self.run_model()
        self.assertEqual(r["correct"], 3)
        self.assertEqual(r["reported_completion_tokens"], 6)
        self.assertEqual(self.server.calls, 3)
        path, auth, body = self.server.last
        self.assertEqual((path, auth), ("/v1/chat/completions", "Bearer test-token"))
        self.assertEqual(body["max_tokens"], 8)
        self.assertFalse(body["stream"])
        self.assertNotIn("test-token", self.out.read_text())
        self.assertTrue(m.verify(json.loads(self.out.read_text()))["integrity_valid"])
        self.assertFalse(m.verify(r)["endpoint_identity_verified"])
    def test_explicit_authorization(self):
        with self.assertRaises(PermissionError):
            self.run_model(authorize=False)
        self.assertEqual(self.server.calls, 0)
        self.assertFalse(self.out.exists())
    def test_budget_preflight(self):
        with self.assertRaises(ValueError):
            self.run_model(budget=23)
        self.assertEqual(self.server.calls, 0)
    def test_no_overwrite(self):
        self.out.write_text("original")
        with self.assertRaises(FileExistsError):
            self.run_model()
        self.assertEqual(self.out.read_text(), "original")
        self.assertEqual(self.server.calls, 0)
    def test_invalid_token(self):
        with patch.dict(os.environ, {"MYRIAD_LOCAL_MODEL_TOKEN": "bad\nheader"}):
            with self.assertRaises(PermissionError):
                self.run_model()
        self.assertEqual(self.server.calls, 0)
    def test_invalid_responses_fail_closed(self):
        for mode in ("redirect", "overbudget", "wrong_model", "missing_usage", "oversize"):
            with self.subTest(mode=mode):
                self.server.mode = mode
                self.out = Path(self.tmp.name)/(mode+".json")
                before = self.server.calls
                with self.assertRaises(ValueError):
                    self.run_model()
                self.assertEqual(self.server.calls, before+1)
                receipt = json.loads(self.out.read_text())
                self.assertEqual(receipt["status"], "incomplete")
                self.assertEqual(receipt["completed_requests"], 0)
                self.assertTrue(m.verify(receipt)["integrity_valid"])
    def test_tampering_and_resealed_aggregate(self):
        r = self.run_model()
        r["correct"] = 99
        with self.assertRaises(ValueError):
            m.verify(r)
        r.pop("receipt_sha256")
        r["receipt_sha256"] = m.digest(m.canonical(r))
        with self.assertRaises(ValueError):
            m.verify(r)

if __name__ == "__main__":
    unittest.main()
