#!/usr/bin/env python3
"""Provenance-aware source seed registry for ambitious cross-domain algorithm research.

References are independently named public methods/published project capabilities,
NOT redistributable source code, nor 250K invented methods. Ingestion is opt-in,
metadata-first, license-gated, and must pass a human reviewer before execution.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3, urllib.parse
from pathlib import Path

SOURCES={
 'deap':('https://github.com/DEAP/deap','evolutionary-optimization'),
 'scipy':('https://docs.scipy.org/doc/scipy/reference/optimize.html','numerical-optimization'),
 'optuna':('https://optuna.readthedocs.io/en/stable/','hyperparameter-optimization'),
 'pymoo':('https://pymoo.org/','multiobjective-optimization'),
 'river':('https://riverml.xyz/latest/','online-machine-learning'),
 'sklearn':('https://scikit-learn.org/stable/','statistical-learning'),
 'rl':('https://github.com/DLR-RM/stable-baselines3','reinforcement-learning'),
 'talib':('https://github.com/TA-Lib/ta-lib-python','technical-indicators'),
 'lean':('https://github.com/QuantConnect/Lean','backtesting-engine'),
 'tv':('https://www.tradingview.com/scripts/','community-strategy-directory'),
 'pines':('https://github.com/TradingSignalBot/tradingview-strategies','pine-script-examples'),
 'pynecore':('https://github.com/theonetrade/pynecore-strategies','community-strategy-ports'),
 'reddit':('https://www.reddit.com/r/algotrading/','community-research-ideas'),
}
# Names are real, established methods/indicators or described strategy patterns;
# none is installed, validated, or copied merely by appearing in this list.
METHODS={
 'deap':['genetic-algorithm','genetic-programming','evolution-strategy','nsga-ii','nsga-iii','spea2','cma-es','particle-swarm','differential-evolution','estimation-of-distribution','mo-cma-es'],
 'scipy':['bfgs','l-bfgs-b','nelder-mead','powell','newton-cg','conjugate-gradient','slsqp','trust-constr','differential-evolution','dual-annealing','basinhopping'],
 'optuna':['tpe-sampler','cmaes-sampler','grid-sampler','random-sampler','hyperband-pruning','median-pruning','successive-halving-pruning'],
 'pymoo':['moead','rnsga2','rnsga3','age-moea','sms-emoa','constraint-handling','niching-survival'],
 'river':['adwin-drift','page-hinkley','online-linear-regression','adaptive-random-forest','streaming-kmeans','online-anomaly-detection'],
 'sklearn':['random-forest','gradient-boosting','elastic-net','ridge-regression','lasso-regression','support-vector-machine','kmeans','isolation-forest','gaussian-process','cross-validation'],
 'rl':['ppo','sac','td3','a2c','dqn','ddpg','her-replay'],
 'talib':['rsi','adx','atr','macd','bollinger-bands','stochastic-oscillator','cci','obv','mfi','ichimoku-proxy','moving-average','sar','aroon','keltner-proxy'],
 'lean':['walk-forward-optimization','event-driven-backtesting','portfolio-construction','risk-management','slippage-model','fill-model','scheduled-universe-selection'],
 'tv':['opening-range-breakout','supertrend','volume-profile','order-block-zone','liquidity-sweep','vwap-deviation','session-reversal'],
 'pines':['london-breakout','ema-crossover','macd-crossover','rsi-divergence','break-and-retest','opening-range-breakout'],
 'pynecore':['bar-by-bar-strategy-port','historical-backtest-parity','pine-indicator-port'],
 'reddit':['purged-chronological-validation','walk-forward-regime-testing','realistic-slippage-sensitivity','multiple-testing-control','parameter-stability-testing'],
}
SCHEMA='umbra.evolution.sourced_algorithms.v1'

def entries():
    seen=set()
    for source, names in METHODS.items():
        url,domain=SOURCES[source]
        for name in names:
            key=f'{source}:{name}'
            if key in seen:raise ValueError('duplicate sourced method')
            seen.add(key)
            yield {'source_method_id':key,'method_name':name,'source_id':source,'source_url':url,
                   'domain':domain,'provenance':'public_reference_only',
                   'source_code_copied':False,'license_audit':'required_before_code_reuse',
                   'independent_runtime_verified':False,'training_completed':False,
                   'research_use':'candidate_method_or_inspiration'}

def validate():
    rows=list(entries()); hosts={k:urllib.parse.urlparse(v[0]).hostname for k,v in SOURCES.items()}
    if any(not h or not h.endswith(('github.com','reddit.com','tradingview.com','scipy.org','readthedocs.io','pymoo.org','riverml.xyz','scikit-learn.org')) for h in hosts.values()):raise ValueError('Unknown source host')
    return {'schema':SCHEMA,'distinct_source_method_records':len(rows),'source_directories':len(SOURCES),
            'independent_validated_implementations_imported':0,
            'copyright_or_license_cleared_source_copies':0,
            'target_independent_algorithms':250000,'target_met':False,
            'source_kinds':list(SOURCES),'audit_status':'metadata_records_only'}

def ingest(path, db_path):
    # This imports only trusted *metadata*, not executable downloaded code.
    p=Path(path)
    if p.stat().st_size>2_000_000:raise ValueError('Metadata manifest too large')
    items=json.loads(p.read_text())
    if not isinstance(items,list) or len(items)>5000:raise ValueError('Invalid metadata batch')
    conn=sqlite3.connect(db_path);conn.execute('''CREATE TABLE IF NOT EXISTS candidates (
     id TEXT PRIMARY KEY, source_url TEXT NOT NULL, title TEXT NOT NULL, sha256 TEXT NOT NULL,
     license_state TEXT NOT NULL CHECK(license_state='pending'), state TEXT NOT NULL CHECK(state='quarantined'))''')
    added=0
    try:
        for x in items:
            if set(x)!={'url','title'}:raise ValueError('Unrecognized metadata keys')
            u=urllib.parse.urlparse(x['url']); title=x['title']
            if u.scheme!='https' or not u.hostname or len(x['url'])>600 or not isinstance(title,str) or not 3<=len(title)<=180:raise ValueError('Invalid source metadata')
            # URLs from unknown domains are not trusted for implementation, even if indexed.
            k=hashlib.sha256((x['url']+'\0'+title).encode()).hexdigest()
            cur=conn.execute('INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?,?)',(k,x['url'],title,k,'pending','quarantined'))
            added+=cur.rowcount
        conn.commit()
    finally:conn.close()
    return {'new_quarantined_source_candidates':added,'new_executable_algorithms':0,'auto_promotions':0}

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True);s.add_parser('validate');x=s.add_parser('export');x.add_argument('--out',required=True)
    x=s.add_parser('ingest');x.add_argument('--manifest',required=True);x.add_argument('--db',required=True)
    a=p.parse_args()
    if a.command=='validate':v=validate()
    elif a.command=='export':
        o=Path(a.out);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(list(entries()),indent=2)+'\n');v={**validate(),'written':str(o)}
    else:v=ingest(a.manifest,a.db)
    print(json.dumps(v,indent=2))
if __name__=='__main__':main()
