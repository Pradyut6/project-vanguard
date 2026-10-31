# KB-002: Recovering a Terminated StatefulSet & Stale Block Storage Lock

**Article ID:** KB-002  
**Environment:** Ubuntu 24.04 LTS, Kubernetes StatefulSet, Persistent Block Storage, PostgreSQL 16  
**Severity:** P1 - Database Availability & Data Integrity  

## Symptoms
* After an ungraceful node reboot or process crash, the database pod remains stuck in `ContainerCreating` or `Terminating`.
* Downstream microservices return `503 Service Unavailable` on readiness probes due to failed database connections.

## Root Cause Analysis
StatefulSets enforce strict identity guarantees to prevent split-brain corruption on ReadWriteOnce block volumes. When a node loses power or a pod is terminated ungracefully, the kubelet volume manager or PostgreSQL lock file (`postmaster.pid`) may block immediate volume re-mounting until node readiness and filesystem integrity are confirmed.

## Diagnostic Verification
1. Check the pod lifecycle events and volume attachment status:
   ```bash
   kubectl -n vanguard describe pod vanguard-db-0
   kubectl -n vanguard get pvc,pv
   ```

2. Inspect kernel ring buffer logs for ext4 or block device I/O errors:
    ```bash
    dmesg -T | grep -iE "ext4|blk_update_request|error"
    ```

## Resolution & Prevention
1. Confirm the old pod process is fully terminated on the underlying worker node before forcing pod deletion:
    ```bash
    kubectl -n vanguard delete pod vanguard-db-0 --grace-period=0 --force
    ```

2. Verify the StatefulSet controller binds the existing PersistentVolumeClaim (postgres-block-data-vanguard-db-0) to the replacement pod:
    ```bash
    kubectl -n vanguard wait --for=condition=ready pod/vanguard-db-0 --timeout=90s
    ```

3. Validate database table integrity and trigger an off-site S3 backup job to MinIO:
    ```bash
    curl -s http://localhost:30080/incidents | python3 -m json.tool
    kubectl -n vanguard create job --from=cronjob/postgres-s3-backup post-recovery-backup
    ```
