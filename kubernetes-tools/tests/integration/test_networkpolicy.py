from kubernetes_tools import networkpolicy
from kubernetes_tools import pods, debug

from tests.test_utils import create_nwp, apply_nwp, delete_nwp


class TestNetworkPolicy:

    # TODO: Decompose this tests: Refactor code into smaller helper functions
    def test_matching_network_policy(self):
        backend = pods.get_pod(name="backend", namespace="test-app")

        matching_policies = networkpolicy.get_network_policies_matching_pod(backend)
        assert len(matching_policies) == 2  # deny-all and allow dns

        mysql = pods.get_pod(name="mysql", namespace="test-app")

        matching_policies = networkpolicy.get_network_policies_matching_pod(mysql)
        assert len(matching_policies) == 2  # deny-all and allow dns

        mysql_pod_ip = pods.get_pod_ips(mysql)[0]
        netcat_command = ["nc", "-vz", "-w", "10", mysql_pod_ip, "3306"]

        nc_output, connected = debug.run_debug_command(
            namespace="test-app",
            pod_name="backend",
            command=netcat_command,
            image="nicolaka/netshoot",
            max_wait=30
        )

        assert "timed out" in nc_output
        assert connected is False

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

            assert len(matching_policies) == 3  # deny-all, allow dns, allow backend to mysql

            ingress_nwp = apply_nwp(ingress_nwp)

            assert networkpolicy.contains_ingress_rule(ingress_nwp, port=3306, peer_selector={"app": "backend"}, protocol="TCP") is True
            assert networkpolicy.contains_egress_rule(egress_nwp, port=3306, selector={"app": "mysql"}, protocol="TCP") is True

            nc_output, connected = debug.run_debug_command(
                namespace="test-app",
                pod_name="backend",
                command=netcat_command,
                image="nicolaka/netshoot",
                max_wait=30
            )

            assert "succeeded" in nc_output
            assert connected is True
        finally:
            # TODO: Use fixtures for cleanup instead of try/finally
            delete_nwp(egress_nwp.metadata.name, egress_nwp.metadata.namespace)
            delete_nwp(ingress_nwp.metadata.name, ingress_nwp.metadata.namespace)


