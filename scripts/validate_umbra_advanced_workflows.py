#!/usr/bin/env python3
"""Audit all 5000 distinct manual GitHub Actions contracts without third-party packages."""
from pathlib import Path
import json,re,sys,hashlib
ROOT=Path(__file__).resolve().parent.parent
catalog=json.loads((ROOT/'scripts'/'umbra_advanced_registry.json').read_text())
items=[r for part in catalog['shards'] for r in json.loads((ROOT/'scripts'/part).read_text(encoding='utf8'))]; errors=[]
files=list((ROOT/'.github'/'workflows').glob('umbra-u[0-9][0-9][0-9][0-9]-*.yml'))
if catalog['schema']!='umbra.advanced.5000.v1' or catalog['count']!=5000 or len(items)!=5000:errors.append('wrong catalog size')
if len(files)!=5000:errors.append(f'expected 5000 YAML files, found {len(files)}')
if len({x['id'] for x in items})!=5000 or len({x['name'] for x in items})!=5000:errors.append('duplicate ID or display name')
if len({(x['method'],x['metric'],x['variant']) for x in items})!=5000:errors.append('duplicate experimental combination')
tiers={}
for i,r in enumerate(items):
    ident=f'U{i+301:04d}'
    if r['id']!=ident or r['number']!=i+301:errors.append(f'incorrect catalog ID {i}')
    tiers[r['tier']]=tiers.get(r['tier'],0)+1
    if r['method'] not in catalog['tiers'][str(r['tier'])]['methods']:errors.append(f'{ident} unknown method')
    if r['metric'] not in catalog['metrics']:errors.append(f'{ident} unknown metric')
    if not (0 <= r['variant'] <20):errors.append(f'{ident} bad variant')
    path=ROOT/'.github'/'workflows'/f"umbra-{ident.lower()}-{r['method']}-{r['metric']}-p{r['variant']+1:02d}.yml"
    if not path.exists():errors.append(f'{ident} missing YAML');continue
    t=path.read_text()
    checks={
      'manual_only':t.count('  workflow_dispatch:')==1 and re.search(r'(?m)^on:$\n  workflow_dispatch:$',t),
      'no_auto_triggers':not re.search(r'(?m)^\s*(schedule|push|pull_request|workflow_run|repository_dispatch|workflow_call):',t),
      'read_only':re.search(r'(?m)^permissions:$\n  contents: read$',t),
      'specific_runner':f'node scripts/umbra_advanced_lab.mjs --id {ident} --out-dir advanced-evidence' in t,
      'evidence':f'advanced-evidence/{ident}.json' in t,
      'timeout':re.search(r'(?m)^    timeout-minutes: 12$',t),
      'limits':len(t.encode())<500_000,
      'no_unsafe_tokens':not any(s in t for s in ('secrets.','sudo ','curl ','wget ','pull_request_target:','script:','npm install','gh pr merge'))
    }
    for kind,ok in checks.items():
        if not ok:errors.append(f'{ident} failed {kind}')
if any(tiers.get(i)!=1000 for i in range(4,9)):errors.append(f'invalid tier size {tiers}')
result={'schema':'umbra.advanced.5000.catalog-validation.v1','valid':not errors,'count':len(items),'workflow_files':len(files),
    'tier_counts':tiers,'unique_algorithms':len({x['method'] for x in items}),'unique_model_metrics':len(catalog['metrics']),
    'unique_scenario_combinations':len({(x['method'],x['metric'],x['variant']) for x in items}),
    'manual_only':True,'repo_write':False,'errors':errors[:35],'errorsTotal':len(errors),
    'catalog_sha256':hashlib.sha256((ROOT/'scripts'/'umbra_advanced_registry.json').read_bytes()).hexdigest()}
print(json.dumps(result,indent=2));sys.exit(0 if not errors else 1)
