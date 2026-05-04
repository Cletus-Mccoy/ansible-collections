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