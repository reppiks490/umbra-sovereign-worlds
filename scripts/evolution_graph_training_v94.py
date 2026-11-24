"""Matched synthetic weighted graph-reasoning curricula, CPU research only.

Same learned message function, initialization, graph batches and optimizer-step
count; teacher-state versus closed-loop curriculum. Compute cost differs.
Independent Dijkstra labels and held-out graph sizes/weight distributions.
No model calls, user weights, semantic mastery, or production routing.
"""
import argparse,hashlib,heapq,json,math,random,time
from pathlib import Path
import torch
from torch import nn

SIZES=(4,8,16,32)
SCALES=(1,3)
TRAIN_SEEDS=(11001,11002,11003)
EVAL_SEEDS=(21001,21002,21003)
INF=10000.0
SCHEMA='myriad.graph_training.v94'


def integer(x,a,b):return type(x) is int and a<=x<=b


def reference(g,s):
    n=len(g);d=[math.inf]*n;d[s]=0;q=[(0,s)]
    while q:
        dist,u=heapq.heappop(q)
        if dist!=d[u]:continue
        for v,w in enumerate(g[u]):
            if w>0 and dist+w<d[v]:
                d[v]=dist+w;heapq.heappush(q,(d[v],v))
    if any(not math.isfinite(x) for x in d):raise ValueError('unreachable reference')
    return d


def batch(n,count,seed,scale=1):
    if n not in SIZES or type(n) is not int or not integer(count,1,64) or not integer(seed,0,2**63-1) or type(scale) is not int or scale not in SCALES:raise ValueError('graph bounds')
    rng=random.Random(seed);weights=[];sources=[];labels=[]
    for _ in range(count):
        p=list(range(n));rng.shuffle(p);g=[[-1]*n for _ in range(n)]
        for i in range(n-1):g[p[i]][p[i+1]]=rng.randint(1,20)*scale
        for i in range(n):
            for j in range(n):
                if i!=j and g[i][j]<0 and rng.random()<min(.4,3/n):g[i][j]=rng.randint(1,20)*scale
        s=p[0];d=reference(g,s)
        weights.append([[w/20 if w>0 else -1 for w in row] for row in g]);sources.append(s);labels.append([x/20 for x in d])
    return torch.tensor(weights,dtype=torch.float64),torch.tensor(sources,dtype=torch.long),torch.tensor(labels,dtype=torch.float64)


def source_mask(w,s):return torch.arange(w.shape[1],device=w.device)[None,:]==s[:,None]


def initial(w,s):
    return torch.where(source_mask(w,s),torch.zeros_like(w[:,:,0]),torch.full_like(w[:,:,0],INF))


def candidates(w,d):
    x=d[:,:,None].expand_as(w);valid=(w>0)&(x<INF)
    return x,valid


def exact_step(w,d,s):
    x,valid=candidates(w,d)
    c=torch.where(valid,x+w,torch.full_like(w,INF)).amin(dim=1)
    return torch.where(source_mask(w,s),torch.zeros_like(d),torch.minimum(d,c))


def teacher_states(w,s):
    rows=[initial(w,s)]
    for _ in range(w.shape[1]-1):rows.append(exact_step(w,rows[-1],s))
    return rows


def model(seed):
    if not integer(seed,0,100000):raise ValueError('model seed')
    # Keep initial weights matched without perturbing a caller's RNG.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        return nn.Sequential(nn.Linear(2,16),nn.ReLU(),nn.Linear(16,1),nn.Softplus()).double()


def learned_step(net,w,d,s):
    x,valid=candidates(w,d)
    inputs=torch.stack((torch.where(valid,x,0.0),torch.where(valid,w,0.0)),dim=-1)
    v=net(inputs).squeeze(-1)
    c=torch.where(valid,v,torch.full_like(w,INF)).amin(dim=1)
    return torch.where(source_mask(w,s),torch.zeros_like(d),torch.minimum(d,c))


def rollout(net,w,s):
    rows=[initial(w,s)]
    for _ in range(w.shape[1]-1):rows.append(learned_step(net,w,rows[-1],s))
    return rows


def weights(net):
    return [float(v) for p in net.parameters() for v in p.detach().flatten().tolist()]


def fingerprint(w,s):return hashlib.sha256(w.numpy().tobytes()+s.numpy().tobytes()).hexdigest()


def masked_loss(pred,target):
    mask=target<INF
    if not bool(mask.any()):raise ValueError('empty target')
    return ((pred[mask]-target[mask])**2).mean()


