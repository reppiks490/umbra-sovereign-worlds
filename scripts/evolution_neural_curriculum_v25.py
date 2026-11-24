#!/usr/bin/env python3
"""Opt-in two-regime synthetic PyTorch training on the exact 10-agent/10k-adapter sample.

Experimental architecture only. Real gradient updates to saved candidate weights,
with independent holdouts and post-FP16 quantization evaluation. No source mutation,
real-world mastery, full historical bank attestation, model auto-promotion or trades.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import zipfile
from pathlib import Path

import myriad_bank_fabric as bank

SCHEMA='myriad.synthetic_neural_curriculum.v25'


def plan():
    return {'schema':SCHEMA,'agents':10,'ability_adapters':10_000,
            'parameters_per_agent':bank.BASE_AGENT_WIDTH,
            'ability_parameters_per_adapter':bank.BASE_ABILITY_WIDTH,
            'agent_training_stages':2,'ability_training_stages':2,
            'max_steps_per_stage':32,
            'historical_original_trained_banks_verified':False,
            'trained_large_banks':False,'production_authority':False,
            'data_source':'synthetic generated tasks and original sampled parameters',
            'real_model_updates':True,'automatic_model_promotion':False}


def sha(data): return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def valid(agents_count,steps,seed):
    if type(agents_count) is not int or not 1 <= agents_count <= 10:raise ValueError('1..10 sampled agents only')
    if type(steps) is not int or not 1 <= steps <= 32:raise ValueError('1..32 synthetic steps per stage only')
    if type(seed) is not int or not 1 <= seed <= 2**32-1:raise ValueError('Invalid deterministic seed')


def _model(torch):
    from torch import nn
    class Policy(nn.Module):
        def __init__(self):
            super().__init__()
            self.layers=nn.Sequential(nn.Linear(32,512),nn.GELU(),nn.Linear(512,544),nn.GELU(),nn.Linear(544,208),nn.GELU(),nn.Linear(208,8))
        def forward(self,x):return self.layers(x)
    m=Policy()
    if sum(p.numel() for p in m.parameters())!=bank.BASE_AGENT_WIDTH:
        raise RuntimeError('Unexpected model parameter count')
    return m


def _agent_data(torch,agent,seed,context):
    g=torch.Generator(device='cpu').manual_seed(seed+agent*1103)
    W=torch.randn((32,8),generator=g)*0.115
    def target(x):return x@W+0.07*torch.sin(x[:,:8])+context[:8].reshape(1,8)*0.025
    d1=torch.randn((64,32),generator=g)
    d2=torch.randn((64,32),generator=g)*1.25+1.75
    h1=torch.randn((80,32),generator=g)
    h2=torch.randn((80,32),generator=g)*1.25+1.75
    return [(d1,target(d1)),(d2,target(d2))], [(h1,target(h1)),(h2,target(h2))]


def _ability_data(torch,seed):
    # This deterministic non-market teacher is intentionally independent of
    # the original unverified weights. It is not evidence of learned abilities.
    ids=torch.arange(1,10001,dtype=torch.float32).reshape(-1,1)
    dims=torch.arange(1,33,dtype=torch.float32).reshape(1,-1)
    target_theta=0.16*torch.sin(ids*0.0153+dims*0.171)
    g=torch.Generator(device='cpu').manual_seed(seed+987654)
    training=[torch.randn((32,16),generator=g),torch.randn((32,16),generator=g)*1.2+0.55]
    holdout=[torch.randn((32,20),generator=g),torch.randn((32,20),generator=g)*1.2+0.55]
    return target_theta, training,holdout


def _mse(torch,m,y):return float(torch.nn.functional.mse_loss(m,y).item())


def train(archive,out,agents_count=10,steps=8,seed=1337,*,authorize=False):
    valid(agents_count,steps,seed)
    if authorize is not True:raise PermissionError('Explicit --authorize-synthetic-training required')
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise FileExistsError('Quarantined output must be empty')
    proof=bank.verify_sample(archive)
    import numpy as np
    import torch
    from torch.nn.utils import parameters_to_vector,vector_to_parameters
    torch.set_num_threads(1)
    with zipfile.ZipFile(archive) as z:
        agent_bytes=z.read('agent_weights.fp16')
        ability_bytes=z.read('ability_weights.fp16')
    raw_ability=np.frombuffer(ability_bytes,dtype='<f2').astype('float32').reshape(10000,32)
    if not np.isfinite(raw_ability).all():raise ValueError('Non-finite source ability parameters')
    agents=[]
    # Fail closed on any nonfinite source agent bytes before creating outputs.
    for agent in range(1,agents_count+1):
        raw=agent_bytes[(agent-1)*bank.BASE_AGENT_WIDTH*2:agent*bank.BASE_AGENT_WIDTH*2]
        if not np.isfinite(np.frombuffer(raw,dtype='<f2')).all():raise ValueError('Non-finite source agent parameters')
        agents.append(raw)
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for idx,raw in enumerate(agents,1):
        context=torch.from_numpy(raw_ability[(idx-1)*1000:idx*1000].mean(axis=0).copy())
        stage_data,heldout=_agent_data(torch,idx,seed,context)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(seed+idx)
            model=_model(torch)
            vector_to_parameters(torch.from_numpy(np.frombuffer(raw,dtype='<f2').astype('float32').copy()),model.parameters())
            with torch.no_grad():before=[_mse(torch,model(x),y) for x,y in heldout]
            opt=torch.optim.AdamW(model.parameters(),lr=0.0007,weight_decay=0)
            for data_x,data_y in stage_data:
                for _ in range(steps):
                    opt.zero_grad(set_to_none=True)
                    loss=torch.nn.functional.mse_loss(model(data_x),data_y)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
                    opt.step()
            vector=parameters_to_vector(model.parameters()).detach().numpy().astype('<f2')
            if not np.isfinite(vector).all():raise RuntimeError('Non-finite trained agent parameters')
            saved=_model(torch)
            vector_to_parameters(torch.from_numpy(vector.astype('float32').copy()),saved.parameters())
            with torch.no_grad():after=[_mse(torch,saved(x),y) for x,y in heldout]
        name=f'AG-{idx:05d}.synthetic_v25.fp16'
        with (out/name).open('xb') as f:
            f.write(vector.tobytes());f.flush();os.fsync(f.fileno())
        records.append({'agent':idx,'source_sha256':sha(raw),'candidate_sha256':sha(vector.tobytes()),
                        'candidate_path':name,'gradient_steps':steps*2,'parameters':bank.BASE_AGENT_WIDTH,
                        'stage_count':2,'holdout_iid_before':before[0],'holdout_iid_after':after[0],
                        'holdout_shift_before':before[1],'holdout_shift_after':after[1],
                        'candidate_improved_iid':after[0]<before[0],
                        'candidate_improved_shift':after[1]<before[1],
                        'promotion':'QUARANTINED'})
    # Full 10,000 ability subset receives real vectorized gradient updates.
    target,training,heldout=_ability_data(torch,seed)
    theta=torch.nn.Parameter(torch.from_numpy(raw_ability.copy()))
    with torch.no_grad():
        before_a=[_mse(torch,theta@h,target@h) for h in heldout]
    opt=torch.optim.AdamW([theta],lr=0.002,weight_decay=0)
    for feature in training:
        label=target@feature
        for _ in range(steps):
            opt.zero_grad(set_to_none=True)
            loss=torch.nn.functional.mse_loss(theta@feature,label)
            loss.backward()
            opt.step()
    ability_candidate=theta.detach().numpy().astype('<f2')
    if not np.isfinite(ability_candidate).all():raise RuntimeError('Non-finite trained ability parameters')
    q=torch.from_numpy(ability_candidate.astype('float32'))
    with torch.no_grad():after_a=[_mse(torch,q@h,target@h) for h in heldout]
    ability_file='abilities-10000.synthetic_v25.fp16'
    with (out/ability_file).open('xb') as f:
        f.write(ability_candidate.tobytes());f.flush();os.fsync(f.fileno())
    if sha(Path(archive).read_bytes())!=proof['source_archive_sha256']:
        raise RuntimeError('Original checkpoint mutated during training')
    report={'schema':SCHEMA,'status':'QUARANTINED_RESEARCH_CANDIDATES',
            'source_archive_sha256':proof['source_archive_sha256'],
            'source_import_status':proof['source_import_status'],
            'training_provenance_independently_attested':False,
            'original_checkpoint_modified':False,
            'agent_count':agents_count,'ability_count':10_000,
            'gradient_steps_per_stage':steps,'stages':2,'seed':seed,
            'agent_records':records,
            'ability_result':{'candidate_path':ability_file,
                'source_sha256':sha(ability_bytes),'candidate_sha256':sha(ability_candidate.tobytes()),
                'parameters_per_adapter':32,'adapter_count':10_000,
                'gradient_steps_per_adapter':steps*2,
                'holdout_iid_before':before_a[0],'holdout_iid_after':after_a[0],
                'holdout_shift_before':before_a[1],'holdout_shift_after':after_a[1],
                'candidate_improved_iid':after_a[0]<before_a[0],
                'candidate_improved_shift':after_a[1]<before_a[1]},
            'model_intelligence_certified':False,
            'market_profitability_certified':False,
            'target_30gb_agent_bank_trained':False,
            'target_10gb_ability_bank_trained':False,
            'production_authority':False,'auto_promote':False}
    report['receipt_sha256']=sha(canonical(report))
    with (out/'SYNTHETIC_TRAINING_REPORT_V25.json').open('x') as f:
        json.dump(report,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    return report


def verify(archive,out):
    """Replay every stored FP16 candidate against deterministic independent holdouts.

    This is an independent *scoring run*, not a cryptographically independent
    model identity signature and not proof of any external domain expertise.
    """
    proof=bank.verify_sample(archive)
    out=Path(out)
    report=json.loads((out/'SYNTHETIC_TRAINING_REPORT_V25.json').read_text())
    r=dict(report);digest=r.pop('receipt_sha256',None)
    if digest!=sha(canonical(r)) or report.get('schema')!=SCHEMA or report.get('production_authority') is not False or report.get('auto_promote') is not False:
        raise ValueError('Invalid training receipt')
    if proof['source_archive_sha256']!=report.get('source_archive_sha256') or report.get('original_checkpoint_modified') is not False:
        raise ValueError('Source lineage mismatch')
    valid(report['agent_count'],report['gradient_steps_per_stage'],report['seed'])
    if len(report['agent_records'])!=report['agent_count'] or report.get('ability_count')!=10_000:
        raise ValueError('Incomplete candidate coverage')
    with zipfile.ZipFile(archive) as z:
        base_agents=z.read('agent_weights.fp16')
        base_abilities=z.read('ability_weights.fp16')
    import numpy as np
    import torch
    from torch.nn.utils import vector_to_parameters
    torch.set_num_threads(1)
    ability_source=np.frombuffer(base_abilities,dtype='<f2').astype('float32').reshape(10000,32)
    metric_keys=['holdout_iid_before','holdout_iid_after','holdout_shift_before','holdout_shift_after']
    def compare_reported(row,values,label):
        for key,actual in zip(metric_keys,values):
            observed=row.get(key)
            if type(observed) not in (float,int) or not math.isfinite(observed) or abs(observed-actual)>0.00001:
                raise ValueError(f'Replayed holdout metric mismatch: {label} {key}')
        if row.get('candidate_improved_iid') is not (values[1]<values[0]) or row.get('candidate_improved_shift') is not (values[3]<values[2]):
            raise ValueError(f'Improvement status mismatch: {label}')
    for i,row in enumerate(report['agent_records'],1):
        name=f'AG-{i:05d}.synthetic_v25.fp16'
        if row['agent']!=i or row['candidate_path']!=name or row['gradient_steps']!=report['gradient_steps_per_stage']*2:
            raise ValueError('Agent candidate row mismatch')
        cand=out/name
        if cand.is_symlink() or not cand.is_file():raise ValueError('Symlink or missing candidate prohibited')
        raw=cand.read_bytes()
        source=base_agents[(i-1)*bank.BASE_AGENT_WIDTH*2:i*bank.BASE_AGENT_WIDTH*2]
        if len(raw)!=bank.BASE_AGENT_WIDTH*2 or sha(raw)!=row['candidate_sha256'] or sha(source)!=row['source_sha256']:
            raise ValueError('Agent source or candidate hash mismatch')
        context=torch.from_numpy(ability_source[(i-1)*1000:i*1000].mean(axis=0).copy())
        _,heldout=_agent_data(torch,i,report['seed'],context)
        def restored(weights):
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(report['seed']+i)
                model=_model(torch)
                vector_to_parameters(torch.from_numpy(np.frombuffer(weights,dtype='<f2').astype('float32').copy()),model.parameters())
            return model
        initial=restored(source);candidate=restored(raw)
        with torch.no_grad():
            b=[_mse(torch,initial(x),y) for x,y in heldout]
            a=[_mse(torch,candidate(x),y) for x,y in heldout]
        compare_reported(row,(b[0],a[0],b[1],a[1]),f'agent {i}')
    b=report['ability_result']
    if b['candidate_path']!='abilities-10000.synthetic_v25.fp16' or b['adapter_count']!=10_000 or b['gradient_steps_per_adapter']!=report['gradient_steps_per_stage']*2:
        raise ValueError('Ability candidate coverage mismatch')
    ability_path=out/b['candidate_path']
    if ability_path.is_symlink() or not ability_path.is_file():raise ValueError('Symlink or missing ability candidate prohibited')
    raw=ability_path.read_bytes()
    if len(raw)!=10_000*32*2 or sha(raw)!=b['candidate_sha256'] or sha(base_abilities)!=b['source_sha256']:
        raise ValueError('Ability source or candidate hash mismatch')
    target,_,heldout=_ability_data(torch,report['seed'])
    original=torch.from_numpy(ability_source)
    candidate=torch.from_numpy(np.frombuffer(raw,dtype='<f2').astype('float32').reshape(10000,32).copy())
    with torch.no_grad():
        bb=[_mse(torch,original@h,target@h) for h in heldout]
        aa=[_mse(torch,candidate@h,target@h) for h in heldout]
    compare_reported(b,(bb[0],aa[0],bb[1],aa[1]),'ability bank')
    return {'source_hash_valid':True,'candidate_hashes_valid':True,
            'agents':len(report['agent_records']),'abilities':10_000,
            'independently_recomputed_holdout_metrics':True,
            'model_identity_attested':False,'promotion_allowed':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='cmd',required=True)
    s.add_parser('plan')
    a=s.add_parser('train');a.add_argument('--archive',required=True);a.add_argument('--out',required=True)
    a.add_argument('--agents-count',type=int,default=10);a.add_argument('--steps',type=int,default=8)
    a.add_argument('--seed',type=int,default=1337);a.add_argument('--authorize-synthetic-training',action='store_true')
    v=s.add_parser('verify');v.add_argument('--archive',required=True);v.add_argument('--out',required=True)
    x=p.parse_args()
    if x.cmd=='plan':response=plan()
    elif x.cmd=='train':response=train(x.archive,x.out,x.agents_count,x.steps,x.seed,authorize=x.authorize_synthetic_training)
    else:response=verify(x.archive,x.out)
    print(json.dumps(response,sort_keys=True,indent=2))

if __name__=='__main__':main()
