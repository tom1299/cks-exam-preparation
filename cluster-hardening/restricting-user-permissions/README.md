## Restricting User Permissions
* Users can be assigned to groups when using certificates by adding the `-subj "/CN=username/O=mygroup"` option to the `openssl req` command.
* Groups can be specified in role bindings:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-reader
subjects:
- kind: Group
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```