#!/usr/bin/env bash
set -e
BASE_DIR=$(dirname -- "$(readlink -f -- "$0"; )"; )

rm -rf webhook-impl || true
git clone --depth 1 https://github.com/bmuschko/cks-study-guide.git webhook-impl

cd webhook-impl/ch06/image-validation-webhook

# Append DNS:kind-control-plane to webhook cert
sed -i 's/subjectAltName = DNS:image-validation-webhook/&,DNS:kind-control-plane/' ./gen-certs.sh

./gen-certs.sh

cp ./certs/api-server-client.crt ../../../admission-control/api-server-client.crt
cp ./certs/api-server-client.key ../../../admission-control/api-server-client.key
cp ./certs/ca.crt ../../../admission-control/ca.crt

docker build -t image-validation-webhook:1.0.0 .

kind load docker-image image-validation-webhook:1.0.0


kubectl delete pod image-validation-webhook --ignore-not-found=true
kubectl delete service image-validation-webhook --ignore-not-found=true

kubectl run image-validation-webhook --image=image-validation-webhook:1.0.0 --port=8080
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: image-validation-webhook
spec:
  type: NodePort
  ports:
  - port: 8080
    nodePort: 30080
  selector:
    run: image-validation-webhook
EOF

kubectl wait --for=condition=Ready pod/image-validation-webhook --timeout=60s

# Create a debug pod with curl to test the service from inside the cluster
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
    curl -X POST --fail-with-body --insecure -H "Content-Type: application/json" \
    -d '{"apiVersion":"imagepolicy.k8s.io/v1alpha1", "kind": "ImageReview", "spec": {"containers": [{"image": "nginx:1.19.0"}]}}' https://image-validation-webhook:8080/validate


# Run a pod that would violate the policy
kubectl run nginx --image=nginx:latest

kubectl wait --for=condition=Ready pod/nginx --timeout=60s

kubectl delete pod nginx

# At this point the api server uses the webhook with the admission controller
# still allowing images even if they don't meet the policy. Now enforce the policy
# Change to the folder where the script is located
cd $BASE_DIR
sed -i 's/defaultAllow: true/defaultAllow: false/' admission-control/image-policy-webhook-admission-config.yaml

API_SERVER_ID=$(docker exec kind-control-plane crictl ps --name kube-apiserver -q)
docker exec kind-control-plane crictl stop --timeout 30 $API_SERVER_ID

echo "Waiting for API server to restart..."
ATTEMPT=0
MAX_ATTEMPTS=6
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker exec kind-control-plane crictl ps --name kube-apiserver -q | grep -q .; then
        echo "API server has successfully restarted"
        break
    fi
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Timed out waiting for API server to restart"
    exit 1
fi

MAX_RETRIES=6
for i in $(seq 1 $MAX_RETRIES); do
    echo "Attempt $i: Waiting for kube-apiserver to be ready..."
    kubectl wait -n kube-system --for=condition=Ready pod/kube-apiserver-kind-control-plane && break
    if [ $i -lt $MAX_RETRIES ]; then
        echo "Attempt $i failed. Sleeping for 5 seconds before retry..."
        sleep 5
    else
        echo "All $MAX_RETRIES attempts failed."
        exit 1
    fi
done

return kubectl run pod nginx --image=nginx:latest 2>&1 | grep "invalid image repo nginx:latest"