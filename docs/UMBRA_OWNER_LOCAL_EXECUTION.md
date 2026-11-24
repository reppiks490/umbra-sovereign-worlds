# UMBRA owner-device execution

Stacked on native compute PR #26 at `666eca1187d416c0ecc832fcc78cdb63444df36d`. `mcp/owner_once.mjs` admits exactly one JSON request on stdin (64 KiB maximum), initializes the existing MCP bridge, discovers available tools and either lists schemas or performs one validated operation. It emits one JSON value or a generic error with nonzero exit; no remote listener, shell tool, arbitrary path input or new permissions. The optional checkpoint evaluator remains operator-configured, read-only and synthetic.

PowerShell from a separately reviewed checkout (Node 22+):

```powershell
'{"operation":"list"}' | node mcp/owner_once.mjs
'{"operation":"call","name":"umbra_simulate","arguments":{"seed":42,"steps":2}}' | node mcp/owner_once.mjs
node --test tests/owner_once.test.mjs
node --test tests/*.test.mjs
```

Use only an authorized connected owner device with an exact reviewed commit. Validate the discovered input schema, check the command exit status, and report actual output. Do not treat the plugin as a direct MCP connection; Desktop Commander is a separate connector. Do not expose secrets, local weight files, paths, or credentials. Model downloads are separate from inference, and inference is separate from training. No automatic training, merge, deployment or changes to existing schedules. Real engine qualification and owner-bank evaluation must be separately evidenced. The regression file was authored before implementation; full branch CI is required.
