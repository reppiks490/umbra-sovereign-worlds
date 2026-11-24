"""Matched-budget synthetic distribution intervention; private immutable candidates only."""
import argparse,ctypes,json,math,os,shutil,uuid
from pathlib import Path
import evolution_agent_bank_v51 as base
import evolution_task_adapter_v61 as prior
import evolution_adapter_stress_v77 as stress

TEST_FAMILIES=('bimodal','heteroskedastic','block_correlation','asymmetric_sparse')
TRAIN_SAMPLES=2048
TEST_SAMPLES=256
SEEDS=4
WIDTH=prior.PARAMETERS*2
FIELDS=('mixed','iid','prior','quadratic','source','zero','retention_delta')
SCHEMA='myriad.adapter_intervention.v80'

def bounds(agent,steps):
    if type(agent) is not int or not 1<=agent<=base.TARGET or type(steps) is not int or not 1<=steps<=512:
        raise ValueError('intervention bounds')
def target(torch,x):
    a,b,c,d=x.split(8,dim=1)
    return torch.sin(a*b)+.3*c*d+.2*torch.tanh(a+d)
def dataset(torch,agent,arm,n=TRAIN_SAMPLES):
    bounds(agent,1)
    if arm not in ('iid','mixed') or type(n) is not int or not 16<=n<=4096 or n%4:raise ValueError('training geometry')
    blocks=[]
    for k in range(4):
        g=torch.Generator().manual_seed(8000000000+agent*4096+k)
        x=torch.randn(n//4,32,generator=g)
        if arm=='mixed':
            if k==1:x=.6*x+.8*torch.randn(n//4,1,generator=g)
            elif k==2:x=x*torch.where(torch.rand(n//4,1,generator=g)<.1,3.,.8)
            elif k==3:x=x*(torch.rand(n//4,32,generator=g)>.55)+.5
        blocks.append(x)
    x=torch.cat(blocks);return x,target(torch,x)
def test_data(torch,agent,family,seed,n=TEST_SAMPLES):
    bounds(agent,1)
    if family not in TEST_FAMILIES or type(seed) is not int or not 0<=seed<SEEDS or type(n) is not int or not 64<=n<=1024:raise ValueError('test geometry')
    g=torch.Generator().manual_seed(8100000000+agent*4096+seed*4+TEST_FAMILIES.index(family))
    x=torch.randn(n,32,generator=g)
    if family=='bimodal':
        x=x*.7+torch.where(torch.rand(n,1,generator=g)<.5,-1.25,1.25)
    elif family=='heteroskedastic':
        x=x*(.4+1.6*torch.rand(n,32,generator=g))
    elif family=='block_correlation':
        x=.55*x+.85*torch.randn(n,4,generator=g).repeat_interleave(8,dim=1)-.2
    else:
        x=x*(torch.rand(n,32,generator=g)>.7)+torch.linspace(-.8,.8,32)
    return x,target(torch,x)
def summarize(rows):
    if not isinstance(rows,list) or len(rows)!=len(TEST_FAMILIES)*SEEDS:raise ValueError('incomplete design')
    seen=set();wins=iid=old=retention=0;families={}
    for r in rows:
        if not isinstance(r,dict) or set(r)!=set(FIELDS)|{'family','seed'} or r['family'] not in TEST_FAMILIES or type(r['seed']) is not int or not 0<=r['seed']<SEEDS or any(type(r[k]) not in (int,float) or not math.isfinite(r[k]) or r[k]<0 for k in FIELDS):
            raise ValueError('invalid observation')
        key=(r['family'],r['seed'])
        if key in seen:raise ValueError('duplicate observation')
        seen.add(key)
        w=r['mixed']<min(r[k] for k in ('iid','prior','quadratic','source','zero'))
        i=r['mixed']<r['iid'];o=r['mixed']<r['prior'];bad=r['retention_delta']!=0
        wins+=int(w);iid+=int(i);old+=int(o);retention+=int(bad)
        f=families.setdefault(r['family'],{'observations':0,'mixed_wins_vs_iid':0,'mixed_wins_vs_all':0,'mixed_mse_sum':0.,'iid_mse_sum':0.})
        f['observations']+=1;f['mixed_wins_vs_iid']+=int(i);f['mixed_wins_vs_all']+=int(w);f['mixed_mse_sum']+=r['mixed'];f['iid_mse_sum']+=r['iid']
    return {'observations':len(rows),'mixed_wins_vs_iid':iid,'mixed_wins_vs_prior':old,'mixed_wins_vs_all':wins,'retention_failures':retention,'families':families}
def restore(torch,agent,raw):
    if len(raw)!=WIDTH:raise ValueError('adapter width')
    v=torch.frombuffer(bytearray(raw),dtype=torch.float16).float()
    if not torch.isfinite(v).all():raise ValueError('nonfinite weights')
    a=prior.model(torch,agent);torch.nn.utils.vector_to_parameters(v,a.parameters());return a
def encode(torch,a):
    v=torch.nn.utils.parameters_to_vector(a.parameters()).detach().half().contiguous()
    if v.numel()!=prior.PARAMETERS or not torch.isfinite(v).all():raise ValueError('adapter geometry')
    return ctypes.string_at(v.data_ptr(),v.numel()*2)
def load(torch,source,old,agent):
    r=prior.verify(source,Path(old)/f'{agent:05d}',True)
    m,origin=prior.load_source(torch,source,agent)
    raw=(Path(old)/f'{agent:05d}'/'adapter.fp16').read_bytes()
    if origin['weight_sha256']!=r['source_sha256'] or base.sha(raw)!=r['adapter_sha256']:raise ValueError('changed parent')
    return m,raw,r
def train_arm(torch,m,raw,agent,steps,arm):
    a=restore(torch,agent,raw);a.train();x,y=dataset(torch,agent,arm)
    with torch.no_grad():target_residual=y-m(x)
    opt=torch.optim.AdamW(a.parameters(),lr=.0005,weight_decay=.01)
    g=torch.Generator().manual_seed(8200000000+agent)
    for _ in range(steps):
        idx=torch.randint(0,len(x),(128,),generator=g);opt.zero_grad(set_to_none=True)
        loss=((a(x[idx])-target_residual[idx])**2).mean();loss.backward()
        torch.nn.utils.clip_grad_norm_(a.parameters(),1.);opt.step()
    return encode(torch,a)
def evaluate(torch,m,old,iid,mixed,agent):
    m.eval();old.eval();iid.eval();mixed.eval();x,y=dataset(torch,agent,'mixed')
    with torch.no_grad():
        beta=stress.fit(torch,x,y,True);rows=[]
        for f in TEST_FAMILIES:
            for seed in range(SEEDS):
                u,v=test_data(torch,agent,f,seed);z=m(u)
                mse=lambda p:float(((p-v)**2).mean())
                rows.append({'family':f,'seed':seed,'mixed':mse(prior.predict(m,mixed,u,'nonlinear')),'iid':mse(prior.predict(m,iid,u,'nonlinear')),'prior':mse(prior.predict(m,old,u,'nonlinear')),'quadratic':mse(stress.features(torch,u.double(),True)@beta),'source':mse(z),'zero':mse(torch.zeros_like(v)),'retention_delta':float((prior.predict(m,mixed,u,'original')-z).abs().max())})
    return rows
def train_compare(source,old,root,agent,steps):
    bounds(agent,steps);root=Path(root);root.mkdir(exist_ok=True);dest=root/f'{agent:05d}'
    if dest.exists():raise FileExistsError('immutable intervention')
    if root.is_symlink() or shutil.disk_usage(root).free<6*1024**3:raise ValueError('storage guard')
    import torch
    torch.set_num_threads(1);m,raw,r=load(torch,source,old,agent)
    i=train_arm(torch,m,raw,agent,steps,'iid');a=train_arm(torch,m,raw,agent,steps,'mixed')
    rows=evaluate(torch,m,restore(torch,agent,raw),restore(torch,agent,i),restore(torch,agent,a),agent)
    receipt={'schema':SCHEMA,'agent':agent,'steps_per_arm':steps,'training_samples_per_arm':TRAIN_SAMPLES,'test_samples':TEST_SAMPLES,'test_seeds':SEEDS,'source_sha256':r['source_sha256'],'prior_sha256':r['adapter_sha256'],'iid_sha256':base.sha(i),'mixed_sha256':base.sha(a),'weight_bytes_per_arm':WIDTH,'observations':rows,'summary':summarize(rows),'production_authority':False,'auto_promote':False,'semantic_mastery_certified':False}
    receipt['receipt_sha256']=base.sha(base.canonical(receipt));temp=root/('.staged-'+uuid.uuid4().hex);temp.mkdir()
    for name,blob in [('iid.fp16',i),('mixed.fp16',a),('receipt.json',base.canonical(receipt)+b'\n')]:
        with (temp/name).open('xb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
    temp.rename(dest);return receipt
def verify(source,old,folder,replay=False):
    p=Path(folder);paths=[p/'receipt.json',p/'iid.fp16',p/'mixed.fp16']
    if p.is_symlink() or not p.is_dir() or any(f.is_symlink() or not f.is_file() for f in paths) or paths[0].stat().st_size>65536 or any(f.stat().st_size!=WIDTH for f in paths[1:]):raise ValueError('invalid intervention artifacts')
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out:raise ValueError('duplicate field')
            out[k]=v
        return out
    r=json.loads(paths[0].read_bytes(),object_pairs_hook=unique)
    fields={'schema','agent','steps_per_arm','training_samples_per_arm','test_samples','test_seeds','source_sha256','prior_sha256','iid_sha256','mixed_sha256','weight_bytes_per_arm','observations','summary','production_authority','auto_promote','semantic_mastery_certified','receipt_sha256'}
    if not isinstance(r,dict) or set(r)!=fields:raise ValueError('invalid receipt fields')
    sig=r.pop('receipt_sha256');agent=r['agent'];bounds(agent,r['steps_per_arm'])
    counts={'training_samples_per_arm':TRAIN_SAMPLES,'test_samples':TEST_SAMPLES,'test_seeds':SEEDS,'weight_bytes_per_arm':WIDTH}
    if p.name!=f'{agent:05d}' or r['schema']!=SCHEMA or any(type(r[k]) is not int or r[k]!=v for k,v in counts.items()) or any(r[k] is not False for k in ('production_authority','auto_promote','semantic_mastery_certified')) or sig!=base.sha(base.canonical(r)) or base.canonical(r['summary'])!=base.canonical(summarize(r['observations'])):raise ValueError('invalid intervention receipt')
    origin=prior.verify(source,Path(old)/f'{agent:05d}')
    i,a=[f.read_bytes() for f in paths[1:]]
    if any(len(v)!=WIDTH for v in (i,a)) or base.sha(i)!=r['iid_sha256'] or base.sha(a)!=r['mixed_sha256'] or origin['source_sha256']!=r['source_sha256'] or origin['adapter_sha256']!=r['prior_sha256']:raise ValueError('lineage mismatch')
    if replay:
        import torch
        torch.set_num_threads(1);m,raw,origin=load(torch,source,old,agent)
        rows=evaluate(torch,m,restore(torch,agent,raw),restore(torch,agent,i),restore(torch,agent,a),agent)
        if base.canonical(rows)!=base.canonical(r['observations']):raise ValueError('evaluation replay mismatch')
    r['receipt_sha256']=sig;return r
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--prior',required=True);p.add_argument('--root',required=True);p.add_argument('--agents',type=int,default=4);p.add_argument('--steps',type=int,default=128);p.add_argument('--authorize',action='store_true');a=p.parse_args()
    if not a.authorize or not 1<=a.agents<=4:raise PermissionError('bounded research only')
    root=Path(a.root);old=Path(a.prior);source=Path(a.source)
    if not root.parent.is_dir() or not old.is_dir() or not source.is_dir() or root.is_symlink() or old.is_symlink() or source.is_symlink():raise ValueError('invalid roots')
    ids=sorted(int(p.name) for p in old.iterdir() if p.is_dir() and not p.is_symlink() and len(p.name)==5 and p.name.isdecimal())[:a.agents]
    rows=[];new=0
    for i in ids:
        dest=root/f'{i:05d}'
        if not dest.exists():train_compare(source,old,root,i,a.steps);new+=1
        r=verify(source,old,dest,True)
        if r['steps_per_arm']!=a.steps:raise ValueError('existing cohort budget mismatch')
        rows.append(r)
    keys=('observations','mixed_wins_vs_iid','mixed_wins_vs_prior','mixed_wins_vs_all','retention_failures')
    print(json.dumps({'schema':SCHEMA,'agents':len(rows),'new_agents':new,'weight_bytes':2*WIDTH*len(rows),'gradient_steps':sum(2*r['steps_per_arm'] for r in rows),**{k:sum(r['summary'][k] for r in rows) for k in keys},'production_authority':False,'semantic_mastery_certified':False},sort_keys=True))
if __name__=='__main__':main()
