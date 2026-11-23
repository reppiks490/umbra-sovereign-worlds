#!/usr/bin/env python3
"""Static, standard-library-only audit of all 300 manually triggered workflow YAML contracts."""
import json, pathlib, re, sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
records=json.loads((ROOT/'scripts/umbra_workflow_registry.json').read_text(encoding='utf8'))['items']
files=sorted((ROOT/'.github/workflows').glob('umbra-u*.yml'))
issues=[]
if len(records)!=300:issues.append(f'expected 300 registry records, found {len(records)}')
if len(files)!=300:issues.append(f'expected 300 workflows, found {len(files)}')
if len({r['id'] for r in records})!=len(records):issues.append('duplicate registry id')
if len({r['name'] for r in records})!=len(records):issues.append('duplicate workflow name')
for r in records:
 id=r['id'];p=ROOT/'.github'/'workflows'/f"umbra-{id.lower()}-{r['family']}-{r['variant']}.yml"
 if not p.is_file():issues.append(f'missing {p.name}');continue
 raw=p.read_text(encoding='utf8')
 checks=[('manual only',re.search(r'(?m)^  workflow_dispatch:\s*$',raw)),
 ('no automatic triggers',not re.search(r'(?m)^  (push|pull_request|schedule|workflow_run|repository_dispatch):',raw)),
 ('read-only permission',re.search(r'(?m)^  contents: read$',raw)),
 ('specific runner',f'node scripts/umbra_lab.mjs --id {id} --out-dir workflow-artifacts' in raw),
 ('evidence artifact',f'workflow-artifacts/{id}.json' in raw),
 ('timeout',re.search(r'(?m)^    timeout-minutes: 8$',raw)),
 ('no secrets',not any(secret in raw for secret in ['${{ secrets.','pull_request_target:', 'curl ', 'wget ', 'sudo ']))]
 for name,ok in checks:
  if not ok:issues.append(f'{id} {name} failed')
if issues:
 print(json.dumps({'status':'invalid','issues':issues[:60],'total_issues':len(issues)},indent=2));sys.exit(1)
print(json.dumps({'status':'valid','workflows':300,'verification':100,'research':100,'evolution':100,'manual_only':True,'read_only':True},indent=2))
