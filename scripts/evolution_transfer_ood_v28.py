#!/usr/bin/env python3
"""v2.8 predeclared cross-task neural transfer audit and null-predictor tribunal.

Compare real saved FP16 candidates with original FP16 checkpoints AND zero baseline
on three deliberately unseen teacher functions. Results are synthetic-only and
must not be interpreted as real-world transfer, market alpha, or model promotion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import zipfile

import myriad_bank_fabric as bank
import evolution_neural_curriculum_v25 as curriculum
import evolution_neural_probe_v27 as prior

SCHEMA='myriad.synthetic_cross_task_transfer.v28'
FAMILIES=('antipodal','nonlinear_interaction','independent_linear')
PREREGISTERED_SEEDS=(980004,980005)
AGENT_BYTES=bank.BASE_AGENT_WIDTH * bank.DTYPE_BYTES
ABILITY_BYTES=10000*bank.BASE_ABILITY_WIDTH*bank.DTYPE_BYTES


def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def validate_seed(seed):
    if type(seed) is not int or seed not in PREREGISTERED_SEEDS:
        raise ValueError('Only preregistered unseen cross-task seeds are qualified')
    return seed

def score(source_mse,candidate_mse,zero_mse):
    for value in (source_mse,candidate_mse,zero_mse):
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:
            raise ValueError('Scores must be finite, nonnegative numbers')
    return {'source_mse':float(source_mse),'candidate_mse':float(candidate_mse),'zero_mse':float(zero_mse),
            'beats_source':bool(candidate_mse<source_mse),
            'beats_zero':bool(candidate_mse<zero_mse)}

def seal(payload):
    raw=dict(payload)
    raw.pop('receipt_sha256',None)
    raw['receipt_sha256']=sha(canonical(raw))
    return raw

def verify_seal(report):
    if type(report) is not dict or report.get('schema')!=SCHEMA:raise ValueError('Wrong transfer evidence schema')
    raw=dict(report);claimed=raw.pop('receipt_sha256',None)
    if type(claimed) is not str or claimed!=sha(canonical(raw)):raise ValueError('Receipt digest mismatch')
    validate_seed(report.get('seed'))
    if report.get('families')!=list(FAMILIES):raise ValueError('Experiment family plan changed')
    for k in ('production_authority','trading_alpha_certified','model_promotion'):
        if report.get(k) is not False:raise ValueError('Unauthorized research-to-production claim')
    rows=report.get('rows')
    if type(rows) is not list:raise ValueError('Invalid result records')
    for row in rows:
        if type(row) is not dict:raise ValueError('Invalid transfer score record')
        metrics=score(row.get('source_mse'),row.get('candidate_mse'),row.get('zero_mse'))
        if any(row.get(k)!=metrics[k] for k in metrics):raise ValueError('Transfer metric or baseline flag inconsistent')
    return True

def _target(torch,x,family,seed,agent,training_seed,context):
    if family=='antipodal':
        generator=torch.Generator(device='cpu').manual_seed(training_seed+agent*1103)
        original_w=torch.randn((32,8),generator=generator)*0.115
        return -(x@original_w+0.07*torch.sin(x[:,:8])+context[:8].reshape(1,8)*0.025)
    if family=='nonlinear_interaction':
        return 0.35*torch.tanh(x[:,:8]*x[:,8:16])+0.20*torch.sin(x[:,16:24]*x[:,24:32])
    if family=='independent_linear':
        generator=torch.Generator(device='cpu').manual_seed(seed+agent*881)
        return x@(torch.randn((32,8),generator=generator)*0.19)
    raise ValueError('Unregistered target family')

def _ability_teacher(torch,seed,training_seed,family):
    original,_train,_hold=curriculum._ability_data(torch,training_seed)
    if family=='antipodal':return -original
    ids=torch.arange(1,10001,dtype=torch.float32).reshape(-1,1)
    dims=torch.arange(1,33,dtype=torch.float32).reshape(1,-1)
    if family=='nonlinear_interaction':
        return 0.15*torch.cos(ids*.023+dims*.29)*torch.sin(ids*.004+dims*.13)
    if family=='independent_linear':
        g=torch.Generator(device='cpu').manual_seed(seed+441177)
        # A predeclared independent per-adapter mathematical teacher, unrelated
        # to the periodic original source task; not a pretrained external model.
        return torch.randn((10000,32),generator=g)*.10
    raise ValueError('Unregistered ability teacher family')

def _compute(archive,candidates,seed):
    validate_seed(seed)
    import numpy as np
    import torch
    from torch.nn.utils import vector_to_parameters
    torch.set_num_threads(1)
    candidates=Path(candidates)
    training=prior.read_strict_json((candidates/'SYNTHETIC_TRAINING_REPORT_V25.json').read_text())
    digest=training.get('receipt_sha256')
    if digest!=sha(curriculum.canonical({k:v for k,v in training.items() if k!='receipt_sha256'})):
        raise ValueError('Original v2.5 training receipt mismatch')
    training_seed=training.get('seed')
    if training.get('agent_count')!=10 or len(training.get('agent_records',[]))!=10 or training.get('ability_count')!=10000:
        raise ValueError('Expected all ten agents and 10000 ability adapters')
    if training.get('production_authority') is not False or training.get('auto_promote') is not False:
        raise ValueError('Training was marked for promotion')
    proof=bank.verify_sample(archive)
    if proof['source_archive_sha256']!=training.get('source_archive_sha256'):
        raise ValueError('Source archive identity differs from v2.5 training')
    with zipfile.ZipFile(archive) as z:
        agents=z.read('agent_weights.fp16');abilities=z.read('ability_weights.fp16')
    original_ability=np.frombuffer(abilities,dtype='<f2').astype('float32').reshape((10000,32))
    rows=[]; family_results={name:[] for name in FAMILIES}
    for i,r in enumerate(training['agent_records'],1):
        name=f'AG-{i:05d}.synthetic_v25.fp16'
        if r.get('agent')!=i or r.get('candidate_path')!=name or r.get('promotion')!='QUARANTINED':
            raise ValueError('Agent source identity mismatch')
        base=agents[(i-1)*AGENT_BYTES:i*AGENT_BYTES]
        file=candidates/name
        if sha(base)!=r.get('source_sha256'):
            raise ValueError('Original source row SHA mismatch')
        prior.check_file_digest(file,r.get('candidate_sha256'),AGENT_BYTES)
        candidate=file.read_bytes()
        ctx=torch.from_numpy(original_ability[(i-1)*1000:i*1000].mean(axis=0).copy())
        def restore(raw):
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(training_seed+i)
                model=curriculum._model(torch)
                vector_to_parameters(torch.from_numpy(np.frombuffer(raw,dtype='<f2').astype('float32').copy()),model.parameters())
            model.eval()
            return model
        baseline=restore(base);trained=restore(candidate)
        gen=torch.Generator(device='cpu').manual_seed(seed+i*29)
        x=torch.randn((112,32),generator=gen)*1.10+0.20
        with torch.no_grad():
            base_pred=baseline(x);cand_pred=trained(x)
            for family in FAMILIES:
                y=_target(torch,x,family,seed,i,training_seed,ctx)
                m=score(curriculum._mse(torch,base_pred,y),curriculum._mse(torch,cand_pred,y),curriculum._mse(torch,torch.zeros_like(y),y))
                rows.append({'subject':'agent','identity':i,'family':family,'inputs_sha256':sha(x.numpy().tobytes()),'target_sha256':sha(y.numpy().tobytes()),**m})
                family_results[family].append(m)
    ability_row=training['ability_result'];p=candidates/'abilities-10000.synthetic_v25.fp16'
    if ability_row.get('candidate_path')!=p.name or ability_row.get('source_sha256')!=sha(abilities):
        raise ValueError('Ability source provenance mismatch')
    prior.check_file_digest(p,ability_row.get('candidate_sha256'),ABILITY_BYTES)
    trained_ability=torch.from_numpy(np.frombuffer(p.read_bytes(),dtype='<f2').astype('float32').reshape((10000,32)).copy())
    source_ability=torch.from_numpy(original_ability.copy())
    rng=torch.Generator(device='cpu').manual_seed(seed+8891)
    features=torch.randn((32,12),generator=rng)*1.1+0.2
    with torch.no_grad():
        for family in FAMILIES:
            target=_ability_teacher(torch,seed,training_seed,family)@features
            m=score(curriculum._mse(torch,source_ability@features,target),curriculum._mse(torch,trained_ability@features,target),curriculum._mse(torch,torch.zeros_like(target),target))
            rows.append({'subject':'ability_bank','identity':10000,'family':family,'inputs_sha256':sha(features.numpy().tobytes()),'target_sha256':sha(target.numpy().tobytes()),**m})
            family_results[family].append(m)
    summary={family:{'comparisons':len(result),'beats_source':sum(x['beats_source'] for x in result),'beats_zero':sum(x['beats_zero'] for x in result),'wins_both':sum(x['beats_source'] and x['beats_zero'] for x in result)} for family,result in family_results.items()}
    return {'schema':SCHEMA,'seed':seed,'families':list(FAMILIES),'source_archive_sha256':proof['source_archive_sha256'],
            'source_import_status':proof.get('source_import_status','imported_unverified'),
            'v25_training_receipt_sha256':digest,'candidate_agent_count':10,'candidate_adapter_count':10000,
            'rows':rows,'summary':summary,'unseen_target_families':3,
            'precommitted_seeds':list(PREREGISTERED_SEEDS),'selection_rule':'all 3 families; 10 agents and full ability adapter bank; zero baseline included',
            'scope':'cross-task synthetic targets; no real-world OOD or trading transfer',
            'production_authority':False,'trading_alpha_certified':False,'model_promotion':False}

def run(archive,candidates,out,seed=980004,*,authorize=False):
    if authorize is not True:raise PermissionError('Explicit local inference permission required')
    validate_seed(seed)
    p=Path(out)
    if p.exists():raise FileExistsError('Existing synthetic transfer evidence is immutable')
    payload=seal(_compute(archive,candidates,seed))
    verify_seal(payload)
    with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
        f.write(canonical(payload)+b'\n');f.flush();os.fsync(f.fileno())
    return payload

def verify(archive,candidates,receipt):
    data=prior.read_strict_json(Path(receipt).read_text())
    verify_seal(data)
    expected=seal(_compute(archive,candidates,data['seed']))
    prior._compare_recomputed(expected,data)
    return {'independent_replay':True,'seed':data['seed'],'families':len(FAMILIES),
            'agents':10,'adapters':10000,'comparisons':len(expected['rows']),
            'zero_baseline_checked':True,'no_model_promotion':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('run','verify'):
        q=sub.add_parser(name)
        q.add_argument('--archive',required=True);q.add_argument('--candidates',required=True);q.add_argument('--receipt',required=True)
        if name=='run':
            q.add_argument('--seed',type=int,default=980004);q.add_argument('--authorize',action='store_true')
    a=vars(p.parse_args());command=a.pop('command')
    output=run(a['archive'],a['candidates'],a['receipt'],seed=a['seed'],authorize=a['authorize']) if command=='run' else verify(a['archive'],a['candidates'],a['receipt'])
    print(json.dumps(output,indent=2,sort_keys=True))
if __name__=='__main__':main()
