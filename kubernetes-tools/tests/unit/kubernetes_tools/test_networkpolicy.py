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
