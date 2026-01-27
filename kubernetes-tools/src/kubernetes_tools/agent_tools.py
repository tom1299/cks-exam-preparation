"""
LLM-friendly tool wrappers for Kubernetes operations.

These tools accept only primitive types (strings, ints, etc.) that can be 
serialized to JSON Schema for LLM tool calling. They internally fetch and 
process Kubernetes objects.

TODO: AI generated wrapper code => Review and derive better return values
for example for the network policies which should not just return names
but should also return the full content of the policies or at least their rules.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from langchain_core.tools import tool
from kubernetes import client

from kubernetes_tools import pods, networkpolicy


class ExposedContainerPort(BaseModel):
    container_name: str
    port: dict

class PortConnectivityResult(BaseModel):
    output: str
    success: bool
    command: str

@tool(parse_docstring=True)
def get_pod_by_name(
    name: str,
    namespace: str = "default"
) -> Optional[dict]:
    """
    Get a pod by name from a specific namespace and return its client.V1Pod
    representation as a dict.

    Args:
        name: The name of the pod to retrieve
        namespace: The Kubernetes namespace where the pod is located (default: "default")

    Returns:
        client.V1Pod as a dict

    Example:
        pod_info = get_pod_by_name(name="backend", namespace="test-app")
        if pod_info:
            print(f"Pod image: {pod_info['spec']['containers'][0]['image']}")
    """
    pod = pods.get_pod_by_name(name=name, namespace=namespace)
    if pod:
        return pod.to_dict()
    return None

def get_pods_by_labels(
    labels: dict,
    namespace: str = "default"
) -> list[dict]:
    """
    Get pods by labels from a specific namespace.

    Args:
        labels: The labels of the pods to retrieve
        namespace: The Kubernetes namespace where the pods are located (default: "default")

    Returns:
        A list of dictionaries representing the pods matching the labels or an empty list if none found

    Example:
        pods = get_pods_by_labels_tool(labels={"app": "backend"}, namespace="default")
        for pod in pods:
            print(f"Found pod: {pod['metadata']['name']}")
    """

    pod_list = pods.get_pods_by_labels(labels, namespace)
    return [pod.to_dict() for pod in pod_list.items]


@tool(parse_docstring=True)
def get_pod_ip_addresses(
    pod_name: str,
    namespace: str = "default"
) -> Optional[List[str]]:
    """
    Get all IP addresses assigned to a pod.

    Args:
        pod_name: The name of the pod
        namespace: The Kubernetes namespace where the pod is located (default: "default")

    Returns:
        A list of IP addresses (as strings) assigned to the pod, None if pod not found

    Example:
        ips = get_pod_ip_addresses(pod_name="backend", namespace="test-app")
        if ips:
            print(f"Pod IPs: {ips}")
    """
    pod = pods.get_pod_by_name(name=pod_name, namespace=namespace)
    if pod is None:
        return None
    
    return pods.get_pod_ips(pod)


@tool(parse_docstring=True)
def check_pod_exposes_port(
    pod_name: str,
    namespace: str,
    port: int,
    protocol: str = "TCP"
) -> Optional[ExposedContainerPort]:
    """
    Check if a pod exposes a specific port with the given protocol.

    Args:
        pod_name: The name of the pod to check
        namespace: The Kubernetes namespace where the pod is located
        port: The port number to search for
        protocol: The protocol to match (default: "TCP"). Common values: "TCP", "UDP"

    Returns:
        An object of type ExposedContainerPort containing the container name and port details if found,
        otherwise returns None

    Example:
        exposed_port = check_pod_exposes_port(
            pod_name="backend",
            namespace="test-app",
            port=3306,
            protocol="TCP"
        )
        if exposed_port:
            print(f"Container '{exposed_port['container_name']}' exposes port {exposed_port['port']}")
    """
    pod = pods.get_pod_by_name(name=pod_name, namespace=namespace)
    if pod is None:
        return None
    
    exposed = pods.find_exposed_port(pod, port=port, protocol=protocol)
    
    if exposed:
        return ExposedContainerPort(
            container_name=exposed.container_name,
            port=exposed.port.to_dict()
        )
    return None


@tool(parse_docstring=True)
def get_network_policies_for_pod(
    pod_name: str,
    namespace: str
) -> List[dict]:
    """
    Get all NetworkPolicies whose selector matches the given pod.

    Args:
        pod_name: The name of the pod
        namespace: The Kubernetes namespace where the pod is located

    Returns:
        List of NetworkPolicies as a dict that match the pod

    Example:
        policies = get_network_policies_for_pod(pod_name="backend", namespace="test-app")
        for policy in policies:
            print(f"Matching policy name: {policy['metadata']['name']}")
    """
    pod = pods.get_pod_by_name(name=pod_name, namespace=namespace)
    if pod is None:
        return []
    
    policies = networkpolicy.get_network_policies_matching_pod(pod)
    return [policy.to_dict()for policy in policies]


@tool(parse_docstring=True)
def check_network_policy_allows_ingress(
    policy_name: str,
    namespace: str,
    port: int,
    peer_selector: Dict[str, str],
    protocol: str = "TCP"
) -> bool:
    """
    Check if a network policy contains an ingress rule matching the specified criteria.

    Args:
        policy_name: The name of the NetworkPolicy to check
        namespace: The namespace where the NetworkPolicy is located
        port: The port number to match
        peer_selector: Pod selector labels to match (e.g., {"app": "backend"})
        protocol: The protocol to match (default: "TCP")

    Returns:
        True if the network policy contains a matching ingress rule, False otherwise

    Example:
        allowed = check_network_policy_allows_ingress(
            policy_name="allow-mysql-from-backend-ingress",
            namespace="test-app",
            port=3306,
            peer_selector={"app": "backend"}
        )
    """
    networking_v1 = client.NetworkingV1Api()
    
    try:
        network_policy = networking_v1.read_namespaced_network_policy(
            name=policy_name,
            namespace=namespace
        )
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return False
        raise
    
    return networkpolicy.contains_ingress_rule(
        network_policy=network_policy,
        port=port,
        peer_selector=peer_selector,
        protocol=protocol
    )


@tool(parse_docstring=True)
def check_network_policy_allows_egress(
    policy_name: str,
    namespace: str,
    port: int,
    selector: Dict[str, str],
    protocol: str = "TCP"
) -> bool:
    """
    Check if a network policy contains an egress rule matching the specified criteria.

    Args:
        policy_name: The name of the NetworkPolicy to check
        namespace: The namespace where the NetworkPolicy is located
        port: The port number to match
        selector: Pod selector labels to match (e.g., {"app": "mysql"})
        protocol: The protocol to match (default: "TCP")

    Returns:
        True if the network policy contains a matching egress rule, False otherwise

    Example:
        allowed = check_network_policy_allows_egress(
            policy_name="allow-backend-to-mysql-egress",
            namespace="test-app",
            port=3306,
            selector={"app": "mysql"}
        )
    """
    networking_v1 = client.NetworkingV1Api()
    
    try:
        network_policy = networking_v1.read_namespaced_network_policy(
            name=policy_name,
            namespace=namespace
        )
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return False
        raise
    
    return networkpolicy.contains_egress_rule(
        network_policy=network_policy,
        port=port,
        selector=selector,
        protocol=protocol
    )


@tool(parse_docstring=True)
def test_pod_connectivity(
    source_pod_name: str,
    namespace: str,
    target_ip: str,
    target_port: int,
    protocol: str = "TCP",
    timeout: int = 5,
    image: str = "nicolaka/netshoot"
) -> PortConnectivityResult:
    """
    Test connectivity from a source pod to a target IP and port using netcat in an ephemeral container.

    Args:
        source_pod_name: The name of the pod to run the test from
        namespace: The Kubernetes namespace where the pod is located
        target_ip: The IP address to connect to
        target_port: The port number to connect to
        protocol: The protocol to use (default: "TCP")
        timeout: Connection timeout in seconds (default: 5)
        image: The container image to use for debugging (default: "nicolaka/netshoot")

    Returns:
        An object of type PortConnectivityResult containing the output, success status, and command used

    Example:
        result = test_pod_connectivity(
            source_pod_name="backend",
            namespace="test-app",
            target_ip="10.96.1.156",
            target_port=3306
        )
        print(f"Success: {result['success']}, Output: {result['output']}")
    """
    from kubernetes_tools.debug import create_netcat_command_fot_connectivity_test, run_debug_command
    
    # Create the netcat command
    command = create_netcat_command_fot_connectivity_test(
        target_ip=target_ip,
        target_port=target_port,
        protocol=protocol,
        timeout=timeout
    )
    
    # Run the debug command
    output, success = run_debug_command(
        namespace=namespace,
        pod_name=source_pod_name,
        command=command,
        image=image,
        max_wait=timeout + 30  # Give extra time for container to start
    )
    
    return PortConnectivityResult(
        output=output,
        success=success,
        command=" ".join(command)
    )
