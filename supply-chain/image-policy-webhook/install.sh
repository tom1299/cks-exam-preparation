rm -rf webhook-impl || true
git clone --depth 1 https://github.com/bmuschko/cks-study-guide.git webhook-impl

cd webhook-impl/ch06/image-validation-webhook

./gen-certs.sh

cp ./certs/api-server-client.crt ../../../admission-control/api-server-client.crt
cp ./certs/api-server-client.key ../../../admission-control/api-server-client.key

docker build -t image-validation-webhook:1.0.0 .

kind load docker-image image-validation-webhook:1.0.0


kubectl delete pod image-validation-webhook --ignore-not-found=true
kubectl delete service image-validation-webhook --ignore-not-found=true

kubectl run image-validation-webhook --image=image-validation-webhook:1.0.0 --port=8080
kubectl expose pod image-validation-webhook --port=8080

kubectl wait --for=condition=Ready pod/image-validation-webhook --timeout=60s

# Create a debug pod with curl to test the service from inside the cluster
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
    curl -X POST -H "Content-Type: application/json" \
    -d '{"apiVersion":"imagepolicy.k8s.io/v1alpha1", "kind": "ImageReview", "spec": {"containers": [{"image": "nginx:1.19.0"}]}}' \
    --fail-with-body --insecure https://image-validation-webhook:8080/validate
