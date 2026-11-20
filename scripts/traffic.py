import collections
import json
import math
import threading
import time
from .common import URL, RUNTIME, request, switch, cohort, compose, app_health, save


def sample(count=200, path='/work', users=False):
    observations=[]
    for index in range(count):
        start=time.perf_counter()
        try:
            code, data=request(URL+path,headers={'X-Lab-User':f'user-{index}'} if users else {})
            observations.append({'status':code,'environment':data.get('environment','unknown'),
                'ms':round((time.perf_counter()-start)*1000,3)})
        except Exception:
            observations.append({'status':0,'environment':'unavailable','ms':round((time.perf_counter()-start)*1000,3)})
    errors=sum(x['status']!=200 for x in observations)
    times=sorted(x['ms'] for x in observations)
    return {'requests':count,'errors':errors,'error_rate':errors/count,
        'p95_ms':times[math.ceil(count*.95)-1],
        'environment_counts':dict(collections.Counter(x['environment'] for x in observations))}


def blue_green():
    assert app_health('blue') and app_health('green')
    switch({'blue':100,'green':0})
    statuses=[];envs=[];stop=threading.Event()
    def traffic():
        while not stop.is_set():
            try:
                status,data=request(URL+'/version');statuses.append(status);envs.append(data.get('environment'))
            except Exception:
                statuses.append(0)
            time.sleep(.005)
    worker=threading.Thread(target=traffic);worker.start();time.sleep(.5)
    start=time.perf_counter();switch({'blue':0,'green':100});elapsed=time.perf_counter()-start
    time.sleep(.5);switch({'blue':100,'green':0});time.sleep(.5);stop.set();worker.join()
    result={'name':'Rishav','roll_no':'2301730245','requests_during_switches':len(statuses),
        'errors':sum(s!=200 for s in statuses),'observed_environments':sorted(set(envs)),
        'switch_seconds':round(elapsed,3),'switches':['blue to green','green to blue rollback'],
        'measurement':'continuous sequential requests at roughly 5 ms intervals; not a universal availability guarantee'}
    assert result['errors']==0 and result['observed_environments']==['blue','green']
    save('blue-green.json',result);return result


def canary():
    stages=[]
    for green in [10,25,50,100]:
        cohort(green)
        metrics=sample(users=True);metrics['requested_green_percent']=green
        metrics['sample_users']=200
        stable=True
        for user in range(20):
            first=request(URL+'/version',headers={'X-Lab-User':f'user-{user}'})[1]['environment']
            second=request(URL+'/version',headers={'X-Lab-User':f'user-{user}'})[1]['environment']
            stable=stable and first==second
        metrics['repeated_user_assignment_stable']=stable
        assert stable
        metrics['decision']='promote' if metrics['error_rate']<.01 and metrics['p95_ms']<250 else 'rollback'
        stages.append(metrics)
        if metrics['decision']=='rollback':
            switch({'blue':100,'green':0});break
    assert len(stages)==4 and all(s['errors']==0 for s in stages)
    switch({'blue':100,'green':0})
    (RUNTIME/'deploy.env').write_text('BLUE_VERSION=1.0.0\nGREEN_VERSION=2.0.0\nFAIL_HEALTH=false\nFAIL_WORK=true\n')
    compose('up','-d','--wait','green')
    cohort(10)
    bad=sample(users=True);bad['decision']='rollback' if bad['error_rate']>=.01 or bad['p95_ms']>=250 else 'promote'
    if bad['decision']=='rollback':switch({'blue':100,'green':0})
    after=sample(100)
    assert bad['decision']=='rollback' and after['errors']==0
    result={'name':'Rishav','roll_no':'2301730245','promotion_stages':stages,'failed_release':bad,
        'after_rollback':after,'thresholds':{'error_rate':.01,'p95_ms':250},
        'cohort_key':'X-Lab-User header, deterministic Nginx split_clients hash',
        'limitation':'short local batches; a production deployment should use a trusted user identity'}
    save('canary.json',result)
    (RUNTIME/'deploy.env').write_text('BLUE_VERSION=1.0.0\nGREEN_VERSION=2.0.0\nFAIL_HEALTH=false\nFAIL_WORK=false\n')
    compose('up','-d','--wait','green');switch({'blue':100,'green':0})
    return result


if __name__=='__main__':
    print(json.dumps({'blue_green':blue_green(),'canary':canary()},indent=2))
