#!/bin/bash

set -euxo pipefail

# Get the node container name
NODE_CONTAINER_NAME=$(docker ps --filter "name=kind-control-plane" --format "{{.Names}}")

# Split the certificate and create the new ca.crt file
docker exec "$NODE_CONTAINER_NAME" /bin/bash -c "awk 'BEGIN {c=0;} /BEGIN CERTIFICATE/ {c++} { if (c==2) print }' /var/lib/kubelet/pki/kubelet.crt > /var/lib/kubelet/pki/ca.crt"

# Create the symbolic link
docker exec "$NODE_CONTAINER_NAME" ln -s /var/lib/kubelet/pki/ca.crt /etc/kubernetes/pki/kubelet-ca.crt

# Verification
# Compare the created ca.crt with the second part of the original kubelet.crt
docker exec "$NODE_CONTAINER_NAME" /bin/bash -c "diff /var/lib/kubelet/pki/ca.crt <(awk 'BEGIN {c=0;} /BEGIN CERTIFICATE/ {c++} { if (c==2) print }' /var/lib/kubelet/pki/kubelet.crt)"

# Verify the symbolic link
docker exec "$NODE_CONTAINER_NAME" ls -l /etc/kubernetes/pki/kubelet-ca.crt | grep -q '/var/lib/kubelet/pki/ca.crt'

echo "Verification successful!"