def train(net,arm,seed,*,steps=300,batch_size=12):
    if arm not in ('teacher','rollout') or not integer(seed,0,100000) or not integer(steps,1,512) or not integer(batch_size,1,32):raise ValueError('training bounds')
    opt=torch.optim.Adam(net.parameters(),lr=.003);hashes=[];losses=[];start=time.perf_counter()
    net.train()
    for k in range(steps):
        n=(4,8)[k%2];w,s,y=batch(n,batch_size,940000000+seed*10000+k)
        hashes.append(fingerprint(w,s));t=teacher_states(w,s)
        if not torch.allclose(t[-1],y,atol=1e-10,rtol=0):raise ValueError('independent reference mismatch')
        opt.zero_grad(set_to_none=True)
        if arm=='teacher':
            j=k%(n-1);loss=masked_loss(learned_step(net,w,t[j],s),t[j+1])
        else:
            p=rollout(net,w,s);loss=torch.stack([masked_loss(a,b) for a,b in zip(p[1:],t[1:])]).mean()
        if not bool(torch.isfinite(loss)):raise ValueError('nonfinite training')
        loss.backward();nn.utils.clip_grad_norm_(net.parameters(),5.0);opt.step()
        losses.append(float(loss.detach()))
    if not all(math.isfinite(x) for x in weights(net)):raise ValueError('nonfinite weights')
    return {'optimizer_steps':steps,'batch_fingerprints':hashes,'first_loss':losses[0],'last_loss':losses[-1],'mean_last_20':sum(losses[-20:])/len(losses[-20:]),'seconds':time.perf_counter()-start}


@torch.no_grad()
def evaluate(net,seed,*,graphs=16):
    if not integer(seed,0,100000) or not integer(graphs,1,32):raise ValueError('evaluation bounds')
    net.eval();rows=[]
    for n in SIZES:
        for scale in SCALES:
            w,s,y=batch(n,graphs,9410000000+seed*10000+n*10+scale,scale)
            exact=teacher_states(w,s)[-1];p=rollout(net,w,s)[-1]
            mask=~source_mask(w,s);e=(p-y).abs()[mask]*20;ref=(exact-y).abs()[mask]*20
            if not bool(torch.isfinite(e).all()):raise ValueError('nonfinite evaluation')
            rows.append({'n':n,'scale':scale,'graphs':graphs,'nodes':int(mask.sum()),'mae':float(e.mean()),'rmse':float((e**2).mean().sqrt()),'max_abs':float(e.max()),'within_one_unit':float((e<=1).double().mean()),'exact_reference_mae':float(ref.mean()),'production_authority':False})
    return rows


def summarize(rows):
    return {'mean_mae':sum(r['mae'] for r in rows)/len(rows),'id_mae':sum(r['mae'] for r in rows if r['n']<=8 and r['scale']==1)/2,'ood_mae':sum(r['mae'] for r in rows if r['n']>8 or r['scale']!=1)/6}


def experiment(steps=300,batch_size=12,graphs=16):
    torch.set_num_threads(1);results=[];candidates=[]
    for seed,eval_seed in zip(TRAIN_SEEDS,EVAL_SEEDS):
        a=model(seed);b=model(seed)
        initial_weights=weights(a)
        if initial_weights!=weights(b):raise ValueError('unmatched initialization')
        base=evaluate(a,eval_seed,graphs=graphs)
        ta=train(a,'teacher',seed,steps=steps,batch_size=batch_size);tb=train(b,'rollout',seed,steps=steps,batch_size=batch_size)
        if ta['batch_fingerprints']!=tb['batch_fingerprints']:raise ValueError('unmatched data')
        hashes=ta.pop('batch_fingerprints');tb.pop('batch_fingerprints');batch_sha=hashlib.sha256(''.join(hashes).encode()).hexdigest()
        ea=evaluate(a,eval_seed,graphs=graphs);eb=evaluate(b,eval_seed,graphs=graphs)
        if any(r['exact_reference_mae']>1e-8 for r in ea+eb):raise ValueError('reference disagreement')
        wa=weights(a);wb=weights(b)
        if wa==initial_weights or wb==initial_weights:raise ValueError('no weight update')
        results.append({'seed':seed,'eval_seed':eval_seed,'batch_sha256':batch_sha,'initial':base,'teacher':ea,'rollout':eb,'teacher_training':ta,'rollout_training':tb,'summaries':{'initial':summarize(base),'teacher':summarize(ea),'rollout':summarize(eb)}})
        candidates.append({'seed':seed,'initial':initial_weights,'teacher':wa,'rollout':wb})
    report={'schema':SCHEMA,'torch_version':str(torch.__version__),'device':'cpu','seeds':len(results),'parameters_per_model':len(candidates[0]['teacher']),'optimizer_steps':steps*2*len(results),'training_graph_instances':steps*batch_size*2*len(results),'evaluation_graphs_per_arm':graphs*len(SIZES)*len(SCALES)*len(results),'results':results,'rollout_ood_wins':sum(x['summaries']['rollout']['ood_mae']<x['summaries']['teacher']['ood_mae'] for x in results),'promotion_authorized':False,'production_authority':False,'semantic_mastery_certified':False,'actual_model_calls':0,'private_source_weights_used':False}
    return report,candidates


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--steps',type=int,default=300);p.add_argument('--authorize-synthetic-training',action='store_true');a=p.parse_args()
    if not a.authorize_synthetic_training:raise PermissionError('synthetic training authorization required')
    root=Path(a.root)
    if not root.is_dir() or root.is_symlink():raise ValueError('existing safe output root required')
    r,w=experiment(a.steps)
    for name,data in [('graph-training-v94-report.json',r),('graph-training-v94-weights.json',w)]:
        with (root/name).open('x',encoding='utf-8') as f:json.dump(data,f,sort_keys=True,allow_nan=False)
    print(json.dumps({k:v for k,v in r.items() if k!='results'},sort_keys=True))

if __name__=='__main__':main()
