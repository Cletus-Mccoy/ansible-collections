import subprocess


class AdbError(Exception):
    pass


def run_adb_command(adb_path, args, device=None, timeout=30):
    cmd = [adb_path]

    if device:
        cmd += ["-s", device]

    cmd += args

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout
    )

    if result.returncode != 0:
        raise AdbError(result.stderr.strip() or result.stdout.strip())

    return result.stdout.strip()


def adb_shell(adb_path, command, device=None):
    return run_adb_command(adb_path, ["shell", command], device=device)


def adb_push(adb_path, src, dest, device=None):
    return run_adb_command(adb_path, ["push", src, dest], device=device)


def adb_pull(adb_path, src, dest, device=None):
    return run_adb_command(adb_path, ["pull", src, dest], device=device)


def run_adb_binary(adb_path, args, device=None, timeout=30):
    """Run an adb command that emits binary stdout (e.g. ``exec-out screencap``).

    Returns the raw ``bytes`` of stdout. Raises :class:`AdbError` on a non-zero
    exit, decoding stderr best-effort for the message.
    """
    cmd = [adb_path]
    if device:
        cmd += ["-s", device]
    cmd += args

    result = subprocess.run(cmd, capture_output=True, timeout=timeout)

    if result.returncode != 0:
        err = (result.stderr or result.stdout or b"").decode("utf-8", "replace").strip()
        raise AdbError(err or "adb command failed")

    return result.stdout


def list_devices(adb_path):
    """Return a list of ``(serial, state)`` tuples from ``adb devices``.

    ``state`` is e.g. ``device``, ``offline``, ``unauthorized``. The header line
    is skipped.
    """
    out = run_adb_command(adb_path, ["devices"])
    devices = []
    for line in out.splitlines()[1:]:
        line = line.strip()
        if not line or "\t" not in line:
            continue
        serial, state = line.split("\t", 1)
        devices.append((serial.strip(), state.strip()))
    return devices