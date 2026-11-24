#!/usr/bin/env python3
"""MYRIAD v2.9 HMAC-protected, exact-byte private model artifact inventory.

This is a *local integrity and admission* gate, not supply-chain origin attestation.
Never loads pickle or PyTorch deserialization, auto-downloads, deploys, or trades.
"""
from __future__ import annotations
import argparse
import hashlib
import hmac
import json
import os
import re
import stat
import struct
from pathlib import Path

SCHEMA='myriad.model_artifact_registry.v29'
KEY_ENV='MYRIAD_ARTIFACT_REGISTRY_KEY'
MAX_FILE_BYTES=2_000_000_000
MAX_FILES=256
MAX_TOTAL_BYTES=12_000_000_000
MAX_HEADER_BYTES=1_048_576
ALLOWED_SUFFIXES={'.fp16','.safetensors','.json'}
DTYPE_BYTES={'F16':2,'BF16':2,'F32':4,'F64':8,'I64':8,'I32':4,'I16':2,'I8':1,'U8':1,'BOOL':1}
BASENAME=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,120}\Z')
PIN=re.compile(r'[0-9a-fA-F]{40}\Z')


def unique_json(data):
    def reject_duplicates(pairs):
        out={}
        for k,v in pairs:
            if k in out:raise ValueError('Duplicate JSON field is forbidden')
            out[k]=v
        return out
    return json.loads(data,object_pairs_hook=reject_duplicates,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON literal')))

def canonical(data):return json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def require_key():
    key=os.environ.get(KEY_ENV,'')
    if not isinstance(key,str) or not 32<=len(key)<=1024:
        raise PermissionError('Set a strong, private artifact-registry signing key')
    return key

def seal(payload,key):
    if not isinstance(key,str) or len(key)<32:raise PermissionError('Invalid signing key')
    content={k:v for k,v in payload.items() if k!='hmac_sha256'}
    content['hmac_sha256']=hmac.new(key.encode(),canonical(content),hashlib.sha256).hexdigest()
    return content

def check_hmac(data,key):
    if not isinstance(data,dict):raise ValueError('Invalid registry document')
    sig=data.get('hmac_sha256')
    if type(sig) is not str or not re.fullmatch(r'[0-9a-f]{64}',sig):raise ValueError('Missing signature')
    expected=seal(data,key)['hmac_sha256']
    if not hmac.compare_digest(sig,expected):raise ValueError('Artifact registry HMAC mismatch')

def valid_name(name):
    if type(name) is not str or not BASENAME.fullmatch(name) or name in ('.','..') or '..' in name:
        raise ValueError('Unsafe artifact name')
    if Path(name).suffix not in ALLOWED_SUFFIXES:raise ValueError('Disallowed model artifact extension')
    return name

def validate_safetensors(path):
    path=Path(path)
    with path.open('rb') as f:
        prefix=f.read(8)
        if len(prefix)!=8:raise ValueError('Short safetensors prefix')
        n=struct.unpack('<Q',prefix)[0]
        total=path.stat().st_size
        if n<2 or n>MAX_HEADER_BYTES or n+8>total:raise ValueError('Invalid safe header extent')
        raw=f.read(n)
        if not raw.startswith(b'{'):raise ValueError('Safetensors header must be JSON object')
    try:header=unique_json(raw.decode('utf-8'))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise ValueError('Invalid safetensors header JSON') from exc
    if type(header) is not dict or not header:raise ValueError('Empty safetensors header')
    data_size=total-8-n
    segments=[]
    for k,v in header.items():
        if k=='__metadata__':
            if type(v) is not dict or any(type(t) is not str for t in v.values()):raise ValueError('Malformed tensor metadata')
            continue
        if type(k) is not str or not k or type(v) is not dict or set(v)!={'dtype','shape','data_offsets'}:
            raise ValueError('Malformed tensor header field')
        dtype=v['dtype'];shape=v['shape'];offsets=v['data_offsets']
        if dtype not in DTYPE_BYTES or type(shape) is not list or len(shape)>16 or any(type(x) is not int or x<0 or x>10**9 for x in shape):
            raise ValueError('Unsupported tensor dtype or shape')
        if type(offsets) is not list or len(offsets)!=2 or any(type(x) is not int or x<0 for x in offsets):
            raise ValueError('Invalid tensor offsets')
        a,b=offsets
        size=DTYPE_BYTES[dtype]
        for x in shape:
            size*=x
            if size>MAX_FILE_BYTES:raise ValueError('Tensor exceeds pilot limit')
        if b-a!=size or b>data_size:raise ValueError('Tensor offset does not match dtype/shape/bytes')
        if a!=b:segments.append((a,b))
    if not segments or segments[0][0]<0:raise ValueError('Missing tensor data')
    segments.sort()
    pos=0
    for start,end in segments:
        if start!=pos or end<=start:raise ValueError('Overlapping or unindexed tensor byte range')
        pos=end
    if pos!=data_size:raise ValueError('Unindexed safetensors tail')
    return True

def hash_file(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Symbolic links and absent artifact files rejected')
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    try:
        initial=os.fstat(fd)
        if not stat.S_ISREG(initial.st_mode) or initial.st_size<1 or initial.st_size>MAX_FILE_BYTES:
            raise ValueError('Invalid artifact regular file size')
        h=hashlib.sha256()
        with os.fdopen(fd,'rb',closefd=False) as f:
            while True:
                data=f.read(1_048_576)
                if not data:break
                h.update(data)
        after=os.fstat(fd)
        if (initial.st_dev,initial.st_ino,initial.st_size,initial.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
            raise ValueError('Artifact modified during reading')
        if path.suffix=='.fp16' and initial.st_size%2:raise ValueError('FP16 payload length must be even')
        if path.suffix=='.json':
            if initial.st_size>1_048_576:raise ValueError('Oversized JSON metadata file')
            unique_json(path.read_text())
        if path.suffix=='.safetensors':validate_safetensors(path)
        return {'name':path.name,'size_bytes':initial.st_size,'sha256':h.hexdigest(),'format':path.suffix.lstrip('.')}
    finally:
        os.close(fd)

def inspect(root):
    root=Path(root)
    if not root.is_dir() or root.is_symlink():raise ValueError('Artifact root must be a real existing directory')
    children=sorted(root.iterdir(),key=lambda p:p.name)
    if not children or len(children)>MAX_FILES:raise ValueError('Empty or oversized model cohort')
    rows=[];total=0
    for p in children:
        valid_name(p.name)
        if not p.is_file() or p.is_symlink():raise ValueError('Nested, unsafe, or symlinked artifact')
        row=hash_file(p);rows.append(row);total+=row['size_bytes']
        if total>MAX_TOTAL_BYTES:raise ValueError('Pilot registry resource budget exceeded')
    return rows,total

def metadata(model_id,source,license_id,revision):
    if type(model_id) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',model_id):raise ValueError('Invalid model label')
    if source not in ('imported_unverified','huggingface_pinned'):raise ValueError('Unsupported source type')
    if type(license_id) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',license_id):raise ValueError('Invalid declared license label')
    if source=='huggingface_pinned' and (type(revision) is not str or not PIN.fullmatch(revision)):
        raise ValueError('Hugging Face model must pin an immutable 40-character commit revision')
    if source=='imported_unverified' and revision is not None:
        raise ValueError('Imported source has no independently pinned Hub revision')
    return {'model_id':model_id,'source':source,'declared_license_id':license_id,'pinned_revision':revision}

def register(root,out,model_id,source='imported_unverified',license_id='unknown',revision=None,*,authorize=False):
    if authorize is not True:raise PermissionError('Explicit private model registration authorization required')
    key=require_key();meta=metadata(model_id,source,license_id,revision)
    output=Path(out)
    if output.exists():raise FileExistsError('Refuse to overwrite prior registry evidence')
    rows,total=inspect(root)
    result={'schema':SCHEMA,**meta,'artifacts':rows,'total_bytes':total,'artifact_count':len(rows),
            'bytes_verified_locally':True,'model_origin_authenticated':False,'license_independently_verified':False,
            'production_authority':False,'automatic_promotion':False,
            'scope':'private bytes and HMAC authenticated only; remote model origin and license independently unverified'}
    result=seal(result,key)
    with os.fdopen(os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
        f.write(canonical(result)+b'\n');f.flush();os.fsync(f.fileno())
    return result

def verify(root,manifest):
    key=require_key();report=unique_json(Path(manifest).read_text())
    check_hmac(report,key)
    if report.get('schema')!=SCHEMA:raise ValueError('Registry schema mismatch')
    for field in ('model_origin_authenticated','license_independently_verified','production_authority','automatic_promotion'):
        if report.get(field) is not False:raise ValueError('Unverified provenance or promotion claim')
    meta=metadata(report.get('model_id'),report.get('source'),report.get('declared_license_id'),report.get('pinned_revision'))
    if any(report.get(k)!=v for k,v in meta.items()):raise ValueError('Source metadata mismatch')
    rows,total=inspect(root)
    if report.get('artifacts')!=rows or report.get('total_bytes')!=total or report.get('artifact_count')!=len(rows):
        raise ValueError('Local model artifacts diverge from sealed registry')
    return {'all_bytes_verified':True,'model_origin_authenticated':False,'license_independently_verified':False,
            'file_count':len(rows),'total_bytes':total,'production_authority':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('register');a.add_argument('--root',required=True);a.add_argument('--manifest',required=True);a.add_argument('--model-id',required=True)
    a.add_argument('--source',default='imported_unverified');a.add_argument('--license-id',default='unknown');a.add_argument('--revision');a.add_argument('--authorize',action='store_true')
    v=sub.add_parser('verify');v.add_argument('--root',required=True);v.add_argument('--manifest',required=True)
    x=p.parse_args()
    out=register(x.root,x.manifest,x.model_id,x.source,x.license_id,x.revision,authorize=x.authorize) if x.cmd=='register' else verify(x.root,x.manifest)
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
