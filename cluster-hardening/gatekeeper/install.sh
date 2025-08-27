#!/bin/bash

kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.20.0/deploy/gatekeeper.yaml

echo "Waiting for Gatekeeper pods to be ready..."
if ! kubectl wait --for=condition=ready pod --all -n gatekeeper-system --timeout=300s; then
    echo "Error: Gatekeeper pods failed to become ready within timeout"
    exit 1
fi
echo "Gatekeeper is ready!"

kubectl apply -f https://raw.githubusercontent.com/bmuschko/cks-study-guide/refs/heads/master/ch05/gatekeeper/constraint-template-labels.yaml
kubectl apply -f https://raw.githubusercontent.com/bmuschko/cks-study-guide/refs/heads/master/ch05/gatekeeper/constraint-ns-labels.yaml

