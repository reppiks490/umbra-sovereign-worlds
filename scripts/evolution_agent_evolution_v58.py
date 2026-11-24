"""Immutable continued-training candidates for v51 agents, retaining source checkpoints."""
import argparse,hashlib,json,math,os,shutil,uuid
from pathlib import Path
import evolution_agent_bank_v51 as base
def data(torch,i,g,split,n):
    # Fixed test seeds across generations, separate from the changing training seed.
    rng=torch.Generator().manual_seed(580001+i*1009+{'train':g*97,'holdout':1000001,'shift':1000002}[split])
    x=torch.randn(n,32,generator=rng)
    if split=='shift':x=x*1.4+.25
    a,b,c,d=x.split(8,dim=1)
    y=torch.sin(a*b)+.3*c*d+.2*torch.tanh(a+d)
    return x,y
def metrics(torch,m,i):
    out={};m.eval()
    x,y=data(torch,i,0,'train',512)
    z=torch.cat((x,torch.ones(len(x),1)),1)
    beta=torch.linalg.solve(z.T@z+.01*torch.eye(33),z.T@y)
    with torch.no_grad():
        for s in ('holdout','shift'):
            u,v=data(torch,i,0,s,256)
            linear=torch.cat((u,torch.ones(len(u),1)),1)@beta
            out[s]={'mse':float(((m(u)-v)**2).mean()),'linear_baseline':float(((linear-v)**2).mean()),'zero_baseline':float((v*v).mean())}
    for s,v in base.metrics(torch,m,i).items():out['retention_'+s]=v
    if any(not math.isfinite(n) for v in out.values() for n in v.values()):raise ValueError('nonfinite')
    return out
def latest(source,root,i,replay=False):
    p=Path(root)/f'{i:05d}';origin=base.verify(Path(source)/f'{i:05d}')
    parent=origin['weight_sha256'];previous=None
    for g,folder in enumerate(sorted(p.glob('[0-9]*')),1):
        r=json.loads((folder/'receipt.json').read_text());sig=r.pop('receipt_sha256');raw=(folder/'weights.fp16').read_bytes()
        if folder.name!=f'{g:06d}' or folder.is_symlink() or sig!=base.sha(base.canonical(r)) or r.get('schema')!='myriad.agent_evolution.v58' or r['agent']!=i or r['generation']!=g or r['parent_sha256']!=parent or r['previous_receipt_sha256']!=previous or r['production_authority'] is not False or len(raw)!=base.WIDTH or base.sha(raw)!=r['weight_sha256']:raise ValueError('broken lineage')
        if replay:
            import torch
            torch.set_num_threads(1);m=base.restore(torch,base.model(torch,i),raw);after=metrics(torch,m,i)
            if any(abs(after[s][k]-r['after'][s][k])>1e-6 for s in after for k in after[s]):raise ValueError('replay mismatch')
        parent=r['weight_sha256'];previous=sig;r['receipt_sha256']=sig
    return r if previous else None
def train(source,root,i,steps):
    if type(i) is not int or not 1<=i<=base.TARGET or type(steps) is not int or not 1<=steps<=128:raise ValueError('bounds')
    source=Path(source);root=Path(root);root.mkdir(exist_ok=True)
    if root.is_symlink() or shutil.disk_usage(root).free<6*1024**3:raise ValueError('storage guard')
    prior=latest(source,root,i);folder=root/f'{i:05d}';folder.mkdir(exist_ok=True)
    g=prior['generation']+1 if prior else 1
    raw=((folder/f'{g-1:06d}' if prior else source/f'{i:05d}')/'weights.fp16').read_bytes()
    import torch
    torch.set_num_threads(1);m=base.restore(torch,base.model(torch,i),raw);before=metrics(torch,m,i)
    x,y=data(torch,i,g,'train',2048);u,v=base.data(torch,i,'train',2048)
    rng=torch.Generator().manual_seed(890001+i*101+g);opt=torch.optim.AdamW(m.parameters(),lr=.0003,weight_decay=.01);m.train()
    for _ in range(steps):
        ix=torch.randint(0,len(x),(64,),generator=rng);j=torch.randint(0,len(u),(64,),generator=rng)
        opt.zero_grad(set_to_none=True);loss=((m(x[ix])-y[ix])**2).mean()+((m(u[j])-v[j])**2).mean();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1);opt.step()
    candidate=base.encode(torch,m);base.restore(torch,m,candidate);after=metrics(torch,m,i)
    passes=all(after[s]['mse']<min(before[s]['mse'],after[s]['linear_baseline'],after[s]['zero_baseline']) for s in ('holdout','shift'))
    retention=all(after[s]['mse']<=before[s]['mse']*1.05 for s in ('retention_holdout','retention_shift'))
    r={'schema':'myriad.agent_evolution.v58','agent':i,'generation':g,'steps':steps,'parameters':base.PARAMETERS,'weight_bytes':len(candidate),'parent_sha256':base.sha(raw),'weight_sha256':base.sha(candidate),'previous_receipt_sha256':prior['receipt_sha256'] if prior else None,'before':before,'after':after,'novel_task_pass':passes,'retention_pass':retention,'candidate_qualified':passes and retention,'production_authority':False,'auto_promote':False,'scope':'synthetic conflicting task pilot; no real market or LLM training'}
    r['receipt_sha256']=base.sha(base.canonical(r));temp=folder/('.staged-'+uuid.uuid4().hex);temp.mkdir()
    for name,b in [('weights.fp16',candidate),('receipt.json',base.canonical(r)+b'\n')]:
        with (temp/name).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    temp.rename(folder/f'{g:06d}');return r
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--root',required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--agents',type=int,default=4);p.add_argument('--steps',type=int,default=64);a=p.parse_args()
    if not a.authorize or not 1<=a.agents<=8:raise PermissionError('bounded authorized training only')
    root=Path(a.root);source=Path(a.source);root.mkdir(exist_ok=True)
    ids=[int(f.name) for f in source.glob('[0-9]*')];ids.sort(key=lambda i:((latest(source,root,i) or {}).get('generation',0),i))
    rows=[]
    for i in ids[:a.agents]:
        r=train(source,root,i,a.steps);latest(source,root,i,True);rows.append(r)
    print(json.dumps({'agents':len(rows),'steps':sum(r['steps'] for r in rows),'new_bytes':sum(r['weight_bytes'] for r in rows),'novel_passes':sum(r['novel_task_pass'] for r in rows),'retention_passes':sum(r['retention_pass'] for r in rows),'qualified':sum(r['candidate_qualified'] for r in rows),'production_authority':False}))
if __name__=='__main__':main()
