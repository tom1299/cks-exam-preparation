# Fix kube-bench findings for the cluster kind

## Command line tools to use
Besides usual shell commands use the following commands:
- `kubectl`: to run commands against Kubernetes clusters
- `kind`: to manage clusters
- `docker`: to manage examine the running containers that make up the cluster and execute commands in them

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
- Only fix the issues of type `FAIL` one by one by adding the necessary configuration to the `kind-config.yaml` file
- After each fix, delete the cluster and recreate it using the command:
  ```bash
  kind delete cluster --name kind
  kind create cluster --name kind --config kind-config.yaml
  ```
  and verify that the issue is fixed by running kube-bench again
- Write the description of the issues that could not be solved into a text file named "kube-bench-findings.txt" in this directory with a short description why the issue could not be fixed.