"""Replay council results against pinned human-authored validation records.

This verifies scoring and dataset binding, not the provenance of model generation
or novelty relative to public pretraining corpora. Never uses test answers.
"""
import argparse, json, math
from pathlib import Path
from council_qualification import evaluate
from council_ledger import validate, entries, summarize

def replay_trial(report,truths):
    m=validate(report)
    if set(truths)!=set(m['validation_records']) or 'rows' not in report:
        raise ValueError('missing validation evidence')
    actual=evaluate(truths,m['models'],report['rows'])
    for key in ('ensemble','baselines','paired','disagreement_cases'):
        if actual[key]!=report.get(key):
            raise ValueError('replay mismatch: '+key)
    if not math.isclose(actual['inference_seconds'],report['inference_seconds'],rel_tol=1e-12,abs_tol=1e-9):
        raise ValueError('replay duration mismatch')
    return actual['ensemble']

def run(root):
    from student_council import load_corpus, lesson, answer_value
    from human_corpus import REPO, REV
    from hf_weight_cache import lock
    bank=root/'experience'/'council-qualification'
    if not bank.is_dir():
        return {'status':'no_evidence','production_authority':False}
    with lock(bank/'qualification.lock'):
        trials=entries(bank)
        if not trials:
            return {'status':'no_evidence','production_authority':False}
        corpus=load_corpus(root)
        verified=0
        for r in trials:
            m=r['manifest']
            selected=[lesson(corpus,i)[1] for i in range(m['offset'],m['offset']+m['count'])]
            ids=[v['record_sha256'] for v in selected]
            if ids!=m['validation_records']:
                raise ValueError('pinned development record order mismatch')
            truths={v['record_sha256']:answer_value(v['answer']) for v in selected}
            replay_trial(r,truths)
            verified+=len(ids)
        return {'status':'replayed','replayed_trials':len(trials),'replayed_cases':verified,
                'corpus':REPO,'revision':REV,'aggregate':summarize(bank),
                'scope':'recomputed metrics against publisher-digest-verified development labels; no fresh inference',
                'weight_training':False,'production_authority':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    print(json.dumps(run(p.parse_args().root),sort_keys=True))
