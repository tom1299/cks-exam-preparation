helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

helm uninstall falco -n falco --ignore-not-found

helm install falco falcosecurity/falco \
    --create-namespace \
    --namespace falco \
    --set driver.kind=ebpf \
    --values ./falco-values.yaml

kubectl wait --for=condition=Ready pods -l app.kubernetes.io/name=falco -n falco --timeout=300s