#!/bin/bash

# strace should be generated like this:
# strace --summary-only -f --trace=all --summary-columns=name --summary-sort-by=name --output=syscalls.log <command>

STRACE_OUTPUT_FILE="${1:-syscalls.log}"
POLICY_OUTPUT_FILE="${2:-seccomp-policy.json}"

# Extract syscalls: remove first 2 and^ last 2 lines, format as JSON array
SYSCALL_LINES=$(cat "$STRACE_OUTPUT_FILE" | tail -n +3 | head -n -2)

for line in $SYSCALL_LINES; do
    SYSCALLS+=$(echo "\"$line\",")
done

# Remove trailing comma
SYSCALLS=${SYSCALLS%,}

# Generate seccomp policy
cat > "$POLICY_OUTPUT_FILE" << EOF
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
    "syscalls": [{
        "names": [$SYSCALLS],
        "action": "SCMP_ACT_ALLOW",
        "args": []
    }]
}
EOF
