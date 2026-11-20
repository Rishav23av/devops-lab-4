Lab 4 evidence index

Rishav | Roll no. 2301730245 | Executed 20 November 2026

The final scripts ran from Ubuntu 24.04.5 LTS in the dedicated Jenkins container.
Docker Desktop hosts the isolated services on one macOS machine. This is a virtualized
Ubuntu laboratory environment. Git, the Linux VS Code package, Java, Python and Jenkins
were installed and verified there; the tool record is CLI output.

**Question and configuration map**

| Upload | Configuration and scripts | Main records |
| --- | --- | --- |
| 1. Recovery | [recovery.py](../scripts/recovery.py), [Compose](../deploy/compose.yml) | [Recovery](commands/disaster-recovery.json), [failback guard](commands/failback-guard.txt) |
| 2. Testing gates | [Jenkinsfile](../security/Jenkinsfile), [pipeline.py](../scripts/pipeline.py), [promote.py](../scripts/promote.py), [tests](../tests), [GitHub CI](../.github/workflows/ci.yml) | [Jenkins runs](commands/jenkins-builds.json), [successful run 8](commands/jenkins-build-8.txt), [failed unit gate](commands/jenkins-build-6.txt), [failed integration gate](commands/jenkins-build-7.txt) |
| 3. Blue-green | [Nginx](../deploy/nginx.conf), [traffic.py](../scripts/traffic.py) | [Switch measurements](commands/blue-green.json) |
| 4. GitOps | [desired.json](../gitops/desired.json), [reconcile.py](../scripts/reconcile.py) | [Reconciliation](commands/gitops-reconciliation.json), [drift timing](commands/gitops-drift-check.json), [retry verification](commands/gitops-retry-verification.json) |
| 5. Comparison | [Application](../app/server.py), [Dockerfile](../docker/Dockerfile), all configurations above | [Report](../submission/05-Advanced-Strategies-Report-Rishav-2301730245.pdf) |
| 6. Secrets | [Vault server](../vault/config/server.hcl), [policy](../vault/app-policy.hcl), [vault_store.py](../scripts/vault_store.py) | [Access/revocation](commands/secret-management.json), [rotation](commands/secret-rotation.json) |
| 7. Canary | [traffic.py](../scripts/traffic.py), [routing helpers](../scripts/common.py) | [Stable-user cohort results](commands/canary.json) |

**Commands and installation**

[Command index](commands/executed-commands.txt), [Ubuntu tool verification](commands/ubuntu-tools.txt),
[installation output](commands/ubuntu-image-installation.txt), and
[final image build](commands/ubuntu-image-final-build.txt) retain the commands and output.
The [Ubuntu Dockerfile](../jenkins/Dockerfile), [tooling Dockerfile](../jenkins/Tooling.Dockerfile),
[start script](../jenkins/start.sh), [Jenkins initialization](../jenkins/init.groovy), and
[launcher](../scripts/start_jenkins.py) record the environment configuration.
The [VS Code settings](../.vscode/settings.json) provide consistent editing defaults.

**Screenshots and records**

[The screenshot index](screenshots/README.md) explains how each image was captured.
The eight [saved-output HTML pages](evidence) are generated from retained records;
they are labeled as saved output. The ninth screenshot is the actual authenticated
Jenkins stage view. Credentials are excluded from all public artifacts.

Final advanced-experiment JSON records include an execution_environment field showing
Ubuntu and Python versions. The pipeline-*.json/text records and
canary-request-weights.json preserve earlier local development runs. The final canary
uses stable user cohorts in canary.json. Jenkins console files 1–4 preserve setup
problems; 5–8 are the completed gate demonstrations. The raw stage API can label
unreached stages FAILED; console messages establish which stages were skipped.

**Observations**

- Unit and integration failures stopped promotion. The Deploy stage rechecks the
  validated candidate ID, so a replaced container cannot reuse an earlier validation.
- Blue-green completed the sampled switch and rollback without observed failed
  requests. Both sides still share one host and must retain compatible data contracts.
- Canary assignment remained stable for repeated IDs within each stage. The client
  header is suitable for the demonstration; production needs trusted identity and
  larger samples. Error and p95 thresholds are lab thresholds.
- The GitOps controller pulled committed declarations and repaired stopped-container
  and routing drift. A transient Git fetch problem led to a retry fix that retains the
  last good state. A subsequent Ubuntu run completed healthy polls.
- Vault allowed only the scoped read, denied an unrelated path and denied the revoked
  token. Application-key rotation separately invalidated the old key. Bootstrap files
  require protected storage and an operator recovery process.
- Snapshot restore excluded a write made after the backup. Fencing preceded standby
  promotion. The test lost no acknowledged record, but asynchronous replication and
  a one-host topology do not provide a general zero-loss guarantee.
- GitOps, direct CI promotion and traffic strategies were separate experiments. A
  combined production design should publish an accepted desired state from CI and
  let a single reconciler apply it. Immutable images, TLS, redundant hosts and a
  tested recovery schedule would be required beyond this lab.

[Seven submission PDFs](../submission) | [History snapshot](commands/commit-history.txt) | [Complete current commit history](https://github.com/Rishav23av/devops-lab-4/commits/main/)
