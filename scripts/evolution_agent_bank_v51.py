"""Fresh 1.5M-parameter agent bank, independent seeded networks, immutable FP16 artifacts."""
import argparse,ctypes,hashlib,json,math,os,shutil,time,uuid
from pathlib import Path
TARGET=10000;PARAMETERS=1500000;WIDTH=PARAMETERS*2
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def model(torch,agent):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(510000+agent)
        m=torch.nn.Sequential(torch.nn.Linear(32,1072),torch.nn.GELU(),torch.nn.Linear(1072,832),torch.nn.GELU(),torch.nn.Linear(832,680),torch.nn.GELU(),torch.nn.Linear(680,8))
    if sum(p.numel() for p in m.parameters())!=PARAMETERS:raise ValueError('parameter geometry')
    return m
def data(torch,agent,split,n):
    g=torch.Generator().manual_seed(610000+agent*101+{'train':1,'holdout':2,'shift':3}[split])
    x=torch.randn(n,32,generator=g)
    if split=='shift':x=x*1.25+.2
    a,b,c,d=x.split(8,dim=1)
    phase=(agent%19)/19
    y=torch.tanh(a+b*phase)+.3*c*torch.sin(d+phase)
    return x,y
def metrics(torch,m,agent):
    out={};m.eval()
    with torch.no_grad():
        for split in ('holdout','shift'):
            x,y=data(torch,agent,split,128);err=float(((m(x)-y)**2).mean());zero=float((y*y).mean())
            if not math.isfinite(err):raise ValueError('nonfinite metrics')
            out[split]={'mse':err,'zero_mse':zero}
    return out
def encode(torch,m):
    v=torch.nn.utils.parameters_to_vector(m.parameters()).detach().to(torch.float16).contiguous()
    if not torch.isfinite(v).all():raise ValueError('nonfinite weights')
    return ctypes.string_at(v.data_ptr(),v.numel()*v.element_size())
def restore(torch,m,raw):
    if len(raw)!=WIDTH:raise ValueError('geometry')
    v=torch.frombuffer(bytearray(raw),dtype=torch.float16).float()
    if not torch.isfinite(v).all():raise ValueError('nonfinite weights')
    torch.nn.utils.vector_to_parameters(v,m.parameters());return m
def train(root,agent,steps):
    if type(agent) is not int or not 1<=agent<=TARGET or type(steps) is not int or not 1<=steps<=128:raise ValueError('bounds')
    root=Path(root);root.mkdir(exist_ok=True)
    if root.is_symlink() or shutil.disk_usage(root).free<WIDTH+5*1024**3:raise ValueError('disk guard')
    final=root/f'{agent:05d}'
    if final.exists():raise FileExistsError('immutable checkpoint')
    import torch
    torch.set_num_threads(1);m=model(torch,agent);initial=encode(torch,m);restore(torch,m,initial);before=metrics(torch,m,agent)
    x,y=data(torch,agent,'train',2048);g=torch.Generator().manual_seed(710000+agent)
    opt=torch.optim.AdamW(m.parameters(),lr=.0007,weight_decay=.01);m.train()
    for _ in range(steps):
        ids=torch.randint(0,len(x),(64,),generator=g);opt.zero_grad(set_to_none=True)
        loss=torch.nn.functional.mse_loss(m(x[ids]),y[ids]);loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1.);opt.step()
    raw=encode(torch,m);restore(torch,m,raw);after=metrics(torch,m,agent)
    r={'schema':'myriad.fresh_agent_bank.v51','agent':agent,'parameters':PARAMETERS,'weight_bytes':len(raw),'source_sha256':sha(initial),'weight_sha256':sha(raw),'steps':steps,'before':before,'after':after,'review_eligible_synthetic':all(after[s]['mse']<min(before[s]['mse'],after[s]['zero_mse']) for s in after),'scope':'synthetic regression only; no historical weights recovered','production_authority':False,'auto_promote':False}
    r['receipt_sha256']=sha(canonical(r));temp=root/('.staged-'+uuid.uuid4().hex);temp.mkdir()
    for name,b in [('weights.fp16',raw),('receipt.json',canonical(r)+b'\n')]:
        with (temp/name).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    temp.rename(final);return r
def verify(folder,replay=False):
    folder=Path(folder);p=folder/'weights.fp16';r=json.loads((folder/'receipt.json').read_text());sig=r.pop('receipt_sha256')
    if folder.is_symlink() or p.is_symlink() or sig!=sha(canonical(r)) or r['schema']!='myriad.fresh_agent_bank.v51' or folder.name!=f"{r['agent']:05d}" or r['parameters']!=PARAMETERS or r['production_authority'] is not False or r['auto_promote'] is not False:raise ValueError('invalid agent receipt')
    raw=p.read_bytes()
    if len(raw)!=WIDTH or sha(raw)!=r['weight_sha256']:raise ValueError('weight digest')
    if replay:
        import torch
        torch.set_num_threads(1);m=model(torch,r['agent']);restore(torch,m,raw);after=metrics(torch,m,r['agent'])
        if any(abs(after[s][k]-r['after'][s][k])>1e-6 for s in after for k in after[s]):raise ValueError('score replay mismatch')
    r['receipt_sha256']=sig;return r
def status(root):
    n=steps=eligible=0
    for p in sorted(Path(root).glob('[0-9]*')):
        r=verify(p);n+=1
        if r['agent']!=n:raise ValueError('noncontiguous bank')
        steps+=r['steps'];eligible+=int(r['review_eligible_synthetic'])
    return {'trained_agents':n,'trained_parameters':n*PARAMETERS,'trained_bytes':n*WIDTH,'gradient_steps':steps,'synthetic_review_eligible':eligible,'target_agents':TARGET,'target_bytes':TARGET*WIDTH,'production_authority':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--agents',type=int,default=4);p.add_argument('--steps',type=int,default=32);p.add_argument('command',choices=['train','status']);a=p.parse_args();root=Path(a.root)
    if not a.authorize or not root.parent.is_dir() or not 1<=a.agents<=16:raise PermissionError('explicit bounded local training')
    root.mkdir(exist_ok=True)
    if a.command=='train':
        n=status(root)['trained_agents']
        for i in range(n+1,min(n+a.agents,TARGET)+1):train(root,i,a.steps);verify(root/f'{i:05d}',True)
    print(json.dumps(status(root),sort_keys=True))
if __name__=='__main__':main()
