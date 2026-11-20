import argparse
import json
import os
import sys
import time
from .common import RUNTIME, run, compose, switch, save
from .vault_store import deliver
from tests.integration_check import check


def pipeline(scenario='success'):
    result={'name':'Rishav','roll_no':'2301730245','scenario':scenario,'deployment_performed':False}
    env=os.environ.copy()
    if scenario=='unit-failure':
        env['APP_VERSION']='broken-contract'
    unit=run([sys.executable,'-m','unittest','tests.test_unit','-v'],check=False,env=env)
    save(f'pipeline-{scenario}-unit.txt',unit.stdout)
    result['unit_passed']=unit.returncode==0
    if unit.returncode:
        result['blocked_at']='unit';save(f'pipeline-{scenario}.json',result);return result
    deliver()
    (RUNTIME/'deploy.env').write_text('BLUE_VERSION=1.0.0\nGREEN_VERSION=2.0.0\n'
        f'FAIL_HEALTH={"true" if scenario=="integration-failure" else "false"}\nFAIL_WORK=false\n')
    compose('up','-d','--build','green')
    time.sleep(1)
    code,text=check()
    save(f'pipeline-{scenario}-integration.txt',text)
    result['integration_passed']=code==0
    if code:
        result['blocked_at']='integration';save(f'pipeline-{scenario}.json',result);return result
    switch({'blue':0,'green':100})
    result.update(deployment_performed=True,blocked_at=None)
    save(f'pipeline-{scenario}.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scenario',default='success',choices=['success','unit-failure','integration-failure'])
    args=parser.parse_args();data=pipeline(args.scenario);print(json.dumps(data,indent=2))
    raise SystemExit(0 if data['deployment_performed'] else 1)
