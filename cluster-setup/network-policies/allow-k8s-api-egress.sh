#!/bin/bash

# Usage: ./allow-k8s-api-egress.sh [namespace]

NAMESPACE=${1:-default}

echo "Creating network policy for namespace: $NAMESPACE"

# Get the IP addresses of ready Kubernetes API endpoints
K8S_IPS=$(kubectl get endpointslices.discovery.k8s.io kubernetes -o jsonpath='{.endpoints[?(@.conditions.ready==true)].addresses[*]}')

if [ -z "$K8S_IPS" ]; then
    echo "No ready Kubernetes API endpoints found!"
    exit 1
fi

echo "Found Kubernetes API endpoints: $K8S_IPS"

# Generate the network policy YAML
cat > allow-k8s-api-egress.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-k8s-api-egress
  namespace: $NAMESPACE
spec:
  podSelector: {}  # Apply to all pods in namespace
  policyTypes:
  - Egress
  egress:
EOF

# Add each IP address as an egress rule
for ip in $K8S_IPS; do
    cat >> allow-k8s-api-egress.yaml << EOF
  - to:
    - ipBlock:
        cidr: ${ip}/32
    ports:
    - protocol: TCP
      port: 6443
EOF
done

cat allow-k8s-api-egress.yaml