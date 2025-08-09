# Cluster setup

## Notes
- Visual policy editor: [networkpolicy.io](https://networkpolicy.io/)
- Use a default network policy to deny ingress traffic to all pods and then add fine grained policies to allow specific traffic.
- Center of Internet Security (CIS) benchmarks for Kubernetes: [CIS Kubernetes](https://www.cisecurity.org/benchmark/kubernetes/)
- kube-bench: [kube-bench](https://github.com/aquasecurity/kube-bench) is a tool to check if Kubernetes meets the CIS benchmarks.