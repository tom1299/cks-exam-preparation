from kubernetes import client, config
from typing import List

def get_network_policies_matching_pod(
    pod: client.V1Pod
) -> List[str]:
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
            matching_policies.append(network_policy.metadata.name)
            continue

        # Check if all selector labels match the pod's labels
        if all(
            pod_labels.get(key) == value
            for key, value in pod_selector.match_labels.items()
        ):
            matching_policies.append(network_policy.metadata.name)

    return matching_policies
