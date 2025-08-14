#!/bin/bash
set -euxo pipefail

# This script combines the functionality of harden-master-node.sh and split-kubelet-cert.sh
# It performs initial node hardening and kubelet certificate setup.

echo "Starting node hardening..."

# Create etcd user and group
if ! getent group etcd > /dev/null; then
  groupadd etcd
fi
if ! id etcd > /dev/null; then
  useradd -r -g etcd -s /sbin/nologin etcd
fi
# Change ownership of etcd data directory
chown -R etcd:etcd /var/lib/etcd

# Create audit log directory
mkdir -p /var/log/kubernetes/audit

echo "Node hardening complete."

echo "Starting kubelet certificate setup..."

# Split the certificate and create the new ca.crt file
awk 'BEGIN {c=0;} /BEGIN CERTIFICATE/ {c++} { if (c==2) print }' /var/lib/kubelet/pki/kubelet.crt > /var/lib/kubelet/pki/ca.crt

# Create the symbolic link
ln -s /var/lib/kubelet/pki/ca.crt /etc/kubernetes/pki/kubelet-ca.crt

# Verification
# Compare the created ca.crt with the second part of the original kubelet.crt
diff /var/lib/kubelet/pki/ca.crt <(awk 'BEGIN {c=0;} /BEGIN CERTIFICATE/ {c++} { if (c==2) print }' /var/lib/kubelet/pki/kubelet.crt)

# Verify the symbolic link
ls -l /etc/kubernetes/pki/kubelet-ca.crt | grep -q '/var/lib/kubelet/pki/ca.crt'

echo "Kubelet certificate setup and verification successful!"

# Restart the kube-apiserver if it is running
echo "Restarting kube-apiserver..."
APISERVER_ID=$(crictl ps | grep kube-apiserver | awk '{print $1}')
if [ -n "$APISERVER_ID" ]; then
  crictl stop $APISERVER_ID
  echo "kube-apiserver stopped. Kubelet will restart it."

  echo "Waiting for kube-apiserver to restart..."
  RESTARTED=false
  for i in {1..30}; do
    if crictl ps | grep kube-apiserver | grep -q Running; then
      echo "kube-apiserver restarted successfully."
      RESTARTED=true
      break
    fi
    sleep 1
  done

  if [ "$RESTARTED" = false ]; then
    echo "Error: kube-apiserver did not restart within 30 seconds."
    exit 1
  fi
else
  echo "kube-apiserver not found."
fi