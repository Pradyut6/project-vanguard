# KB-001: Resolving Silent Packet Drops Caused by VXLAN Overlay MTU Mismatch

**Article ID:** KB-001  
**Environment:** Ubuntu 24.04 LTS (Noble Numbat), Linux Bridge Networking, Kubernetes VXLAN Overlay  
**Severity:** P1 - Production Network Degradation  

## Symptoms
* ICMP echo requests (`ping`) and small HTTP health checks succeed between cluster nodes.
* Large HTTP POST payloads, TLS handshakes, and bulk PostgreSQL queries hang indefinitely and time out.
* TCP retransmission counters increment rapidly in node network telemetry.

## Root Cause Analysis
Standard Ethernet and virtual bridge interfaces (`vanguard-br0` / `eth0`) default to a Maximum Transmission Unit (MTU) of `1500` bytes. VXLAN overlay networks encapsulate Layer 2 frames inside UDP packets, adding **50 bytes of header overhead**:
* **Outer IPv4 Header:** 20 bytes
* **Outer UDP Header:** 8 bytes
* **VXLAN Header:** 8 bytes
* **Inner Ethernet Header:** 14 bytes

When the overlay interface is misconfigured with an MTU mismatch (or exceeds the underlying bridge capacity minus 50 bytes), frames with the `DF` (Don't Fragment) bit set are dropped with `Frag needed and DF set` (`Message too long`).

## Diagnostic Verification
1. Inspect the active MTU on both the host bridge interface and the VXLAN interface:
   ```bash
   sg lxd -c "lxc exec vanguard-node-1 -- ip -d link show eth0"
   sg lxd -c "lxc exec vanguard-node-1 -- ip -d link show vxlan0"
   ```

2. Test path MTU discovery with the Don't Fragment bit enabled:
    ```bash
    sg lxd -c "lxc exec vanguard-node-1 -- ping -c 2 -M do -s 1420 10.240.0.12"
    ```

3. Capture ICMP fragmentation-needed packets on the host interface:
    ```bash
    sg lxd -c "lxc exec vanguard-node-1 -- tcpdump -i eth0 -c 5 -nn icmp"
    ```

## Resolution & Prevention
1. Set the VXLAN overlay MTU to 1450 bytes across all Ubuntu nodes (50 bytes below the 1500-byte bridge MTU):
    ```bash
    sg lxd -c "lxc exec vanguard-node-1 -- ip link set dev vxlan0 mtu 1450 up"
    ```

2. Persist the configuration inside the Ansible inventory and network role (overlay_mtu=1450) and re-run the playbook:
    ```bash
    ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/playbooks/site-networking.yml
    ```

3. Enable TCP MSS clamping on egress traffic so upstream routers automatically negotiate compatible segment sizes.