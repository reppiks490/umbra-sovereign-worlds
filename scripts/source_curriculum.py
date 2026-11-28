"""Source-only continual curriculum, retention gate, and original equation audit."""
import argparse,hashlib,json,math,re
from fractions import Fraction
from pathlib import Path
from verified_reasoner import calculate,ReasoningError

MAX_EPOCHS=3
TRAIN_ROWS=6758
MAX_SCAN=MAX_EPOCHS*TRAIN_ROWS

def corpus_identity(rows):
    ids=[r['record_sha256'] for r in rows]
    if not ids or len(set(ids))!=len(ids) or any(not re.fullmatch('[a-f0-9]{64}',x) for x in ids):
        raise ValueError('corpus identity')
    return hashlib.sha256('\n'.join(ids).encode()).hexdigest()

def window(rows,cursor,count,encode):
    """Scan each record once per traversal; skip ineligible records visibly."""
    if type(cursor) is not int or cursor<0 or type(count) is not int or not 1<=count<=len(rows):
        raise ValueError('window bounds')
    corpus_identity(rows)
    selected=[]
    for i in range(len(rows)):
        r=rows[(cursor+i)%len(rows)]
        x=encode(r)
        if x is not None:selected.append((r,x))
        if len(selected)==count:return selected,cursor+i+1
    raise ValueError('insufficient eligible source records')

def gate(retention_before,retention_after,fresh_before,fresh_after):
    groups=(retention_before,retention_after,fresh_before,fresh_after)
    if any(len(v)!=8 or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in v) for v in groups):
        return False
    # Preserve established anchors while requiring improvement on a rotating
    # development block. This is candidate retention, not qualification.
    return (sum(fresh_after)/8<sum(fresh_before)/8-.01
            and sum(retention_after)/8<=sum(retention_before)/8+.02
            and max(a-b for a,b in zip(retention_after,retention_before))<=.10
            and max(a-b for a,b in zip(fresh_after,fresh_before))<=.10)

def trace_audit(rows):
    result={'records':len(rows),'records_with_annotations':0,'annotations':0,
            'verified':0,'mismatch':0,'unsupported':0,'fully_verified_records':0,
            'scope':'original annotated arithmetic only; not full-solution correctness or model evaluation'}
    for row in rows:
        annotations=re.findall(r'<<([^<>\r\n]{1,512})>>',row['answer'])
        if annotations:result['records_with_annotations']+=1
        good=0
        for annotation in annotations:
            result['annotations']+=1
            try:
                if annotation.count('=')!=1:raise ValueError('annotation schema')
                lhs,rhs=annotation.split('=')
                lhs=lhs.replace(',','').strip()
                rhs=rhs.replace(',','').strip()
                if not re.fullmatch(r'-?(?:[0-9]{1,24}(?:\.[0-9]{1,24})?|\.[0-9]{1,24})',rhs):raise ValueError('label')
                exact=Fraction(calculate(lhs)['value']);expected=Fraction(rhs)
                if exact==expected:result['verified']+=1;good+=1
                else:result['mismatch']+=1
            except (ValueError,ZeroDivisionError,ReasoningError):result['unsupported']+=1
        if annotations and good==len(annotations):result['fully_verified_records']+=1
    return result

def run(root):
    from student_council import load_corpus
    from native_lora_train import atomic
    rows=load_corpus(root)
    report={'status':'audited','training':trace_audit(rows['train']),
            'development':trace_audit(rows['validation']),
            'training_identity':corpus_identity(rows['train']),
            'validation_identity':corpus_identity(rows['validation']),
            'test_partition_evaluated':False,'weight_training':False,'production_authority':False}
    out=root/'experience'/'source-knowledge'/'human-corpus'/'curriculum-audit.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    atomic(out,report)
    return report

def pending_reconciliation(state):
    return isinstance(state,dict) and (state.get('status')=='attempting' or bool(state.get('pending_attempt')))

def campaign_eligible(state):
    if pending_reconciliation(state):return False
    cur=state.get('curriculum',{})
    cursor=cur.get('train_cursor',0)
    attempts=cur.get('attempts',0)
    return type(cursor) is int and 0<=cursor<MAX_SCAN and type(attempts) is int and 0<=attempts<MAX_SCAN

def verify_development_isolation(train,validation):
    """Authenticate both accessible splits without reading the protected test partition."""
    from human_corpus import validate
    seen=set()
    for rows in (train,validation):
        for row in rows:
            verified=validate({'question':row['question'],'answer':row['answer']})
            question=verified['question_sha256']
            if row.get('question_sha256')!=question:raise ValueError('question identity')
            if row.get('record_sha256')!=verified['record_sha256']:raise ValueError('record identity')
            if question in seen:raise ValueError('question overlap')
            seen.add(question)

def plan_cycle(corpus, prior, steps, encode):
    """Plan a resumable source-only window. Advance only after a recorded run."""
    if not 1<=steps<=8:raise ValueError('optimizer step budget')
    train,validation=corpus['train'],corpus['validation']
    verify_development_isolation(train,validation)
    ti,vi=corpus_identity(train),corpus_identity(validation)
    if prior and (prior.get('train_identity')!=ti or prior.get('validation_identity')!=vi):
        raise ValueError('curriculum source changed')
    tc,vc=prior.get('train_cursor',0),prior.get('validation_cursor',0)
    retention,_=window(validation,0,8,encode)
    anchors={r['record_sha256'] for r,x in retention}
    fresh_pool=[r for r in validation if r['record_sha256'] not in anchors]
    training,tn=window(train,tc,steps,encode)
    fresh,vn=window(fresh_pool,vc,8,encode)
    if tn>MAX_EPOCHS*len(train):raise ValueError('curriculum traversal budget exhausted')
    return {'training':training,'retention':retention,'fresh':fresh,'next_state':{
        'train_identity':ti,'validation_identity':vi,'train_cursor':tn,
        'validation_cursor':vn,'completed_steps':prior.get('completed_steps',0)+steps,
        'attempts':prior.get('attempts',0)+1,'train_rows':len(train),
        'validation_rows':len(validation),'max_epochs':MAX_EPOCHS}}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);a=p.parse_args();print(json.dumps(run(a.root)))
