# Local model evidence layer

Stacked on native compute PR #26, pinned parent 666eca1187d416c0ecc832fcc78cdb63444df36d. This read-only CLI accepts an operator-supplied Ollama /api/tags JSON response through stdin, bounds input to 1 MiB and 256 models, validates names, sizes and digests, rejects duplicate names, and produces a deterministically ordered SHA-256 receipt. Unknown fields are dropped. Logical manifest byte totals are not physical disk usage; identical manifest digests are not distinct weights. The receipt is not a signature or proof of live inference.

Example in a reviewed Windows checkout: (Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 -Uri http://127.0.0.1:11434/api/tags).Content | node mcp/local_model_inventory.mjs

Use node --test tests/local_model_inventory.test.mjs. Four focused tests passed in isolated Node 22 after observing the missing-module failure. Whole repository CI and live owner inventory receipt remain separate qualification gates. No network access inside the CLI, no model execution, no training, no deployment, no changes to schedules or native MCP server. Do not publish owner inventory without authorization. Model admission requires a measured resource check and model-specific held-out tests. Relevant roadmap lanes O01/O03/O06; this is inventory provenance only, not closure of those gates.
