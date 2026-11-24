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
    folder=Path(folder);p=folder/'weights.fp16';receipt=folder/'receipt.json'
    if folder.is_symlink() or not folder.is_dir() or p.is_symlink() or receipt.is_symlink() or not p.is_file() or not receipt.is_file() or receipt.stat().st_size>16384:
        raise ValueError('invalid shard paths')
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out:raise ValueError('duplicate receipt field')
            out[k]=v
        return out
    r=json.loads(receipt.read_bytes(),object_pairs_hook=unique)
    fields={'schema','start','trained_rows','parameters_per_row','weight_bytes','gradient_steps_per_row','gradient_row_updates','weight_sha256','heldout_projections_per_row','mean_mse','zero_mean_mse','improved_rows','semantic_skills_certified','production_authority','historical_bank_recovered','receipt_sha256'}
    if not isinstance(r,dict) or set(r)!=fields:raise ValueError('invalid receipt fields')
    sig=r.pop('receipt_sha256');bounds(r['start'],r['trained_rows'],r['gradient_steps_per_row'])
    n=r['trained_rows'];size=n*WIDTH*2
    counts={'parameters_per_row':WIDTH,'weight_bytes':size,'gradient_row_updates':n*r['gradient_steps_per_row'],'heldout_projections_per_row':12,'semantic_skills_certified':0}
    if any(type(r[k]) is not int or r[k]!=v for k,v in counts.items()) or type(r['improved_rows']) is not int or not 0<=r['improved_rows']<=n:
        raise ValueError('inconsistent training counters')
    if any(type(r[k]) not in (int,float) or not math.isfinite(r[k]) or r[k]<0 for k in ('mean_mse','zero_mean_mse')):
        raise ValueError('invalid score')
    digest=lambda v:isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v)
    if not digest(sig) or not digest(r['weight_sha256']) or folder.name!=f"{r['start']:08d}" or sig!=sha(canonical(r)) or r['schema']!='myriad.synthetic_ability_shard.v47' or r['production_authority'] is not False or r['historical_bank_recovered'] is not False:
        raise ValueError('invalid receipt')
    if p.stat().st_size!=size:raise ValueError('weight geometry mismatch')
    raw=p.read_bytes()
    if len(raw)!=size or sha(raw)!=r['weight_sha256']:raise ValueError('weight digest mismatch')
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
