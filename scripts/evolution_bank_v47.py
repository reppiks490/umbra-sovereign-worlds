"""Independently optimized synthetic linear ability rows, sharded, byte-verifiable.
Rows are not distinct semantic skills or LLM adapters. No sparse allocation.
"""
import argparse,hashlib,json,math,os,shutil,time,uuid
from pathlib import Path
ABILITIES=10_000_000;WIDTH=500;AGENTS=10_000;AGENT_WIDTH=1_500_000;SHARD=8192
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def bounds(start,n,steps):
    if any(type(x) is not int for x in (start,n,steps)) or start<1 or (start-1)%SHARD or not 1<=n<=SHARD or start+n-1>ABILITIES or not 1<=steps<=64:raise ValueError('invalid shard geometry')
def target(torch,start,n):
    # Distinct seeded supervised linear task per row; 16 feature emphasis families.
    g=torch.Generator().manual_seed(470000+start)
    y=torch.randn(n,WIDTH,generator=g)*.15
    families=(torch.arange(start,start+n)-1)%16
    y+=.25*((torch.arange(WIDTH)[None,:]%16)==families[:,None]).float()
    return y
def evaluate(torch,w,y,start):
    # Independent heldout random feature projections, not the coordinate training inputs.
    g=torch.Generator().manual_seed(970000+start)
    errs=torch.zeros(w.shape[0]);base=torch.zeros_like(errs)
    for _ in range(12):
        x=torch.randn(w.shape,generator=g)/math.sqrt(WIDTH)
        truth=(x*y).sum(1);pred=(x*w).sum(1)
        errs+=(pred-truth)**2;base+=truth**2
    return errs/12,base/12
def encode(torch,w):
    v=w.to(torch.float16).contiguous()
    if not torch.isfinite(v).all():raise ValueError('nonfinite row')
    return bytes(v.view(torch.uint8).reshape(-1).tolist())
def train(root,start,n,steps):
    bounds(start,n,steps);root=Path(root);root.mkdir(exist_ok=True)
    if root.is_symlink() or shutil.disk_usage(root).free<n*WIDTH*2+5*1024**3:raise ValueError('disk safety guard')
    final=root/f'{start:08d}'
    if final.exists():raise FileExistsError('immutable shard exists')
    # Never permit a partial shard to leave a gap before later shards.
    if n<SHARD and start+n-1!=ABILITIES and any(root.glob('[0-9]*')):raise ValueError('partial shard only in isolated pilot')
    import torch
    torch.set_num_threads(1);y=target(torch,start,n);w=torch.zeros_like(y)
    g=torch.Generator().manual_seed(570000+start)
    for _ in range(steps):
        # Exact separable per-row gradient from randomized coordinate observations.
        amplitude=torch.rand(w.shape,generator=g)*.8+.6
        residual=(w-y)*amplitude
        grad=2*residual*amplitude
        w-=.10*grad
    v=w.to(torch.float16).contiguous()
    if not torch.isfinite(v).all():raise ValueError('nonfinite row')
    # torch storage bytes avoids Python list explosion.
    import ctypes
    raw=ctypes.string_at(v.data_ptr(),v.numel()*v.element_size())
    if len(raw)!=n*WIDTH*2:raise ValueError('weight geometry')
    mse,zero=evaluate(torch,v.float(),y,start)
    r={'schema':'myriad.synthetic_ability_shard.v47','start':start,'trained_rows':n,'parameters_per_row':WIDTH,'weight_bytes':len(raw),'gradient_steps_per_row':steps,'gradient_row_updates':n*steps,'weight_sha256':sha(raw),'heldout_projections_per_row':12,'mean_mse':float(mse.mean()),'zero_mean_mse':float(zero.mean()),'improved_rows':int((mse<zero).sum()),'semantic_skills_certified':0,'production_authority':False,'historical_bank_recovered':False}
    r['receipt_sha256']=sha(canonical(r));temp=root/('.staged-'+uuid.uuid4().hex);temp.mkdir()
    for name,b in [('weights.fp16',raw),('receipt.json',canonical(r)+b'\n')]:
        with (temp/name).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    temp.rename(final);return r
def verify(folder,replay=False):
    folder=Path(folder);p=folder/'weights.fp16';r=json.loads((folder/'receipt.json').read_text());sig=r.pop('receipt_sha256')
    bounds(r['start'],r['trained_rows'],r['gradient_steps_per_row'])
    if folder.is_symlink() or p.is_symlink() or folder.name!=f"{r['start']:08d}" or sig!=sha(canonical(r)) or r['schema']!='myriad.synthetic_ability_shard.v47' or r['production_authority'] is not False or r['semantic_skills_certified']!=0:raise ValueError('invalid receipt')
    raw=p.read_bytes()
    if len(raw)!=r['trained_rows']*WIDTH*2 or sha(raw)!=r['weight_sha256']:raise ValueError('weight digest mismatch')
    if replay:
        import torch
        torch.set_num_threads(1);v=torch.frombuffer(bytearray(raw),dtype=torch.float16).reshape(-1,WIDTH).float()
        if not torch.isfinite(v).all():raise ValueError('nonfinite')
        y=target(torch,r['start'],r['trained_rows']);mse,zero=evaluate(torch,v,y,r['start'])
        if int((mse<zero).sum())!=r['improved_rows'] or abs(float(mse.mean())-r['mean_mse'])>1e-7 or abs(float(zero.mean())-r['zero_mean_mse'])>1e-7:raise ValueError('score replay mismatch')
    r['receipt_sha256']=sig;return r
def status(root):
    root=Path(root);rows=bytes_=updates=improved=0;expected=1
    for p in sorted(root.glob('[0-9]*')):
        r=verify(p)
        if r['start']!=expected:raise ValueError('noncontiguous shard coverage')
        expected+=r['trained_rows'];rows+=r['trained_rows'];bytes_+=r['weight_bytes'];updates+=r['gradient_row_updates'];improved+=r['improved_rows']
    return {'trained_rows':rows,'trained_bytes':bytes_,'row_updates':updates,'improved_rows':improved,'target_rows':ABILITIES,'target_bytes':ABILITIES*WIDTH*2,'semantic_skills_certified':0,'production_authority':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--shards',type=int,default=1);p.add_argument('--steps',type=int,default=16);p.add_argument('command',choices=['train','status']);a=p.parse_args()
    root=Path(a.root)
    if not a.authorize or not root.parent.is_dir() or not 1<=a.shards<=8:raise PermissionError('private bounded research only')
    root.mkdir(exist_ok=True)
    if a.command=='train':
        r=status(root);start=r['trained_rows']+1
        for _ in range(a.shards):
            if start>ABILITIES:break
            n=min(SHARD,ABILITIES-start+1);result=train(root,start,n,a.steps);verify(root/f'{start:08d}',True);start+=n
    print(json.dumps(status(root),sort_keys=True))
if __name__=='__main__':main()
