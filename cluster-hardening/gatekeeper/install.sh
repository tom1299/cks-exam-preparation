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

kubectl apply -f https://raw.githubusercontent.com/bmuschko/cks-study-guide/refs/heads/master/ch06/supply-chain/whitelisting-registries/gatekeeper/allowed-repos-constraint-template.yaml
kubectl apply -f ./gcr-allowed-repos-constraint-namespaced.yaml

kubectl wait --for=jsonpath='{.status.byPod[0]}' k8sallowedrepos.constraints.gatekeeper.sh/repo-is-gcr-namespaced --timeout=300s

# Run a pod and capture output
output=$(kubectl run pod nginx --image=nginx:latest 2>&1)

echo "$output" | grep "container <pod> has an invalid image repo" 
