# Project Vanguard: Ubuntu 24.04 Cloud-Native Platform & Reliability Engineering Suite

An end-to-end Cloud and DevOps engineering portfolio project built on **Ubuntu 24.04 LTS (Noble Numbat)**. Project Vanguard pairs automated multi-node infrastructure provisioning, Kubernetes stateful orchestration, CI/CD CVE scanning, and full-stack observability with **three production Root-Cause Analysis (RCA) Knowledge Base runbooks**.

## 5-Minute Recruiter & Hiring Manager Tour
* **Hardened Ubuntu 24.04 Microservice:** [`app/Dockerfile`](app/Dockerfile) & [`app/main.py`](app/main.py) (PEP 668 virtual environment isolation, non-root `ubuntu` UID 1000 execution, Prometheus metrics, and structured JSON logging).
* **Linux Host Networking & UFW Firewall Automation:** [`scripts/provision-nodes.sh`](scripts/provision-nodes.sh) & [`ansible/playbooks/site-networking.yml`](ansible/playbooks/site-networking.yml) (Custom Linux bridge `vanguard-br0`, VXLAN MTU tuning, `sysctl` kernel forwarding, and default-deny UFW rules).
* **Ubuntu LTS Lifecycle & Patch Governance:** [`ansible/playbooks/ubuntu-lifecycle.yml`](ansible/playbooks/ubuntu-lifecycle.yml) (`unattended-upgrades` restricted to `noble-security`, `apt-mark hold` package pinning, and automated JSON compliance auditing).
* **Stateful Kubernetes & S3 Disaster Recovery:** [`k8s/storage/postgres-statefulset.yaml`](k8s/storage/postgres-statefulset.yaml) & [`k8s/storage/minio-s3-backup.yaml`](k8s/storage/minio-s3-backup.yaml) (Persistent block storage `StatefulSet` and automated `pg_dump` backups to S3-compatible MinIO object storage).
* **CI/CD & Ubuntu Security Notice (USN) Scanning:** [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) (Automated Flake8 linting, Docker builds, **Trivy** OS/library vulnerability scanning, and **Kubeconform** manifest validation).
* **Centralized Observability (PLG Stack):** [`k8s/monitoring/observability-stack.yaml`](k8s/monitoring/observability-stack.yaml) (**Prometheus**, **Grafana**, **Loki**, and **Promtail** DaemonSet).
* **Customer Escalation & RCA Knowledge Base:**
  * [**KB-001:** Resolving Silent Packet Drops Caused by VXLAN Overlay MTU Mismatch](knowledge-base/KB-001-vxlan-mtu-mismatch.md)
  * [**KB-002:** Recovering a Terminated StatefulSet & Stale Block Storage Lock](knowledge-base/KB-002-statefulset-block-storage-recovery.md)
  * [**KB-003:** Debugging Microservice OOMKills & Ubuntu Package Lifecycle Governance](knowledge-base/KB-003-oomkiller-memory-leak-lifecycle.md)

## System Architecture

