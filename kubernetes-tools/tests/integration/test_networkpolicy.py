from kubernetes_tools import networkpolicy
from kubernetes_tools import pods

from tests.test_utils import create_nwp, apply_nwp, delete_nwp


class TestNetworkPolicy:

    def test_matching_network_policy(self):
        backend = pods.get_pod(name="backend", namespace="test-app")

        matching_policies = networkpolicy.get_network_policies_matching_pod(backend)

        assert len(matching_policies) == 0

        egress_nwp = create_nwp(
            pod_match_labels={"app": "backend"},
            peer_match_labels={"app": "mysql"},
            namespace="test-app",
            name="allow-backend-to-mysql-egress",
            port=3306,
            ingress=False
        )

        ingress_nwp = create_nwp(
            pod_match_labels={"app": "mysql"},
            peer_match_labels={"app": "backend"},
            namespace="test-app",
            name="allow-mysql-from-backend-ingress",
            port=3306,
            ingress=True
        )

        try:
            egress_nwp = apply_nwp(egress_nwp)
            matching_policies = networkpolicy.get_network_policies_matching_pod(backend)

            assert len(matching_policies) == 1

            ingress_nwp = apply_nwp(ingress_nwp)

            assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, selector={"app": "backend"}, protocol="TCP") is True
        finally:
            delete_nwp(egress_nwp.metadata.name, egress_nwp.metadata.namespace)
            delete_nwp(ingress_nwp.metadata.name, ingress_nwp.metadata.namespace)


