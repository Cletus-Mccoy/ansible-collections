import subprocess

import pytest
from unittest.mock import patch, MagicMock

from adb import (
    run_adb_command,
    adb_shell,
    AdbError,
    AdbTimeout,
    server_responsive,
    ensure_server,
    device_state,
    probe_device,
)


class TestRunAdbCommand:
    def _mock_result(self, returncode=0, stdout="ok", stderr=""):
        r = MagicMock()
        r.returncode = returncode
        r.stdout = stdout
        r.stderr = stderr
        return r

    def test_basic_command(self):
        with patch("adb.subprocess.run", return_value=self._mock_result()) as mock_run:
            result = run_adb_command("/usr/bin/adb", ["devices"])
            mock_run.assert_called_once_with(
                ["/usr/bin/adb", "devices"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result == "ok"

    def test_with_device_serial(self):
        with patch("adb.subprocess.run", return_value=self._mock_result(stdout="output")) as mock_run:
            result = run_adb_command("/usr/bin/adb", ["shell", "getprop"], device="192.168.1.10:42135")
            cmd = mock_run.call_args[0][0]
            assert cmd == ["/usr/bin/adb", "-s", "192.168.1.10:42135", "shell", "getprop"]
            assert result == "output"

    def test_server_port_adds_dash_p(self):
        with patch("adb.subprocess.run", return_value=self._mock_result()) as mock_run:
            run_adb_command("/usr/bin/adb", ["devices"], server_port=5038)
            cmd = mock_run.call_args[0][0]
            assert cmd == ["/usr/bin/adb", "-P", "5038", "devices"]

    def test_server_port_precedes_device_selector(self):
        with patch("adb.subprocess.run", return_value=self._mock_result()) as mock_run:
            run_adb_command("/usr/bin/adb", ["shell", "id"], device="1.2.3.4:5555", server_port=5040)
            cmd = mock_run.call_args[0][0]
            assert cmd == ["/usr/bin/adb", "-P", "5040", "-s", "1.2.3.4:5555", "shell", "id"]

    def test_no_server_port_keeps_plain_cmd(self):
        with patch("adb.subprocess.run", return_value=self._mock_result()) as mock_run:
            run_adb_command("/usr/bin/adb", ["devices"])
            assert mock_run.call_args[0][0] == ["/usr/bin/adb", "devices"]

    def test_raises_adb_error_on_nonzero_rc(self):
        with patch("adb.subprocess.run", return_value=self._mock_result(returncode=1, stderr="error: device not found")):
            with pytest.raises(AdbError, match="error: device not found"):
                run_adb_command("/usr/bin/adb", ["devices"])

    def test_raises_adb_error_uses_stdout_when_stderr_empty(self):
        with patch("adb.subprocess.run", return_value=self._mock_result(returncode=1, stdout="failed", stderr="")):
            with pytest.raises(AdbError, match="failed"):
                run_adb_command("/usr/bin/adb", ["devices"])

    def test_custom_timeout(self):
        with patch("adb.subprocess.run", return_value=self._mock_result()) as mock_run:
            run_adb_command("/usr/bin/adb", ["devices"], timeout=5)
            assert mock_run.call_args[1]["timeout"] == 5

    def test_strips_trailing_whitespace(self):
        with patch("adb.subprocess.run", return_value=self._mock_result(stdout="  value  \n")):
            result = run_adb_command("/usr/bin/adb", ["shell", "echo value"])
            assert result == "value"


class TestAdbShell:
    def test_wraps_run_adb_command(self):
        with patch("adb.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="prop_value", stderr="")
            result = adb_shell("/usr/bin/adb", "getprop ro.product.model", device="emulator-5554")
            cmd = mock_run.call_args[0][0]
            assert cmd == ["/usr/bin/adb", "-s", "emulator-5554", "shell", "getprop ro.product.model"]
            assert result == "prop_value"

    def test_without_device(self):
        with patch("adb.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="result", stderr="")
            adb_shell("/usr/bin/adb", "ls /sdcard")
            cmd = mock_run.call_args[0][0]
            assert "-s" not in cmd


class TestTimeoutHandling:
    def test_run_adb_command_raises_adb_timeout(self):
        exc = subprocess.TimeoutExpired(cmd=["adb"], timeout=30)
        with patch("adb.subprocess.run", side_effect=exc):
            with pytest.raises(AdbTimeout):
                run_adb_command("/usr/bin/adb", ["devices"])

    def test_adb_timeout_is_adb_error(self):
        assert issubclass(AdbTimeout, AdbError)


class TestServerLifecycle:
    def test_server_responsive_true(self):
        with patch("adb.subprocess.run", return_value=MagicMock()):
            assert server_responsive("/usr/bin/adb") is True

    def test_server_responsive_false_on_timeout(self):
        with patch("adb.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd=["adb"], timeout=5)):
            assert server_responsive("/usr/bin/adb") is False

    def test_ensure_server_noop_when_responsive(self):
        with patch("adb.server_responsive", return_value=True):
            with patch("adb.kill_server") as kill:
                result = ensure_server("/usr/bin/adb")
        assert result == {"restarted": False, "responsive": True}
        kill.assert_not_called()

    def test_ensure_server_restarts_when_hung(self):
        # First probe says hung, post-restart probe says responsive.
        responses = iter([False, True])
        with patch("adb.server_responsive", side_effect=lambda *a, **k: next(responses)):
            with patch("adb.kill_server") as kill, patch("adb.start_server") as start:
                result = ensure_server("/usr/bin/adb")
        kill.assert_called_once()
        start.assert_called_once()
        assert result == {"restarted": True, "responsive": True}


class TestDeviceState:
    DEVICES = "List of devices attached\n192.168.1.5:5555\tdevice\nabc123\toffline\n"

    def test_device_state_found(self):
        with patch("adb.subprocess.run",
                   return_value=MagicMock(returncode=0, stdout=self.DEVICES, stderr="")):
            assert device_state("/usr/bin/adb", "192.168.1.5:5555") == "device"
            assert device_state("/usr/bin/adb", "abc123") == "offline"

    def test_device_state_absent(self):
        with patch("adb.subprocess.run",
                   return_value=MagicMock(returncode=0, stdout=self.DEVICES, stderr="")):
            assert device_state("/usr/bin/adb", "nope:1") is None


class TestProbeDevice:
    def test_unreachable_when_not_listed(self):
        with patch("adb.device_state", return_value=None):
            assert probe_device("/usr/bin/adb", "1.2.3.4:5555") == "unreachable"

    def test_returns_device_state(self):
        with patch("adb.device_state", return_value="device"):
            assert probe_device("/usr/bin/adb", "1.2.3.4:5555") == "device"

    def test_connect_timeout_marks_unreachable(self):
        with patch("adb.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd=["adb"], timeout=5)):
            state = probe_device("/usr/bin/adb", "1.2.3.4:5555",
                                 connect=True, connect_timeout=5)
        assert state == "unreachable"
