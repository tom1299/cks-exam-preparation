#!/bin/bash
set -e

rm -rf certs/*

# 1. Delete and recreate the cluster
kind delete cluster || true
kind create cluster

# 2. Apply all permission yamls
kubectl apply -f list-namespaces-authenticated.yaml
kubectl apply -f list-pods-pod-reader.yaml
kubectl apply -f list-configmaps-configmap-reader.yaml

# 3. Create users
./create-user.sh test-user1
./create-user.sh test-user2 pod-reader
./create-user.sh test-user3 pod-reader configmap-reader

# 4. Check permissions for test-user1
kubectl auth can-i list namespaces --as=test-user1
if kubectl auth can-i list pods --as=test-user1; then
  echo "test-user1 should NOT be able to list pods"; exit 1
else
  echo "test-user1 cannot list pods (expected)"
fi

# 5. Check permissions for test-user2
kubectl auth can-i list namespaces --as=test-user2
kubectl auth can-i list pods --as=test-user2 --as-group=pod-reader
if kubectl auth can-i list configmaps --as=test-user2; then
  echo "test-user2 should NOT be able to list configmaps"; exit 1
else
  echo "test-user2 cannot list configmaps (expected)"
fi

# 6. Check permissions for test-user3
kubectl auth can-i list namespaces --as=test-user3
kubectl auth can-i list pods --as=test-user3 --as-group=pod-reader
kubectl auth can-i list configmaps --as=test-user3 --as-group=configmap-reader
if kubectl auth can-i list services --as=test-user3; then
  echo "test-user3 should NOT be able to list services"; exit 1
else
  echo "test-user3 cannot list services (expected)"
fi
