import pytest
from kubernetes_tools.pods import get_pod
from kubernetes_tools.networkpolicy import get_network_policy_rules, associate_ingress_egress_rules, find_egress_with_matching_ingress

class TestNetworkPolicy:

    @pytest.mark.xfail(reason="Test is under development")
    def test_connectivity_test(self):
        backend_pod = get_pod(name="backend", namespace="backend")
        mysql_pod = get_pod(name="mysql", namespace="backend")

        egress = get_network_policy_rules(backend_pod, port=3306, rule_type="egress")
        ingress = get_network_policy_rules(mysql_pod, port=3306, rule_type="ingress")

        # TODO: This is strictly speaking not necessary.
        ingress, egress = associate_ingress_egress_rules(ingress, egress)

        # Find egress rules that have matching ingress for port 3306
        matching = find_egress_with_matching_ingress(egress, port=3306, protocol="TCP")
        for egress_rule in matching:
            print(f"Egress rule from {egress_rule.network_policy_name} has {len(egress_rule.matching_ingress_rules)} matching ingress rules")
