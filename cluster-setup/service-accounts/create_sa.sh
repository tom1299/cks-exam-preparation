#!/bin/bash
set -e

openssl genrsa -out jill.key 3072

openssl req -new -key jill.key -out jill.csr -subj "/CN=jill/O=observer"

CSR=$(base64 < jill.csr | tr -d "\n")

ORIGINAL_CONTEXT=$(kubectl config current-context)

cleanup() {
  kubectl config use-context "$ORIGINAL_CONTEXT"
  kubectl config delete-user jill || true
}

trap cleanup EXIT

kubectl config use-context kind-kind

kubectl delete csr jill --ignore-not-found

cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: jill
spec:
  request: $CSR
  signerName: kubernetes.io/kube-apiserver-client
  usages:
  - client auth
EOF

kubectl certificate approve jill

rm jill.crt | true

kubectl get csr jill -o jsonpath="{.status.certificate}" | base64 -d > jill.crt

# TODO: Make feature request for --ignore-not-found
kubectl config delete-user jill | true

kubectl config set-credentials jill --client-key=jill.key --client-certificate=jill.crt --embed-certs=true

CLUSTER=$(kubectl config current-context)

kubectl config set-context jill --cluster=$CLUSTER --user=jill

kubectl delete role pod-lister --ignore-not-found

kubectl create role pod-lister --verb=get --verb=list --resource=pods

kubectl delete rolebinding pod-lister-binding-jill --ignore-not-found

kubectl create rolebinding pod-lister-binding-jill --role=pod-lister --user=jill

kubectl delete role secret-lister --ignore-not-found

kubectl create role secret-lister --verb=get --verb=list --resource=secrets

kubectl delete rolebinding secret-lister-binding-observer --ignore-not-found

kubectl create rolebinding secret-lister-binding-observer --role=secret-lister --group=observer

kubectl config use-context jill

kubectl get pods -n default

if ! kubectl get pods -n kube-system; then
  echo "Error: jill does not have permission to list pods in kube-system namespace."
fi

kubectl get secrets -n default

if ! kubectl get secrets -n kube-system; then
  echo "Error: jill does not have permission to list secrets in kube-system namespace."
fi


