"""Start only the dedicated, loopback-bound laboratory controller."""
import os
import secrets
from .common import ROOT,RUNTIME,run


if __name__=='__main__':
    password=RUNTIME/'jenkins-admin-password'
    if not password.exists():
        password.write_text(secrets.token_urlsafe(24));os.chmod(password,0o600)
    result=run(['docker','inspect','rishav-lab4-jenkins'],check=False)
    if result.returncode==0:
        run(['docker','start','rishav-lab4-jenkins'])
    else:
        run(['docker','run','-d','--name','rishav-lab4-jenkins','--label','devops.lab=4',
            '-p','127.0.0.1:8089:8080','-v','/var/run/docker.sock:/var/run/docker.sock',
            '-v',str(ROOT)+':/workspace','-v','rishav-lab4-jenkins-home:/var/jenkins_home',
            '-v',str(password)+':/run/secrets/jenkins-admin-password:ro',
            '-e','LAB4_HOST_ROOT='+str(ROOT),'-e','VAULT_ADDR=http://host.docker.internal:8240',
            '-e','LAB4_URL=http://host.docker.internal:5040',
            'rishav-lab4-jenkins-ubuntu:local'])
    print('Dedicated Ubuntu Jenkins controller: http://localhost:8089')
    print('Login: rishav; password remains in the protected runtime file.')
