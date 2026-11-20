import json
import os
import subprocess
import time
import urllib.request
import urllib.error
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.getenv('LAB4_RUNTIME_DIR',str(ROOT/'.runtime')))
RUNTIME.mkdir(exist_ok=True)
os.chmod(RUNTIME, 0o700)
URL = os.getenv('LAB4_URL','http://127.0.0.1:5040')
DEFAULT_ROUTING = 'map $host $lab4_backend { default application; }\n'


def run(args, check=True, env=None):
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    if check and result.returncode:
        raise RuntimeError(result.stdout)
    return result


def compose(*args):
    command = ['docker', 'compose', '-f', 'deploy/compose.yml']
    if (RUNTIME/'deploy.env').exists():
        command += ['--env-file', str(RUNTIME/'deploy.env')]
    return run(command+list(args))


def request(url, method='GET', data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as response:
        raw = response.read()
        return response.code, json.loads(raw) if raw else {}


def save(name, data):
    p = ROOT/'docs/commands'/name
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        p.write_text(data.replace(str(ROOT), '.'))
    else:
        if isinstance(data,dict):
            release=Path('/etc/os-release')
            operating_system=platform.platform()
            if release.exists():
                for line in release.read_text().splitlines():
                    if line.startswith('PRETTY_NAME='):operating_system=line.split('=',1)[1].strip('"')
            data=dict(data,execution_environment={'os':operating_system,'python':sys.version.split()[0]})
        p.write_text(json.dumps(data, indent=2)+'\n')


def upstream(weights):
    assert sum(weights.values()) == 100 and all(isinstance(v, int) and v >= 0 for v in weights.values())
    return ''.join(f'server {name}:8080 weight={weight} max_fails=0;\n'
                   for name, weight in weights.items() if weight)


def switch(weights):
    folder = RUNTIME/'gateway'
    folder.mkdir(exist_ok=True)
    path = folder/'upstreams.conf'
    old = path.read_text() if path.exists() else ''
    temp = folder/'upstreams.tmp'
    temp.write_text(upstream(weights));temp.replace(path)
    (folder/'routing.conf').write_text(DEFAULT_ROUTING)
    result = run(['docker','exec','rishav-lab4-gateway','nginx','-t','-c','/etc/nginx/lab4-source/nginx.conf'], check=False)
    if result.returncode:
        path.write_text(old)
        raise RuntimeError('Gateway configuration rejected')
    run(['docker','exec','rishav-lab4-gateway','nginx','-c','/etc/nginx/lab4-source/nginx.conf','-s','reload'])
    time.sleep(0.2)


def cohort(percent):
    assert isinstance(percent,int) and 0 < percent <= 100
    if percent==100:
        text='map $host $lab4_backend { default green_pool; }\n'
    else:
        text=f'split_clients "$http_x_lab_user" $lab4_backend {{ {percent}% green_pool; * blue_pool; }}\n'
    (RUNTIME/'gateway/routing.conf').write_text(text)
    run(['docker','exec','rishav-lab4-gateway','nginx','-t','-c','/etc/nginx/lab4-source/nginx.conf'])
    run(['docker','exec','rishav-lab4-gateway','nginx','-c','/etc/nginx/lab4-source/nginx.conf','-s','reload'])
    time.sleep(.2)


def app_health(name):
    result = run(['docker','exec',f'rishav-lab4-{name}','python','-c',
        "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/health').status)"],check=False)
    return result.returncode == 0
