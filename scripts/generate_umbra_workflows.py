#!/usr/bin/env python3
"""Generate 300 uniquely identified *manual*, read-only UMBRA research workflows."""
import json, pathlib, re
ROOT=pathlib.Path(__file__).resolve().parent.parent
FAMILIES={
"verification":["seed-replay","chunk-equivalence","world-regions","resource-bounds","census-balance","civic-accounting","faction-coverage","corridor-geometry","treasury-solvency","passport-roundtrip","passport-rejection","policy-clamping","paired-null","paired-repeatability","weather-noise","timeline-consistency","history-samples","reality-court","scientific-gate","stress-replay"],
"research":["climate-response","trade-response","conservation-response","medicine-response","innovation-response","migration-response","conflict-response","sensitivity-map","paired-uncertainty","seasonal-trajectory","biodiversity-profile","food-security","water-security","energy-resilience","epidemic-path","migration-network","civic-legitimacy","fiscal-transfers","emissions-trajectory","inequality-profile"],
"evolution":["policy-tournament","pareto-frontier","shock-resilience","bounded-search","minimax-stability","seed-transfer","drought-response","trade-fragility","equity-growth","conservation-innovation","epidemic-resilience","carbon-efficiency","regional-survival","regime-rotation","resource-portfolio","replication-audit","counterfactual-race","adversarial-seeds","null-contender","policy-tradeoffs"]}
VARIANTS=["baseline","edge","stress","cross-seed","adversarial"]
entries=[]
for stage,families in FAMILIES.items():
 for family in families:
  for rank,variant in enumerate(VARIANTS,1):
   n=len(entries)+1
   id=f"U{n:03d}"
   display=f"{id} | {stage.upper()} / {family.replace('-', ' ').title()} / {variant.replace('-', ' ').title()}"
   steps=[35,55,80,105,130][rank-1]
   seed=1009+n*727+rank*191
   record={"id":id,"number":n,"stage":stage,"family":family,"variant":variant,"rank":rank,"steps":steps,"seed":seed,"name":display,"purpose":f"Run bounded {stage} analysis for {family} using {variant} inputs; preserve synthetic-only evidence."}
   entries.append(record)
   filename=f"umbra-{id.lower()}-{family}-{variant}.yml"
   contents=(
    f"# UMBRA Ω / {id}: manually invoked synthetic research. No automatic deployment or trading.\n"
    f"name: '{display}'\n"
    "on:\n  workflow_dispatch:\n"
    "permissions:\n  contents: read\n"
    "concurrency:\n"
    f"  group: 'umbra-{id.lower()}-${{{{ github.ref }}}}'\n"
    "  cancel-in-progress: true\n"
    "jobs:\n  evidence:\n"
    "    runs-on: ubuntu-latest\n    timeout-minutes: 8\n"
    "    steps:\n      - uses: actions/checkout@v4\n"
    "      - uses: actions/setup-node@v4\n        with:\n          node-version: '22'\n"
    f"      - name: 'Execute {id} evidence case'\n"
    f"        run: 'node scripts/umbra_lab.mjs --id {id} --out-dir workflow-artifacts'\n"
    "      - name: Upload synthetic evidence (not independent scientific validation)\n"
    "        uses: actions/upload-artifact@v4\n"
    "        with:\n"
    f"          name: 'umbra-{id.lower()}-synthetic-evidence'\n"
    f"          path: 'workflow-artifacts/{id}.json'\n"
    "          if-no-files-found: error\n"
    "          retention-days: 14\n"
   )
   (ROOT/".github"/"workflows"/filename).write_text(contents,encoding="utf8")
assert len(entries)==300
(ROOT/"scripts"/"umbra_workflow_registry.json").write_text(json.dumps({"schema":"umbra.actions.v1","purpose":"Manually launched synthetic research and engineered verification only","stages":{k:100 for k in FAMILIES},"workflow_count":300,"items":entries},indent=2)+"\n",encoding="utf8")
print(f"Generated {len(entries)} unique workflows. 100 verification + 100 research + 100 evolution; all manual.")
