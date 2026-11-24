"""Task-conditioned residual learning over immutable original agents.
The original route never executes the adapter. Separate synthetic qualification only.
"""
import argparse,ctypes,json,math,os,shutil,uuid
from pathlib import Path
import evolution_agent_bank_v51 as base
import evolution_agent_evolution_v58 as novel
PARAMETERS=21768
def model(torch,i):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(610000+i)
        return torch.nn.Sequential(torch.nn.Linear(32,128),torch.nn.GELU(),torch.nn.Linear(128,128),torch.nn.GELU(),torch.nn.Linear(128,8))
def predict(source,adapter,x,task):
    if task=='original':return source(x)
    if task=='nonlinear':return source(x)+adapter(x)
    raise ValueError('unknown task')
def metrics(torch,source,adapter,i):
    x,y=novel.data(torch,i,0,'train',512);z=torch.cat((x,torch.ones(len(x),1)),1);beta=torch.linalg.solve(z.T@z+.01*torch.eye(33),z.T@y)
    out={};source.eval();adapter.eval()
    with torch.no_grad():
        for s in ('holdout','shift'):
            u,v=novel.data(torch,i,0,s,256);linear=torch.cat((u,torch.ones(len(u),1)),1)@beta
            out[s]={'mse':float(((predict(source,adapter,u,'nonlinear')-v)**2).mean()),'source_mse':float(((source(u)-v)**2).mean()),'linear_mse':float(((linear-v)**2).mean()),'zero_mse':float((v*v).mean())}
        deltas=[]
        for s in ('holdout','shift'):
            u,_=base.data(torch,i,s,128);deltas.append(float((predict(source,adapter,u,'original')-source(u)).abs().max()))
    if any(not math.isfinite(n) for v in out.values() for n in v.values()):raise ValueError('nonfinite')
    return out,max(deltas)
def load_source(torch,root,i):
    p=Path(root)/f'{i:05d}';r=base.verify(p)
    m=base.restore(torch,base.model(torch,i),(p/'weights.fp16').read_bytes())
    m.requires_grad_(False);m.eval();return m,r
def train(source,root,i,steps):
    if type(i) is not int or not 1<=i<=base.TARGET or type(steps) is not int or not 1<=steps<=512:raise ValueError('bounds')
    root=Path(root);root.mkdir(exist_ok=True);dest=root/f'{i:05d}'
    if dest.exists():raise FileExistsError('immutable adapter')
    if root.is_symlink() or shutil.disk_usage(root).free<6*1024**3:raise ValueError('storage guard')
    import torch
    torch.set_num_threads(1);m,origin=load_source(torch,source,i);a=model(torch,i)
    n=sum(p.numel() for p in a.parameters())
    if n!=PARAMETERS:raise ValueError('adapter geometry')
    x,y=novel.data(torch,i,1,'train',4096)
    with torch.no_grad():target=y-m(x)
    opt=torch.optim.AdamW(a.parameters(),lr=.001,weight_decay=.01);g=torch.Generator().manual_seed(611001+i)
    a.train()
    for _ in range(steps):
        idx=torch.randint(0,len(x),(128,),generator=g);opt.zero_grad(set_to_none=True);loss=((a(x[idx])-target[idx])**2).mean();loss.backward();opt.step()
    v=torch.nn.utils.parameters_to_vector(a.parameters()).detach().half().contiguous()
    if not torch.isfinite(v).all():raise ValueError('nonfinite')
    raw=ctypes.string_at(v.data_ptr(),v.numel()*2);torch.nn.utils.vector_to_parameters(v.float(),a.parameters())
    scores,delta=metrics(torch,m,a,i)
    r={'schema':'myriad.task_adapter.v61','agent':i,'source_sha256':origin['weight_sha256'],'adapter_sha256':base.sha(raw),'parameters':n,'weight_bytes':len(raw),'steps':steps,'scores':scores,'retention_max_delta':delta,'candidate_qualified':delta==0 and all(s['mse']<min(s['source_mse'],s['linear_mse'],s['zero_mse']) for s in scores.values()),'production_authority':False,'auto_promote':False,'scope':'task-selected residual; original path unchanged; synthetic data only'}
    r['receipt_sha256']=base.sha(base.canonical(r));temp=root/('.staged-'+uuid.uuid4().hex);temp.mkdir()
    for name,b in [('adapter.fp16',raw),('receipt.json',base.canonical(r)+b'\n')]:
        with (temp/name).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    temp.rename(dest);return r
def verify(source,folder,replay=False):
    p=Path(folder);r=json.loads((p/'receipt.json').read_text());sig=r.pop('receipt_sha256');raw=(p/'adapter.fp16').read_bytes();i=r['agent']
    origin=base.verify(Path(source)/f'{i:05d}')
    if p.is_symlink() or (p/'adapter.fp16').is_symlink() or p.name!=f'{i:05d}' or sig!=base.sha(base.canonical(r)) or r['schema']!='myriad.task_adapter.v61' or r['source_sha256']!=origin['weight_sha256'] or r['parameters']!=PARAMETERS or len(raw)!=PARAMETERS*2 or r['weight_bytes']!=len(raw) or base.sha(raw)!=r['adapter_sha256'] or r['production_authority'] is not False or r['auto_promote'] is not False:raise ValueError('invalid adapter')
    if replay:
        import torch
        torch.set_num_threads(1);m,_=load_source(torch,source,i);a=model(torch,i);v=torch.frombuffer(bytearray(raw),dtype=torch.float16).float()
        if not torch.isfinite(v).all():raise ValueError('nonfinite')
        torch.nn.utils.vector_to_parameters(v,a.parameters());scores,delta=metrics(torch,m,a,i)
        if delta!=r['retention_max_delta'] or any(abs(scores[s][k]-r['scores'][s][k])>1e-6 for s in scores for k in scores[s]):raise ValueError('score replay mismatch')
        if r['candidate_qualified']!=(delta==0 and all(s['mse']<min(s['source_mse'],s['linear_mse'],s['zero_mse']) for s in scores.values())):raise ValueError('qualification mismatch')
    r['receipt_sha256']=sig;return r
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--root',required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--agents',type=int,default=16);p.add_argument('--steps',type=int,default=192);a=p.parse_args()
    if not a.authorize or not 1<=a.agents<=32:raise PermissionError('bounded authorized training only')
    root=Path(a.root);source=Path(a.source);root.mkdir(exist_ok=True);rows=[]
    for i in sorted(int(f.name) for f in source.glob('[0-9]*')):
        if (root/f'{i:05d}').exists():continue
        train(source,root,i,a.steps);rows.append(verify(source,root/f'{i:05d}',True))
        if len(rows)>=a.agents:break
    print(json.dumps({'trained_adapters':len(rows),'parameters':sum(r['parameters'] for r in rows),'bytes':sum(r['weight_bytes'] for r in rows),'gradient_steps':sum(r['steps'] for r in rows),'qualified':sum(r['candidate_qualified'] for r in rows),'exact_retention':sum(r['retention_max_delta']==0 for r in rows),'production_authority':False},sort_keys=True))
if __name__=='__main__':main()
