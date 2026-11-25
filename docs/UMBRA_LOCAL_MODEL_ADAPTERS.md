# Local model adapters — owner-authorized research
Stacked on PR #28, independently of inventory PR #27 and MYRIAD PR #21. No changes to deterministic engine rules, training, schedules, public deployment or trading. Only synthetic simulator aggregates cross the local Ollama boundary; never send private datasets, raw weights, arbitrary prompts or credentials. Model outputs are untrusted advisory data, never executable instructions or changes to the simulation.
 
From an exact reviewed local checkout:
```powershell
'{"operation":"model_list"}' | node mcp/owner_once.mjs
'{"operation":"model","arguments":{"role":"triage","model":"qwen3:0.6b","seed":42,"steps":2}}' | node mcp/owner_once.mjs
node --test tests/*.test.mjs
```
 
The 21-tag allowlist maps installed models to reasoning, research, critique, coding, triage and retrieval. Uninstalled tags do not appear in discovery. Fixed loopback HTTP only, no arbitrary URL, redirects or external endpoints. Admission requires model manifest bytes plus 1 GiB of available RAM and an empty Ollama running-model list. This is conservative best-effort admission, not a global cross-process lease. The existing model download process retains its separate disk guard. One explicit local request per owner process; generation limited to 128 tokens and 1024 context, bounded responses and 180-second deadline. Embedding adapters return dimension and digest, not raw vectors. The deterministic world and manifest digests identify the evidence. Advisory response is not verified scientific inference; model weights are not changed. Fixture tests validate the transport boundary and actual engine inputs, not live model performance. Live smoke tests require sufficient idle resources. No LoRA or trained weight adapter claimed; these are runtime role adapters.