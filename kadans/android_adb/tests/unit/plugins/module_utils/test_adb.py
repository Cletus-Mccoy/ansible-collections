import pytest
from unittest.mock import patch, MagicMock

from adb import run_adb_command, adb_shell, AdbError


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
