from __future__ import annotations

from typing import List, Union, Literal

from kubernetes import client, config

from pydantic import BaseModel, ConfigDict


class IngressRules(BaseModel):
    # TODO: Refactor to use other types than the kubernetes client models.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    network_policy_name: str
    pod_name: str
    ingress_rules: List[client.V1NetworkPolicyPeer]
    port: int
    protocol: str
    matching_egress_rules: List[EgressRules]

class EgressRules(BaseModel):
    # TODO: Refactor to use other types than the kubernetes client models.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    network_policy_name: str
    pod_name: str
    egress_rules: List[client.V1NetworkPolicyPeer]
    port: int
    protocol: str
    matching_ingress_rules: List[IngressRules]

def get_network_policies_matching_pod(
    pod: client.V1Pod
) -> List[client.V1NetworkPolicy]:
    """
    Get the names of all NetworkPolicies whose selector matches the given pod.

    Args:
        pod: Kubernetes Pod object (V1Pod)

    Returns:
        List of NetworkPolicy names that select this pod
    """
    try:
        config.load_kube_config()
    except config.ConfigException:
        config.load_incluster_config()

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


def get_network_policy_rules(
    pod: client.V1Pod,
    port: int,
    protocol: str = "TCP",
    rule_type: Literal["ingress", "egress"] = "ingress"
) -> List[Union[IngressRules, EgressRules]]:
    """
    Get ingress or egress rules for a pod matching a specific port and protocol.

    Args:
        pod: Kubernetes Pod object (V1Pod)
        port: The port number to match
        protocol: The protocol to match (default: "TCP"). Common values: "TCP", "UDP", "SCTP"
        rule_type: Whether to retrieve "ingress" or "egress" rules (default: "ingress")

    Returns:
        List of IngressRules or EgressRules objects containing matching network policy rules

    Example:
        from kubernetes_tools.pods import get_pod

        pod = get_pod(name="backend", namespace="backend")
        if pod:
            ingress_rules = get_network_policy_rules(pod, port=8080, protocol="TCP", rule_type="ingress")
            for rule in ingress_rules:
                print(f"Network Policy: {rule.network_policy_name}")
                print(f"Matching rules: {len(rule.ingress_rules)}")
    """
    # Get all network policies matching the pod
    matching_policies = get_network_policies_matching_pod(pod)

    protocol = protocol.upper()
    pod_name = pod.metadata.name

    results: List[Union[IngressRules, EgressRules]] = []

    for network_policy in matching_policies:
        policy_name = network_policy.metadata.name

        # TODO: Find out how to avoid duplicate code here
        if rule_type == "ingress":
            # Process ingress rules
            matching_peers = []

            if network_policy.spec.ingress:
                for ingress_rule in network_policy.spec.ingress:
                    # Check if the rule has ports defined
                    if ingress_rule.ports:
                        for policy_port in ingress_rule.ports:
                            # Match port and protocol
                            port_matches = policy_port.port == port
                            protocol_matches = (policy_port.protocol or "TCP").upper() == protocol

                            if port_matches and protocol_matches:
                                # Add all peers from this ingress rule
                                if ingress_rule._from:
                                    matching_peers.extend(ingress_rule._from)
                                break
                    else:
                        # If no ports are specified, the rule applies to all ports
                        if ingress_rule._from:
                            matching_peers.extend(ingress_rule._from)

            # Create IngressRules object
            ingress_rules_obj = IngressRules(
                network_policy_name=policy_name,
                pod_name=pod_name,
                ingress_rules=matching_peers,
                port=port,
                protocol=protocol,
                matching_egress_rules=[]  # To be populated by caller if needed
            )
            results.append(ingress_rules_obj)

        else:  # egress
            # Process egress rules
            matching_peers = []

            if network_policy.spec.egress:
                for egress_rule in network_policy.spec.egress:
                    # Check if the rule has ports defined
                    if egress_rule.ports:
                        for policy_port in egress_rule.ports:
                            # Match port and protocol
                            port_matches = policy_port.port == port
                            protocol_matches = (policy_port.protocol or "TCP").upper() == protocol

                            if port_matches and protocol_matches:
                                # Add all peers from this egress rule
                                if egress_rule.to:
                                    matching_peers.extend(egress_rule.to)
                                break
                    else:
                        # If no ports are specified, the rule applies to all ports
                        if egress_rule.to:
                            matching_peers.extend(egress_rule.to)

            # Create EgressRules object
            egress_rules_obj = EgressRules(
                network_policy_name=policy_name,
                pod_name=pod_name,
                egress_rules=matching_peers,
                port=port,
                protocol=protocol,
                matching_ingress_rules=[]  # To be populated by caller if needed
            )
            results.append(egress_rules_obj)

    return results


