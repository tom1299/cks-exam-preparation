
#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <username> [group]"
  exit 1
fi

USER="$1"
GROUP="$2"
DIR="certs"
mkdir -p "$DIR"
KEY="$DIR/$USER.key"
CSR="$DIR/$USER.csr"
CRT="$DIR/$USER.crt"
K8S_CSR_NAME="$USER-csr"

# 1. Create private key
openssl genrsa -out "$KEY" 2048

# 2. Create CSR with CN=username and optional O=group
if [ -n "$GROUP" ]; then
  openssl req -new -key "$KEY" -subj "/CN=$USER/O=$GROUP" -out "$CSR"
else
  openssl req -new -key "$KEY" -subj "/CN=$USER" -out "$CSR"
fi

# 3. Base64 encode CSR for Kubernetes
CSR_BASE64=$(base64 -w0 < "$CSR")

# 4. Create Kubernetes CSR manifest
cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: $K8S_CSR_NAME
spec:
  groups:
  - system:authenticated
  request: $CSR_BASE64
  signerName: kubernetes.io/kube-apiserver-client
  usages:
  - client auth
EOF

# 5. Approve the CSR
kubectl certificate approve "$K8S_CSR_NAME"

# 6. Extract the certificate
kubectl get csr "$K8S_CSR_NAME" -o jsonpath='{.status.certificate}' | base64 -d > "$CRT"

# 7. Test the certificate and key with the current context
kubectl config set-credentials "$USER" --client-certificate="$CRT" --client-key="$KEY" --embed-certs=true
kubectl --user="$USER" get namespaces
