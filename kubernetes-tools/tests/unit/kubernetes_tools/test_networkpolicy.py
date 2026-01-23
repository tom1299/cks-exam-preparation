from kubernetes_tools import networkpolicy, pods

# TODO: Test cases not really check something. Add test scenario with known policies.
class TestNetworkPolicy:

    def test_get_network_policies_matching_pod(self):
        """Test getting network policies that match a pod"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        assert pod is not None

        policies = networkpolicy.get_network_policies_matching_pod(pod)

        # Should return a list (may be empty if no policies exist)
        assert isinstance(policies, list)

    def test_get_ingress_rules_for_pod(self):
        """Test getting ingress rules for a pod on a specific port"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        assert pod is not None

        ingress_rules = networkpolicy.get_network_policy_rules(
            pod=pod,
            port=8080,
            protocol="TCP",
            rule_type="ingress"
        )

        # Should return a list of IngressRules
        assert isinstance(ingress_rules, list)

        # If there are rules, verify structure
        for rule in ingress_rules:
            assert isinstance(rule, networkpolicy.IngressRules)
            assert rule.network_policy_name is not None
            assert rule.pod_name == "backend"
            assert rule.port == 8080
            assert rule.protocol == "TCP"
            assert isinstance(rule.ingress_rules, list)
            assert isinstance(rule.matching_egress_rules, list)

    def test_get_egress_rules_for_pod(self):
        """Test getting egress rules for a pod on a specific port"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        assert pod is not None

        egress_rules = networkpolicy.get_network_policy_rules(
            pod=pod,
            port=3306,
            protocol="TCP",
            rule_type="egress"
        )

        # Should return a list of EgressRules
        assert isinstance(egress_rules, list)

        # If there are rules, verify structure
        for rule in egress_rules:
            assert isinstance(rule, networkpolicy.EgressRules)
            assert rule.network_policy_name is not None
            assert rule.pod_name == "backend"
            assert rule.port == 3306
            assert rule.protocol == "TCP"
            assert isinstance(rule.egress_rules, list)
            assert isinstance(rule.matching_ingress_rules, list)

    def test_get_rules_with_udp_protocol(self):
        """Test getting rules with UDP protocol"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        assert pod is not None

        rules = networkpolicy.get_network_policy_rules(
            pod=pod,
            port=53,
            protocol="UDP",
            rule_type="egress"
        )

        # Should return a list
        assert isinstance(rules, list)

        # If there are rules, verify protocol is UDP
        for rule in rules:
            assert rule.protocol == "UDP"

    def test_get_rules_default_protocol(self):
        """Test that default protocol is TCP"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        assert pod is not None

        rules = networkpolicy.get_network_policy_rules(
            pod=pod,
            port=8080,
            rule_type="ingress"
        )

        # Should return a list
        assert isinstance(rules, list)

        # If there are rules, verify default protocol is TCP
        for rule in rules:
            assert rule.protocol == "TCP"
