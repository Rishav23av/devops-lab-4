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
