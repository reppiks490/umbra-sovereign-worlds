"""Independent fresh research-only neural checkpoint lineage; never restores historic banks."""
import argparse,hashlib,json,math,os,re,struct,sys,uuid
from pathlib import Path
N=411000;WIDTH=N*2;QUOTA=1024**3

def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(r):return json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def verify_receipt(r,agent,g,prev):
    if r.get('receipt_sha256')!=sha(canonical({k:v for k,v in r.items() if k!='receipt_sha256'})) or r.get('schema')!='myriad.fresh_training.v34' or r.get('agent')!=agent or r.get('generation')!=g or r.get('parameter_count')!=N or r.get('production_authority') is not False or r.get('historic_bank_recovered') is not False or r.get('automatic_promotion') is not False or r.get('previous_receipt_sha256')!=prev:raise ValueError('Invalid lineage receipt')

def latest(root,agent):
    folder=Path(root)/f'NEW-{agent:05d}'
    if not folder.exists():return None
    if folder.is_symlink():raise ValueError('Invalid bank path')
    dirs=sorted(p for p in folder.iterdir() if re.fullmatch(r'\d{6}',p.name))
    prev=None;last=None
    for g,p in enumerate(dirs,1):
        if p.name!=f'{g:06d}' or p.is_symlink() or not p.is_dir():raise ValueError('Noncontiguous lineage')
        receipt=p/'receipt.json';weights=p/'weights.fp16'
        if receipt.is_symlink() or weights.is_symlink() or not receipt.is_file() or not weights.is_file() or receipt.stat().st_size>32768 or weights.stat().st_size!=WIDTH:raise ValueError('Incomplete checkpoint')
        r=json.loads(receipt.read_bytes());verify_receipt(r,agent,g,prev)
        if last and r['source_sha256']!=last['candidate_sha256']:raise ValueError('Broken checkpoint lineage')
        if sha(weights.read_bytes())!=r['candidate_sha256']:raise ValueError('Checkpoint digest mismatch')
        prev=r['receipt_sha256'];last=r
    return last

def model(torch,agent):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(481911+agent)
        m=torch.nn.Sequential(torch.nn.Linear(32,512),torch.nn.GELU(),torch.nn.Linear(512,544),torch.nn.GELU(),torch.nn.Linear(544,208),torch.nn.GELU(),torch.nn.Linear(208,8))
    if sum(p.numel() for p in m.parameters())!=N:raise RuntimeError('Unexpected architecture')
    return m

def encode(torch,m):
    v=torch.nn.utils.parameters_to_vector(m.parameters()).detach().to(torch.float16).contiguous()
    if not torch.isfinite(v).all():raise ValueError('Nonfinite checkpoint')
    return struct.pack('<'+str(N)+'e',*v.tolist())
def restore(torch,m,b):
    if sys.byteorder!='little' or len(b)!=WIDTH:raise ValueError('Unsupported checkpoint format')
    v=torch.frombuffer(bytearray(b),dtype=torch.float16).float()
    if not torch.isfinite(v).all():raise ValueError('Nonfinite source')
    torch.nn.utils.vector_to_parameters(v,m.parameters());return m

def batch(torch,agent,g,split,n):
    tag={'train':13,'iid':31,'shift':47,'novel':79}[split]
    rng=torch.Generator(device='cpu').manual_seed(38119+agent*100003+g*1009+tag)
    z=torch.randn(n,8,generator=rng)
    if split=='shift':z=z*1.35+.2
    a,b,c=[torch.rand(n,8,generator=rng)*2-1 for _ in range(3)]
    x=torch.cat([z,a,b,c],dim=1)
    if split=='novel':y=a*torch.cos(z)+b*(z**2-1)+c*torch.sin(z*2)
    else:y=a*torch.sin(z)+b*z*torch.roll(z,1,dims=1)+c*torch.tanh(z*z-1)
    return x,y

