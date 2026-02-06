# Fix kube-bench findings for the cluster kind

## Command line tools to use
Besides usual shell commands use the following commands:
- `kubectl`: to run commands against Kubernetes clusters
- `kind`: to manage clusters
- `docker`: to manage examine the running containers that make up the cluster and execute commands in them
- `crictl`: to manage container runtimes in the docker container of the node

## Instructions
- Create a sig/kind cluster from the configuration file `kind-config.yaml`
- Delete the cluster if it already exists
- Run kube-bench against the cluster using the command:
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-master.yaml
  ```
- Check the results of kube-bench by running:
  ```bash
  kubectl logs -l job-name=kube-bench-master --all-containers=true --tail=-1
  ``` 
- Analyze the report
- Only fix the issues of type `FAIL` one by one by adding the necessary configuration to the `kind-config.yaml` file. Ignore the issue `[FAIL] 1.2.5 Ensure that the --kubelet-certificate-authority argument is set as appropriate (Automated)`.
- After each fix, delete the cluster and recreate it using the command:
  ```bash
  kind delete cluster --name kind
  kind create cluster --name kind --config kind-config.yaml
  ```
  and verify that the issue is fixed by running kube-bench again. Verify that the cluster is still working by creating a pod with the command:
  ```bash
  kubectl run nginx --image=nginx --restart=Never
  ```
  and accessing its logs
- Write the description of the issues that could not be solved into a text file named "kube-bench-findings.txt" in this directory with a short description why the issue could not be fixed.

## Hints for fixing issues
- Read the "Remediation" section of the kube-bench report
- For issues related to API server, controller manager, scheduler, etc., you may need to add the necessary flags to the `kind-config.yaml` file under the `kind` section. Especially, by using "Kubeadm Config Patches".
- For issues related to the nodes host, run commands for fixing issues using `docker exec`. Successful commands should be added to a script named `harden-master-node.sh` that can be run on the node after the cluster has been created. This script should be placed in the same directory as this file.
- Look at the logs of the components on the node (e.g., kubelet, kube-proxy) to understand the issues better. You can use `docker exec <command>` to view the logs of a specific component. For example:
  ```bash
  docker exec kind-control-plane journalctl -u kubelet
  ```

## Resources
- [kube-bench documentation](https://github.com/aquasecurity/kube-bench/blob/main/docs/running.md)
- [kube-bench repository](https://github.com/aquasecurity/kube-bench)
- [kube-bench job configuration](https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-master.yaml)
- [kind configuration reference](https://kind.sigs.k8s.io/docs/user/configuration/)
- [kind repository](https://github.com/kubernetes-sigs/kind)
- [kubectl documentation](https://kubernetes.io/docs/reference/kubectl/overview/)