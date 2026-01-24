from kubernetes import client, config
from typing import Optional

from kubernetes.client import V1ContainerPort
from pydantic import BaseModel, ConfigDict

class ExposedContainerPort(BaseModel):
    """
    TODO: Refactor to use other types than the kubernetes client models.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    container_name: str
    port: V1ContainerPort

def get_pod(
    name: str,
    namespace: str = "default"
) -> Optional[client.V1Pod]:
    """
    Get a pod by name from a specific namespace.

    Args:
        name: The name of the pod to retrieve
        namespace: The Kubernetes namespace where the pod is located (default: "default")

    Returns:
        A V1Pod object if found, None if the pod doesn't exist

    Example:
        pod = get_pod(name="backend", namespace="backend")
        if pod:
            print(f"Found pod: {pod.metadata.name}")
        else:
            print("Pod not found")
    """
    try:
        config.load_kube_config()
    except config.ConfigException:
        config.load_incluster_config()

    v1 = client.CoreV1Api()

    try:
        pod = v1.read_namespaced_pod(name=name, namespace=namespace)
        return pod
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return None
        raise


def find_exposed_port(
    pod: client.V1Pod,
    port: int,
    # TODO: Consider using Enum for protocol
    protocol: str = "TCP"
) -> Optional[ExposedContainerPort]:
    """
    Check if any container in a Pod exposes a specific port with the given protocol.

    Args:
        pod: The Kubernetes Pod object (V1Pod) to examine
        port: The port number to search for
        protocol: The protocol to match (default: "TCP"). Common values: "TCP", "UDP", "SCTP"

    Returns:
        An ExposedContainerPort object containing the container name and port details if found,
        None if no container exposes the specified port with the given protocol

    Example:
        pod = get_pod(name="backend", namespace="backend")
        if pod:
            exposed = find_exposed_port(pod, port=3306, protocol="TCP")
            if exposed:
                print(f"Container '{exposed.container_name}' exposes port {exposed.port.container_port}")
            else:
                print("Port not exposed")
    """
    protocol = protocol.upper()

    # Check all containers in the pod
    for container in pod.spec.containers:
        if not container.ports:
            continue

        # Check each port in the container
        for container_port in container.ports:
            # Match port number and protocol
            if container_port.container_port == port:
                # Default protocol is TCP if not specified
                port_protocol = (container_port.protocol or "TCP").upper()
                if port_protocol == protocol:
                    return ExposedContainerPort(
                        container_name=container.name,
                        port=container_port
                    )

    return None

def get_pod_ips(pod: client.V1Pod) -> list[str]:
    """
    Get all IP addresses assigned to a pod.

    Args:
        pod: The Kubernetes Pod object (V1Pod)

    Returns:
        A list of IP addresses (as strings) assigned to the pod

    Example:
        pod = get_pod(name="backend", namespace="backend")
        if pod:
            ips = get_pod_ips(pod)
            print(f"Pod IPs: {ips}")
    """
    ips = []

    # Primary Pod IP
    if pod.status.pod_ip:
        ips.append(pod.status.pod_ip)

    # Additional Pod IPs (for dual-stack or multiple IPs)
    if pod.status.pod_i_ps:
        for pod_ip in pod.status.pod_i_ps:
            if pod_ip.ip not in ips:
                ips.append(pod_ip.ip)

    return ips

