#!/usr/bin/env bash
set -euo pipefail

BRIDGE_NAME="vanguard-br0"
SUBNET="10.240.0.1/24"
SSH_KEY_PATH="$HOME/.ssh/vanguard_ed25519"
NODES=("vanguard-node-1" "vanguard-node-2" "vanguard-node-3")

echo "=== 1. Generating Dedicated SSH Keypair (Outside Git Repo) ==="
if [ ! -f "$SSH_KEY_PATH" ]; then
    ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N "" -C "ansible@project-vanguard"
fi

echo "=== 2. Creating Custom Linux Bridge: $BRIDGE_NAME (MTU 1500) ==="
if ! lxc network show "$BRIDGE_NAME" >/dev/null 2>&1; then
    lxc network create "$BRIDGE_NAME" \
        ipv4.address="$SUBNET" \
        ipv4.nat=true \
        ipv6.address=none \
        bridge.mtu="1500"
fi

echo "=== 3. Launching 3 Ubuntu 24.04 LTS Nodes ==="
for i in "${!NODES[@]}"; do
    NODE="${NODES[$i]}"
    STATIC_IP="10.240.0.1$((i+1))"

    if ! lxc info "$NODE" >/dev/null 2>&1; then
        echo "Launching $NODE with IP $STATIC_IP..."
        lxc init ubuntu:24.04 "$NODE" \
            -c security.nesting=true \
            -c linux.kernel_modules=ip_tables,ip6_tables,netlink_diag,nf_nat,overlay
        lxc network attach "$BRIDGE_NAME" "$NODE" eth0 eth0
        lxc config device set "$NODE" eth0 ipv4.address "$STATIC_IP"
        lxc start "$NODE"
    else
        echo "$NODE already exists, skipping creation."
    fi
done

echo "=== 4. Waiting for Nodes to Boot & Injecting SSH Keys ==="
sleep 8
for NODE in "${NODES[@]}"; do
    lxc exec "$NODE" -- cloud-init status --wait >/dev/null 2>&1 || true
    lxc exec "$NODE" -- apt-get update -qq
    lxc exec "$NODE" -- apt-get install -y -qq openssh-server python3 sudo ufw iproute2 tcpdump
    lxc exec "$NODE" -- mkdir -p /root/.ssh
    lxc file push "${SSH_KEY_PATH}.pub" "$NODE/root/.ssh/authorized_keys"
    lxc exec "$NODE" -- chmod 600 /root/.ssh/authorized_keys
    lxc exec "$NODE" -- chown root:root /root/.ssh/authorized_keys
    lxc exec "$NODE" -- systemctl enable --now ssh
done

echo "=== 5. Cluster Nodes Ready ==="
lxc list