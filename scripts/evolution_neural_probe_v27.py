#!/usr/bin/env python3
"""Independent-input CPU neural inference on quarantined v2.5 FP16 checkpoints.

No live trading, general intelligence, original historical training attestation,
model promotion, remote model calls or hidden execution. Only synthetic teacher
function generalization to *fresh input samples* (same teacher/task family).
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
import evolution_neural_curriculum_v25 as curriculum

SCHEMA='myriad.synthetic_neural_probe.v27'
AGENT_BYTES=bank.BASE_AGENT_WIDTH*bank.DTYPE_BYTES
ABILITY_BYTES=10_000*bank.BASE_ABILITY_WIDTH*bank.DTYPE_BYTES


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode('utf-8')


def read_strict_json(text):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate JSON evidence field')
            result[key]=value
        return result
    return json.loads(text,object_pairs_hook=unique,parse_constant=lambda s: (_ for _ in ()).throw(ValueError('Nonfinite JSON value')))


def check_seed(training_seed, probe_seed):
    if type(probe_seed) is not int or not 100_000 <= probe_seed <= 2**32-1:
        raise ValueError('Probe requires an independent fresh seed')
    if type(training_seed) is not int or not 0 <= training_seed < 2**32:
        raise ValueError('Invalid training seed')
    if probe_seed == training_seed or any(probe_seed == training_seed+i*1103 for i in range(1,11)):
        raise ValueError('Probe RNG seed collides with model training RNG')
    return probe_seed


def check_file_digest(path, expected, size):
    path=Path(path)
    if not path.is_file() or path.is_symlink() or type(size) is not int or size<=0 or path.stat().st_size!=size:
        raise ValueError('Missing, symlinked, or wrong-sized saved model weights')
    raw=path.read_bytes()
    actual=sha(raw)
    if not isinstance(expected,str) or len(expected)!=64 or actual !=expected:
        raise ValueError('Saved model weight digest mismatch')
    return actual


def proof_metric(before,after):
    for v in (before,after):
        if type(v) not in (float,int) or not math.isfinite(v) or v < 0:
            raise ValueError('Invalid synthetic neural model error')
    return {'before_mse':float(before),'after_mse':float(after),'candidate_improved':after<before}


def assert_close_recomputed(observed, expected):
    if type(observed) not in (float,int) or type(observed) is bool or not math.isfinite(observed):
        raise ValueError('Nonfinite or invalid observed neural score')
    if not math.isclose(observed,expected,rel_tol=1e-5,abs_tol=2e-6):
        raise ValueError('Replayed independent-input neural score mismatch')


def finalize_probe(payload, seed):
    if type(payload) is not dict:raise ValueError('Malformed research payload')
    result={'schema':SCHEMA,'probe_seed':seed,'source_hash':payload.get('source_hash'),
            'source_import_status':payload.get('source_import_status','imported_unverified'),
            'training_seed':payload.get('training_seed'),
            'training_receipt_sha256':payload.get('training_receipt_sha256'),
            'agent_evaluations':payload.get('agent_evaluations',[]),
            'ability_evaluation':payload.get('ability_evaluation'),
            'model_identity_authenticated':False,'production_authority':False,
            'trading_alpha_certified':False,'automatic_promotion':False,
            'model_weights_published':False,
            'scope':'fresh synthetic input; same seeded teacher/task family, not real-world transfer'}
    result['receipt_sha256']=sha(canonical(result))
    return result


def verify_seal(report):
    if not isinstance(report,dict) or report.get('schema')!=SCHEMA:raise ValueError('Wrong neural probe receipt schema')
    raw=dict(report);digest=raw.pop('receipt_sha256',None)
    if not isinstance(digest,str) or digest!=sha(canonical(raw)):
        raise ValueError('Synthetic neural probe receipt SHA mismatch')
    for k in ('model_identity_authenticated','production_authority','trading_alpha_certified','automatic_promotion','model_weights_published'):
        if report.get(k) is not False:
            raise ValueError('Unqualified neural promotion or model identity claim')
    check_seed(report.get('training_seed',1337) if report.get('training_seed') is not None else 1337,report['probe_seed'])
    if not isinstance(report['agent_evaluations'],list):raise ValueError('Invalid research rows')
    return True


def write_receipt(path,report):
    verify_seal(report)
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
        f.write(canonical(report)+b'\n');f.flush();os.fsync(f.fileno())


def _scored_models(archive,candidates,probe_seed):
    import numpy as np
    import torch
    from torch.nn.utils import vector_to_parameters
    torch.set_num_threads(1)
    candidates=Path(candidates)
    report=read_strict_json((candidates/'SYNTHETIC_TRAINING_REPORT_V25.json').read_text())
    if report.get('schema')!=curriculum.SCHEMA or report.get('auto_promote') is not False or report.get('production_authority') is not False:
        raise ValueError('Invalid original synthetic training report')
    raw_report=dict(report)
    if sha(curriculum.canonical({k:v for k,v in raw_report.items() if k!='receipt_sha256'}))!=report.get('receipt_sha256'):
        raise ValueError('Unverified v2.5 source report')
    training_seed=report['seed']
    check_seed(training_seed,probe_seed)
    evidence=bank.verify_sample(archive)
    if evidence['source_archive_sha256']!=report.get('source_archive_sha256'):
        raise ValueError('Original archive digest disagrees with training ledger')
    if report.get('agent_count')!=10 or len(report.get('agent_records',[]))!=10 or report.get('ability_count')!=10000:
        raise ValueError('Incomplete preserved candidate coverage')
    with zipfile.ZipFile(archive) as z:
        original_agents=z.read('agent_weights.fp16')
        original_abilities=z.read('ability_weights.fp16')
    ability_source=np.frombuffer(original_abilities,dtype='<f2').astype('float32').reshape(10000,32)
    rows=[]
    for agent,receipt in enumerate(report['agent_records'],1):
        path=candidates/f'AG-{agent:05d}.synthetic_v25.fp16'
        if receipt.get('agent')!=agent or path.name!=receipt.get('candidate_path') or receipt.get('promotion')!='QUARANTINED':
            raise ValueError('Model receipt is incorrectly ordered, promoted or renamed')
        source=original_agents[(agent-1)*AGENT_BYTES:agent*AGENT_BYTES]
        if sha(source)!=receipt.get('source_sha256'):
            raise ValueError('Agent source checkpoint mismatch')
        check_file_digest(path,receipt.get('candidate_sha256'),AGENT_BYTES)
        candidate=path.read_bytes()
        context=torch.from_numpy(ability_source[(agent-1)*1000:agent*1000].mean(axis=0).copy())
        # Match the teacher function of v2.5, but generate inputs using a fresh,
        # independently seeded RNG that never produced its train or holdout rows.
        generator=torch.Generator(device='cpu').manual_seed(training_seed+agent*1103)
        teacher_W=torch.randn((32,8),generator=generator)*0.115
        input_gen=torch.Generator(device='cpu').manual_seed(probe_seed+agent*29)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(training_seed+agent)
            baseline=curriculum._model(torch)
            vector_to_parameters(torch.from_numpy(np.frombuffer(source,dtype='<f2').astype('float32').copy()),baseline.parameters())
            trained=curriculum._model(torch)
            vector_to_parameters(torch.from_numpy(np.frombuffer(candidate,dtype='<f2').astype('float32').copy()),trained.parameters())
        metrics=[]
        for shifted in (False,True):
            samples=torch.randn((96,32),generator=input_gen)
            if shifted:samples=samples*1.25+1.75
            target=samples@teacher_W+0.07*torch.sin(samples[:,:8])+context[:8].reshape(1,8)*0.025
            with torch.no_grad():
                old=curriculum._mse(torch,baseline(samples),target)
                newer=curriculum._mse(torch,trained(samples),target)
            metrics.append({'input_sha256':sha(samples.numpy().tobytes()),**proof_metric(old,newer)})
        rows.append({'agent':agent,'source_sha256':sha(source),
                     'candidate_sha256':sha(candidate),'standard':metrics[0],
                     'shifted_input':metrics[1]})
    source_sha=sha(original_abilities)
    ability_receipt=report['ability_result']
    a_path=candidates/'abilities-10000.synthetic_v25.fp16'
    if ability_receipt.get('source_sha256')!=source_sha or ability_receipt.get('candidate_path')!=a_path.name:
        raise ValueError('Ability source/candidate labels mismatch')
    check_file_digest(a_path,ability_receipt.get('candidate_sha256'),ABILITY_BYTES)
    trained_abilities=torch.from_numpy(np.frombuffer(a_path.read_bytes(),dtype='<f2').astype('float32').reshape(10000,32).copy())
    original_tensor=torch.from_numpy(ability_source)
    teacher,_,_=curriculum._ability_data(torch,training_seed)
    rng=torch.Generator(device='cpu').manual_seed(probe_seed+1000)
    ability_metrics=[]
    for shifted in (False,True):
        h=torch.randn((32,30),generator=rng)
        if shifted:h=h*1.20+0.55
        y=teacher@h
        with torch.no_grad():
            old=curriculum._mse(torch,original_tensor@h,y)
            new=curriculum._mse(torch,trained_abilities@h,y)
        ability_metrics.append({'input_sha256':sha(h.numpy().tobytes()),**proof_metric(old,new)})
    return {'source_hash':evidence['source_archive_sha256'],
            'source_import_status':evidence.get('source_import_status','imported_unverified'),
            'training_seed':training_seed,'training_receipt_sha256':report['receipt_sha256'],
            'agent_evaluations':rows,
            'ability_evaluation':{'candidate_sha256':sha(a_path.read_bytes()),
                                 'source_sha256':source_sha,'standard':ability_metrics[0],
                                 'shifted_input':ability_metrics[1]}}


def run(archive,candidates,out,seed=900000,*,authorize=False):
    if authorize is not True:raise PermissionError('Explicit authorization for local neural inference required')
    output=Path(out)
    if output.exists():raise FileExistsError('Never overwrite an earlier neural probe receipt')
    payload=_scored_models(archive,candidates,seed)
    receipt=finalize_probe(payload,seed)
    write_receipt(output,receipt)
    return receipt


def _compare_recomputed(expected,actual,path='root'):
    if type(expected) is not type(actual):
        # JSON numeric scientific evaluation may vary slightly across Torch patch versions.
        if type(expected) not in (int,float) or type(actual) not in (int,float) or type(expected) is bool or type(actual) is bool:
            raise ValueError(f'Independent replay type mismatch at {path}')
    if isinstance(expected,(float,int)) and not isinstance(expected,bool):
        assert_close_recomputed(actual,expected)
    elif isinstance(expected,dict):
        if set(expected)!=set(actual):raise ValueError(f'Evidence columns differ at {path}')
        for k,v in expected.items():_compare_recomputed(v,actual[k],path+'.'+k)
    elif isinstance(expected,list):
        if len(expected)!=len(actual):raise ValueError(f'Evidence row coverage mismatch at {path}')
        for i,(x,y) in enumerate(zip(expected,actual)):_compare_recomputed(x,y,f'{path}[{i}]')
    elif expected!=actual:
        raise ValueError(f'Independent model replay differs at {path}')


def verify(archive,candidates,receipt):
    data=read_strict_json(Path(receipt).read_text())
    verify_seal(data)
    expected=finalize_probe(_scored_models(archive,candidates,data['probe_seed']),data['probe_seed'])
    old_hash=expected.pop('receipt_sha256');provided=data.pop('receipt_sha256')
    _compare_recomputed(expected,data)
    return {'independently_replayed_from_fp16':True,
            'agent_networks_replayed':len(expected['agent_evaluations']),
            'ability_adapters_replayed':10000,
            'new_input_seed':data['probe_seed'],
            'no_source_weights_modified':True,'full_original_weight_bank_verified':False,
            'trading_alpha_certified':False,'production_authority':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='cmd',required=True)
    for name in ('run','verify'):
        p=sub.add_parser(name)
        p.add_argument('--archive',required=True)
        p.add_argument('--candidates',required=True)
        p.add_argument('--receipt',required=True)
        if name=='run':
            p.add_argument('--seed',type=int,default=900000)
            p.add_argument('--authorize',action='store_true')
    a=vars(parser.parse_args())
    command=a.pop('cmd')
    result=run(a['archive'],a['candidates'],a['receipt'],a['seed'],authorize=a['authorize']) if command=='run' else verify(a['archive'],a['candidates'],a['receipt'])
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__':main()
