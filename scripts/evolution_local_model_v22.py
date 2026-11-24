"""Bounded, explicitly authorized local-model evaluation; no training or promotion."""
from __future__ import annotations
import argparse
import hashlib
import http.client
import json
import os
import random
import re
import tempfile
from pathlib import Path

SCHEMA = "myriad.local_model_evaluation.v22"
MAX_RESPONSE_BYTES = 65536
MAX_REQUESTS = 8
MAX_COMPLETION_TOKENS = 64

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def tasks(seed, count):
    rng = random.Random(seed)
    result = []
    for i in range(count):
        a, b = rng.randint(11, 99), rng.randint(11, 99)
        op = ("+", "-", "*")[i % 3]
        answer = {"+": a+b, "-": a-b, "*": a*b}[op]
        result.append((f"Return only the integer result of {a} {op} {b}.", str(answer)))
    return result

def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"Invalid {name}")
    return value

def config(port, model, seed, count, max_tokens, budget, timeout):
    integer(port, 1, 65535, "port")
    integer(seed, 0, 2**32-1, "seed")
    integer(count, 1, MAX_REQUESTS, "request count")
    integer(max_tokens, 1, MAX_COMPLETION_TOKENS, "max tokens")
    integer(budget, 1, MAX_REQUESTS*MAX_COMPLETION_TOKENS, "completion budget")
    integer(timeout, 1, 30, "socket timeout")
    if count * max_tokens > budget:
        raise ValueError("Requested completion budget exceeded before inference")
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", model):
        raise ValueError("Invalid model identifier")

def request(port, model, prompt, token, max_tokens, timeout):
    body = canonical({"model": model, "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0, "max_tokens": max_tokens, "stream": False})
    # Fixed numeric loopback: no arbitrary hosts, proxy environment, DNS or redirects.
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        conn.request("POST", "/v1/chat/completions", body=body,
                     headers={"Authorization": "Bearer "+token, "Content-Type": "application/json"})
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(f"Local endpoint returned HTTP {response.status}")
        raw = response.read(MAX_RESPONSE_BYTES+1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Response byte limit exceeded")
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("model") != model:
            raise ValueError("Model identifier mismatch")
        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise ValueError("Invalid choices")
        message = choices[0].get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("Invalid completion")
        usage = data.get("usage")
        if not isinstance(usage, dict):
            raise ValueError("Missing provider-reported token usage")
        used = integer(usage.get("completion_tokens"), 0, max_tokens, "reported completion tokens")
        return message["content"], used, digest(raw)
    finally:
        conn.close()

def run(port, model, seed, count, max_tokens, budget, timeout, out, *, authorize=False):
    config(port, model, seed, count, max_tokens, budget, timeout)
    if authorize is not True:
        raise PermissionError("Explicit local inference authorization required")
    token = os.environ.get("MYRIAD_LOCAL_MODEL_TOKEN", "")
    if not re.fullmatch(r"[A-Za-z0-9._~+/-]{1,512}={0,2}", token):
        raise PermissionError("Set a valid local bearer token in MYRIAD_LOCAL_MODEL_TOKEN")
    out = Path(out)
    # Reserve a new private receipt before any request. Never overwrite or retry automatically.
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    rows = []
    status = "incomplete"
    try:
        for i, (prompt, answer) in enumerate(tasks(seed, count), 1):
            content, used, response_hash = request(port, model, prompt, token, max_tokens, timeout)
            rows.append({"task": i, "prompt_sha256": digest(prompt.encode()),
                         "expected_sha256": digest(answer.encode()),
                         "completion_sha256": digest(content.encode()),
                         "response_sha256": response_hash, "reported_completion_tokens": used,
                         "exact_match": content.strip() == answer})
        status = "completed"
    finally:
        receipt = {"schema": SCHEMA, "status": status, "model": model, "seed": seed,
                   "planned_requests": count, "max_tokens_per_request": max_tokens,
                   "requested_completion_budget": budget, "completed_requests": len(rows),
                   "reported_completion_tokens": sum(r["reported_completion_tokens"] for r in rows),
                   "correct": sum(r["exact_match"] for r in rows), "rows": rows,
                   "scope": "toy arithmetic; endpoint identity and usage are self-reported",
                   "trained_weights": 0, "live_trading_authorized": False,
                   "automatic_promotion": False}
        receipt["receipt_sha256"] = digest(canonical(receipt))
        with os.fdopen(fd, "wb") as f:
            f.write(canonical(receipt)+b"\n")
            f.flush()
            os.fsync(f.fileno())
    return receipt

def verify(receipt):
    if not isinstance(receipt, dict):
        raise ValueError("Invalid receipt")
    payload = dict(receipt)
    checksum = payload.pop("receipt_sha256", None)
    if checksum != digest(canonical(payload)) or payload.get("schema") != SCHEMA:
        raise ValueError("Receipt integrity mismatch")
    if payload.get("automatic_promotion") is not False or payload.get("live_trading_authorized") is not False or payload.get("trained_weights") != 0:
        raise ValueError("Invalid authority or training claim")
    count = integer(payload["planned_requests"], 1, MAX_REQUESTS, "count")
    seed = integer(payload["seed"], 0, 2**32-1, "seed")
    cap = integer(payload["max_tokens_per_request"], 1, MAX_COMPLETION_TOKENS, "cap")
    budget = integer(payload["requested_completion_budget"], 1, MAX_REQUESTS*MAX_COMPLETION_TOKENS, "budget")
    if count*cap > budget:
        raise ValueError("Budget mismatch")
    rows = payload["rows"]
    if not isinstance(rows, list) or len(rows) > count or payload["completed_requests"] != len(rows):
        raise ValueError("Invalid row coverage")
    if payload["status"] not in ("completed", "incomplete") or (payload["status"] == "completed") != (len(rows) == count):
        raise ValueError("Invalid completion status")
    for i, (row, (prompt, answer)) in enumerate(zip(rows, tasks(seed, count)), 1):
        if row["task"] != i or row["prompt_sha256"] != digest(prompt.encode()) or row["expected_sha256"] != digest(answer.encode()):
            raise ValueError("Task lineage mismatch")
        integer(row["reported_completion_tokens"], 0, cap, "reported usage")
        if type(row["exact_match"]) is not bool or any(not isinstance(row[k], str) or not re.fullmatch(r"[0-9a-f]{64}", row[k]) for k in ("completion_sha256", "response_sha256")):
            raise ValueError("Invalid row evidence")
    if payload["correct"] != sum(r["exact_match"] for r in rows) or payload["reported_completion_tokens"] != sum(r["reported_completion_tokens"] for r in rows):
        raise ValueError("Aggregate mismatch")
    # Hash-only receipts cannot independently reconstruct model output or prove endpoint identity.
    return {"integrity_valid": True, "completed_requests": len(rows), "independent_output_replay": False,
            "endpoint_identity_verified": False, "production_authority": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run")
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--count", type=int, default=4)
    p.add_argument("--max-tokens", type=int, default=16)
    p.add_argument("--budget", type=int, default=64)
    p.add_argument("--timeout", type=int, default=10)
    p.add_argument("--out", required=True)
    p.add_argument("--authorize", action="store_true")
    v = sub.add_parser("verify")
    v.add_argument("receipt")
    args = vars(parser.parse_args())
    command = args.pop("command")
    result = run(**args) if command == "run" else verify(json.loads(Path(args["receipt"]).read_text()))
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
