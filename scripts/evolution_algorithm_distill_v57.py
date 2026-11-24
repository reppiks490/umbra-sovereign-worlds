"""Algorithm-derived supervised ability pilot: 500 trainable random-feature coefficients per task."""
import argparse,ctypes,hashlib,json,math,os,shutil,uuid
from pathlib import Path
import evolution_algorithms_v49 as a
import evolution_algorithms_v56 as b
WIDTH=500;FAMILIES=('drawdown','autocorr','median','trend','variance','slope','wavelet_energy','rolling_median')
def sha(x):return hashlib.sha256(x).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def target(role,values):
    v=list(values)
    if role==0:return float(a.max_drawdown([math.exp(max(-5,min(5,x))) for x in v]))
    if role==1:return float(a.autocorr(v,1))
    if role==2:return float(a.quickselect(v,len(v)//2))
    if role==3:return float(b.mann_kendall(v)/120)
    if role==4:return float(b.welford(v)[1])
    if role==5:return float(b.theil_sen(list(range(len(v))),v)*4)
    if role==6:return float(sum(x*x for x in b.haar(v)[1:])/len(v))
    if role==7:return float(sum(a.rolling_median(v,5))/12)
    raise ValueError('unknown task')
def data(torch,i,split,n):
    g=torch.Generator().manual_seed(570011+i*101+{'train':1,'holdout':2,'shift':3}[split])
    x=torch.randn(n,16,generator=g)
    if split=='shift':x=x*1.3+.3
    y=torch.tensor([target((i-1)%8,v) for v in x.tolist()])
    return x,y
def features(torch,x,i):
    g=torch.Generator().manual_seed(880011+i)
    w=torch.randn(16,483,generator=g)/4
    phase=torch.rand(483,generator=g)*2*math.pi
    return torch.cat((torch.ones(len(x),1),x,torch.cos(x@w+phase)),dim=1)
def evaluate(torch,i,w):
    x,y=data(torch,i,'train',256)
    z=torch.cat((torch.ones(len(x),1),x),1)
    beta=torch.linalg.solve(z.T@z+.001*torch.eye(17),z.T@y)
    mean=y.mean();out={}
    for split in ('holdout','shift'):
        u,v=data(torch,i,split,128)
        pred=features(torch,u,i)@w
        linear=torch.cat((torch.ones(len(u),1),u),1)@beta
        out[split]={'mse':float(((pred-v)**2).mean()),'mean_baseline':float(((mean-v)**2).mean()),'linear_baseline':float(((linear-v)**2).mean())}
    return out
def train(root,start,n,steps):
    if any(type(x) is not int for x in (start,n,steps)) or not 1<=start<=10000000 or not 1<=n<=64 or not 1<=steps<=128:raise ValueError('bounds')
    root=Path(root);root.mkdir(exist_ok=True);dest=root/f'{start:05d}'
    if dest.exists():raise FileExistsError('immutable shard')
    if root.is_symlink() or shutil.disk_usage(root).free<5*1024**3:raise ValueError('storage guard')
    import torch
    torch.set_num_threads(1);rows=[];weights=[]
    for i in range(start,start+n):
        x,y=data(torch,i,'train',256);z=features(torch,x,i)
        w=torch.zeros(WIDTH,requires_grad=True);opt=torch.optim.AdamW([w],lr=.008,weight_decay=.01)
        g=torch.Generator().manual_seed(950001+i)
        for _ in range(steps):
            ids=torch.randint(0,len(x),(64,),generator=g);opt.zero_grad(set_to_none=True)
            loss=((z[ids]@w-y[ids])**2).mean();loss.backward();opt.step()
        half=w.detach().half().contiguous()
        if not torch.isfinite(half).all():raise ValueError('nonfinite weight')
        metrics=evaluate(torch,i,half.float())
        rows.append({'id':i,'family':FAMILIES[(i-1)%8],'metrics':metrics,'beats_both_baselines':all(v['mse']<min(v['mean_baseline'],v['linear_baseline']) for v in metrics.values())})
        weights.append(ctypes.string_at(half.data_ptr(),half.numel()*half.element_size()))
    raw=b''.join(weights);r={'schema':'myriad.algorithm_distillation.v57','start':start,'rows':n,'weight_bytes':len(raw),'steps_per_row':steps,'gradient_row_updates':steps*n,'weight_sha256':sha(raw),'tasks':rows,'baseline_passes':sum(v['beats_both_baselines'] for v in rows),'production_authority':False,'scope':'synthetic sequences; executable reference algorithms supply labels; approximation not exact algorithm replacement'}
    r['receipt_sha256']=sha(canonical(r));temp=root/('.staged-'+uuid.uuid4().hex);temp.mkdir()
    for name,blob in [('weights.fp16',raw),('receipt.json',canonical(r)+b'\n')]:
        with (temp/name).open('xb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
    temp.rename(dest);return r
def verify(folder,replay=False):
    folder=Path(folder);r=json.loads((folder/'receipt.json').read_text());sig=r.pop('receipt_sha256');raw=(folder/'weights.fp16').read_bytes()
    if sig!=sha(canonical(r)) or r['schema']!='myriad.algorithm_distillation.v57' or r['production_authority'] is not False or sha(raw)!=r['weight_sha256'] or len(raw)!=r['rows']*WIDTH*2 or r['weight_bytes']!=len(raw):raise ValueError('invalid distillation receipt')
    if replay:
        import torch
        torch.set_num_threads(1);w=torch.frombuffer(bytearray(raw),dtype=torch.float16).reshape(-1,WIDTH).float()
        for i,row in enumerate(r['tasks']):
            v=evaluate(torch,row['id'],w[i])
            if any(abs(v[s][k]-row['metrics'][s][k])>1e-6 for s in v for k in v[s]):raise ValueError('replay mismatch')
    r['receipt_sha256']=sig;return r
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--rows',type=int,default=16);p.add_argument('--steps',type=int,default=96);a_=p.parse_args();root=Path(a_.root)
    if not a_.authorize or not root.parent.is_dir():raise PermissionError('private research only')
    root.mkdir(exist_ok=True);start=1
    for f in sorted(root.glob('[0-9]*')):
        r=verify(f)
        if r['start']!=start:raise ValueError('noncontiguous shard')
        start+=r['rows']
    r=train(root,start,a_.rows,a_.steps);verify(root/f'{start:05d}',True)
    print(json.dumps({k:v for k,v in r.items() if k!='tasks'},sort_keys=True))
if __name__=='__main__':main()
