from kubernetes import client
from kubernetes.client import V1NetworkPolicyIngressRule

from kubernetes_tools import networkpolicy, pods

# TODO: Test cases not really check something. Add test scenario with known policies.
class TestNetworkPolicy:

    def test_get_network_policies_matching_pod(self):
        """Test getting network policies that match a pod"""
        pod = pods.get_pod(
            name="backend",
            namespace="test-app"
        )

        assert pod is not None

        policies = networkpolicy.get_network_policies_matching_pod(pod)

        # Should return a list (may be empty if no policies exist)
        assert isinstance(policies, list)

    def test_contains_ingress_rule_match(self):

        ingress_nwp  = create_nwp(
            pod_match_labels={"app": "pod-b"},
            peer_match_labels={"app": "pod-a"},
            namespace="test-app",
            name="ingress-policy",
            port=3306,
            protocol="TCP",
            ingress=True
        )

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, selector={"app": "pod-a"}, protocol="TCP") is True

    def test_contains_ingress_rule_wrong_port(self):

        ingress_nwp  = create_nwp(
            pod_match_labels={"app": "pod-b"},
            peer_match_labels={"app": "pod-a"},
            namespace="test-app",
            name="ingress-policy",
            port=3306,
            protocol="TCP",
            ingress=True
        )

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3307, selector={"app": "pod-a"}, protocol="TCP") is False

    def test_contains_ingress_rule_wrong_selector(self):

        ingress_nwp  = create_nwp(
            pod_match_labels={"app": "pod-b"},
            peer_match_labels={"app": "pod-a"},
            namespace="test-app",
            name="ingress-policy",
            port=3306,
            protocol="TCP",
            ingress=True
        )

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, selector={"app": "xxx"}, protocol="TCP") is False

    def test_contains_ingress_rule_wrong_protocol(self):

        ingress_nwp  = create_nwp(
            pod_match_labels={"app": "pod-b"},
            peer_match_labels={"app": "pod-a"},
            namespace="test-app",
            name="ingress-policy",
            port=3306,
            protocol="TCP",
            ingress=True
        )

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, selector={"app": "pod-a"}, protocol="UDP") is False

    def test_contains_ingress_rule_no_port_in_nwp(self):

        ingress_nwp  = create_nwp(
            pod_match_labels={"app": "pod-b"},
            peer_match_labels={"app": "pod-a"},
            namespace="test-app",
            name="ingress-policy",
            port=3306,
            protocol="TCP",
            ingress=True
        )

        ingress_nwp.spec.ingress[0].ports = []

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3307, selector={"app": "pod-a"}, protocol="TCP") is True

    def test_contains_ingress_rule_match_multiple_peer_labels(self):

        ingress_nwp  = create_nwp(
            pod_match_labels={"app": "pod-b"},
            peer_match_labels={"app": "pod-a", "tier": "frontend"},
            namespace="test-app",
            name="ingress-policy",
            port=3306,
            protocol="TCP",
            ingress=True
        )

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, selector={"app": "pod-a", "tier": "frontend"}, protocol="TCP") is True

    def test_contains_ingress_rule_match_multiple_peer_labels_different_order(self):

        ingress_nwp  = create_nwp(
            pod_match_labels={"app": "pod-b"},
            peer_match_labels={"tier": "frontend", "app": "pod-a"},
            namespace="test-app",
            name="ingress-policy",
            port=3306,
            protocol="TCP",
            ingress=True
        )

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, selector={"app": "pod-a", "tier": "frontend"}, protocol="TCP") is True

    def test_contains_ingress_rule_match_multiple_peer_labels_not_matching(self):

        ingress_nwp  = create_nwp(
            pod_match_labels={"app": "pod-b"},
            peer_match_labels={"app": "pod-a", "tier": "frontend"},
            namespace="test-app",
            name="ingress-policy",
            port=3306,
            protocol="TCP",
            ingress=True
        )

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, selector={"app": "pod-a"}, protocol="TCP") is False

    def test_contains_ingress_rule_match_multiple_ports(self):

        ingress_nwp  = create_nwp(
            pod_match_labels={"app": "pod-b"},
            peer_match_labels={"app": "pod-a"},
            namespace="test-app",
            name="ingress-policy",
            port=3306,
            protocol="TCP",
            ingress=True
        )

        # Add another port to the ingress rule
        another_port = client.V1NetworkPolicyPort(
            protocol="TCP",
            port=8080
        )
        existing_port = ingress_nwp.spec.ingress[0].ports[0]
        ingress_nwp.spec.ingress[0].ports = [another_port, existing_port]

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, selector={"app": "pod-a"}, protocol="TCP") is True


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
