from kubernetes_tools import debug


def test_debug():
    """
    Example test showing how to use run_debug_command.
    This test would need a real Kubernetes cluster with a pod to run.
    """
    # Example usage matching: kubectl debug -n backend pod/backend --image=nicolaka/netshoot -c debugger-7 --attach -- nc -vz mysql.db 3306
    output, success = debug.run_debug_command(
        namespace="backend",
        pod_name="backend",
        command=["nc", "-vz", "mysql.db", "3306"],
        image="nicolaka/netshoot"
    )

    # The function returns output and success status
    assert isinstance(output, str)
    assert isinstance(success, bool)
