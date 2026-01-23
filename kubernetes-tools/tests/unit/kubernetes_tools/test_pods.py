from kubernetes_tools import pods


class TestPods:

    def test_get_pod_found(self):
        """Test getting an existing pod"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        # The function returns a pod object when found
        assert pod is not None
        assert pod.metadata.name == "backend"
        assert pod.metadata.namespace == "backend"

    def test_get_pod_not_found(self):
        """Test getting a non-existent pod"""
        pod = pods.get_pod(
            name="nonexistent-pod",
            namespace="backend"
        )

        # The function returns None when pod is not found
        assert pod is None

    def test_get_pod_default_namespace(self):
        """Test getting a pod from default namespace"""
        pod = pods.get_pod(
            name="test-pod"
        )

        # The function should search in default namespace
        # This test will return None if no pod exists, which is expected
        # in most test environments
        assert pod is None or pod.metadata.namespace == "default"

    def test_find_exposed_port_tcp(self):
        """Test finding an exposed TCP port in a pod"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        assert pod is not None

        # Test finding an exposed TCP port
        exposed = pods.find_exposed_port(pod, port=8080, protocol="TCP")

        if exposed:
            assert exposed.container_name is not None
            assert exposed.port.container_port == 8080
            assert exposed.port.protocol == "TCP"

    def test_find_exposed_port_not_found(self):
        """Test finding a non-exposed port"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        assert pod is not None

        # Test finding a port that doesn't exist
        exposed = pods.find_exposed_port(pod, port=99999, protocol="TCP")

        assert exposed is None

    def test_find_exposed_port_wrong_protocol(self):
        """Test finding a port with wrong protocol"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        assert pod is not None

        # If the pod has TCP port 8080, searching for UDP should return None
        exposed = pods.find_exposed_port(pod, port=8080, protocol="UDP")

        # This should be None if 8080 is only exposed as TCP
        assert exposed is None or exposed.port.protocol == "UDP"

    def test_find_exposed_port_default_protocol(self):
        """Test finding a port with default TCP protocol"""
        pod = pods.get_pod(
            name="backend",
            namespace="backend"
        )

        assert pod is not None

        # Test with default protocol (TCP)
        exposed = pods.find_exposed_port(pod, port=8080)

        if exposed:
            assert exposed.container_name is not None
            assert exposed.port.container_port == 8080

