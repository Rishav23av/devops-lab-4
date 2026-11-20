import json
from .common import RUNTIME,run,app_health,switch,save


def promote():
    path=RUNTIME/'validated-candidate.json'
    gate=json.loads(path.read_text())
    current=run(['docker','inspect','--format','{{.Id}}','rishav-lab4-green']).stdout.strip()
    assert gate['unit_passed'] and gate['integration_passed'] and gate['candidate_id']==current
    assert app_health('green')
    switch({'blue':0,'green':100})
    path.unlink()
    result={'name':'Rishav','roll_no':'2301730245','unit_passed':True,
        'integration_passed':True,'candidate_identity_verified':True,'deployment_performed':True}
    save('jenkins-promotion.json',result)
    return result


if __name__=='__main__':print(json.dumps(promote(),indent=2))
