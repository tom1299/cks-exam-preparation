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

    def test_create_netcat_command_tcp_default(self):
        """Test creating netcat command with TCP protocol (default)"""
        command = debug.create_netcat_command_fot_connectivity_test(
            target_ip="10.2.3.123",
            target_port=3306,
            protocol="TCP",
            timeout=1
        )

        assert command == ["nc", "-vz", "-w", "1", "10.2.3.123", "3306"]

    def test_create_netcat_command_tcp_implicit(self):
        """Test creating netcat command with implicit TCP (no protocol specified)"""
        command = debug.create_netcat_command_fot_connectivity_test(
            target_ip="10.2.3.123",
            target_port=3306,
            timeout=1
        )

        assert command == ["nc", "-vz", "-w", "1", "10.2.3.123", "3306"]

    def test_create_netcat_command_udp(self):
        """Test creating netcat command with UDP protocol"""
        command = debug.create_netcat_command_fot_connectivity_test(
            target_ip="10.2.3.123",
            target_port=53,
            protocol="UDP",
            timeout=2
        )

        assert command == ["nc", "-vz", "-w", "2", "-u", "10.2.3.123", "53"]

    def test_create_netcat_command_different_timeout(self):
        """Test creating netcat command with different timeout"""
        command = debug.create_netcat_command_fot_connectivity_test(
            target_ip="192.168.1.1",
            target_port=80,
            timeout=10
        )

        assert command == ["nc", "-vz", "-w", "10", "192.168.1.1", "80"]

    def test_create_netcat_command_default_timeout(self):
        """Test creating netcat command with default timeout (5 seconds)"""
        command = debug.create_netcat_command_fot_connectivity_test(
            target_ip="10.0.0.1",
            target_port=443
        )

        assert command == ["nc", "-vz", "-w", "5", "10.0.0.1", "443"]

    def test_create_netcat_command_lowercase_protocol(self):
        """Test that protocol is case-insensitive"""
        command = debug.create_netcat_command_fot_connectivity_test(
            target_ip="10.2.3.123",
            target_port=53,
            protocol="udp",
            timeout=1
        )

        assert command == ["nc", "-vz", "-w", "1", "-u", "10.2.3.123", "53"]


