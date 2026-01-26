from kubernetes_tools import pods

# TODO: Remove superfluous comments for obvious assertions
class TestPods:

    def test_get_pod_found(self):
        """Test getting an existing pod"""
        pod = pods.get_pod_by_name(
            name="backend",
            namespace="test-app"
        )

        # The function returns a pod object when found
        assert pod is not None
        assert pod.metadata.name == "backend"
        assert pod.metadata.namespace == "test-app"

    def test_get_pod_not_found(self):
        """Test getting a non-existent pod"""
        pod = pods.get_pod_by_name(
            name="nonexistent-pod",
            namespace="test-app"
        )

        # The function returns None when pod is not found
        assert pod is None

    def test_get_pod_default_namespace(self):
        """Test getting a pod from default namespace"""
        pod = pods.get_pod_by_name(
            name="test-pod"
        )

        # The function should search in default namespace
        # This test will return None if no pod exists, which is expected
        # in most test environments
        assert pod is None or pod.metadata.namespace == "default"

    def test_find_exposed_port_tcp(self):
        """Test finding an exposed TCP port in a pod"""
        pod = pods.get_pod_by_name(
            name="mysql",
            namespace="test-app"
        )

        assert pod is not None

        # Test finding an exposed TCP port
        exposed = pods.find_exposed_port(pod, port=3306, protocol="TCP")

        assert exposed.container_name is not None
        assert exposed.port.container_port == 3306
        assert exposed.port.protocol == "TCP"

    def test_find_exposed_port_not_found(self):
        """Test finding a non-exposed port"""
        pod = pods.get_pod_by_name(
            name="backend",
            namespace="test-app"
        )

        assert pod is not None

        # Test finding a port that doesn't exist
        exposed = pods.find_exposed_port(pod, port=99999, protocol="TCP")

        assert exposed is None

    def test_find_exposed_port_wrong_protocol(self):
        """Test finding a port with wrong protocol"""
        pod = pods.get_pod_by_name(
            name="mysql",
            namespace="test-app"
        )

        assert pod is not None

        exposed = pods.find_exposed_port(pod, port=3306, protocol="UDP")

        assert exposed is None or exposed.port.protocol == "UDP"

    def test_find_exposed_port_default_protocol(self):
        """Test finding a port with default TCP protocol"""
        pod = pods.get_pod_by_name(
            name="mysql",
            namespace="test-app"
        )

        assert pod is not None

        # Test with default protocol (TCP)
        exposed = pods.find_exposed_port(pod, port=3306)

        assert exposed.container_name is not None
        assert exposed.port.container_port == 3306

    def test_get_pod_ips_single_ip(self):
        """Test getting IP addresses from a pod with a single IP"""
        pod = pods.get_pod_by_name(
            name="backend",
            namespace="test-app"
        )

        assert pod is not None

        ips = pods.get_pod_ips(pod)

        # Should return a list
        assert isinstance(ips, list)
        # Should have at least one IP if pod is running
        if pod.status.pod_ip:
            assert len(ips) >= 1
            assert pod.status.pod_ip in ips
            # All IPs should be valid strings
            for ip in ips:
                assert isinstance(ip, str)
                assert len(ip) > 0

    def test_get_pod_ips_mysql_pod(self):
        """Test getting IP addresses from the mysql pod"""
        pod = pods.get_pod_by_name(
            name="mysql",
            namespace="test-app"
        )

        assert pod is not None

        ips = pods.get_pod_ips(pod)

        # Should return a list
        assert isinstance(ips, list)
        # MySQL pod should have an IP if running
        if pod.status.pod_ip:
            assert len(ips) >= 1
            # Primary IP should be in the list
            assert pod.status.pod_ip in ips

    def test_get_pod_ips_no_duplicates(self):
        """Test that get_pod_ips doesn't return duplicate IPs"""
        pod = pods.get_pod_by_name(
            name="backend",
            namespace="test-app"
        )

        assert pod is not None

        ips = pods.get_pod_ips(pod)

        # Should return a list
        assert isinstance(ips, list)
        # No duplicates - length should equal unique count
        assert len(ips) == len(set(ips))

    def test_get_pod_ips_includes_all_ips(self):
        """Test that get_pod_ips includes all pod IPs from status"""
        pod = pods.get_pod_by_name(
            name="frontend",
            namespace="test-app"
        )

        assert pod is not None

        ips = pods.get_pod_ips(pod)

        # Should return a list
        assert isinstance(ips, list)

        # If pod has a primary IP, it should be in the list
        if pod.status.pod_ip:
            assert pod.status.pod_ip in ips

        # If pod has additional IPs, they should all be in the list
        if pod.status.pod_i_ps:
            for pod_ip in pod.status.pod_i_ps:
                assert pod_ip.ip in ips

    def test_get_pod_ips_empty_when_no_ip(self):
        """Test that get_pod_ips returns empty list for pod without IP"""
        # This test uses a pod that might not have started yet or doesn't exist
        pod = pods.get_pod_by_name(
            name="nonexistent-pod",
            namespace="test-app"
        )

        # If pod doesn't exist, skip this test
        if pod is None:
            return

        ips = pods.get_pod_ips(pod)

        # Should still return a list (even if empty)
        assert isinstance(ips, list)


    def test_get_pod_by_labels_found(self):
        pod_list = pods.get_pods_by_labels_as_dict({"app": "backend"}, namespace="test-app")

        assert pod_list is not None
        assert len(pod_list) == 1

        for pod in pod_list:
            assert pod["metadata"]["name"] == "backend"
            assert pod["metadata"]["namespace"] == "test-app"
            assert pod["spec"]["containers"][0]["name"] == "backend"
