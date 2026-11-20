"""Pull a public Git repository and reconcile its declared versions and traffic."""
import argparse
import json
import re
import time
from .common import ROOT, RUNTIME, compose, run, switch, upstream, save, DEFAULT_ROUTING


def once(remote):
    folder=RUNTIME/'gitops-source'
    if not (folder/'.git').exists():
        run(['git','clone','--depth','1','--no-checkout',remote,str(folder)])
    run(['git','-c','gc.auto=0','-C',str(folder),'fetch','origin','main'])
    revision=run(['git','-C',str(folder),'rev-parse','FETCH_HEAD']).stdout.strip()
    desired=json.loads(run(['git','-C',str(folder),'show','FETCH_HEAD:gitops/desired.json']).stdout)
    for name in ['blue','green']:
        assert re.fullmatch(r'\d+\.\d+\.\d+',desired[name+'_version'])
    assert set(desired['traffic'])=={'blue','green'}
    expected=upstream(desired['traffic'])
    drift=[]
    for name in ['blue','green']:
        result=run(['docker','inspect',f'rishav-lab4-{name}'],check=False)
        if result.returncode:
            drift.append(name+' missing');continue
        info=json.loads(result.stdout)[0]
        env=dict(s.split('=',1) for s in info['Config']['Env'] if '=' in s)
        if not info['State']['Running']:
            drift.append(name+' stopped')
        if env.get('APP_VERSION')!=desired[name+'_version']:
            drift.append(name+' version differs')
        if env.get('FAIL_WORK','false')!='false' or env.get('FAIL_HEALTH','false')!='false':
            drift.append(name+' fault flag differs')
    if drift:
        (RUNTIME/'deploy.env').write_text(f"BLUE_VERSION={desired['blue_version']}\nGREEN_VERSION={desired['green_version']}\nFAIL_HEALTH=false\nFAIL_WORK=false\n")
        compose('up','-d','--wait','blue','green')
    path=RUNTIME/'gateway/upstreams.conf'
    mode=RUNTIME/'gateway/routing.conf'
    routing_drift=(not path.exists() or path.read_text()!=expected or
                   not mode.exists() or mode.read_text()!=DEFAULT_ROUTING)
    if drift or routing_drift:
        switch(desired['traffic'])
    return {'at':time.time(),'revision':revision,'desired':desired,
        'container_drift':drift,'routing_drift':routing_drift,'reconciled':bool(drift or routing_drift)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--remote',default='https://github.com/Rishav23av/devops-lab-4.git');p.add_argument('--duration',type=int,default=60)
    p.add_argument('--record',default='gitops-reconciliation.json')
    args=p.parse_args();events=[];deadline=time.monotonic()+args.duration
    while time.monotonic()<deadline:
        try:
            event=once(args.remote)
        except (RuntimeError,OSError,json.JSONDecodeError) as error:
            event={'at':time.time(),'reconciled':False,'retrying':True,
                   'error':str(error).replace(str(ROOT),'.')}
        events.append(event)
        print(json.dumps(event),flush=True)
        save(args.record,{'name':'Rishav','roll_no':'2301730245','remote':args.remote,'events':events})
        time.sleep(1)
