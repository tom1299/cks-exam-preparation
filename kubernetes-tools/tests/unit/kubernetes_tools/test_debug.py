import pytest
from kubernetes_tools import debug


class TestDebug:

    def test_debug_command_succeeds(self):
        output, success = debug.run_debug_command(
            namespace="test-app",
            pod_name="backend",
            command=["nc", "-vz", "-w", "1", "mysql", "3306"],
            image="nicolaka/netshoot"
        )

        # The function returns output and success status
        assert "succeeded" in output
        assert success is True

    def test_debug_command_fails(self):
        output, success = debug.run_debug_command(
            namespace="test-app",
            pod_name="backend",
            command=["nc", "-vz", "-w", "1", "mysql", "3307"],
            image="nicolaka/netshoot"
        )

        # The function returns output and success status
        assert "timed out" in output
        assert success is False

    def test_debug_command_timeout(self):
        with pytest.raises(Exception):
            debug.run_debug_command(
                namespace="test-app",
                pod_name="backend",
                command=["sleep", "3"],
                image="busybox",
                max_wait=2
            )

