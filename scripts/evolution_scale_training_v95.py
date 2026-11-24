"""Matched synthetic scale-equivariance intervention; no production promotion.

The homogeneous wrapper explicitly supplies the positive scale factor, so
scale invariance is architectural, not evidence of learned arithmetic mastery.
"""
import argparse,hashlib,json,math
from pathlib import Path
import torch
from torch import nn
import evolution_graph_training_v94 as base

TRAIN_SEEDS=(12001,12002,12003)
EVAL_SEEDS=(31001,31002,31003)
SCALES=(1,3,5)

class Homogeneous(nn.Module):
    def __init__(self,seed):
        super().__init__();self.net=base.model(seed)
    def forward(self,x):
        total=x.sum(dim=-1,keepdim=True)
        safe=torch.where(total>0,total,torch.ones_like(total))
        return total*self.net(x/safe)

def model(seed):return Homogeneous(seed)

def scaled(w,factor):
    if type(factor) is not int or factor not in SCALES:raise ValueError('unsupported scale')
    return torch.where(w>0,w*factor,w)

@torch.no_grad()
def evaluate(net,seed,*,graphs=16):
    if not base.integer(seed,0,100000) or not base.integer(graphs,1,32):raise ValueError('evaluation bounds')
    net.eval();rows=[]
    for n in base.SIZES:
        w,s,y=base.batch(n,graphs,9510000000+seed*10000+n)
        original=base.rollout(net,w,s)[-1];mask=~base.source_mask(w,s)
        for factor in SCALES:
            z=scaled(w,factor);target=y*factor
            pred=base.rollout(net,z,s)[-1];exact=base.teacher_states(z,s)[-1]
            # Independent integer-weight Dijkstra check at every scale.
            labels=torch.tensor([base.reference(g,int(src)) for g,src in zip(torch.round(z*20).tolist(),s)],dtype=torch.float64)/20
            if not torch.allclose(labels,target,atol=1e-10,rtol=0):raise ValueError('scaled reference disagreement')
            err=(pred-target).abs()[mask]*20
            if not bool(torch.isfinite(err).all()):raise ValueError('nonfinite evaluation')
            rows.append({'n':n,'scale':factor,'graphs':graphs,'base_graph_sha256':base.fingerprint(w,s),'mae':float(err.mean()),'normalized_mae':float(err.mean())/factor,'reference_mae':float((exact-labels).abs()[mask].mean()*20),'equivariance_error':float((pred-original*factor).abs()[mask].max()*20)})
    return rows

def summary(rows):
    id_rows=[r for r in rows if r['n']<=8 and r['scale']==1]
    ood=[r for r in rows if r['n']>8 or r['scale']!=1]
    return {'id_mae':sum(r['mae'] for r in id_rows)/len(id_rows),'ood_mae':sum(r['mae'] for r in ood)/len(ood),'ood_normalized_mae':sum(r['normalized_mae'] for r in ood)/len(ood),'max_equivariance_error':max(r['equivariance_error'] for r in rows)}

def experiment(steps=300,batch_size=12,graphs=16):
    torch.set_num_threads(1);results=[];weights=[]
    for seed,eval_seed in zip(TRAIN_SEEDS,EVAL_SEEDS):
        a=base.model(seed);b=model(seed);initial=base.weights(a)
        if initial!=base.weights(b):raise ValueError('unmatched weights')
        ia=evaluate(a,eval_seed,graphs=graphs);ib=evaluate(b,eval_seed,graphs=graphs)
        ta=base.train(a,'teacher',seed,steps=steps,batch_size=batch_size);tb=base.train(b,'teacher',seed,steps=steps,batch_size=batch_size)
        if ta['batch_fingerprints']!=tb['batch_fingerprints']:raise ValueError('unmatched data')
        hashes=ta.pop('batch_fingerprints');tb.pop('batch_fingerprints')
        ea=evaluate(a,eval_seed,graphs=graphs);eb=evaluate(b,eval_seed,graphs=graphs)
        if any(r['reference_mae']>1e-8 for r in ea+eb):raise ValueError('reference mismatch')
        if max(r['equivariance_error'] for r in eb)>1e-8:raise ValueError('equivariance violation')
        wa=base.weights(a);wb=base.weights(b)
        if wa==initial or wb==initial:raise ValueError('unchanged weights')
        results.append({'seed':seed,'eval_seed':eval_seed,'training_batches_sha256':hashlib.sha256(''.join(hashes).encode()).hexdigest(),'initial_unstructured':ia,'initial_homogeneous':ib,'unstructured':ea,'homogeneous':eb,'unstructured_training':ta,'homogeneous_training':tb,'summaries':{k:summary(v) for k,v in [('initial_unstructured',ia),('initial_homogeneous',ib),('unstructured',ea),('homogeneous',eb)]}})
        weights.append({'seed':seed,'initial':initial,'unstructured':wa,'homogeneous':wb})
    return {'schema':'myriad.scale_training.v95','torch_version':str(torch.__version__),'seeds':len(results),'parameters_per_model':len(weights[0]['homogeneous']),'optimizer_steps':steps*2*len(results),'training_graph_instances':steps*batch_size*2*len(results),'base_eval_graphs_per_arm':graphs*len(base.SIZES)*len(results),'scaled_eval_observations_per_arm':graphs*len(base.SIZES)*len(SCALES)*len(results),'homogeneous_ood_wins':sum(r['summaries']['homogeneous']['ood_mae']<r['summaries']['unstructured']['ood_mae'] for r in results),'results':results,'promotion_authorized':False,'production_authority':False,'semantic_mastery_certified':False,'actual_model_calls':0,'private_source_weights_used':False},weights

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--steps',type=int,default=300);p.add_argument('--authorize-synthetic-training',action='store_true');a=p.parse_args()
    if not a.authorize_synthetic_training:raise PermissionError('synthetic training authorization required')
    root=Path(a.root)
    if not root.is_dir() or root.is_symlink():raise ValueError('existing safe output root required')
    r,w=experiment(a.steps)
    for name,data in [('scale-training-v95-report.json',r),('scale-training-v95-weights.json',w)]:
        with (root/name).open('x',encoding='utf-8') as f:json.dump(data,f,sort_keys=True,allow_nan=False)
    print(json.dumps({k:v for k,v in r.items() if k!='results'},sort_keys=True))

if __name__=='__main__':main()
