#!/usr/bin/env python3
"""Read-only v3.1 observatory build/start preflight; never stages or deploys."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SCHEMA='myriad.evolution.railway_preflight.v31'
EXPECTED_DOCKERFILE='evolution/Dockerfile'
HEALTH='/api/health'

def assess_builder(service):
    if not isinstance(service,dict):
        raise ValueError('Railway service data must be an object from the live API')
    builder=service.get('builder')
    if builder not in ('RAILPACK','DOCKERFILE'):
        raise ValueError('Unexpected or unobserved Railway builder')
    path=service.get('dockerfilePath')
    if path!=EXPECTED_DOCKERFILE:
        raise ValueError('Expected only the authorized in-repository Dockerfile')
    if service.get('healthcheckPath')!=HEALTH:
        raise ValueError('Healthcheck must match read-only observatory route')
    status='BLOCKED_BUILDER_MISMATCH' if builder!='DOCKERFILE' else 'PREVIEW_CANDIDATE_ONLY'
    return {'schema':SCHEMA,'status':status,
            'observed_builder':builder,'dockerfile_path':path,
            'corrective_action':'select DOCKERFILE builder and evolution/Dockerfile; verify in preview' if builder!='DOCKERFILE' else 'verify image and health endpoint in isolated preview before release decision',
            'build_artifact_verified':False,'preview_deployment_verified':False,
            'production_deployment_authorized':False,'live_service_mutated':False,
            'release_gates_completed':0}

def analyze(source):
    data=json.loads(Path(source).read_text())
    return assess_builder(data)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--redacted-service-json',required=True,help='Previously retrieved non-secret Railway builder config, not live fetch')
    args=p.parse_args()
    print(json.dumps(analyze(args.redacted_service_json),indent=2,sort_keys=True))
if __name__=='__main__':main()