def metrics(torch,m,agent,g):
    result={};m.eval()
    with torch.no_grad():
        for s in ('iid','shift','novel'):
            x,y=batch(torch,agent,g,s,128);v=float(torch.mean((m(x)-y)**2));zero=float(torch.mean(y*y))
            if not math.isfinite(v) or not math.isfinite(zero):raise ValueError('Invalid metric')
            result[s]={'mse':v,'zero_mse':zero}
    return result

def run(root,agents=8,steps=64,authorize=False):
    if authorize is not True:raise PermissionError('Explicit research training approval required')
    if type(agents) is not int or not 1<=agents<=8 or type(steps) is not int or not 1<=steps<=128:raise ValueError('Training budget exceeded')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if root.is_symlink():raise ValueError('Invalid bank root')
    used=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    if used+agents*(WIDTH+32768)>QUOTA:raise ValueError('Private bank quota exceeded; no deletion')
    import torch
    torch.set_num_threads(1);rows=[]
    for agent in range(1,agents+1):
        p=root/f'NEW-{agent:05d}';p.mkdir(exist_ok=True);prev=latest(root,agent);g=prev['generation']+1 if prev else 1
        m=model(torch,agent)
        b=(p/f'{g-1:06d}'/'weights.fp16').read_bytes() if prev else encode(torch,m)
        restore(torch,m,b);before=metrics(torch,m,agent,g)
        x,y=batch(torch,agent,g,'train',16384);rng=torch.Generator().manual_seed(87191+agent*1009+g)
        opt=torch.optim.AdamW(m.parameters(),lr=.0005,weight_decay=.01);m.train()
        for _ in range(steps):
            i=torch.randint(0,len(x),(256,),generator=rng);opt.zero_grad(set_to_none=True);loss=torch.nn.functional.mse_loss(m(x[i]),y[i]);loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1.0);opt.step()
        candidate=encode(torch,m);restore(torch,m,candidate);after=metrics(torch,m,agent,g)
        r={'schema':'myriad.fresh_training.v34','agent':agent,'generation':g,'parameter_count':N,'steps':steps,'training_protocol':'v35_diverse_synthetic_curriculum','training_samples':16384,'batch_size':256,'source_sha256':sha(b),'candidate_sha256':sha(candidate),'previous_receipt_sha256':prev['receipt_sha256'] if prev else None,'before':before,'after':after,'research_review_eligible':all(after[s]['mse']<min(before[s]['mse'],after[s]['zero_mse']) for s in ('iid','shift','novel')),'historic_bank_recovered':False,'production_authority':False,'automatic_promotion':False,'dataset':'synthetic math only; generation-specific disjoint seeds; novel teacher withheld'}
        r['receipt_sha256']=sha(canonical(r));temp=p/('.staged-'+uuid.uuid4().hex);temp.mkdir()
        for name,raw in [('weights.fp16',candidate),('receipt.json',canonical(r)+b'\n')]:
            with (temp/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        final=p/f'{g:06d}'
        if final.exists():raise FileExistsError('Concurrent generation')
        temp.rename(final);rows.append(r)
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--agents',type=int,default=8);p.add_argument('--steps',type=int,default=64);p.add_argument('--authorize-synthetic-training',action='store_true');a=p.parse_args()
    rows=run(a.root,a.agents,a.steps,a.authorize_synthetic_training)
    print(json.dumps({'agents':len(rows),'gradient_steps':sum(r['steps'] for r in rows),'parameters_per_agent':N,'generations':[r['generation'] for r in rows],'iid_improved':sum(r['after']['iid']['mse']<r['before']['iid']['mse'] for r in rows),'shift_improved':sum(r['after']['shift']['mse']<r['before']['shift']['mse'] for r in rows),'novel_improved':sum(r['after']['novel']['mse']<r['before']['novel']['mse'] for r in rows),'review_eligible':sum(r['research_review_eligible'] for r in rows),'production_authority':False,'historic_bank_recovered':False},sort_keys=True))
if __name__=='__main__':main()
