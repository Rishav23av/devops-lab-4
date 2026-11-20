import json
from .common import RUNTIME, compose, upstream, URL, request, DEFAULT_ROUTING
from .vault_store import bootstrap


def setup():
    result = bootstrap()
    (RUNTIME/'gateway').mkdir(exist_ok=True)
    (RUNTIME/'gateway/upstreams.conf').write_text(upstream({'blue':100,'green':0}))
    (RUNTIME/'gateway/routing.conf').write_text(DEFAULT_ROUTING)
    (RUNTIME/'deploy.env').write_text('BLUE_VERSION=1.0.0\nGREEN_VERSION=2.0.0\nFAIL_HEALTH=false\nFAIL_WORK=false\n')
    compose('up','-d','--build','--wait','blue','green','redis-primary','redis-standby','gateway')
    status, data = request(URL+'/health')
    assert status == 200 and data['environment'] == 'blue'
    print(json.dumps({'stack':'ready','gateway':URL,'version':data['version'],
        'secret_read_status':result['allowed_read_status']},indent=2))


if __name__ == '__main__':
    setup()
