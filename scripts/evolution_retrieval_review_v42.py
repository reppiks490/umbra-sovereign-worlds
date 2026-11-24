"""Actual source retrieval followed by a digest-bound, non-executable LLM review."""
from __future__ import annotations
import argparse,ast,json,math,os,time
from pathlib import Path
import evolution_teacher_v40 as teacher
import evolution_live_research_v38 as live
import evolution_model_evidence_v24 as ev
import evolution_fleet_scale_v36 as scale
import evolution_native_ollama_v33 as native
CODER='qwen2.5-coder:1.5b'
CODER_DIGEST='d7372fd828518a4d38b1eb196c673c31a85f2ed302b3d1e406c4c2d1b64a0668'
QUERIES=('fenced worker lease ownership and expiration duplicate settlement',
 'checkpoint lineage previous hashes finite FP16 weights integrity',
 'independent evaluation rubric wrong answers receipt authentication',
 'memory admission bounded inference elapsed time disk capacity',
 'source excerpt digest citations and untrusted model output',
 'idempotent enrollment SQLite transaction durable identity')
def query(slot):return QUERIES[slot%len(QUERIES)]
def packet(root,hit,goal):
    root=Path(root).resolve()
    if hit['file'] not in teacher.FILES or not isinstance(hit['function'],str):raise ValueError('unapproved source')
    path=root/hit['file']
    if path.is_symlink() or not path.is_file() or path.stat().st_size>256*1024:raise ValueError('invalid source')
    raw=path.read_bytes()
    if teacher.sha(raw)!=hit['source_sha256']:raise ValueError('retrieved source changed')
    text=raw.decode('utf-8-sig');lines=text.splitlines()
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==hit['function']]
    if len(nodes)!=1:raise ValueError('function not found')
    n=nodes[0];ids=[];excerpt=[]
    for i in range(n.lineno,min(n.end_lineno+1,n.lineno+20)):
        line=f'{i}: {lines[i-1]}'
        if len('\n'.join(excerpt+[line]))>2000:break
        ids.append(i);excerpt.append(line)
    if not ids:raise ValueError('empty excerpt')
    p={'schema':'myriad.retrieval_review.v42','goal':goal,'source':{'file':hit['file'],'function':hit['function'],'file_sha256':hit['source_sha256'],'lines':ids,'excerpt':'\n'.join(excerpt),'partial':ids[-1]!=n.end_lineno},'retrieval_similarity':hit['similarity'],'production_authority':False}
    p['packet_sha256']=teacher.sha(ev.canonical(p));return p
def assess(p,raw):return live.assess(p,raw)
def run(private,key,slot):
    root=Path(__file__).resolve().parent
    goal=query(slot)
    retrieval=teacher.retrieve(private,key,goal)
    if retrieval.get('schema')!='myriad.retrieval.v40':return {'retrieval':retrieval,'review_status':'deferred'}
    result={'retrieval':retrieval,'review_status':'deferred_memory','proposals_executed':0}
    if scale.free_mb()<2200:return result
    native._pin(11434,CODER,CODER_DIGEST,10)
    p=packet(root,retrieval['top'][0],goal)
    raw,rh,tokens=live.infer(p,CODER,CODER_DIGEST)
    record={'schema':'myriad.retrieval_review.v42','packet':p,'model':CODER,'observed_model_digest':CODER_DIGEST,'raw':raw,'response_sha256':rh,'tokens':tokens,'assessment':assess(p,raw),'retrieval_hmac':retrieval['hmac_sha256'],'production_authority':False,'model_origin_authenticated':False,'proposals_executed':0}
    teacher.save(private,'retrieval-review',record,key)
    result.update(review_status='completed',review={k:v for k,v in record.items() if k not in ('raw','packet')},source={'file':p['source']['file'],'function':p['source']['function'],'line_count':len(p['source']['lines'])})
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--slot',type=int,default=0);a=p.parse_args()
    if not a.authorize:raise PermissionError('explicit research authorization required')
    print(json.dumps(run(Path(a.private),ev.secret(),a.slot),sort_keys=True))
if __name__=='__main__':main()
