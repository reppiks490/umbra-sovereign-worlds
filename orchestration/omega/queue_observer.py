"""Advisory, read-only task projection; never an admission or execution authority."""
import sqlite3,json,argparse
from pathlib import Path
LANES=('OMEGA','ICARUS','EXASOVEREIGN','MYRIAD','UMBRA')
STATES={'ready','leased','reported','qualified','blocked'}
def observe(path,lane):
    if lane not in LANES:raise ValueError('unknown lane')
    p=Path(path)
    if not p.is_file() or p.is_symlink():raise ValueError('existing ledger required')
    c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True,timeout=5,isolation_level=None)
    c.row_factory=sqlite3.Row
    try:
        c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
        rows=c.execute('SELECT id,lane,state,score,resource,deps FROM tasks ORDER BY score DESC,id ASC').fetchall()
        states={r['id']:r['state'] for r in rows}
        if any(v not in STATES for v in states.values()):raise ValueError('unrecognized state')
        busy={r['resource'] for r in rows if r['resource'] and r['state'] in ('leased','reported')}
        result=[]
        for r in rows:
            if r['lane']!=lane:continue
            deps=json.loads(r['deps'])
            if not isinstance(deps,list) or any(not isinstance(d,str) for d in deps):raise ValueError('invalid dependencies')
            if r['state']!='ready':eligible=r['state']
            elif any(states.get(d)!='qualified' for d in deps):eligible='dependency-pending'
            elif r['resource'] and r['resource'] in busy:eligible='resource-busy'
            else:eligible='candidate'
            result.append({'id':r['id'],'lane':lane,'state':r['state'],'eligibility':eligible,'score':r['score']})
        return {'lane':lane,'authority':'advisory-snapshot-only','candidate_count':sum(x['eligibility']=='candidate' for x in result),'tasks':result}
    finally:
        c.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('lane',choices=LANES);a=p.parse_args()
    print(json.dumps(observe(a.db,a.lane),sort_keys=True))
