# Seccomp container hardening

## generate seccomp profile
* Create a trace file for all the system calls a process makes. For example for sleep:  
    `strace --summary-only -f --trace=all --summary-columns=name --summary-sort-by=name --output=syscalls.log sleep 1s`
* Call the script `generate-seecomp-profile.sh`. For example:  
    `./genearte-seccomp-profile.sh syscall.log sleep`
* The generated seccomp profile will be output into the file `sleep-seccomp-profile.json`

## TODO
* Generate the profile for the sleep command
* Assign the profile to a container in a Pod
* If it works remove one of the syscalls. The Pod should not start
* Try to find an easy way to find out which system call was violated