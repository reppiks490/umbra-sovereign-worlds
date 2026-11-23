#!/usr/bin/env python3
"""MYRIAD PENTARCH neural bank lineage, expansion and *real* PyTorch subset training.

Never equates a reserved/sparse byte with a trained parameter. Historical full
bank data must be supplied and verified before expanding their storage. Originals
are read-only; extensions are separate content-addressed data layers.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, shutil, sqlite3, zipfile
from pathlib import Path

AGENTS=10_000
ABILITIES=10_000_000
BASE_AGENT_WIDTH=411_000
BASE_ABILITY_WIDTH=32
EXPANDED_AGENT_WIDTH=1_500_000
EXPANDED_ABILITY_WIDTH=500
DTYPE_BYTES=2
BASE_AGENT_BYTES=AGENTS*BASE_AGENT_WIDTH*DTYPE_BYTES
BASE_ABILITY_BYTES=ABILITIES*BASE_ABILITY_WIDTH*DTYPE_BYTES
TARGET_AGENT_BYTES=AGENTS*EXPANDED_AGENT_WIDTH*DTYPE_BYTES
TARGET_ABILITY_BYTES=ABILITIES*EXPANDED_ABILITY_WIDTH*DTYPE_BYTES
EXTRA_AGENT_BYTES=TARGET_AGENT_BYTES-BASE_AGENT_BYTES
EXTRA_ABILITY_BYTES=TARGET_ABILITY_BYTES-BASE_ABILITY_BYTES
SCHEMA='myriad.weight_fabric.v1'


def sha256(data): return hashlib.sha256(data).hexdigest()


def plan():
    return {'schema':SCHEMA,'agents':AGENTS,'abilities':ABILITIES,
            'source_agent_bytes':BASE_AGENT_BYTES,'source_ability_bytes':BASE_ABILITY_BYTES,
            'target_agent_bytes':TARGET_AGENT_BYTES,'target_ability_bytes':TARGET_ABILITY_BYTES,
            'extra_agent_bytes':EXTRA_AGENT_BYTES,'extra_ability_bytes':EXTRA_ABILITY_BYTES,
            'agent_parameters_per_identity':EXPANDED_AGENT_WIDTH,
            'ability_parameters_per_identity':EXPANDED_ABILITY_WIDTH,
            'agent_additional_parameters_per_identity':EXPANDED_AGENT_WIDTH-BASE_AGENT_WIDTH,
            'ability_additional_parameters_per_identity':EXPANDED_ABILITY_WIDTH-BASE_ABILITY_WIDTH,
            'dtype':'IEEE754 little-endian FP16','origin_required':'historical verified source files AND ledgers',
            'expanded_weights_trained':False,'sparse_files_are_training_proof':False,
            'additional_banks':[{'name':'experiment_replay','target_bytes':64_000_000_000,'status':'proposed_capacity_only'},
                                {'name':'causal_evidence','target_bytes':16_000_000_000,'status':'proposed_capacity_only'},
                                {'name':'retrieval_memory','target_bytes':8_000_000_000,'status':'proposed_capacity_only'}]}


def verify_sample(archive):
    """Read the actual ten-agent, 10,000-ability saved checkpoint, row by row."""
    with zipfile.ZipFile(archive) as z:
        names={p.filename for p in z.infolist()}
        required={'manifest.json','agent_weights.fp16','ability_weights.fp16','ability_steps.u8'}
        if not required<=names or any(z.getinfo(x).file_size>25_000_000 for x in required):
            raise ValueError('Invalid or oversized portable checkpoint')
        m=json.loads(z.read('manifest.json'))
        if m.get('schema')!='myriad.portable_joint_bank.v1':raise ValueError('Wrong saved-bank schema')
        agent=z.read('agent_weights.fp16');abilities=z.read('ability_weights.fp16');steps=z.read('ability_steps.u8')
        if len(agent)!=10*BASE_AGENT_WIDTH*2 or len(abilities)!=10_000*BASE_ABILITY_WIDTH*2 or len(steps)!=10_000:
            raise ValueError('Incorrect sample extent')
        if sha256(agent)!=m['agent_weight_sha256'] or sha256(abilities)!=m['ability_weight_sha256']:
            raise ValueError('Checkpoint hash mismatch')
        for item in m['agent_rows']:
            i=item['agent'];raw=agent[(i-1)*BASE_AGENT_WIDTH*2:i*BASE_AGENT_WIDTH*2]
            if sha256(raw)!=item['sha256']:raise ValueError(f'Agent row {i} mismatch')
        for item in m['ability_ranges']:
            lo,hi=item['start']-1,item['end']
            if sha256(abilities[lo*BASE_ABILITY_WIDTH*2:hi*BASE_ABILITY_WIDTH*2])!=item['sha256']:
                raise ValueError('Ability block mismatch')
            if sha256(steps[lo:hi])!=item['steps_sha256']:raise ValueError('Ability step receipt mismatch')
        return {'schema':SCHEMA,'source':'original saved ten-agent checkpoint',
                'verified_agents':10,'verified_ability_adapters':10_000,
                'complete_original_10k_agent_bank_verified':False,
                'complete_original_10m_ability_bank_verified':False,
                'agent_sha256':sha256(agent),'ability_sha256':sha256(abilities),'ability_steps_sha256':sha256(steps),
                'source_archive_sha256':sha256(Path(archive).read_bytes()),
                'source_training_claim':'archived synthetic training only, no external mastery certification'}


def verify_full(agent_dir, ability_dir):
    a=Path(agent_dir);b=Path(ability_dir)
    file_a=a/'agent_weights.fp16';file_b=b/'weights.fp16'
    for path,size in ((file_a,BASE_AGENT_BYTES),(file_b,BASE_ABILITY_BYTES)):
        if not path.is_file() or path.stat().st_size!=size:raise FileNotFoundError(f'Missing exact historical full bank: {path} {size} bytes required')
    db_a=a/'weight_ledger.sqlite3';db_b=b/'ability_ledger.sqlite3'
    if not db_a.is_file() or not db_b.is_file():raise FileNotFoundError('Original training ledgers required')
    # SQLite table counts alone are insufficient, but catch a missing/empty ledger.
    conn=sqlite3.connect(f'file:{db_a}?mode=ro',uri=True)
    try: agent_count=conn.execute("SELECT COUNT(*) FROM agent_weights WHERE status='trained' AND steps>=1").fetchone()[0]
    finally:conn.close()
    conn=sqlite3.connect(f'file:{db_b}?mode=ro',uri=True)
    try:batch_count=conn.execute('SELECT COUNT(*) FROM batches WHERE gradient_steps>=1').fetchone()[0]
    finally:conn.close()
    if agent_count!=AGENTS or batch_count<200:raise ValueError('Historical ledger incomplete')
    # A 40GB sparse allocation is NOT evidence of trained history. Verify every
    # existing row against its own historic ledger digest before creating ANY
    # additional capacity. Stream reads, never map entire bank into memory.
    conn=sqlite3.connect(f'file:{db_a}?mode=ro',uri=True)
    try:
        agent_receipts=conn.execute("SELECT agent,sha256,steps FROM agent_weights WHERE status='trained' ORDER BY agent").fetchall()
    finally:conn.close()
    if len(agent_receipts)!=AGENTS or any(row[0]!=i or row[2]<1 for i,row in enumerate(agent_receipts,1)):
        raise ValueError('Full agent ledger has missing or untrained rows')
    with file_a.open('rb') as f:
        for agent,digest,steps in agent_receipts:
            chunk=f.read(BASE_AGENT_WIDTH*DTYPE_BYTES)
            if len(chunk)!=BASE_AGENT_WIDTH*DTYPE_BYTES or sha256(chunk)!=digest:
                raise ValueError(f'Historic trained agent {agent} failed SHA-256 integrity')
    conn=sqlite3.connect(f'file:{db_b}?mode=ro',uri=True)
    try:
        batches=conn.execute('SELECT start_id,end_id,sha256,gradient_steps FROM batches ORDER BY start_id').fetchall()
    finally:conn.close()
    if len(batches)<200 or batches[0][0]!=1 or batches[-1][1]!=ABILITIES:
        raise ValueError('Ability ledger coverage incomplete')
    steps_path=b/'steps.u8';states_path=b/'status.u8'
    if not steps_path.is_file() or not states_path.is_file() or steps_path.stat().st_size!=ABILITIES or states_path.stat().st_size!=ABILITIES:
        raise ValueError('Ability training status/step records missing')
    with file_b.open('rb') as f,steps_path.open('rb') as sf,states_path.open('rb') as stf:
        prior=0
        for lo,hi,digest,steps in batches:
            if lo!=prior+1 or hi<lo or steps<1:raise ValueError('Invalid historic ability batch continuity')
            size=(hi-lo+1)*BASE_ABILITY_WIDTH*DTYPE_BYTES
            chunk=f.read(size);state=stf.read(hi-lo+1);train_steps=sf.read(hi-lo+1)
            if len(chunk)!=size or sha256(chunk)!=digest or len(state)!=hi-lo+1 or any(v!=2 for v in state) or any(v==0 for v in train_steps):
                raise ValueError(f'Historic ability batch {lo}:{hi} failed integrity audit')
            prior=hi
        if prior!=ABILITIES:raise ValueError('Incomplete historic ability bank')
    return {'source_agent_bytes':file_a.stat().st_size,'source_ability_bytes':file_b.stat().st_size,
            'historical_agent_ledger_rows':agent_count,'historical_ability_ledger_batches':batch_count,
            'ledger_structure_verified':True,'entire_weight_content_hash_verified':True,
            'requires_full_row_and_batch_digest_audit_before_training':False}


def provision(agent_dir,ability_dir,out,approve=False):
    evidence=verify_full(agent_dir,ability_dir)
    if not approve: raise PermissionError('Expansion requires --approve after reviewing full-source audit')
    out=Path(out).resolve()
    if out.exists() and any(out.iterdir()):raise FileExistsError('Refusing to overwrite nonempty destination')
    out.mkdir(parents=True,exist_ok=True)
    # Place new extension shards in separate immutable-lineage layers. A truncate
    # is a reservation, NOT initialized or trained parameters.
    fn_a=out/'agent_extensions.fp16';fn_b=out/'ability_extensions.fp16'
    for fn,size in ((fn_a,EXTRA_AGENT_BYTES),(fn_b,EXTRA_ABILITY_BYTES)):
        with fn.open('xb') as f:f.truncate(size)
    info={'schema':SCHEMA,'origin':{'agent_source':str(Path(agent_dir).resolve()),'ability_source':str(Path(ability_dir).resolve()),'audit':evidence},
          'expanded_schema':plan(),'extensions':[{'path':fn_a.name,'reserved_bytes':EXTRA_AGENT_BYTES,'trained_rows':0},
                                                   {'path':fn_b.name,'reserved_bytes':EXTRA_ABILITY_BYTES,'trained_rows':0}],
          'status':'sparse_reserved_only_UNTRAINED','live_execution_authorized':False}
    (out/'LINEAGE_MANIFEST.json').write_text(json.dumps(info,indent=2)+'\n')
    return info


def sample_train(archive,out,agents=3,steps=2):
    """Real autograd on copied verified historic 411k weights; archived base untouched.

    A short synthetic adapter-conditioned exercise is a training-path acceptance
    test and makes NO real-world mastery claim. Outputs stay quarantined/private.
    """
    if not 1<=agents<=10 or not 1<=steps<=30:raise ValueError('Budget exceeded')
    import numpy as np
    import torch
    from torch import nn
    from torch.nn.utils import parameters_to_vector,vector_to_parameters
    torch.set_num_threads(1)
    proof=verify_sample(archive)
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise FileExistsError('Fresh isolated output directory required')
    out.mkdir(parents=True,exist_ok=True)
    class AgentPolicy(nn.Module):
        def __init__(self):
            super().__init__()
            self.layers=nn.Sequential(nn.Linear(32,512),nn.GELU(),nn.Linear(512,544),nn.GELU(),nn.Linear(544,208),nn.GELU(),nn.Linear(208,8))
        def forward(self,x):return self.layers(x)
    records=[]
    with zipfile.ZipFile(archive) as z:
        a=z.read('agent_weights.fp16');b=z.read('ability_weights.fp16')
    for i in range(1,agents+1):
        raw=a[(i-1)*BASE_AGENT_WIDTH*2:i*BASE_AGENT_WIDTH*2]
        adapter=np.frombuffer(b[(i-1)*1000*64:i*1000*64],dtype='<f2').reshape(1000,32).astype(np.float32)
        context=torch.tensor(adapter.mean(axis=0),dtype=torch.float32)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(44171+i)
            g=torch.Generator(device='cpu').manual_seed(771_337+i)
            model=AgentPolicy()
            assert sum(p.numel() for p in model.parameters())==BASE_AGENT_WIDTH
            vector_to_parameters(torch.from_numpy(np.frombuffer(raw,dtype='<f2').astype(np.float32).copy()),model.parameters())
            train_x=torch.randn(48,32,generator=g)+context*.2
            holdout_x=torch.randn(48,32,generator=g)+context*.2
            def teacher(x):return (x[:,:8]*torch.arange(1,9,dtype=torch.float32).reshape(1,8)*.12)+context[:8]*.03
            train_y=teacher(train_x); holdout_y=teacher(holdout_x)
            opt=torch.optim.AdamW(model.parameters(),lr=.0008,weight_decay=0)
            with torch.no_grad():before=float(nn.functional.mse_loss(model(holdout_x),holdout_y))
            for _ in range(steps):
                opt.zero_grad(set_to_none=True)
                loss=nn.functional.mse_loss(model(train_x),train_y);loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step()
            weights=parameters_to_vector(model.parameters()).detach().numpy().astype('<f2')
            # Quantization is part of verification: score the exact saved weights.
            saved=AgentPolicy()
            vector_to_parameters(torch.from_numpy(weights.astype(np.float32).copy()),saved.parameters())
            with torch.no_grad():after=float(nn.functional.mse_loss(saved(holdout_x),holdout_y))
        if not math.isfinite(after) or sha256(weights.tobytes())==sha256(raw):raise RuntimeError('No verifiable candidate update')
        fname=f'AG-{i:05d}.candidate.fp16'
        with (out/fname).open('xb') as f:f.write(weights.tobytes());f.flush();os.fsync(f.fileno())
        records.append({'agent':i,'source_sha256':sha256(raw),'candidate_sha256':sha256(weights.tobytes()),
                        'used_original_ability_vectors':1000,'gradient_steps':steps,
                        'quantized_holdout_before':before,'quantized_holdout_after':after,
                        'holdout_improved':after<before,'trained_parameters':BASE_AGENT_WIDTH,
                        'original_modified':False,'promotion':'quarantine_only','candidate':fname})
    report={'schema':'myriad.weight_fabric.synthetic_training.v1','sample_evidence':proof,
            'target_agent_bank_bytes':TARGET_AGENT_BYTES,'target_ability_bank_bytes':TARGET_ABILITY_BYTES,
            'expanded_new_parameters_trained':0,'source_checkpoint_agent_count':10,
            'new_candidate_count':len(records),'results':records,
            'model_intelligence_certified':False,'market_profitability_certified':False}
    (out/'SYNTHETIC_TRAINING_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='cmd',required=True)
    s.add_parser('plan')
    x=s.add_parser('inspect-sample');x.add_argument('--archive',required=True)
    x=s.add_parser('inspect-full');x.add_argument('--agent-dir',required=True);x.add_argument('--ability-dir',required=True)
    x=s.add_parser('provision');x.add_argument('--agent-dir',required=True);x.add_argument('--ability-dir',required=True);x.add_argument('--out',required=True);x.add_argument('--approve',action='store_true')
    x=s.add_parser('train-sample');x.add_argument('--archive',required=True);x.add_argument('--out',required=True);x.add_argument('--agents',type=int,default=3);x.add_argument('--steps',type=int,default=2)
    a=p.parse_args(); kw=vars(a).copy();kw.pop('cmd')
    result={'plan':plan,'inspect-sample':verify_sample,'inspect-full':verify_full,'provision':provision,'train-sample':sample_train}[a.cmd](**{k.replace('-','_'):v for k,v in kw.items()})
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()