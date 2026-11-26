# Native deterministic forecast qualification

Adds explicit exact-architecture PatchTSTForPrediction and PatchTSMixerForPrediction routes. Only deterministic MSE point-forecast configs, bounded context/horizon/channel dimensions and exact output shape are admitted. No tokenizer required for numeric inputs. The existing full-receipt identity checks and offline model loading remain in place. Chronos aliases, probabilistic heads, pretraining variants and remote code remain excluded.

Failing-first routing: one expected failure, two exclusion guards passed; 3/3 routes then passed. Full native Python suite 279/279 passed, 22.734s, including actual isolated PatchTST and PatchTSMixer fixture forwards. Synthetic fixture inputs establish execution only, not authentic market forecasting accuracy or trading authority. No pretrained models newly executed; active native bootstrap retained. No new dependencies installed. Requires independent CI and integration review.
