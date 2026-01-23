from kubernetes import client
from kubernetes.client import V1NetworkPolicyIngressRule

def create_nwp(pod_match_labels: dict, peer_match_labels: dict, namespace: str, name: str, port : int, protocol: str = "TCP", ingress: bool = True) -> client.V1NetworkPolicy:
    """Helper to create a network policy for testing"""
    policy_rule = create_nwp_policy_rule(ingress, peer_match_labels, port, protocol)

    nwp = client.V1NetworkPolicy(
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=namespace
        ),
        spec=client.V1NetworkPolicySpec(
            pod_selector=client.V1LabelSelector(
                match_labels=pod_match_labels
            ),
            policy_types=["Ingress"] if ingress else ["Egress"],
            ingress=[policy_rule] if ingress else None,
            egress=[policy_rule] if not ingress else None
        )
    )
    return nwp


def create_nwp_policy_rule(ingress: bool, peer_match_labels: dict, port: int, protocol: str) -> V1NetworkPolicyIngressRule:
    policy_peer = client.V1NetworkPolicyPeer(
        pod_selector=client.V1LabelSelector(
            match_labels=peer_match_labels
        )
    )

    policy_port = client.V1NetworkPolicyPort(
        protocol=protocol,
        port=port
    )

    if ingress:
        policy_rule = client.V1NetworkPolicyIngressRule(
            ports=[policy_port],
            _from=[policy_peer]
        )
    else:
        policy_rule = client.V1NetworkPolicyEgressRule(
            ports=[policy_port],
            to=[policy_peer]
        )
    return policy_rule

def apply_nwp(nwp: client.V1NetworkPolicy) -> client.V1NetworkPolicy:
    """Helper to apply a network policy for testing"""
    api_instance = client.NetworkingV1Api()
    return api_instance.create_namespaced_network_policy(
        namespace=nwp.metadata.namespace,
        body=nwp
    )

def delete_nwp(name: str, namespace: str):
    """Helper to delete a network policy for testing"""
    api_instance = client.NetworkingV1Api()
    api_instance.delete_namespaced_network_policy(
        name=name,
        namespace=namespace
    )
