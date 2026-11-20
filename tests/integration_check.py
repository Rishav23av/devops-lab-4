"""Real HTTP, mounted credential and Redis checks inside the candidate container."""
import json
from scripts.common import run

CODE = '''
import json, urllib.request, urllib.error
from pathlib import Path
secret = Path('/run/secrets/app-api-key').read_text().strip()
def call(path, data=None, authenticated=False):
    headers = {'Content-Type':'application/json'}
    if authenticated: headers['X-API-Key'] = secret
    req=urllib.request.Request('http://127.0.0.1:8080'+path,
      data=json.dumps(data).encode() if data is not None else None, headers=headers)
    try:
      with urllib.request.urlopen(req,timeout=3) as r: return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
assert call('/health')[0] == 200, 'health gate failed'
assert call('/secure')[0] == 401, 'unauthenticated request accepted'
assert call('/secure',authenticated=True)[0] == 200, 'credential injection failed'
assert call('/data', {'value':'pipeline-integration'},True)[0] == 200, 'Redis write failed'
assert call('/data',authenticated=True)[1]['value']=='pipeline-integration', 'Redis read failed'
print(json.dumps({'integration_checks':5,'failed':0,'secret_printed':False}))
'''


def check(candidate='green'):
    result = run(['docker','exec',f'rishav-lab4-{candidate}','python','-c',CODE],check=False)
    return result.returncode, result.stdout


if __name__ == '__main__':
    status, text = check()
    print(text,end='')
    raise SystemExit(status)
