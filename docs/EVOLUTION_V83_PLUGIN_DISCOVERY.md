# v8.3 exploratory discovery: robust groups, external reasoning, historical evidence

## Evidence and new research channels (2026-11-24)

- Consensus search and fetched ICLR 2020 record: Sagawa, Koh, Hashimoto, Liang, Distributionally Robust Neural Networks for Group Shifts, https://arxiv.org/abs/1911.08731 and https://openreview.net/forum?id=ryxGuJrFvS . Regularization and worst-group performance motivate a separate group-reweighting hypothesis. No copied implementation and no claim of reproducing the paper's experiments.
- External benchmark source identified: https://github.com/google-deepmind/clrs (Apache-2.0 repository; CLRS-Text also available). https://proceedings.mlr.press/v162/velickovic22a.html . Candidate for independent reasoning benchmark; dataset license and split/version audit required before using data. Hugging Face dataset_search disabled by server configuration; no dataset fetched.
- WILDS distribution-shift benchmark: https://proceedings.mlr.press/v139/koh21a.html . Candidate protocol inspiration, not yet imported or trained.
- omgskills returned pinned scientific-brainstorming, scientific-critical-thinking, scholar-evaluation and experiment-planning catalog entries. Catalog descriptions are not installed or audited skills. Brainbase evaluation skill search returned no entries. No external agent execution or paid resources.
- FactorWeave public manifest reports 10768 tickers, 252-day features and labels history, latest date 2026-11-23. Proposed point-in-time regime robustness and leakage audit. No private holdings, no paid feature retrieval, no trading, no public distribution of provider records. Confirm data license, timestamp semantics and split leakage before integrating.

## Bounded empirical Group-DRO-inspired test

Fixed cohort seeds 0..11; four groups with 256,64,32,16 training rows; distinct 128-row test groups per seed with shifted spurious correlations. Three arms start from identical two-coefficient linear predictor; identical 160 full-batch gradient steps, learning rate and L2. Pooled vs equal-group vs adaptive exponential group weighting; log-space numerical update. Fixed hyperparameters before results; 5760 total optimizer steps. This is a synthetic linear experiment (not neural training or live agent learning). Six local unit tests passed after failing missing-module RED.

| Arm | Mean worst-group MSE | Mean group MSE |
|---|---:|---:|
| pooled | 1.0508785445027 | 0.5428251358951622 |
| balanced | 0.32620090175818384 | 0.2662604995555528 |
| DRO | 0.32080503270978283 | 0.25965249258548107 |

DRO beat pooled 12/12, balanced only 3/12 (9 losses). Do not promote. Mean loss lower but majority seed-wise worst-group losses against stronger control; no inferential or generalization claim. Next: preregister fresh neural experiment with balanced baseline and independent split, not optimize against these test seeds. No production authority or semantic mastery. Local exact source git blobs: edad06a55bdf374a767695708bbfb26225923943 and 15a3fc40963c33f46d338fb81b732b4df1b0e1d3. Result output SHA256 b9939d88a7fc7b58daa37caa3ed51e5b481e3f072f39f32563eb4912593de12b. Recompute using CLI --authorize in isolated research runtime.

## Recovered historical archive

Read-only Library archive MYRIAD_OMEGA_v0.8_100_AGENT_WEIGHT_PILOT.zip, 75042904 compressed bytes, SHA256 [private artifact digest retained locally]. Independent archive inspection: SQLite integrity ok, contiguous IDs 1..100, 100 unique matching SHA256 blocks, all finite FP16, 82200000 bytes, no trailing bytes, 41100000 parameters, 500 recorded steps, all marked trained. Results JSONL 1 valid and 17 invalid lines. No original architecture/seed replay or optimizer trajectory certification from this evidence alone; no full 8.22GB or 640MB historical bank recovery. Do not add recovered agent IDs to distinct live agent counts. No weights exported to GitHub.

## Runtime continuity

v8.2 exact 24/24 CI and 15/15 exact local tests. Installed three qualified source modules and updated only existing local phase allowlist: verified live Python hashes f674ce265c04b1759ccde98823c2518cedaf6b86, bc548010d609ac0f4ab2d4b716ece82881ad4ceb, 84530804f742b48da3adc66393905f52cb8795ea; local launcher hash 171868cea528978a4840bcea18a4a13e325846b0. PID 26380 successful. One authorized manual novel_reasoning phase request exclusively reserved for existing scheduler (PID 30600), no automatic cadence change. Actual result pending. v80 real cohort remains below 3500 MiB training guard. Preserve existing scheduler and resource controls. Latest public counts: 136 inference-backed workers, 86 added methods, 270336 numeric ability rows, 109152000 neural checkpoint bytes. No merging or deployment into ICARUS.
