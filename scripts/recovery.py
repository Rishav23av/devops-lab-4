import hashlib
import json
import time
from .common import ROOT, RUNTIME, URL, request, run, save


def redis(name,*args):
    return run(['docker','exec',f'rishav-lab4-{name}','redis-cli',*args]).stdout.strip()


def demonstrate():
    key=(RUNTIME/'app-api-key').read_text().strip();headers={'X-API-Key':key}
    for _ in range(30):
        code,data=request(URL+'/data','POST',{'value':'Rishav 2301730245 backup point'},headers)
        if code==200 and data['replicas_acked']==1:break
        time.sleep(.2)
    else:raise RuntimeError('Replica did not acknowledge the baseline write')
    redis('primary','SAVE');snapshot_time=time.time()
    folder=RUNTIME/'restore-data';folder.mkdir(exist_ok=True)
    run(['docker','cp','rishav-lab4-primary:/data/dump.rdb',str(folder/'dump.rdb')])
    digest=hashlib.sha256((folder/'dump.rdb').read_bytes()).hexdigest()
    code,data=request(URL+'/data','POST',{'value':'after-backup-write'},headers);assert code==200
    time.sleep(.5)
    start=time.perf_counter()
    run(['docker','run','-d','--name','rishav-lab4-restore','--label','devops.lab=4',
        '-v',str(folder)+':/data','redis:7-alpine','redis-server','--appendonly','no'])
    try:
        for _ in range(50):
            result=run(['docker','exec','rishav-lab4-restore','redis-cli','GET','lab4:record'],check=False)
            if result.returncode==0 and 'backup point' in result.stdout:break
            time.sleep(.1)
        else:raise RuntimeError('Restored snapshot did not answer')
        restore_seconds=time.perf_counter()-start;restored=result.stdout.strip()
    finally:
        run(['docker','rm','-f','rishav-lab4-restore'])
    snapshot_age=time.time()-snapshot_time
    code,data=request(URL+'/data','POST',{'value':'last-acknowledged-record'},headers)
    assert code==200 and data['replicas_acked']==1
    start=time.perf_counter();run(['docker','stop','rishav-lab4-primary'])
    redis('standby','REPLICAOF','NO','ONE')
    for _ in range(40):
        code,data=request(URL+'/data',headers=headers)
        if code==200 and data['value']=='last-acknowledged-record':break
        time.sleep(.1)
    else:raise RuntimeError('Failover lost the acknowledged record')
    read_seconds=time.perf_counter()-start
    code,write=request(URL+'/data','POST',{'value':'write-after-failover'},headers);assert code==200
    result={'name':'Rishav','roll_no':'2301730245','backup_sha256':digest,
        'restored_value':restored,'post_backup_write_present_in_restore':False,
        'restore_seconds':round(restore_seconds,3),'snapshot_age_seconds_at_check':round(snapshot_age,3),
        'failover_read_seconds':round(read_seconds,3),'failover_rto_seconds':round(time.perf_counter()-start,3),
        'lost_acknowledged_records':0,'post_failover_write_status':code,
        'objectives':{'snapshot_rpo_seconds':60,'restore_rto_seconds':30,'failover_rto_seconds':10,'failover_rpo_records':0},
        'mechanism':'operator stops/fences primary, promotes standby; application tries the standby after the primary connection fails',
        'limitations':['both Redis instances share one Docker host','manual promotion','WAIT does not provide general strong consistency','new writes have no replica until redundancy is restored']}
    assert restore_seconds<30 and result['failover_rto_seconds']<10
    save('disaster-recovery.json',result);return result


if __name__=='__main__':print(json.dumps(demonstrate(),indent=2))
