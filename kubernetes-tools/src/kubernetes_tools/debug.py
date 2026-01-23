import time
from typing import Tuple, List
from kubernetes import client

def run_debug_command(
    namespace: str,
    pod_name: str,
    command: List[str],
    image: str = "busybox",
    max_wait: int = 60
) -> Tuple[str, bool]:
    """
    Run a debug command in an ephemeral container attached to a pod.

    This function replicates the behavior of:
    kubectl debug -n <namespace> pod/<pod_name> --image=<image> -c <generated_name> --attach -- <command>

    Args:
        namespace: The Kubernetes namespace where the pod is located
        pod_name: The name of the pod to debug
        command: The command to run in the debug container (as a list of strings)
        image: The container image to use for debugging (default: busybox)
        max_wait: How long to wait for debugging (default: 60)

    Returns:
        A tuple of (output: str, success: bool) where:
        - output: The combined stdout/stderr from the command
        - success: True if the command executed successfully (exit code 0), False otherwise

    Example:
        output, success = run_debug_command(
            namespace="backend",
            pod_name="backend",
            command=["nc", "-vz", "mysql.db", "3306"]
        )
    """
    v1 = client.CoreV1Api()

    debug_container_name = f"debug-{int(time.time())}"

    pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)

    # Create ephemeral container spec
    ephemeral_container = client.V1EphemeralContainer(
        name=debug_container_name,
        image=image,
        command=command,
        stdin=True,
        tty=False,
        target_container_name=None,
    )

    if pod.spec.ephemeral_containers is None:
        pod.spec.ephemeral_containers = []

    pod.spec.ephemeral_containers.append(ephemeral_container)

    v1.patch_namespaced_pod_ephemeralcontainers(
        name=pod_name,
        namespace=namespace,
        body=pod,
    )

    # Wait for the ephemeral container to complete (running or terminated)
    wait_interval = 0.2
    elapsed = 0
    container_status = None

    while elapsed < max_wait:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)

        # Check if ephemeral container exists in status and wait for it to terminate
        if pod.status.ephemeral_container_statuses:
            for status in pod.status.ephemeral_container_statuses:
                if status.name == debug_container_name:
                    container_status = status
                    if status.state.terminated:
                        break

        if container_status and container_status.state.terminated:
            break

        time.sleep(wait_interval)
        elapsed += wait_interval

    if not container_status or not container_status.state.terminated:
        raise Exception(f"Timeout waiting for ephemeral container {debug_container_name} to complete")

    logs = v1.read_namespaced_pod_log(
        name=pod_name,
        namespace=namespace,
        container=debug_container_name,
    )

    exit_code = container_status.state.terminated.exit_code

    return logs, exit_code == 0
