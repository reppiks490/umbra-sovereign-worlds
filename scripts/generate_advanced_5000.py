#!/usr/bin/env python3
"""Generate 5,000 distinct, manually dispatched UMBRA synthetic research workflows.

25 real experimental algorithms × 10 model observables × 20 deterministic protocols.
These are simulation workflows, NOT autonomously learning agents or real scientific validation.
"""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parent.parent
METHODS = {
    'causal-inference': ['paired-delta', 'dose-gradient', 'local-curvature', 'interaction-synergy', 'placebo-falsification'],
    'adversarial-resilience': ['shock-recovery', 'cvar-tail-risk', 'adversarial-seed-search', 'seed-invariance', 'multi-horizon-stability'],
    'evolutionary-search': ['policy-tournament', 'heldout-seed-transfer', 'bounded-mutation', 'pareto-frontier', 'regime-transition'],
    'sovereign-optimization': ['minimax-regret', 'preference-robustness', 'budget-constrained-search', 'regional-fairness', 'composite-utility'],
    'metascience': ['exact-replay', 'chunk-equivalence', 'invariant-fuzz', 'robustness-dominance', 'corruption-falsification']
}
METRICS=['population','food','water','energy','wealth','knowledge','infected','carbon','biodiversity','inequality']
LEVELS=['precision','boundary','regime-shift','long-horizon','adversarial']
POLICY_AXES=['trade','climate','medicine','innovation','migration','conservation','conflict']
steps=[25,34,43,52,61,70,79,88,97,106,115,124,133,142,151,160,169,178,187,196]
records=[]
for tier,(stage,methods) in enumerate(METHODS.items(),start=4):
    for method in methods:
        for metric in METRICS:
            for variant in range(20):
                number=301+len(records)
                case_id=f'U{number:04d}'
                band=LEVELS[variant//4]
                axis=POLICY_AXES[(variant+len(records)//20)%7]
                other=POLICY_AXES[(variant+len(records)//13+3)%7]
                if other==axis:other=POLICY_AXES[(POLICY_AXES.index(axis)+1)%7]
                seed=1_000_003+(number*2713)+variant*97
                horizon=steps[variant]
                amp=round(.06+.03*(variant%4)+.02*(variant//4),4)
                description=f'{case_id} | T{tier} {stage} | {method} | {metric} | {band} {variant%4+1}'
                rec=dict(id=case_id,number=number,tier=tier,stage=stage,method=method,metric=metric,variant=variant,band=band,
                         axis=axis,otherAxis=other,seed=seed,steps=horizon,amplitude=amp,name=description,
                         scope='synthetic-only; no model training, external scientific validation or production decisions')
                records.append(rec)
                path=ROOT/'.github'/'workflows'/f'umbra-{case_id.lower()}-{method}-{metric}-p{variant+1:02d}.yml'
                contents=(f'# UMBRA {case_id} — bounded, manually invoked synthetic research case; no deployment/trading.\n'
                    f'name: "{description}"\n'
                    'on:\n  workflow_dispatch:\n'
                    'permissions:\n  contents: read\n'
                    f'concurrency:\n  group: "umbra-{case_id.lower()}-${{{{ github.ref }}}}"\n  cancel-in-progress: true\n'
                    'jobs:\n  experiment:\n    runs-on: ubuntu-latest\n    timeout-minutes: 12\n'
                    '    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-node@v4\n        with:\n          node-version: "22"\n'
                    f'      - name: "Execute {case_id} advanced synthetic experiment"\n'
                    f'        run: node scripts/umbra_advanced_lab.mjs --id {case_id} --out-dir advanced-evidence\n'
                    '      - name: Upload independent simulation evidence\n        uses: actions/upload-artifact@v4\n        with:\n'
                    f'          name: "umbra-{case_id.lower()}-evidence"\n'
                    f'          path: advanced-evidence/{case_id}.json\n'
                    '          if-no-files-found: error\n          retention-days: 7\n')
                path.write_text(contents,encoding='utf-8')
assert len(records)==5000
assert len(set(r['id'] for r in records))==5000
assert len(set(r['name'] for r in records))==5000
assert len(set((r['tier'],r['method'],r['metric'],r['variant']) for r in records))==5000
catalog={'schema':'umbra.advanced.5000.v1','project':'UMBRA Sovereign Worlds, synthetic only','first':'U0301','last':'U5300',
         'count':5000,'tiers':{str(i+4):{'stage':k,'count':1000,'methods':v} for i,(k,v) in enumerate(METHODS.items())},
         'metrics':METRICS,'variantCountPerMethodMetric':20,'risk':'bounded, read-only, deterministic synthetic simulation'}
shard_dir=ROOT/'scripts'/'advanced_registry'
shard_dir.mkdir(parents=True,exist_ok=True)
shards=[]
for i in range(0,len(records),250):
    name=f'advanced_registry/shard_{i//250:02d}.json'
    (ROOT/'scripts'/name).write_text(json.dumps(records[i:i+250],separators=(',',':'),ensure_ascii=False)+'\n',encoding='utf-8')
    shards.append(name)
catalog['shards']=shards
(ROOT/'scripts'/'umbra_advanced_registry.json').write_text(json.dumps(catalog,separators=(',',':'),ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'files':len(records),'first':records[0]['name'],'last':records[-1]['name'], 'catalog_bytes':(ROOT/'scripts'/'umbra_advanced_registry.json').stat().st_size}))