```mermaid
graph TB
    subgraph CICD["CI/CD & Security Governance (GitHub Actions)"]
        GH["Git Push / PR"] --> FLAKE["Flake8 Syntax Check"]
        FLAKE --> BUILD["Ubuntu 24.04 Docker Build"]
        BUILD --> TRIVY["Trivy USN & CVE Scan"]
        TRIVY --> KCONF["Kubeconform Manifest Check"]
    end

    subgraph HOST["Ubuntu 24.04 LTS Host & Network Layer (LXD + Ansible)"]
        BR["Linux Bridge: vanguard-br0 (10.240.0.1/24, MTU 1500)"]
        UFW["UFW Firewall + sysctl Kernel Tuning"]
        VXLAN["VXLAN Overlay: vxlan0 (Tuned MTU 1450)"]
        LIFE["Ubuntu Lifecycle: unattended-upgrades + apt-mark hold"]
        BR --> UFW --> VXLAN
    end

    subgraph K8S["Kubernetes Cluster (vanguard namespace)"]
        API["vanguard-api Deployment (2 Replicas, Non-Root UID 1000)"]
        DB["vanguard-db PostgreSQL StatefulSet"]
        PVC["Persistent Block Storage (2Gi ReadWriteOnce)"]
        CRON["CronJob: postgres-s3-backup"]
        MINIO["MinIO S3 Object Storage (s3://vanguard-backups)"]
        API --> DB
        DB --> PVC
        CRON --> DB
        CRON --> MINIO
    end

    subgraph OBS["Observability & Incident Response"]
        PROM["Prometheus (Metrics Scraper)"]
        PROMTAIL["Promtail DaemonSet (Pod Log Shipper)"]
        LOKI["Grafana Loki (Log Aggregation)"]
        GRAF["Grafana Dashboard (NodePort 30300)"]
        KB["Customer Knowledge Base (KB-001, KB-002, KB-003)"]
        PROM --> GRAF
        PROMTAIL --> LOKI --> GRAF
        GRAF --> KB
    end

    KCONF --> K8S
    HOST --> K8S
    K8S --> OBS

## Technology Stack & Engineering Scope

| Domain                    | Technologies                                     | Engineering Implementation                                        |
| ------------------------- | ------------------------------------------------ | ----------------------------------------------------------------- |
| Linux & Virtualization    | Ubuntu 24.04 LTS, Canonical LXD                  | Multi-node system containers with custom bridge networking        |
| System Networking         | iproute2, UFW, VXLAN, tcpdump                    | Bridge MTU 1500 vs VXLAN MTU 1450 tuning and host firewalling     |
| Configuration & Lifecycle | Ansible, unattended-upgrades, dpkg               | Automated security pocket patching and package version pinning    |
| Orchestration & Storage   | Kubernetes (K3s/k3d), StatefulSet, MinIO         | ReadWriteOnce block persistence and automated S3 database backups |
| CI/CD & Observability     | GitHub Actions, Trivy, Prometheus, Loki, Grafana | CVE/USN pipeline scanning and unified metrics/log correlation     |

# Repository Structure

project-vanguard/
├── .github/workflows/
│   └── ci-cd.yml                                      # CI/CD pipeline with Trivy USN scan & Kubeconform
├── ansible/
│   ├── ansible.cfg                                    # Ansible SSH & inventory configuration
│   ├── inventory.ini                                  # 3-node Ubuntu 24.04 cluster inventory & MTU vars
│   └── playbooks/
│       ├── site-networking.yml                        # Linux bridge, sysctl, VXLAN MTU & UFW hardening
│       ├── k8s-cluster.yml                            # Automated Kubernetes node preparation playbook
│       └── ubuntu-lifecycle.yml                       # Ubuntu 24.04 security patching & apt-mark hold audit
├── app/
│   ├── Dockerfile                                     # Hardened Ubuntu 24.04 image (venv + non-root user)
│   ├── main.py                                        # Flask microservice with Prometheus & chaos endpoints
│   └── requirements.txt                               # Pinned Python dependencies
├── k8s/
│   ├── base/api-deployment.yaml                       # Non-root API Deployment, resource limits & NodePort
│   ├── monitoring/observability-stack.yaml            # Prometheus, Loki, Promtail DaemonSet & Grafana
│   └── storage/
│       ├── minio-s3-backup.yaml                       # MinIO S3 server & nightly pg_dump CronJob
│       └── postgres-statefulset.yaml                  # StorageClass & PostgreSQL StatefulSet
├── knowledge-base/
│   ├── KB-001-vxlan-mtu-mismatch.md                   # RCA: VXLAN fragmentation & Path MTU discovery
│   ├── KB-002-statefulset-block-storage-recovery.md   # RCA: StatefulSet recovery & block storage locks
│   └── KB-003-oomkiller-memory-leak-lifecycle.md      # RCA: Linux OOMKiller (Exit 137) & APT pinning
├── scripts/
│   └── provision-nodes.sh                             # Automated LXD bridge & 3-node Ubuntu 24.04 bootstrap
├── .env.example                                       # Environment template (Zero secrets stored in Git)
└── docker-compose.yml                                 # Local multi-container integration test stack


## Quick-Start Reproduction Guide
1. Provision Ubuntu 24.04 Nodes, Networking & Lifecycle Governance
    ```bash
    sg lxd -c "./scripts/provision-nodes.sh"
    ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/playbooks/site-networking.yml
    ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/playbooks/ubuntu-lifecycle.yml
    ```

2. Deploy Kubernetes Storage, Application & Observability Stack
    ```bash
    docker build -t vanguard-api:0.1.0 ./app
    k3d cluster create vanguard --servers 1 --agents 2 -p "30080:30080@server:0" -p "30300:30300@server:0" --k3s-arg "--disable=traefik@server:0"
    k3d image import vanguard-api:0.1.0 -c vanguard

    kubectl apply -f k8s/storage/postgres-statefulset.yaml
    kubectl apply -f k8s/storage/minio-s3-backup.yaml
    kubectl apply -f k8s/base/api-deployment.yaml
    kubectl apply -f k8s/monitoring/observability-stack.yaml

3. Verify Health, S3 Backups & Observability Endpoints
    Microservice Health Check: 
    ```bash
    curl -s http://localhost:30080/health | python3 -m json.tool
    ```
    Grafana UI (Prometheus + Loki): http://localhost:30300