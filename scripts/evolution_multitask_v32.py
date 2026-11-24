#!/usr/bin/env python3
"""MYRIAD v3.2 constrained, quarantined multi-task gradient training.

Task-described nonlinear regression is a synthetic transfer experiment only.
The blind coefficient-composition split must beat BOTH the zero and linear-only
baselines; a novel cubic family is an explicit falsification control. This is
not general intelligence, market validation, or source-weight attestation.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,re,zipfile
from pathlib import Path

SCHEMA='myriad.synthetic_multitask_transfer.v32'
SOURCE='myriad.synthetic_neural_curriculum.v25'
N_PARAMS=411000


def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(record):return json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def valid(agents,steps,seed):
    if type(agents) is not int or not 1<=agents<=10:raise ValueError('Only 1..10 preserved agents allowed')
    if type(steps) is not int or not 1<=steps<=256:raise ValueError('1..256 gradient steps allowed')
    if type(seed) is not int or not 1<=seed<=2**32-1:raise ValueError('Invalid seed')


def batch(torch,seed,agent,split,n):
    """No train/holdout seed overlap. Task coefficients are observed at input time."""
    splits={'train':17,'iid':29,'cross':43,'novel':67}
    if split not in splits or type(n) is not int or not 1<=n<=4096:raise ValueError('Invalid split or bound')
    g=torch.Generator(device='cpu').manual_seed(seed*1009+agent*10007+splits[split])
    z=torch.randn(n,8,generator=g)*(1.0 if split in ('train','iid') else 1.24)
    a=.6+torch.rand(n,8,generator=g)*1.0
    b=.45+torch.rand(n,8,generator=g)*.9
    c=.4+torch.rand(n,8,generator=g)*.7
    sign=(torch.randint(0,2,(n,1),generator=g,dtype=torch.int64)*2-1).float()
    a=a*sign
    if split=='cross':
        # Composition withheld from training: both factors oppose the base.
        b=-b*sign;c=-c*sign
    elif split=='train':
        # Three distinct observed task families teach independent factor effects.
        # The fourth (both opposing) is genuinely absent from training.
        family=torch.randint(0,3,(n,1),generator=g)
        b=b*sign*torch.where(family==1,-1.0,1.0)
        c=c*sign*torch.where(family==2,-1.0,1.0)
    else:
        b=b*sign;c=c*sign
    x=torch.cat([z,a,b,c],dim=1)
    if split=='novel':
        # Unsupported target operator: cubic instead of base quadratic/tanh mix.
        y=a*z*z*z/3+b*torch.sin(z)+c*torch.tanh(z)
    else:y=a*z+b*torch.tanh(z)+c*(z*z-1)
    return x,y


def _model(torch):
    from evolution_neural_curriculum_v25 import _model as arch
    return arch(torch)


def _load_model(torch,raw):
    import numpy as np
    from torch.nn.utils import vector_to_parameters
    if len(raw)!=N_PARAMS*2:raise ValueError('Invalid agent FP16 checkpoint size')
    weights=np.frombuffer(raw,dtype='<f2').astype('float32')
    if not np.isfinite(weights).all():raise ValueError('Nonfinite original or candidate')
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(414)
        model=_model(torch)
        vector_to_parameters(torch.from_numpy(weights.copy()),model.parameters())
    return model


def _model_bytes(torch,model):
    import numpy as np
    from torch.nn.utils import parameters_to_vector
    weights=parameters_to_vector(model.parameters()).detach().numpy().astype('<f2')
    if not np.isfinite(weights).all():raise RuntimeError('Nonfinite training output')
    return weights.tobytes()


def _metrics(torch,model,seed,agent):
    out={}
    model.eval()
    with torch.no_grad():
        for split in ('iid','cross','novel'):
            x,y=batch(torch,seed,agent,split,256)
            actual=model(x)
            if not torch.isfinite(actual).all():raise ValueError('Nonfinite agent output')
            out[split]={
                'model_mse':float(torch.mean((actual-y)**2)),
                'zero_mse':float(torch.mean(y*y)),
                'linear_baseline_mse':float(torch.mean((x[:,8:16]*x[:,:8]-y)**2)),
                'input_sha256':sha(x.numpy().tobytes())}
    return out


def _candidate_path(out,agent):
    return Path(out)/f'AG-{agent:05d}.synthetic_multitask_v32.fp16'


def train(archive,out,agents=10,steps=160,seed=20261124,authorize=False):
    valid(agents,steps,seed)
    if authorize is not True:raise PermissionError('Explicit synthetic training approval required')
    import torch
    torch.set_num_threads(1)
    archive=Path(archive)
    if archive.is_symlink() or not archive.is_file():raise FileNotFoundError('Pinned v2.5 checkpoint missing')
    out=Path(out)
    if out.exists():raise FileExistsError('Fresh private output directory required')
    if archive.stat().st_size>15_000_000:raise ValueError('Oversized source archive')
    origin_hash=sha(archive.read_bytes())
    with zipfile.ZipFile(archive) as z:
        report=json.loads(z.read('SYNTHETIC_TRAINING_REPORT_V25.json'))
        if report.get('schema')!=SOURCE or len(report.get('agent_records',[]))!=10 or report.get('production_authority') is not False:raise ValueError('Source not correct quarantined cohort')
        names={i.filename for i in z.infolist()}
        if len(names)!=len(z.infolist()) or any(z.getinfo(name).file_size>1_000_000 for name in names):raise ValueError('Unsafe source archive')
        raw=[z.read(f'AG-{n:05d}.synthetic_v25.fp16') for n in range(1,agents+1)]
        for i,b in enumerate(raw):
            if sha(b)!=report['agent_records'][i]['candidate_sha256']:raise ValueError('Checkpoint source digest mismatch')
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for agent,weights in enumerate(raw,1):
        model=_load_model(torch,weights)
        before=_metrics(torch,model,seed,agent)
        x,y=batch(torch,seed,agent,'train',2048)
        g=torch.Generator(device='cpu').manual_seed(seed+agent*107)
        opt=torch.optim.AdamW(model.parameters(),lr=.0007,weight_decay=0)
        model.train()
        for _ in range(steps):
            index=torch.randint(0,len(x),(128,),generator=g)
            opt.zero_grad(set_to_none=True)
            loss=torch.nn.functional.mse_loss(model(x[index]),y[index])
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            opt.step()
        candidate_bytes=_model_bytes(torch,model)
        saved=_load_model(torch,candidate_bytes)
        after=_metrics(torch,saved,seed,agent)
        file=_candidate_path(out,agent)
        with file.open('xb') as f:
            f.write(candidate_bytes);f.flush();os.fsync(f.fileno())
        rows.append({'agent':agent,'source_sha256':sha(weights),'candidate_sha256':sha(candidate_bytes),
                     'candidate_filename':file.name,'step_count':steps,'source_metrics':before,'candidate_metrics':after,
                     'cross_beats_both':after['cross']['model_mse']<min(after['cross']['zero_mse'],after['cross']['linear_baseline_mse']),
                     'novel_beats_both':after['novel']['model_mse']<min(after['novel']['zero_mse'],after['novel']['linear_baseline_mse'])})
    result={'schema':SCHEMA,'source':SOURCE,'origin_archive_sha256':origin_hash,'seed':seed,'agents':agents,'steps':steps,
            'rows':rows,'research_review_eligible':all(x['cross_beats_both'] and x['novel_beats_both'] for x in rows),
            'production_authority':False,'broker_orders':False,'source_provenance_independently_attested':False,
            'trained_full_historical_banks':False,'dataset_type':'synthetic coefficient/teacher functions only',
            'blind_splits':'deterministic disjoint pseudo-random seeds; same known target-generator family for iid/cross'}
    result['receipt_sha256']=sha(canonical(result))
    (out/'SYNTHETIC_TRANSFER_V32.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if sha(archive.read_bytes())!=origin_hash:raise RuntimeError('Source modified')
    return result


def verify(archive,out):
    import torch
    torch.set_num_threads(1)
    archive=Path(archive);out=Path(out)
    record=json.loads((out/'SYNTHETIC_TRANSFER_V32.json').read_text())
    payload=dict(record);digest=payload.pop('receipt_sha256',None)
    if digest!=sha(canonical(payload)) or record.get('schema')!=SCHEMA or record.get('production_authority') is not False:
        raise ValueError('Invalid or forged transfer receipt')
    valid(record['agents'],record['steps'],record['seed'])
    if len(record['rows'])!=record['agents'] or sha(archive.read_bytes())!=record['origin_archive_sha256']:
        raise ValueError('Source cohort changed')
    known={_candidate_path(out,i).name for i in range(1,record['agents']+1)}|{'SYNTHETIC_TRANSFER_V32.json'}
    if {p.name for p in out.iterdir()}!=known:raise ValueError('Untracked candidate files')
    with zipfile.ZipFile(archive) as z:
        for agent,row in enumerate(record['rows'],1):
            raw=z.read(f'AG-{agent:05d}.synthetic_v25.fp16')
            candidate=_candidate_path(out,agent)
            if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_size!=N_PARAMS*2:
                raise ValueError('Invalid saved candidate')
            b=candidate.read_bytes()
            if row['agent']!=agent or row['candidate_filename']!=candidate.name or sha(raw)!=row['source_sha256'] or sha(b)!=row['candidate_sha256'] or row['step_count']!=record['steps']:
                raise ValueError('Invalid source candidate digest or mapping')
            for key,model_bytes in [('source_metrics',raw),('candidate_metrics',b)]:
                actual=_metrics(torch,_load_model(torch,model_bytes),record['seed'],agent)
                reported=row[key]
                for split in ('iid','cross','novel'):
                    for metric in ('model_mse','zero_mse','linear_baseline_mse'):
                        val=reported[split][metric]
                        if type(val) not in (int,float) or not math.isfinite(val) or abs(val-actual[split][metric])>2e-5:
                            raise ValueError('Replayed metric mismatch')
                    if reported[split]['input_sha256']!=actual[split]['input_sha256']:raise ValueError('Holdout input hash mismatch')
            for split,label in [('cross','cross_beats_both'),('novel','novel_beats_both')]:
                r=row['candidate_metrics'][split]
                if row[label] is not (r['model_mse']<min(r['zero_mse'],r['linear_baseline_mse'])):raise ValueError('Baseline verdict mismatch')
    if record['research_review_eligible'] is not all(r['cross_beats_both'] and r['novel_beats_both'] for r in record['rows']):
        raise ValueError('Forged aggregate verdict')
    return {'verified':True,'agents':record['agents'],'cross_beats_both':sum(r['cross_beats_both'] for r in record['rows']),
            'novel_beats_both':sum(r['novel_beats_both'] for r in record['rows']),
            'research_review_eligible':record['research_review_eligible'],'production_authority':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);q=p.add_subparsers(dest='cmd',required=True)
    x=q.add_parser('train');x.add_argument('--archive',required=True);x.add_argument('--out',required=True)
    x.add_argument('--agents',type=int,default=10);x.add_argument('--steps',type=int,default=160);x.add_argument('--seed',type=int,default=20261124);x.add_argument('--authorize-synthetic-training',action='store_true')
    v=q.add_parser('verify');v.add_argument('--archive',required=True);v.add_argument('--out',required=True)
    a=p.parse_args()
    if a.cmd=='train':r=train(a.archive,a.out,a.agents,a.steps,a.seed,a.authorize_synthetic_training)
    else:r=verify(a.archive,a.out)
    print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
