"""Regularized algorithm-derived fits; separate train/selection/holdout/shift/final splits.
Features are input-derived, not target labels. Some tasks have exact algebraic
representations in this basis; this is not evidence of broad semantic mastery.
"""
import argparse,ctypes,json,math,os,shutil,uuid
from pathlib import Path
import evolution_algorithm_distill_v57 as old
WIDTH=500
def bounds(start,n,samples):
    if any(type(x) is not int for x in (start,n,samples)) or start<1 or not 1<=n<=64 or start+n-1>10000000 or not 256<=samples<=4096:raise ValueError('bounds')
def data(torch,i,split,n):
    if split in ('holdout','shift'):return old.data(torch,i,split,n)
    g=torch.Generator().manual_seed(6300001+i*1009+{'train':1,'selection':2,'final':3}[split])
    x=torch.randn(n,16,generator=g)
    if split=='train':
        x[::3]=x[::3]*1.3+.3
    elif split=='selection':x[::2]=x[::2]*1.3+.3
    else:x=x*1.65-.35
    y=torch.tensor([old.target((i-1)%8,v) for v in x.tolist()])
    return x,y
def features(torch,x,i):
    p,q=torch.triu_indices(16,16,offset=0);j,k=torch.triu_indices(16,16,offset=1)
    g=torch.Generator().manual_seed(630001+i)
    w=torch.randn(16,180,generator=g)/4;phase=torch.rand(180,generator=g)*2*math.pi
    z=torch.cat((torch.ones(len(x),1),x,x[:,p]*x[:,q],x.abs(),x.sort(dim=1).values,torch.sign(x[:,k]-x[:,j]),(x[:,1:]-x[:,:-1]).abs(),torch.cos(x@w+phase)),1)
    if z.shape[1]!=WIDTH or not torch.isfinite(z).all():raise ValueError('feature geometry')
    return z
def fit(torch,z,y,lam):
    reg=torch.eye(z.shape[1],dtype=z.dtype)*lam;reg[0,0]=1e-5
    return torch.linalg.solve(z.T@z+reg,z.T@y)
def evaluate(torch,i,w,samples):
    x,y=data(torch,i,'train',samples)
    lin=torch.cat((torch.ones(len(x),1),x),1)
    beta=fit(torch,lin,y,.01);mean=y.mean();out={}
    for s in ('holdout','shift','final'):
        u,v=data(torch,i,s,128)
        z=torch.cat((torch.ones(len(u),1),u),1)
        out[s]={'mse':float(((features(torch,u,i)@w-v)**2).mean()),'mean_baseline':float(((mean-v)**2).mean()),'linear_baseline':float(((z@beta-v)**2).mean())}
    if any(not math.isfinite(n) for d in out.values() for n in d.values()):raise ValueError('nonfinite metrics')
    return out
def train(root,start,n,samples):
    bounds(start,n,samples);root=Path(root);root.mkdir(exist_ok=True);dest=root/f'{start:08d}'
    if dest.exists():raise FileExistsError('immutable')
    if root.is_symlink() or shutil.disk_usage(root).free<6*1024**3:raise ValueError('storage guard')
    import torch
    torch.set_num_threads(1);rows=[];weights=[]
    for i in range(start,start+n):
        x,y=data(torch,i,'train',samples);z=features(torch,x,i)
        u,v=data(torch,i,'selection',256);zu=features(torch,u,i)
        candidates=[]
        for lam in (.1,1.,10.,100.):
            w=fit(torch,z,y,lam).half().float()
            if not torch.isfinite(w).all():raise ValueError('nonfinite coefficient')
            candidates.append((float(((zu@w-v)**2).mean()),lam,w))
        sel,lam,w=min(candidates,key=lambda a:(a[0],a[1]))
        metrics=evaluate(torch,i,w,samples)
        half=w.half().contiguous();weights.append(ctypes.string_at(half.data_ptr(),half.numel()*2))
        rows.append({'id':i,'family':old.FAMILIES[(i-1)%8],'regularization':lam,'selection_mse':sel,'metrics':metrics,'qualified':all(s['mse']<min(s['mean_baseline'],s['linear_baseline']) for s in metrics.values())})
    raw=b''.join(weights);r={'schema':'myriad.distill.v63','start':start,'rows':n,'samples_per_row':samples,'weight_bytes':len(raw),'weight_sha256':old.sha(raw),'regularized_fits':4*n,'qualified':sum(x['qualified'] for x in rows),'tasks':rows,'production_authority':False,'scope':'algorithm-informed synthetic regression; exact feature representations possible; no LLM semantic mastery'}
    r['receipt_sha256']=old.sha(old.canonical(r));temp=root/('.staged-'+uuid.uuid4().hex);temp.mkdir()
    for name,b in [('weights.fp16',raw),('receipt.json',old.canonical(r)+b'\n')]:
        with (temp/name).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    temp.rename(dest);return r
def verify(folder,replay=False):
    p=Path(folder);r=json.loads((p/'receipt.json').read_text());sig=r.pop('receipt_sha256');raw=(p/'weights.fp16').read_bytes()
    bounds(r['start'],r['rows'],r['samples_per_row'])
    if p.is_symlink() or (p/'weights.fp16').is_symlink() or p.name!=f"{r['start']:08d}" or r['schema']!='myriad.distill.v63' or r['production_authority'] is not False or sig!=old.sha(old.canonical(r)) or len(raw)!=1000*r['rows'] or r['weight_bytes']!=len(raw) or old.sha(raw)!=r['weight_sha256'] or [x['id'] for x in r['tasks']]!=list(range(r['start'],r['start']+r['rows'])) or r['qualified']!=sum(x['qualified'] for x in r['tasks']):raise ValueError('receipt mismatch')
    if replay:
        import torch
        torch.set_num_threads(1);w=torch.frombuffer(bytearray(raw),dtype=torch.float16).reshape(-1,500).float()
        for j,t in enumerate(r['tasks']):
            metrics=evaluate(torch,t['id'],w[j],r['samples_per_row'])
            if any(abs(metrics[s][k]-t['metrics'][s][k])>1e-6 for s in metrics for k in metrics[s]) or t['qualified']!=all(s['mse']<min(s['mean_baseline'],s['linear_baseline']) for s in metrics.values()):raise ValueError('evaluation replay')
    r['receipt_sha256']=sig;return r
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--rows',type=int,default=32);p.add_argument('--samples',type=int,default=1024);a=p.parse_args();root=Path(a.root)
    if not a.authorize or not root.parent.is_dir():raise PermissionError('private research only')
    root.mkdir(exist_ok=True);start=1
    for f in sorted(root.glob('[0-9]*')):
        r=verify(f)
        if r['start']!=start:raise ValueError('noncontiguous')
        start+=r['rows']
    r=train(root,start,a.rows,a.samples);verify(root/f'{start:08d}',True)
    print(json.dumps({k:v for k,v in r.items() if k!='tasks'},sort_keys=True))
if __name__=='__main__':main()
