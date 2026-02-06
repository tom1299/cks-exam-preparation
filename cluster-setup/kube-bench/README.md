# kube-bench
- kube-bench is provided by Aqua Security
- kube-bench can be run as a cron job in for control plane and worker nodes

## TODO
- Examine the cronjob that runs kube-bench at [this link](https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-master.yaml). Questions: What permissions does it have / need, can these permissions be restricted?
- Create kind configuration that meetts the CIS benchmark
- Give the task of running kube-bench and fixing an issue to gemini-cli

## Findings
### kubectl logs with labels only returns last 10 lines
**Description**:
`kubectl logs kube-bench-master-7j8gg` returns the full logs while `kubectl logs -l job-name=kube-bench-master --all-containers=true` returns only the last 10 lines of the logs.
**Solution**:
Default behavior see https://github.com/kubernetes/kubectl/issues/917#issuecomment-678889306

### Kube-bench agent
**Description**:
Implement a kube-bench agent that can run kube-bench and fix the issues it finds:
- Follow the concept of HolmesGPT of run books for individual prompts for fixing specific issues