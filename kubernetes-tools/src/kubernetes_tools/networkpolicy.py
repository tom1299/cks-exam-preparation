from __future__ import annotations

from typing import List

from kubernetes import client
from langchain.tools import tool


def get_network_policies_matching_pod(
    pod: client.V1Pod
) -> List[client.V1NetworkPolicy]:
    """
    Get the all NetworkPolicies whose selector matches the given pod.

    Args:
        pod: Kubernetes Pod object (V1Pod)

    Returns:
        List of NetworkPolicies
    """

    networking_v1 = client.NetworkingV1Api()

    # Get pod labels and namespace
    pod_labels = pod.metadata.labels or {}
    pod_namespace = pod.metadata.namespace

    # List all NetworkPolicies in the pod's namespace
    network_policies = networking_v1.list_namespaced_network_policy(
        namespace=pod_namespace
    )

    matching_policies = []

    for network_policy in network_policies.items:
        pod_selector = network_policy.spec.pod_selector

        # Empty selector (no match_labels) matches all pods
        if not pod_selector.match_labels:
            matching_policies.append(network_policy)
            continue

        # Check if all selector labels match the pod's labels
        if all(
            pod_labels.get(key) == value
            for key, value in pod_selector.match_labels.items()
        ):
            matching_policies.append(network_policy)

    return matching_policies


# Tool wrapper for LangChain agents
get_network_policies_matching_pod_tool = tool(parse_docstring=True)(get_network_policies_matching_pod)


# TODO: Examine whether is it possible to refactor a generic method for both ingress and egress rules functions.
def contains_ingress_rule(network_policy: client.V1NetworkPolicy, port: int, peer_selector: dict, protocol: str = "TCP") -> bool:
    """
    Check if a network policy contains an ingress rule matching the specified port, peer selector, and protocol.

    Args:
        network_policy: The V1NetworkPolicy to check
        port: The port number to match
        peer_selector: Pod selector labels to match (e.g., {"app": "pod-a"})
        protocol: The protocol to match (default: "TCP")

    Returns:
        True if the network policy contains a matching ingress rule, False otherwise
    """
    if not network_policy.spec.ingress:
        return False

    protocol = protocol.upper()

    # Iterate through all ingress rules
    for ingress_rule in network_policy.spec.ingress:

        if not ingress_rule._from:
            continue

        # Check if any peer matches the selector
        peer_matches = False
        for peer in ingress_rule._from:
            if peer.pod_selector and peer.pod_selector.match_labels:
                # Check if all selector labels match
                if peer.pod_selector.match_labels == peer_selector:
                    peer_matches = True
                    break

        if not peer_matches:
            continue

        # If ports are not specified, rule applies to all ports
        if not ingress_rule.ports:
            return True

        # Check if any port matches
        for policy_port in ingress_rule.ports:
            port_matches = policy_port.port == port
            protocol_matches = (policy_port.protocol or "TCP").upper() == protocol

            if port_matches and protocol_matches:
                return True

    return False


# Tool wrapper for LangChain agents
contains_ingress_rule_tool = tool(parse_docstring=True)(contains_ingress_rule)


def contains_egress_rule(network_policy: client.V1NetworkPolicy, port: int, selector: dict, protocol: str = "TCP") -> bool:
    """
    Check if a network policy contains an egress rule matching the specified port, selector, and protocol.

    Args:
        network_policy: The V1NetworkPolicy to check
        port: The port number to match
        selector: Pod selector labels to match (e.g., {"app": "pod-b"})
        protocol: The protocol to match (default: "TCP")

    Returns:
        True if the network policy contains a matching egress rule, False otherwise
    """
    if not network_policy.spec.egress:
        return False

    protocol = protocol.upper()

    # Iterate through all egress rules
    for egress_rule in network_policy.spec.egress:

        if not egress_rule.to:
            continue

        # Check if any peer matches the selector
        peer_matches = False
        for peer in egress_rule.to:
            if peer.pod_selector and peer.pod_selector.match_labels:
                # Check if all selector labels match
                if peer.pod_selector.match_labels == selector:
                    peer_matches = True
                    break

        if not peer_matches:
            continue

        # If ports are not specified, rule applies to all ports
        if not egress_rule.ports:
            return True

        # Check if any port matches
        for policy_port in egress_rule.ports:
            port_matches = policy_port.port == port
            protocol_matches = (policy_port.protocol or "TCP").upper() == protocol

            if port_matches and protocol_matches:
                return True

    return False


# Tool wrapper for LangChain agents
contains_egress_rule_tool = tool(parse_docstring=True)(contains_egress_rule)


