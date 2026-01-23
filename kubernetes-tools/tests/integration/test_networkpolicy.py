from kubernetes import client
from kubernetes.client import ApiException, V1NetworkPolicy, NetworkingV1Api

from kubernetes_tools.pods import get_pod
from kubernetes_tools.networkpolicy import get_network_policy_rules, associate_ingress_egress_rules, find_egress_with_matching_ingress


def create_network_policy(namespace: str, network_policy: V1NetworkPolicy, networking_v1: NetworkingV1Api):
    try:
        networking_v1.read_namespaced_network_policy(name="deny-all", namespace=namespace)
        delete_network_policy(namespace, network_policy.metadata.name, networking_v1)
    except ApiException as e:
        if e.status != 404:
            raise

    return networking_v1.create_namespaced_network_policy(
        namespace=namespace,
        body=network_policy
    )

def delete_network_policy(namespace: str, name: str, networking_v1: NetworkingV1Api):
    try:
        networking_v1.delete_namespaced_network_policy(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions()
        )
    except ApiException as e:
        if e.status != 404:
            raise

class TestNetworkPolicy:

    def test_connectivity_test(self):
        backend_pod = get_pod(name="backend", namespace="test-app")
        mysql_pod = get_pod(name="mysql", namespace="test-app")

        egress = get_network_policy_rules(backend_pod, port=3306, rule_type="egress")
        ingress = get_network_policy_rules(mysql_pod, port=3306, rule_type="ingress")

        # TODO: This is strictly speaking not necessary.
        ingress, egress = associate_ingress_egress_rules(ingress, egress)

        # TODO: There might be network policies that deny traffic (for example, deny all egress).

        # Find egress rules that have matching ingress for port 3306
        matching = find_egress_with_matching_ingress(egress, port=3306, protocol="TCP")
        for egress_rule in matching:
            print(f"Egress rule from {egress_rule.network_policy_name} has {len(egress_rule.matching_ingress_rules)} matching ingress rules")

        assert len(matching) == 0, "Egress rules with matching ingress rules should not have been found"

        namespace = "test-app"
        networking_v1 = client.NetworkingV1Api()

        try:
            # Create a network policy that allows egress from backend to mysql on port 3306
            network_policy = client.V1NetworkPolicy(
                metadata=client.V1ObjectMeta(
                    name="allow-egress-to-mysql",
                    namespace=namespace
                ),
                spec=client.V1NetworkPolicySpec(
                    pod_selector=client.V1LabelSelector(
                        match_labels={"app": "backend"}
                    ),
                    policy_types=["Egress"],
                    egress=[
                        client.V1NetworkPolicyEgressRule(
                            to=[
                                client.V1NetworkPolicyPeer(
                                    pod_selector=client.V1LabelSelector(
                                        match_labels={"app": "db"}
                                    )
                                )
                            ],
                            ports=[
                                client.V1NetworkPolicyPort(
                                    protocol="TCP",
                                    port=3306
                                )
                            ]
                        )
                    ]
                )
            )

            create_network_policy(namespace, network_policy, networking_v1)

            # Create a network policy that allows ingress from backend to mysql on port 3306
            networking_v1 = client.NetworkingV1Api()
            network_policy = client.V1NetworkPolicy(
                metadata=client.V1ObjectMeta(
                    name="allow-ingress-from-backend",
                    namespace=namespace
                ),
                spec=client.V1NetworkPolicySpec(
                    pod_selector=client.V1LabelSelector(
                        match_labels={"app": "db"}
                    ),
                    policy_types=["Ingress"],
                    ingress=[
                        client.V1NetworkPolicyIngressRule(
                            _from=[
                                client.V1NetworkPolicyPeer(
                                    pod_selector=client.V1LabelSelector(
                                        match_labels={"app": "backend"}
                                    )
                                )
                            ],
                            ports=[
                                client.V1NetworkPolicyPort(
                                    protocol="TCP",
                                    port=3306
                                )
                            ]
                        )
                    ]
                )
            )

            create_network_policy(namespace, network_policy, networking_v1)

            egress = get_network_policy_rules(backend_pod, port=3306, rule_type="egress")
            ingress = get_network_policy_rules(mysql_pod, port=3306, rule_type="ingress")

            # TODO: This is strictly speaking not necessary.
            ingress, egress = associate_ingress_egress_rules(ingress, egress)

            # TODO: There might be network policies that deny traffic (for example, deny all egress).

            # Find egress rules that have matching ingress for port 3306
            matching = find_egress_with_matching_ingress(egress, port=3306, protocol="TCP")
            for egress_rule in matching:
                print(f"Egress rule from {egress_rule.network_policy_name} has {len(egress_rule.matching_ingress_rules)} matching ingress rules")

            assert len(matching) == 1, "Egress rules with matching ingress rules should have been found"
        finally:
            delete_network_policy(namespace, "allow-egress-to-mysql", networking_v1)
            delete_network_policy(namespace, "allow-ingress-from-backend", networking_v1)
