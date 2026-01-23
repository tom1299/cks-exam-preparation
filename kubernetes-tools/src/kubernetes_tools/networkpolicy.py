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


def _peers_match(peer1: client.V1NetworkPolicyPeer, peer2: client.V1NetworkPolicyPeer) -> bool:
    """
    Check if two V1NetworkPolicyPeer objects match.

    Args:
        peer1: First NetworkPolicyPeer to compare
        peer2: Second NetworkPolicyPeer to compare

    Returns:
        True if the peers match, False otherwise
    """
    # Compare pod selector
    pod_selector_match = True
    if peer1.pod_selector or peer2.pod_selector:
        # Both must have pod_selector or both must not have it
        if bool(peer1.pod_selector) != bool(peer2.pod_selector):
            pod_selector_match = False
        elif peer1.pod_selector and peer2.pod_selector:
            # Compare match_labels
            labels1 = peer1.pod_selector.match_labels or {}
            labels2 = peer2.pod_selector.match_labels or {}
            pod_selector_match = labels1 == labels2

    # Compare namespace selector
    namespace_selector_match = True
    if peer1.namespace_selector or peer2.namespace_selector:
        # Both must have namespace_selector or both must not have it
        if bool(peer1.namespace_selector) != bool(peer2.namespace_selector):
            namespace_selector_match = False
        elif peer1.namespace_selector and peer2.namespace_selector:
            # Compare match_labels
            labels1 = peer1.namespace_selector.match_labels or {}
            labels2 = peer2.namespace_selector.match_labels or {}
            namespace_selector_match = labels1 == labels2

    # Compare IP block
    ip_block_match = True
    if peer1.ip_block or peer2.ip_block:
        # Both must have ip_block or both must not have it
        if bool(peer1.ip_block) != bool(peer2.ip_block):
            ip_block_match = False
        elif peer1.ip_block and peer2.ip_block:
            # Compare CIDR and except
            cidr_match = peer1.ip_block.cidr == peer2.ip_block.cidr
            except1 = set(peer1.ip_block._except or [])
            except2 = set(peer2.ip_block._except or [])
            except_match = except1 == except2
            ip_block_match = cidr_match and except_match

    return pod_selector_match and namespace_selector_match and ip_block_match


def associate_ingress_egress_rules(
    ingress_rules: List[IngressRules],
    egress_rules: List[EgressRules]
) -> tuple[List[IngressRules], List[EgressRules]]:
    """
    Associate matching IngressRules and EgressRules based on their NetworkPolicyPeer objects.

    This function finds matching peers between ingress and egress rules and creates bidirectional
    associations between them.

    Args:
        ingress_rules: List of IngressRules objects
        egress_rules: List of EgressRules objects

    Returns:
        A tuple of (ingress_rules, egress_rules) with populated matching_egress_rules and
        matching_ingress_rules fields

    Example:
        from kubernetes_tools.pods import get_pod

        pod = get_pod(name="backend", namespace="backend")
        if pod:
            ingress = get_network_policy_rules(pod, port=8080, rule_type="ingress")
            egress = get_network_policy_rules(pod, port=8080, rule_type="egress")

            ingress, egress = associate_ingress_egress_rules(ingress, egress)

            for ing_rule in ingress:
                print(f"Ingress rule has {len(ing_rule.matching_egress_rules)} matching egress rules")
    """
    # TODO: Refacto this to avoid nested loops / make the function more readable
    # Iterate over IngressRules objects
    for ingress_rule in ingress_rules:
        # Iterate over the ingress_rules property (list of V1NetworkPolicyPeer)
        for ingress_peer in ingress_rule.ingress_rules:
            # Find matching EgressRule
            for egress_rule in egress_rules:
                # Check if any peer in egress_rules matches the ingress peer
                for egress_peer in egress_rule.egress_rules:
                    if _peers_match(ingress_peer, egress_peer):
                        # TODO: Based on pydantic behavior, duplicates should not happen, but may be better to compare
                        # based on network policy name and pod name instead of object reference

                        # Add the EgressRule to matching_egress_rules if not already present
                        if egress_rule not in ingress_rule.matching_egress_rules:
                            ingress_rule.matching_egress_rules.append(egress_rule)

                        # Add the IngressRule to matching_ingress_rules if not already present
                        if ingress_rule not in egress_rule.matching_ingress_rules:
                            egress_rule.matching_ingress_rules.append(ingress_rule)

                        # Break after finding a match to avoid duplicates
                        break

    return ingress_rules, egress_rules


def find_egress_with_matching_ingress(
    egress_rules: List[EgressRules],
    port: int,
    protocol: str = "TCP" # TODO: Consider using Enum for protocol
) -> List[EgressRules]:
    """
    Find EgressRules that have matching IngressRules for a given port and protocol.

    This function filters egress rules to find those that have associated ingress rules
    matching the specified port and protocol.

    Args:
        egress_rules: List of EgressRules objects to search through
        port: The port number to match
        protocol: The protocol to match (default: "TCP"). Common values: "TCP", "UDP"

    Returns:
        List of EgressRules that have at least one matching IngressRule with the specified
        port and protocol
    """
    protocol = protocol.upper()
    result = []

    for egress_rule in egress_rules:
        # Check if this egress rule has any matching ingress rules
        for ingress_rule in egress_rule.matching_ingress_rules:
            # Check if the ingress rule matches the port and protocol
            if ingress_rule.port == port and ingress_rule.protocol == protocol:
                result.append(egress_rule)
                break  # No need to check other ingress rules for this egress rule

    return result


