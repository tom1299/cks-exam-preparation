helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

helm install falco falcosecurity/falco \
    --create-namespace \
    --namespace falco \
    --set driver.kind=ebpf

kubectl wait --for=condition=Ready pods -l app.kubernetes.io/name=falco -n falco --timeout=300s