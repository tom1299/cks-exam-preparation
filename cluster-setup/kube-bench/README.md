# kube-bench
- kube-bench is provided by Aqua Security
- kube-bench can be run as a cron job in for control plane and worker nodes

## TODO
- Examine the cronjob that runs kube-bench at [this link](https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-master.yaml). Questions: What permissions does it have / need, can these permissions be restricted?
- Create kind configuration that meetts the CIS benchmark
- Give the task of running kube-bench and fixing an issue to gemini-cli