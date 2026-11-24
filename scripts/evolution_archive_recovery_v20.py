#!/usr/bin/env python3
"""Recover a MYRIAD research ledger from checksum-pinned split ZIP parts.

Treat the source as untrusted evidence. Nothing is executed or auto-promoted.
No network or credentials, and never overwrites user files. An unkeyed SHA-256
is an integrity check, not authentication, and does not certify model quality.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import re
import sqlite3
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

SCHEMA='myriad.umbra.two_cycle.split_zip.v1'
INNER_SCHEMA='myriad.umbra.two_cycle.fleet_archive.v1'
LEDGER='evolution_fleet_195000_evidence.sqlite3'
MANIFEST='ARCHIVE_SOURCE_MANIFEST.json'
ALLOWED={LEDGER, MANIFEST,'MYRIAD_EVOLUTION_TRIBUNAL_V19_TWO_CYCLES_390000.json'}
MAX_SIZE=1024*1024*1024
BLOCK=1024*1024
SHA=re.compile(r'[0-9a-f]{64}\Z')


def require_sha(x):
    if not isinstance(x,str) or not SHA.fullmatch(x):
        raise ValueError('SHA-256 must be a 64-character lowercase hex string')
    return x


def read_manifest(path):
    obj=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(obj,dict) or obj.get('schema')!=SCHEMA:raise ValueError('Unrecognized split archive manifest')
    parts=obj.get('segments')
    if not isinstance(parts,list) or not 1<=len(parts)<=256:raise ValueError('Invalid part count')
    if not isinstance(obj.get('archive_bytes'),int) or not 1<=obj['archive_bytes']<=MAX_SIZE:raise ValueError('Unbounded archive size')
    require_sha(obj.get('archive_sha256'));require_sha(obj.get('source_database_sha256'))
    for k in ['source_database_bytes','verified_receipt_records']:
        if not isinstance(obj.get(k),int) or not 1<=obj[k]<=MAX_SIZE:raise ValueError('Invalid source metadata')
    basename=obj.get('archive_name')
    if not isinstance(basename,str) or not re.fullmatch(r'[A-Za-z0-9_\-]+\.zip',basename):
        raise ValueError('Invalid archive filename')
    for i,p in enumerate(parts,1):
        if not isinstance(p,dict) or not isinstance(p.get('bytes'),int) or not 1<=p['bytes']<=MAX_SIZE:
            raise ValueError('Invalid part metadata')
        if p.get('path')!=f'{basename}.part{i:02d}':raise ValueError('Missing, duplicate, or unordered split part')
        require_sha(p.get('sha256'))
    if sum(p['bytes'] for p in parts)!=obj['archive_bytes']:raise ValueError('Part lengths do not add up')
    return obj


def check_zip(path,obj):
    results=[]
    with zipfile.ZipFile(path,'r') as z:
        names=set()
        total=0
        for item in z.infolist():
            raw=item.filename
            pp=PurePosixPath(raw)
            if item.is_dir() or not raw or raw.startswith('/') or '\\' in raw or '..' in pp.parts or len(pp.parts)!=1:
                raise ValueError('Unsafe archived path')
            if raw in names:raise ValueError('Duplicate archive member')
            names.add(raw)
            mode=(item.external_attr >> 16) & 0xffff
            if stat.S_ISLNK(mode):raise ValueError('Symlinks are prohibited')
            if item.file_size>MAX_SIZE:raise ValueError('Unbounded member')
            total+=item.file_size
            if total>MAX_SIZE:raise ValueError('Unbounded extraction size')
        if LEDGER not in names or MANIFEST not in names or any(n not in ALLOWED and not re.fullmatch(r'EVOLUTION_V19_TRIBUNAL_\d{6}_\d{6}\.json',n) for n in names):
            raise ValueError('Unrecognized archive member inventory')
        inner=json.loads(z.read(MANIFEST))
        if inner.get('schema')!=INNER_SCHEMA or inner.get('research_only') is not True or inner.get('production_integrations')!=0:
            raise ValueError('Unqualified inner provenance')
        dbmeta=inner.get('sqlite')
        if not isinstance(dbmeta,dict) or dbmeta.get('path')!=LEDGER or dbmeta.get('size_bytes')!=obj['source_database_bytes'] or dbmeta.get('sha256')!=obj['source_database_sha256']:
            raise ValueError('Internal source DB metadata mismatch')
        if inner.get('completed_occurrences')!=obj['verified_receipt_records']:
            raise ValueError('Internal total receipt count mismatch')
        for name in sorted(names):
            h=hashlib.sha256();length=0
            with z.open(name) as src:
                while data:=src.read(BLOCK):
                    length+=len(data);h.update(data)
            if length!=z.getinfo(name).file_size:raise ValueError('Incomplete ZIP stream')
            if name==LEDGER and h.hexdigest()!=obj['source_database_sha256']:
                raise ValueError('Stored SQLite bytes mismatch')
            results.append({'member':name,'bytes':length,'sha256':h.hexdigest()})
    return results


def recover(parts_manifest, *, output_directory=None, check_sqlite=False):
    mp=Path(parts_manifest).resolve()
    meta=read_manifest(mp)
    if output_directory is not None:
        out=Path(output_directory).resolve()
        if out.exists() and any(out.iterdir()):raise FileExistsError('Destination must be an empty directory')
        if out==mp.parent or out==mp.parent.parent:raise ValueError('Destination may not be source directory')
    else:out=None
    all_bytes=0;full=hashlib.sha256();part_receipts=[]
    with tempfile.TemporaryDirectory(prefix='myriad-archive-audit-') as temp:
        candidate=Path(temp)/'archive.zip'
        with candidate.open('xb') as sink:
            for item in meta['segments']:
                source=mp.parent/item['path']
                if not source.is_file() or source.is_symlink():raise FileNotFoundError('Missing or symlinked archive part')
                if source.stat().st_size!=item['bytes']:raise ValueError('Archive part size mismatch')
                h=hashlib.sha256();count=0
                with source.open('rb') as fh:
                    while piece:=fh.read(BLOCK):
                        h.update(piece);full.update(piece);sink.write(piece);count+=len(piece)
                        all_bytes+=len(piece)
                if h.hexdigest()!=item['sha256'] or count!=item['bytes']:
                    raise ValueError('Part checksum mismatch: '+item['path'])
                part_receipts.append({'path':item['path'],'sha256':h.hexdigest(),'bytes':count})
        if all_bytes!=meta['archive_bytes'] or full.hexdigest()!=meta['archive_sha256']:
            raise ValueError('Reassembled archive checksum mismatch')
        files=check_zip(candidate,meta)
        extracted=None
        if out is not None or check_sqlite:
            temp_db=Path(temp)/LEDGER
            with zipfile.ZipFile(candidate) as z, z.open(LEDGER) as src, temp_db.open('xb') as dst:
                import shutil
                shutil.copyfileobj(src,dst,length=BLOCK)
            con=sqlite3.connect(f'file:{temp_db}?mode=ro',uri=True)
            try:
                con.execute('PRAGMA query_only=ON')
                integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
                if integrity!='ok':raise ValueError('SQLite integrity_check failed')
                total=con.execute('SELECT COUNT(*) FROM runs').fetchone()[0]
                distinct=con.execute('SELECT COUNT(DISTINCT workflow) FROM runs').fetchone()[0]
                if total!=meta['verified_receipt_records'] or distinct>195000:raise ValueError('Actual SQLite record count mismatch')
                db_stats={'integrity_check':integrity,'recorded_occurrences':total,'unique_workflow_identities':distinct}
            finally:con.close()
            if out is not None:
                out.mkdir(parents=True,exist_ok=True)
                target=out/LEDGER
                if target.exists():raise FileExistsError('Destination occupied')
                os.replace(temp_db,target)
                target.chmod(0o400)
                extracted=str(target)
        else:db_stats={'integrity_check':'not_requested','recorded_occurrences':'not_independently_queried'}
    result={'schema':'myriad.umbra.recovery.v20','source_archive_sha256':full.hexdigest(),
            'source_db_sha256':meta['source_database_sha256'],'verified_parts':part_receipts,
            'verified_members':files,'sqlite':db_stats,'restored_database':extracted,
            'private_weights_recovered':False,'trained_model_certification':False,
            'production_execution_authorized':False,
            'warning':'SHA-256 checksums are integrity only, not authenticity signatures; all experiments are synthetic.'}
    result['report_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True,help='Exact parts JSON beside numbered .zip.partNN files')
    p.add_argument('--restore-to',help='Empty directory for verified, read-only SQLite file')
    p.add_argument('--sqlite-integrity',action='store_true',help='Extract temporarily and run read-only SQLite integrity/count checks')
    p.add_argument('--report',help='Write result JSON using exclusive create (never overwrite)')
    a=p.parse_args()
    r=recover(a.manifest,output_directory=a.restore_to,check_sqlite=a.sqlite_integrity)
    if a.report:
        d=Path(a.report);d.parent.mkdir(parents=True,exist_ok=True)
        with d.open('x',encoding='utf-8') as fh:json.dump(r,fh,indent=2,sort_keys=True)
    print(json.dumps(r,indent=2,sort_keys=True))

if __name__=='__main__':main()
