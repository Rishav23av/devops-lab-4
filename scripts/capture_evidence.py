"""Render saved experiment records, then capture them in an isolated Chrome session."""
import json
from html import escape
from pathlib import Path
from .common import ROOT,RUNTIME


def load(name):
    return json.loads((ROOT/'docs/commands'/name).read_text())


def pre(data):
    text=data if isinstance(data,str) else json.dumps(data,indent=2)
    return '<pre>'+escape(text)+'</pre>'


def table(headers,rows):
    return '<table><tr>'+''.join('<th>'+escape(str(h))+'</th>' for h in headers)+'</tr>'+''.join(
        '<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</table>'


def stages(build):
    console=(ROOT/'docs/commands'/f"jenkins-build-{build['number']}.txt").read_text()
    labels=[]
    for stage in build.get('stages',[]):
        name=stage['name']
        status='SKIPPED' if f'Stage "{name}" skipped due to earlier failure(s)' in console else stage['status']
        labels.append(name+': '+status)
    return '; '.join(labels)


def pages():
    dr=load('disaster-recovery.json');bg=load('blue-green.json');ca=load('canary.json')
    sec=load('secret-management.json');rot=load('secret-rotation.json');gi=load('gitops-drift-check.json')
    events=load('gitops-reconciliation.json')['events']
    builds=load('jenkins-builds.json')['builds']
    records=[
        ('01-recovery','Backup, restore and failover',pre(dr)),
        ('02-gates','Jenkins unit and integration gates',table(['Build','Scenario','Result','Stages'],[
            [b['number'],b['scenario'],b['result'],stages(b)] for b in builds])),
        ('03-blue-green','Blue-green switching and rollback',pre(bg)),
        ('04-gitops','GitOps reconciliation',pre(gi)+'<h2>Changed-state events pulled from GitHub</h2>'+table(['Revision','Green version','Container drift','Route drift'],[
            [e['revision'][:8],e['desired']['green_version'],', '.join(e['container_drift']),e['routing_drift']] for e in events if e.get('reconciled')
        ])),
        ('05-comparison','Advanced deployment experiment summary',table(['Experiment','Observed evidence'],[
            ['Recovery',f"Restore {dr['restore_seconds']} s; failover {dr['failover_rto_seconds']} s; lost acknowledged records {dr['lost_acknowledged_records']}"],
            ['Blue-green',f"{bg['requests_during_switches']} measured requests, {bg['errors']} errors"],
            ['Canary','Stable user cohorts at 10%, 25%, 50%, 100%; bad-release rollback'],
            ['GitOps',f"Stopped container repaired in {gi['container_restart_seconds']} s"],
            ['Vault',f"Allowed {sec['allowed_read_status']}; denied {sec['forbidden_path_status']}; revoked {sec['read_after_revocation']}; old rotated key {rot['old_key_status']}"],
        ])),
        ('06-secrets','Vault AppRole, policy and credential rotation',pre(sec)+'<h2>Rotation check</h2>'+pre(rot)),
        ('07-canary','Stable-user canary rollout and automatic rollback',table(['Target green','Sample users','Blue / green','Errors','p95 ms','Stable repeat users'],[
            [str(s['requested_green_percent'])+'%',s['sample_users'],f"{s['environment_counts'].get('blue',0)} / {s['environment_counts'].get('green',0)}",s['errors'],s['p95_ms'],s['repeated_user_assignment_stable']] for s in ca['promotion_stages']
        ])+'<h2>Deliberately faulty canary</h2>'+pre(ca['failed_release'])+'<h2>After metric-triggered rollback</h2>'+pre(ca['after_rollback'])),
    ]
    tools=(ROOT/'docs/commands/ubuntu-tools.txt').read_text().splitlines()
    keep=[];skip_os=False
    for line in tools:
        if line.startswith('NAME=') or line.startswith(('VERSION=','VERSION_ID=','PRETTY_NAME=')) or line.startswith('$') or not skip_os:
            keep.append(line)
        if line=='$ cat /etc/os-release':skip_os=True
        if skip_os and line.startswith('$ git --version'):
            skip_os=False
    records.append(('08-ubuntu-tools','Ubuntu 24.04 installation and global Git identity',pre('\n'.join(keep))))
    directory=ROOT/'docs/evidence';directory.mkdir(exist_ok=True)
    for slug,title,body in records:
        html='''<!doctype html><html><head><meta charset="utf-8"><style>
body{font:17px/1.45 system-ui,sans-serif;color:#182638;margin:36px 48px;max-width:1450px}
h1{font-size:29px;margin:0 0 8px}h2{font-size:22px;margin:24px 0 8px}
.sub{color:#526170;margin-bottom:22px}pre{font:15px/1.35 ui-monospace,monospace;background:#f1f5f8;padding:18px;white-space:pre-wrap;overflow-wrap:anywhere}
table{border-collapse:collapse;width:100%;font-size:16px}td,th{padding:12px;text-align:left;border:1px solid #d7e1e8}th{background:#255575;color:white}
</style></head><body>'''+f'<h1>Lab 4 - {escape(title)}</h1><div class="sub">Rishav | Roll no. 2301730245 | 20 November 2026<br>Saved experimental output. Values are from the retained command records.</div>'+body+'</body></html>'
        (directory/(slug+'.html')).write_text(html)
    return [r[0] for r in records]


def capture():
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    options=webdriver.ChromeOptions();options.add_argument('--headless=new');options.add_argument('--window-size=1600,1200')
    folder=ROOT/'docs/screenshots';folder.mkdir(exist_ok=True)
    with webdriver.Chrome(options=options) as browser:
        for name in pages():
            browser.get((ROOT/'docs/evidence'/f'{name}.html').as_uri())
            height=browser.execute_script('return Math.max(document.body.scrollHeight,800)')
            browser.set_window_size(1600,min(height+400,3000))
            browser.save_screenshot(str(folder/(name+'.png')))
        browser.set_window_size(1600,1300)
        browser.get('http://localhost:8089/login')
        wait=WebDriverWait(browser,20)
        wait.until(lambda d:d.find_elements(By.NAME,'j_username'))
        browser.find_element(By.NAME,'j_username').send_keys('rishav')
        browser.find_element(By.NAME,'j_password').send_keys((RUNTIME/'jenkins-admin-password').read_text().strip())
        browser.find_element(By.CSS_SELECTOR,'button[type=submit]').click()
        wait.until(lambda d:'/login' not in d.current_url)
        browser.get('http://localhost:8089/job/devops-lab-4/')
        wait.until(lambda d:'Stage View' in d.page_source)
        browser.save_screenshot(str(folder/'09-jenkins-stage-view.png'))
    print('Captured eight saved-output pages and the actual Jenkins stage view.')


if __name__=='__main__':capture()
