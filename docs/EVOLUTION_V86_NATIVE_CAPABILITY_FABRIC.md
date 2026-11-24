# v8.6 — native public capabilities and autonomous acquisition research

## Actual Windows local qualification

Seven standard-library public read adapters: GitHub repository search, Hugging Face model/space/dataset search, Crossref discovery, Coinbase spot, Bybit spot. Fixed HTTPS endpoint construction, bounded public inputs, no redirects, no authentication or execution of retrieved content, strict response parsing, normalized minimal data, persistent SQLite cache and daily/provider request budgets. Public searches are sent to remote providers; never insert private project information into queries. The module's execution_authorized false flag denies external code execution, not the authorized public read. A cache digest detects accidental corruption, not malicious local rewriting. No evidence of independent historical availability is inferred from current observations.

RED PID 32076: missing module. Initial GREEN PID 27076: five passes and two Windows file-lock errors due to unclosed SQLite connections. Repaired by transaction context manager with explicit close. PID 32572: 7/7 tests passed. Exact tested local blob hashes 1b0ac84d8cb44eabe0cdc02856d5c36badd4e377 and 337a4b8fafc1528f3a7cfe77e3de89889c4ae3d1. CI for this revision pending.

Live smoke PID 26296: GitHub one result, HF Spaces two results, Crossref two results, Coinbase BTC-USD one quote. Each returned successful cached replay. Bybit HTTP 403; preserve as access restriction, no bypass. HF models/datasets implemented and fixture-tested, not live-qualified in this smoke. These are public API reads from the Windows PC, independent of ChatGPT's plugin UI; not seven locally hosted provider databases. No scheduled ingestion, arbitrary MCP execution, or agent routing installed yet.

## Actual local source acquisitions

Quarantined Git objects (no checkout, execution, dependencies or submodules) in capability-acquisition/ under the existing local MYRIAD pilot. Manifest manifest-1795549419.json, PID 30452 exit 0. Nine downloaded repositories: modelcontextprotocol/python-sdk 77001c96f9507be0f4d009b83210a384a5e08bda; searxng/searxng a7163d091037cae586c444b05f22ecca162bb492; google-deepmind/clrs 6d5728b9efadf8648413c8c473929a733caacced; adbar/trafilatura 195a969613c8f262128b7238b534d372a56db2f5; microsoft/markitdown ed178952a6672abdfd35b5f9e76a80b6cefc086e; UKGovernmentBEIS/inspect_ai cab2b874f5ac05937afc1e80b7316cb5873fad98; EleutherAI/lm-evaluation-harness d6de81643928d653435c431bae19945d41d32520; optuna/optuna 0abf066c1e5d9d83987986869daa3c2bb23df519; K-Dense-AI/scientific-agent-skills c21d13b3cc2894680229ba9959a53281acb9200e. Approximately 330 MB. License metadata and license text digests in local manifest. SearXNG AGPL-3.0 requires distribution/network-use compliance review. Blockscout MCP server now has custom LicenseRef-Blockscout, effective 2026-05-15; do not accept additional terms on owner's behalf or assume prior permissive license. CCXT reported repository size 9,025,551 KiB; consider reviewed pinned package release. NetworkX license metadata NOASSERTION; inspect exact license first. All downloads are research candidates, not installed runtime services.

## Research-led capability expansion

- Darwin Godel Machine: https://arxiv.org/abs/2505.22954 — bounded branching improvement archive, not arbitrary self-modification of governance.
- Voyager: https://arxiv.org/abs/2305.16291 — curriculum and executable skill reuse; transfer and retention tests are essential.
- AI Scientist v2: https://arxiv.org/abs/2504.08066 — hypothesis-driven experimental tree search. Custom source license needs review before acquisition. Do not equate automated papers with verified science.
- smolagents: https://huggingface.co/docs/smolagents/en/index — typed tool orchestration, local models, sandboxing.
- Qwen-Agent: https://github.com/QwenLM/Qwen-Agent — tool-call parsing, MCP, retrieval and planning using Qwen.
- Toolformer: https://proceedings.neurips.cc/paper/2023/hash/d842425e4bf79ba039352da0f658a906-Abstract-Conference.html — tool-use learning through utility-filtered training examples.

Next independent experiments: typed read-only skill composition over actual v86 outputs; matched direct vs tool-assisted reasoning with equal budgets and unseen tasks, separately score tool-computed vs model-derived answers; executable skill archive with provenance, versioning, independent acceptance and rollback; adaptive curriculum driven by weakness and novelty, not repeated benchmark optimization. Keep tool-generated examples separate from independent evaluation sets. Review dependency trees and source/license before runtime installs. No arbitrary shell authority or automatic promotion. Retain all original MYRIAD scope targets and release gates.

## Remaining work

v85 24/24 CI. Existing scheduled neural task exit 1; Windows PowerShell 5.1 ordinary stderr warning termination independently reproduced, but original log contains only timestamp and does not prove cause. Permanent repair outstanding. Training guards and schedules preserved. No new actual neural training in v86; no production integration, no Codex, no paid resources, no private data export. Existing release gates remain binding.
