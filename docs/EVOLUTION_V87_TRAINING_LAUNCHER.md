# v8.7 — native Windows training repair and second acquisition wave

Previous scheduled neural task returned exit 1; only timestamp was logged, so original cause is not proven. Windows PowerShell 5.1 stderr handling defect reproduced separately: a successful Python process emitting ordinary stderr was terminated by ErrorActionPreference=Stop. RED PID 26372 missing helper; GREEN PID 26900 verifies both streams, successful warning, real exit 7, preference restoration, invalid log destination. Patched launcher PID 27800 parsed successfully, original launcher hash ffc636f94b945b8a3c96482410d427f2130a7f57. Existing ACL and 5GB disk guards preserved; explicit physical 3500 MiB and virtual 6000 MiB admission and local inference idle check added. Scheduler cadence unchanged. Source kept under scripts/windows; local rollout requires exact blob validation and guarded atomic replacement, and no successful scheduled training claim until observed. Source test is not proof of full training, nor cross-process exclusion against unrelated manual launches.

v86 24/24 CI and exact 7/7 Windows tests; installed hash 3642a7ba18b5df6760ec21c555ec9359a6663728 verified PID 20428. No scheduled acquisition or new agent routing yet.

Second local acquisition batch PID 31456 exit 0, manifest-1795550513.json: 12 additional repositories, shallow Git objects, no checkout/execution/dependency install. Total 21 acquisitions, approximately 467 MB. Exact second-wave commits:
- QwenLM/Qwen-Agent 31a4d36d123688581a9e9744427272b33ce940e0
- huggingface/smolagents d0ec5966bd0bc723988a62f91ae81ffacdddd2fe
- stanfordnlp/dspy 2ae73ca33372aa0a172bcb27584f03aaaf4d7e18
- langchain-ai/langgraph 732da52047a1658cccffca86ac27396871b3f385
- huggingface/lerobot b07adcc5e3ce42c26a248236dbb3571f84c28c43
- dottxt-ai/outlines c52af8472c6fe8a607a733ec11b709476af77a96
- noamgat/lm-format-enforcer 817f944fcc8851917c40300a47f62d1defc3ffc3
- facebookresearch/faiss 6074b69e98a736f5be370c69043b346370a1b3be
- deepset-ai/haystack 68497ec581d759e05f058ece0132f91013b856ff
- microsoft/graphrag 34b2b67ae4601ad0b47bcd179fbe3f2a23aa0857
- ggml-org/llama.cpp 22b99122e1dfe1d8a5175bfa2eaa8389699c0b92
- evidentlyai/evidently 34771fe41c08ca074d96a52aaf4a45cd640cbaf5

License metadata MIT/Apache-2.0 for all twelve; complete dependency, model/data and security review still required. No third-party source executed. Next: exact-source Windows CI, install guarded repair, capture actual training outcome; typed bounded skill composition over local fabric, independent evaluation, no auto-promotion. Preserve all 13 gates, no production merge, no Codex, no paid resources or private artifact export.
