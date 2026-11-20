"""Bootstrap the local file-backed Vault and deliver an AppRole-scoped secret."""
import json
import os
import secrets
import time
from .common import ROOT, RUNTIME, request, compose, save

ADDR = os.getenv('VAULT_ADDR', 'http://127.0.0.1:8240')


def api(path, method='GET', data=None, token=None):
    headers = {'X-Vault-Token': token} if token else {}
    return request(ADDR+'/v1/'+path, method, data, headers)


def write_private(path, text):
    path.write_text(text)
    os.chmod(path, 0o600)


def bootstrap():
    compose('run','--rm','--no-deps','--user','0','--entrypoint','chown',
            'vault','-R','vault:vault','/vault/data')
    compose('up','-d','vault')
    for _ in range(60):
        try:
            status, data = api('sys/init')
            if status == 200:
                break
        except Exception:
            pass
        time.sleep(.3)
    else:
        raise RuntimeError('Vault did not start')
    state = RUNTIME/'vault-bootstrap.json'
    if not data['initialized']:
        status, initialized = api('sys/init', 'PUT', {'secret_shares':1,'secret_threshold':1})
        assert status == 200
        write_private(state,json.dumps(initialized))
    initialized = json.loads(state.read_text())
    status, data = api('sys/unseal','PUT',{'key':initialized['keys'][0]})
    assert status == 200 and not data['sealed']
    root = initialized['root_token']
    api('sys/mounts/secret','POST',{'type':'kv','options':{'version':'2'}},root)
    api('sys/auth/approle','POST',{'type':'approle'},root)
    status,_ = api('sys/policies/acl/lab4-app','PUT',{'policy':(ROOT/'vault/app-policy.hcl').read_text()},root)
    assert status == 204
    status,_ = api('secret/data/lab4/app','POST',{'data':{'api_key':secrets.token_urlsafe(32)}},root)
    assert status == 200
    status,_ = api('auth/approle/role/lab4-pipeline','POST',{'token_policies':['lab4-app'],
        'token_ttl':'60s','token_max_ttl':'120s','secret_id_ttl':'24h'},root)
    assert status == 204
    role = api('auth/approle/role/lab4-pipeline/role-id',token=root)[1]['data']['role_id']
    secret_id = api('auth/approle/role/lab4-pipeline/secret-id','POST',{},root)[1]['data']['secret_id']
    write_private(RUNTIME/'approle.json',json.dumps({'role_id':role,'secret_id':secret_id}))
    return deliver()


def deliver():
    credentials = json.loads((RUNTIME/'approle.json').read_text())
    status, data = api('auth/approle/login','POST',credentials)
    assert status == 200
    token = data['auth']['client_token']
    allowed, data = api('secret/data/lab4/app',token=token)
    assert allowed == 200
    secret = data['data']['data']['api_key']
    write_private(RUNTIME/'app-api-key', secret)
    # Non-root application containers need read access to the delivered file.
    # The parent runtime directory is 0700; the bind mount is read-only.
    os.chmod(RUNTIME/'app-api-key',0o644)
    denied,_ = api('secret/data/unrelated',token=token)
    revoked,_ = api('auth/token/revoke-self','POST',{},token)
    after,_ = api('secret/data/lab4/app',token=token)
    result = {'name':'Rishav','roll_no':'2301730245','store':'HashiCorp Vault KV v2',
        'authentication':'AppRole','token_ttl_seconds':60,'allowed_read_status':allowed,
        'forbidden_path_status':denied,'revoke_status':revoked,'read_after_revocation':after,
        'credentials_printed':False,'runtime_directory_mode':oct(RUNTIME.stat().st_mode & 0o777),
        'delivery':'read-only container mount; secret file protected by runtime directory'}
    save('secret-management.json',result)
    assert denied == 403 and after == 403 and revoked == 204
    return result


if __name__ == '__main__':
    print(json.dumps(bootstrap(),indent=2))
