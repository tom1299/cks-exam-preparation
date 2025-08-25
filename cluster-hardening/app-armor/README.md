## Protocol
```bash
root@jeeatwork:~# aa-status 
apparmor module is loaded.
121 profiles are loaded.
26 profiles are in enforce mode.
   /usr/bin/man
   /usr/lib/snapd/snap-confine
   /usr/lib/snapd/snap-confine//mount-namespace-capture-helper
   cri-containerd.apparmor.d
   k8s-deny-write

root@jeeatwork:~# kubectl exec -ti restricted-pod -c no-write-file -- sh
/ # touch test.txt
touch: test.txt: Permission denied
/ # exit
command terminated with exit code 1
root@jeeatwork:~# kubectl exec -ti restricted-pod -c unrestricted -- sh
/ # touch test.txt
/ # cat test.txt 
/ # exit

root@jeeatwork:~# crictl ps
CONTAINER           IMAGE               CREATED             STATE               NAME                        ATTEMPT             POD ID              POD                                       NAMESPACE
c67015e754232       8c811b4aec35f       3 minutes ago       Running             unrestricted                0                   e0da7c7e71a43       restricted-pod                            default
76382690b6486       8c811b4aec35f       3 minutes ago       Running             no-write-file               0                   e0da7c7e71a43       restricted-pod                            default

root@jeeatwork:~# crictl exec -ti c67015e754232 sh
/ # touch test.txt
/ # exit
root@jeeatwork:~# crictl exec -ti 76382690b6486 sh
/ # touch test.txt
touch: test.txt: Permission denied
```
Violations were not being logged because the profile did not contain the audit keyword. After adding it, violations are logged in the audit log and syslog as well as dmesg.
```bash
root@jeeatwork:/var/log# grep DENIED /var/log/syslog
2025-08-24T06:20:43.875252+00:00 jeeatwork kernel: audit: type=1400 audit(1756016443.873:241): apparmor="DENIED" operation="mknod" class="file" profile="k8s-deny-write" name="/test" pid=16334 comm="touch" requested_mask="c" denied_mask="c" fsuid=0 ouid=0
```
## Notes
Use `apparmor_parser -R <path-to-profile>` to remove the profile.
Process with the profile enforced can be seen like this:
```bash
root@jeeatwork:/var/log# aa-status | grep -i k8s
   k8s-deny-write
   /usr/bin/sleep (18346) k8s-deny-write
```
or
```bash
root@jeeatwork:/var/log# kubectl exec -ti restricted-pod -c no-write-file -- sh
/ # cat /proc/1/attr/current
k8s-deny-write (enforce)
```
Removing the profile and receating the pod will result in an error:
```
Events:
  Type     Reason     Age               From               Message
  ----     ------     ----              ----               -------
  Normal   Scheduled  56s               default-scheduler  Successfully assigned default/restricted-pod to jeeatwork
  Normal   Pulled     55s               kubelet            Container image "busybox:1.28" already present on machine
  Normal   Created    55s               kubelet            Created container: unrestricted
  Normal   Started    55s               kubelet            Started container unrestricted
  Normal   Pulled     5s (x7 over 55s)  kubelet            Container image "busybox:1.28" already present on machine
  Warning  Failed     5s (x7 over 55s)  kubelet            Error: failed to get container spec opts: failed to generate apparmor spec opts: apparmor profile not found k8s-deny-write
```
Run bash with the profile applied:
```bash
sudo aa-exec -p k8s-network-restricted -- /bin/bash
```

## Problems
* Deny network does not work. Look at problem: https://github.com/moby/moby/issues/44984
* AppArmor network mediation must be enabled in the kernel.

## TODO
Do all the examples here: https://kubernetes.io/docs/tutorials/security/apparmor/

