import subprocess


class AdbError(Exception):
    pass


class AdbTimeout(AdbError):
    """An adb invocation exceeded its timeout.

    Raised instead of letting :func:`subprocess.run` propagate a bare
    :class:`subprocess.TimeoutExpired`, so callers can distinguish a hung/slow
    adb call (typically a stale server or an unreachable device) from a normal
    non-zero exit. Every adb call in this collection has a finite timeout —
    there are no unbounded waits.
    """
    pass


def run_adb_command(adb_path, args, device=None, timeout=30):
    cmd = [adb_path]

    if device:
        cmd += ["-s", device]

    cmd += args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise AdbTimeout(
            "adb command timed out after %ss: %s" % (timeout, " ".join(cmd))
        )

    if result.returncode != 0:
        raise AdbError(result.stderr.strip() or result.stdout.strip())

    return result.stdout.strip()


def adb_shell(adb_path, command, device=None, timeout=30):
    return run_adb_command(adb_path, ["shell", command], device=device, timeout=timeout)


def adb_push(adb_path, src, dest, device=None):
    return run_adb_command(adb_path, ["push", src, dest], device=device)


def adb_pull(adb_path, src, dest, device=None):
    return run_adb_command(adb_path, ["pull", src, dest], device=device)


def run_adb_binary(adb_path, args, device=None, timeout=30):
    """Run an adb command that emits binary stdout (e.g. ``exec-out screencap``).

    Returns the raw ``bytes`` of stdout. Raises :class:`AdbError` on a non-zero
    exit (decoding stderr best-effort for the message) or :class:`AdbTimeout`
    when the call exceeds ``timeout``.
    """
    cmd = [adb_path]
    if device:
        cmd += ["-s", device]
    cmd += args

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise AdbTimeout(
            "adb command timed out after %ss: %s" % (timeout, " ".join(cmd))
        )

    if result.returncode != 0:
        err = (result.stderr or result.stdout or b"").decode("utf-8", "replace").strip()
        raise AdbError(err or "adb command failed")

    return result.stdout


def list_devices(adb_path, timeout=10):
    """Return a list of ``(serial, state)`` tuples from ``adb devices``.

    ``state`` is e.g. ``device``, ``offline``, ``unauthorized``. The header line
    is skipped.
    """
    out = run_adb_command(adb_path, ["devices"], timeout=timeout)
    devices = []
    for line in out.splitlines()[1:]:
        line = line.strip()
        if not line or "\t" not in line:
            continue
        serial, state = line.split("\t", 1)
        devices.append((serial.strip(), state.strip()))
    return devices


# --- ADB server lifecycle --------------------------------------------------
#
# A wireless-ADB fleet shares one ``adb -L tcp:5037`` fork-server per controller.
# When that server hangs (it has been observed wedged for days, holding the
# socket and contending with every later run), the only fix is to bounce it.
# These helpers make that recovery explicit and bounded so a stale server can be
# detected and restarted at play start rather than silently degrading unrelated
# work.

def kill_server(adb_path, timeout=10):
    """``adb kill-server``. Best-effort; never raises on a non-zero exit.

    A kill against an already-dead server is a no-op, so failures here are not
    actionable and are swallowed. A timeout still raises :class:`AdbTimeout`.
    """
    try:
        subprocess.run(
            [adb_path, "kill-server"],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise AdbTimeout("adb kill-server timed out after %ss" % timeout)


def start_server(adb_path, timeout=20):
    """``adb start-server``. Raises :class:`AdbError`/:class:`AdbTimeout` on failure."""
    run_adb_command(adb_path, ["start-server"], timeout=timeout)


def server_responsive(adb_path, timeout=5):
    """Return ``True`` if the adb server answers ``adb devices`` within ``timeout``.

    A hung server is exactly one that accepts the connection but never replies,
    so this probes liveness with a short timeout and treats a timeout/OSError as
    "not responsive" rather than letting it hang the caller.
    """
    try:
        subprocess.run(
            [adb_path, "devices"],
            capture_output=True, text=True, timeout=timeout,
        )
        return True
    except (subprocess.TimeoutExpired, OSError):
        return False


def ensure_server(adb_path, timeout=5):
    """Ensure a responsive adb server exists, restarting a hung one.

    Returns a dict ``{"restarted": bool, "responsive": bool}``. If the current
    server does not answer within ``timeout`` it is ``kill-server``'d and a
    fresh one is started. Call this once at play start so a wedged fork-server
    left over from an interrupted run does not poison the whole batch.
    """
    if server_responsive(adb_path, timeout=timeout):
        return {"restarted": False, "responsive": True}
    kill_server(adb_path)
    try:
        start_server(adb_path)
    except AdbError:
        return {"restarted": True, "responsive": server_responsive(adb_path, timeout=timeout)}
    return {"restarted": True, "responsive": server_responsive(adb_path, timeout=timeout)}


def device_state(adb_path, target, timeout=10):
    """Return the ``adb devices`` state for ``target`` or ``None`` if absent.

    ``target`` is a serial or ``ip:port``. Returns e.g. ``device``, ``offline``,
    ``unauthorized``, or ``None`` when the device is not listed at all.
    """
    for serial, state in list_devices(adb_path, timeout=timeout):
        if serial == target:
            return state
    return None


def probe_device(adb_path, device, connect=False, connect_timeout=5):
    """Fast connectivity probe for ``device``; never hangs, never raises.

    Returns one of: ``"device"`` (online and authorized), ``"offline"``,
    ``"unauthorized"``, or ``"unreachable"`` (not connectable within the
    timeout / not present). When ``connect`` is true and ``device`` looks like
    ``ip:port``, a bounded ``adb connect`` is attempted first.

    The point is that one sleeping/offline phone marks itself ``unreachable``
    quickly instead of stalling a ``serial: 1`` run on an unbounded
    ``adb connect``.
    """
    is_network = isinstance(device, str) and ":" in device

    if connect and is_network:
        try:
            subprocess.run(
                [adb_path, "connect", device],
                capture_output=True, text=True, timeout=connect_timeout,
            )
        except (subprocess.TimeoutExpired, OSError):
            return "unreachable"

    try:
        state = device_state(adb_path, device, timeout=connect_timeout)
    except (AdbError, AdbTimeout):
        return "unreachable"

    if state is None:
        return "unreachable"
    return state
