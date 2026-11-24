"""Read-only stress qualification of existing residual adapters; no automatic promotion."""
import argparse,json,math
from pathlib import Path
import evolution_task_adapter_v61 as adapters
import evolution_agent_bank_v51 as base
import evolution_agent_evolution_v58 as novel

FAMILIES=('iid','correlated','heavy_tail','sparse_shift')
METRICS=('adapter_mse','source_mse','zero_mse','linear_mse','quadratic_mse','retention_delta')
def stress_data(torch,agent,seed,family,n):
    if type(agent) is not int or not 1<=agent<=base.TARGET or type(seed) is not int or not 0<=seed<64 or family not in FAMILIES or type(n) is not int or not 1<=n<=2048:
        raise ValueError('stress bounds')
    g=torch.Generator().manual_seed(770000000+agent*4096+seed*4+FAMILIES.index(family))
    x=torch.randn(n,32,generator=g)
    if family=='correlated':
        z=torch.randn(n,1,generator=g);x=.6*x+.8*z
    elif family=='heavy_tail':
        x=x*torch.where(torch.rand(n,1,generator=g)<.1,3.,.8)
    elif family=='sparse_shift':
        x=x*(torch.rand(n,32,generator=g)>.55)+.5
    a,b,c,d=x.split(8,dim=1)
    return x,torch.sin(a*b)+.3*c*d+.2*torch.tanh(a+d)
def features(torch,x,quadratic):
    z=[torch.ones(len(x),1,dtype=x.dtype),x]
    if quadratic:
        i,j=torch.triu_indices(x.shape[1],x.shape[1]);z.append(x[:,i]*x[:,j])
    return torch.cat(z,dim=1)
def fit(torch,x,y,quadratic):
    z=features(torch,x.double(),quadratic);y=y.double()
    return torch.linalg.solve(z.T@z+.1*torch.eye(z.shape[1],dtype=z.dtype),z.T@y)
def summarize(scores):
    if not isinstance(scores,list) or not scores or len(scores)>256:raise ValueError('invalid evaluation count')
    seen=set();wins=quad=retention=0;by_family={}
    for r in scores:
        if not isinstance(r,dict) or set(r)!=set(METRICS)|{'family','seed'} or r['family'] not in FAMILIES or type(r['seed']) is not int or not 0<=r['seed']<64 or any(type(r[k]) not in (int,float) or not math.isfinite(r[k]) or r[k]<0 for k in METRICS):
            raise ValueError('invalid stress observation')
        key=(r['family'],r['seed'])
        if key in seen:raise ValueError('duplicate observation')
        seen.add(key)
        win=r['adapter_mse']<min(r[k] for k in ('source_mse','zero_mse','linear_mse','quadratic_mse'))
        wins+=int(win);quad+=int(r['adapter_mse']<r['quadratic_mse']);retention+=int(r['retention_delta']!=0)
        d=by_family.setdefault(r['family'],{'tests':0,'wins_vs_all':0,'adapter_mse_sum':0.,'quadratic_mse_sum':0.})
        d['tests']+=1;d['wins_vs_all']+=int(win);d['adapter_mse_sum']+=r['adapter_mse'];d['quadratic_mse_sum']+=r['quadratic_mse']
    seeds={s for _,s in seen}
    if seen!={(f,s) for f in FAMILIES for s in seeds}:raise ValueError('incomplete factorial')
    return {'tests':len(scores),'wins_vs_all':wins,'wins_vs_quadratic':quad,'retention_failures':retention,'all_retained':retention==0,'families':by_family,'semantic_mastery_certified':False,'production_authority':False}
def evaluate(torch,source,adapter,agent,samples=256,seeds=4):
    if type(samples) is not int or not 64<=samples<=1024 or type(seeds) is not int or not 1<=seeds<=8:raise ValueError('evaluation budget')
    source.eval();adapter.eval();x,y=novel.data(torch,agent,2,'train',2048)
    with torch.no_grad():
        lin=fit(torch,x,y,False);quad=fit(torch,x,y,True);scores=[]
        for family in FAMILIES:
            for seed in range(seeds):
                u,v=stress_data(torch,agent,seed,family,samples);original=source(u);pred=adapters.predict(source,adapter,u,'nonlinear')
                mse=lambda p:float(((p-v)**2).mean())
                scores.append({'family':family,'seed':seed,'adapter_mse':mse(pred),'source_mse':mse(original),'zero_mse':mse(torch.zeros_like(v)),'linear_mse':mse(features(torch,u.double(),False)@lin),'quadratic_mse':mse(features(torch,u.double(),True)@quad),'retention_delta':float((adapters.predict(source,adapter,u,'original')-original).abs().max())})
    return {**summarize(scores),'observations':scores}
def run(source,root,count=16):
    if type(count) is not int or not 1<=count<=32:raise ValueError('bounded cohort')
    import torch
    torch.set_num_threads(1);source=Path(source);root=Path(root)
    if not source.is_dir() or not root.is_dir() or source.is_symlink() or root.is_symlink():raise ValueError('invalid bank roots')
    paths=sorted(root.glob('[0-9]*'))[:count];out=[]
    for p in paths:
        r=adapters.verify(source,p,True);i=r['agent'];m,_=adapters.load_source(torch,source,i);a=adapters.model(torch,i)
        raw=(p/'adapter.fp16').read_bytes()
        if base.sha(raw)!=r['adapter_sha256']:raise ValueError('adapter changed after verification')
        torch.nn.utils.vector_to_parameters(torch.frombuffer(bytearray(raw),dtype=torch.float16).float(),a.parameters())
        v=evaluate(torch,m,a,i);out.append({'agent':i,'source_sha256':r['source_sha256'],'adapter_sha256':r['adapter_sha256'],**v})
    return {'schema':'myriad.adapter_stress.v77','agents':len(out),'tests':sum(v['tests'] for v in out),'wins_vs_all':sum(v['wins_vs_all'] for v in out),'wins_vs_quadratic':sum(v['wins_vs_quadratic'] for v in out),'retention_failures':sum(v['retention_failures'] for v in out),'agents_all_wins':sum(v['wins_vs_all']==v['tests'] for v in out),'semantic_mastery_certified':False,'production_authority':False,'results':out}
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--root',required=True);p.add_argument('--count',type=int,default=16);p.add_argument('--authorize',action='store_true');a=p.parse_args()
    if not a.authorize:raise PermissionError('authorized research only')
    r=run(a.source,a.root,a.count)
    print(json.dumps({k:v for k,v in r.items() if k!='results'},sort_keys=True))
if __name__=='__main__':main()
