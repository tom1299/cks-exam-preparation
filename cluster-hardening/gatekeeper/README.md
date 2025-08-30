# Gatekeeper
* Use some of the examples from the library [website](https://open-policy-agent.github.io/gatekeeper-library/website/)

## Issues
* After the application of the image registry restriction policies, the following error appeared in the status of the k8s registry constraint:
    ```
    $ kubectl get k8sallowedrepos.constraints.gatekeeper.sh 
    NAME          ENFORCEMENT-ACTION   TOTAL-VIOLATIONS
    repo-is-gcr   deny                 13
    ~/git/github/cks-exam-preparation/cluster-hardening/gatekeeper$ kubectl get k8sallowedrepos.constraints.gatekeeper.sh -oyaml
    apiVersion: v1
    items:
    - apiVersion: constraints.gatekeeper.sh/v1beta1
    kind: K8sAllowedRepos
    metadata:
        annotations:
        kubectl.kubernetes.io/last-applied-configuration: |
            {"apiVersion":"constraints.gatekeeper.sh/v1beta1","kind":"K8sAllowedRepos","metadata":{"annotations":{},"name":"repo-is-gcr"},"spec":{"match":{"kinds":[{"apiGroups":[""],"kinds":["Pod"]}]},"parameters":{"repos":["gcr.io/"]}}}
        creationTimestamp: "2025-08-30T05:05:07Z"
        generation: 1
        name: repo-is-gcr
        resourceVersion: "1171"
        uid: b4852510-be3a-4960-a04c-74cd5af2e18e
    spec:
        enforcementAction: deny
        match:
        kinds:
        - apiGroups:
            - ""
            kinds:
            - Pod
        parameters:
        repos:
        - gcr.io/
    status:
        auditTimestamp: "2025-08-30T05:06:49Z"
        byPod:
        - constraintUID: b4852510-be3a-4960-a04c-74cd5af2e18e
        enforced: true
        enforcementPointsStatus:
        - enforcementPoint: vap.k8s.io
            message: K8sNativeValidation engine is missing
            observedGeneration: 1
            state: error
        id: gatekeeper-audit-7c596b77cd-8m7l9
        observedGeneration: 1
        operations:
        - audit
        - generate
        - mutation-status
        - status
    ```
    Examine what the error means. Does not seem to have an impact on the gatekeeper though.