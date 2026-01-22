from kubernetes_tools import debug


def test_debug(capsys):
    debug.debug()
    captured = capsys.readouterr()
    assert "Debugging Kubernetes Tools..." in captured.out
