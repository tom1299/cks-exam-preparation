# kube-bench
- kube-bench is provided by Aqua Security
- kube-bench can be run as a cron job in for control plane and worker nodes

## TODO
- Examine the cronjob that runs kube-bench at [this link](https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-master.yaml). Questions: What permissions does it have / need, can these permissions be restricted?
- Create kind configuration that meetts the CIS benchmark
- Give the task of running kube-bench and fixing an issue to gemini-cli

## Findings
`kubectl logs kube-bench-master-7j8gg` returns the full logs while `kubectl logs -l job-name=kube-bench-master --all-containers=true` returns only the last 10 lines of the logs.

## Gemini CLI
- Take a closer look at how to setup [mcp servers](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md)