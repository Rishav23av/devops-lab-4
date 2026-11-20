devops-lab-4

Rishav | Roll no. 2301730245

Advanced deployment experiments using a small Python app, Nginx, Redis and
HashiCorp Vault. All host ports are bound to localhost. Python uses only its
standard library; Docker and Docker Compose run the laboratory services.

**Start the lab**

```bash
python3 -m unittest tests.test_unit -v
python3 -m scripts.setup
```

The app is on http://localhost:5040. Vault listens on localhost:8240. The
bootstrap creates a file-backed Vault, initializes and unseals it, and creates
an AppRole with read access only to secret/data/lab4/app. Generated credentials
stay in the ignored .runtime directory. Do not publish that directory.

**Experiments**

```bash
python3 -m scripts.pipeline --scenario unit-failure
python3 -m scripts.pipeline --scenario integration-failure
python3 -m scripts.pipeline
python3 -m scripts.traffic
python3 -m scripts.recovery
python3 -m scripts.reconcile --duration 60
```

The first two pipeline commands are expected to fail and leave live routing
unchanged. The successful pipeline tests the green candidate before promotion.
Traffic experiments measure blue-green switches and a gradual canary, including
a deliberately faulty canary and a metric-triggered rollback. Recovery copies
a Redis snapshot into an isolated instance, then fences the primary and promotes
the standby. GitOps pulls gitops/desired.json from GitHub and repairs version,
container-state and traffic drift.

**Ubuntu 24.04 and Jenkins**

The Jenkins controller and its built-in laboratory agent run in an Ubuntu 24.04
container. Git, Python, Java 21 and the Linux VS Code package are installed there.
The editor is also available on the host for reviewing this repository. Build the
tooling cache and Ubuntu image with:

```bash
docker build -f jenkins/Tooling.Dockerfile -t rishav-lab4-tooling:local .
docker build -f jenkins/Dockerfile -t rishav-lab4-jenkins-ubuntu:local .
python3 -m scripts.start_jenkins
```

The recorded build reused the matching tooling cache from the earlier labs.
jenkins/start.sh sets the Git identity and starts Jenkins from its WAR distribution.
security/Jenkinsfile checks out GitHub, verifies the Ubuntu tools, runs the unit
gate, prepares and integration-tests the candidate, then promotes that exact
validated container in a separate Deploy stage. The controller has one executor
and the ubuntu2404 label. A dedicated local controller with Docker socket access
is used only for trusted lab code.

LAB4_HOST_ROOT allows Docker bind mounts to resolve to the host repository when
Compose runs inside the controller. VAULT_ADDR and LAB4_URL point to the host's
loopback-bound services through host.docker.internal. The Jenkins password and
Vault bootstrap material remain in the ignored runtime directory.

These are controlled, single-host laboratory demonstrations. Vault uses local
HTTP and a one-share bootstrap for this lab. Failover promotion is operator
initiated, Redis replication is asynchronous, and short traffic samples do not
prove availability under every failure. Recovery objectives and observed values
are recorded separately in docs/commands/.

**Cleanup**

```bash
docker compose -f deploy/compose.yml down -v
```

This removes only the named Lab 4 stack and its volumes. Remove .runtime
separately when the saved local bootstrap and backup files are no longer needed.

**References**

- [NGINX configuration reload](https://nginx.org/en/docs/control.html)
- [NGINX weighted upstreams](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)
- [Vault AppRole API](https://developer.hashicorp.com/vault/api-docs/auth/approle)
- [Redis WAIT and its limits](https://redis.io/docs/latest/commands/wait/)
- [OpenGitOps principles](https://github.com/open-gitops/documents/blob/main/PRINCIPLES.md)
