# MYRIAD v3.3 ? native Ollama worker adapter

Research-only. Existing durable v2.6 queue and v2.4 private evidence scoring are preserved.
The native endpoint is numeric loopback only, restricts routes, verifies the locally reported
model digest before and after every request, disables extended reasoning, requests one integer,
bounds tokens, threads, response bytes and elapsed time. Raw model answers are scored exactly;
wrong answers remain wrong. The separate HMAC-sealed batch summary records the observed digest.
The tag registry is self-reported; this is not external attestation. No LLM weights are trained.
The existing Windows ACL-protected directory remains mandatory. This phase does not authorize
live trading, autonomous source mutation or promotion. The suite does not invoke real models in CI.
