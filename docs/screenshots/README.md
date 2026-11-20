Lab 4 screenshots

Rishav | Roll no. 2301730245 | 20 November 2026

Images 01–08 are Chrome captures of the labeled saved-output pages in
[docs/evidence](../evidence). Their values come from the corresponding JSON/text
records in [docs/commands](../commands). Image 09 is an actual Jenkins UI capture.

| Image | Evidence |
| --- | --- |
| [01-recovery.png](01-recovery.png) | Snapshot integrity, restore, failover and recovery objectives |
| [02-gates.png](02-gates.png) | Jenkins result and stage summary; skipped stages identified from console output |
| [03-blue-green.png](03-blue-green.png) | Request sample across switching and rollback |
| [04-gitops.png](04-gitops.png) | Pulled revision, container repair and route repair |
| [05-comparison.png](05-comparison.png) | Summary of the measured experiments |
| [06-secrets.png](06-secrets.png) | Allowed/denied/revoked reads and application-key rotation |
| [07-canary.png](07-canary.png) | Stable cohorts, faulty release and automatic rollback |
| [08-ubuntu-tools.png](08-ubuntu-tools.png) | Ubuntu, Git configuration and installed tool versions |
| [09-jenkins-stage-view.png](09-jenkins-stage-view.png) | Authenticated Jenkins stage view with successful and failed gate runs |

To recapture after running the experiments and recording the console/JSON files:

```bash
python -m pip install -r requirements-evidence.txt
python -m scripts.capture_evidence
```

Chrome/Chromium must be installed. Selenium creates an isolated headless session.
The capture script reads the local ignored Jenkins password only to log in; it
does not put the credential into any screenshot or report.
