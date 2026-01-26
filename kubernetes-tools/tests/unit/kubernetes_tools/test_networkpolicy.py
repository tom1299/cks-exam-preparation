from kubernetes import client
from tests.test_utils import create_nwp

from kubernetes_tools import networkpolicy, pods

# TODO: Refactor repetitive code into helper functions
class TestNetworkPolicy:

    def test_get_network_policies_matching_pod(self):
        """Test getting network policies that match a pod"""
        pod = pods.get_pod_by_name(
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

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, peer_selector={"app": "pod-a"}, protocol="TCP") is True

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

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3307, peer_selector={"app": "pod-a"}, protocol="TCP") is False

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

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, peer_selector={"app": "xxx"}, protocol="TCP") is False

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

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, peer_selector={"app": "pod-a"}, protocol="UDP") is False

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

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3307, peer_selector={"app": "pod-a"}, protocol="TCP") is True

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

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, peer_selector={"app": "pod-a", "tier": "frontend"}, protocol="TCP") is True

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

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, peer_selector={"app": "pod-a", "tier": "frontend"}, protocol="TCP") is True

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

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, peer_selector={"app": "pod-a"}, protocol="TCP") is False

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

        assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, peer_selector={"app": "pod-a"}, protocol="TCP") is True

    def test_contains_egress_rule_match(self):
        """Test that egress rule matches with correct port, selector, and protocol"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "pod-b"}, protocol="TCP") is True

    def test_contains_egress_rule_wrong_port(self):
        """Test that egress rule doesn't match with wrong port"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3307, selector={"app": "pod-b"}, protocol="TCP") is False

    def test_contains_egress_rule_wrong_selector(self):
        """Test that egress rule doesn't match with wrong selector"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "xxx"}, protocol="TCP") is False

    def test_contains_egress_rule_wrong_protocol(self):
        """Test that egress rule doesn't match with wrong protocol"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "pod-b"}, protocol="UDP") is False

    def test_contains_egress_rule_no_port_in_nwp(self):
        """Test that egress rule matches any port when no ports are specified"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        egress_nwp.spec.egress[0].ports = []

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3307, selector={"app": "pod-b"}, protocol="TCP") is True

    def test_contains_egress_rule_match_multiple_peer_labels(self):
        """Test that egress rule matches with multiple peer labels"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b", "tier": "database"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "pod-b", "tier": "database"}, protocol="TCP") is True

    def test_contains_egress_rule_match_multiple_peer_labels_different_order(self):
        """Test that egress rule matches with multiple peer labels in different order"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"tier": "database", "app": "pod-b"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "pod-b", "tier": "database"}, protocol="TCP") is True

    def test_contains_egress_rule_match_multiple_peer_labels_not_matching(self):
        """Test that egress rule doesn't match when peer labels don't match exactly"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b", "tier": "database"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "pod-b"}, protocol="TCP") is False

    def test_contains_egress_rule_match_multiple_ports(self):
        """Test that egress rule matches when one of multiple ports matches"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        # Add another port to the egress rule
        another_port = client.V1NetworkPolicyPort(
            protocol="TCP",
            port=8080
        )
        existing_port = egress_nwp.spec.egress[0].ports[0]
        egress_nwp.spec.egress[0].ports = [another_port, existing_port]

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "pod-b"}, protocol="TCP") is True

    def test_contains_egress_rule_no_egress_rules(self):
        """Test that function returns False when no egress rules exist"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        egress_nwp.spec.egress = []

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "pod-b"}, protocol="TCP") is False

    def test_contains_egress_rule_no_peers(self):
        """Test that function returns False when egress rule has no peers"""
        egress_nwp = create_nwp(
            pod_match_labels={"app": "pod-a"},
            peer_match_labels={"app": "pod-b"},
            namespace="test-app",
            name="egress-policy",
            port=3306,
            protocol="TCP",
            ingress=False
        )

        egress_nwp.spec.egress[0].to = []

        assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "pod-b"}, protocol="TCP") is False

