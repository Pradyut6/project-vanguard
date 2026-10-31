# KB-003: Debugging Microservice OOMKills & Ubuntu Package Lifecycle Governance

**Article ID:** KB-003  
**Environment:** Ubuntu 24.04 LTS, Gunicorn Python Microservice, Prometheus, Grafana Loki  
**Severity:** P2 - Application Stability & OS Patch Management  

## Symptoms
* Application pods restart periodically with exit code `137` (`SIGKILL`).
* Grafana dashboards show container memory utilization climbing linearly to the 128Mi cgroup limit.

## Root Cause Analysis
Unbounded in-memory buffering in the application worker process exhausts the Kubernetes container memory cgroup limit (`128Mi`). When the cgroup threshold is breached, the Linux kernel Out-Of-Memory killer terminates the worker process with `SIGKILL` (exit code 137). In production environments, unpinned OS package upgrades during maintenance windows can also introduce shared library memory regressions.

## Diagnostic Verification
1. Query structured application logs in Grafana Loki or via CLI to identify anomalous memory allocation events:
   ```bash
   kubectl -n vanguard logs -l app=vanguard-api --tail=50 | grep "CHAOS TRIGGERED"
   ```

2. Inspect pod termination reasons and kernel OOM events:
    ```bash
    kubectl -n vanguard describe pod -l app=vanguard-api | grep -A 5 -i "Last State"
    ```

3. Audit recent Ubuntu package modifications and verify held critical packages:
    ```bash
    cat /var/log/vanguard-lifecycle-audit.json
    apt-mark showhold
    ```

## Resolution & Prevention
1. Disable unauthenticated diagnostic/leak endpoints in production (ENABLE_CHAOS_ENDPOINTS=false) and perform a rolling restart:
    ```bash
    kubectl -n vanguard rollout restart deployment/vanguard-api
    ```

2. Enforce Kubernetes requests (64Mi) and limits (128Mi) on all workloads so a single runaway container cannot starve the Ubuntu host kernel.

3. Restrict automated updates strictly to the ${distro_codename}-security pocket via unattended-upgrades and pin critical networking packages using ansible/playbooks/ubuntu-lifecycle.yml.
