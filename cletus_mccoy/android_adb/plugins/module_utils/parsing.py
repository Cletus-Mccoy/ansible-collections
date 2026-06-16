def parse_getprop(output):
    props = {}

    for line in output.splitlines():
        if line.startswith('[') and ']: [' in line:
            key, val = line.split(']: [', 1)
            key = key[1:]
            val = val[:-1]
            props[key] = val

    return props


def extract_device_info(props):
    return {
        "manufacturer": props.get("ro.product.manufacturer", "unknown"),
        "model": props.get("ro.product.model", "unknown"),
        "brand": props.get("ro.product.brand", "unknown"),
        "android_ver": props.get("ro.build.version.release", "unknown"),
        "sdk_version": props.get("ro.build.version.sdk", "unknown"),
        "build_id": props.get("ro.build.id", "unknown"),
        "serial": props.get("ro.serialno", "unknown"),
        "timezone": props.get("persist.sys.timezone", "unknown"),
        "locale": props.get("persist.sys.locale", "unknown"),
    }


def parse_packages(output):
    return [line.replace("package:", "") for line in output.splitlines() if line.startswith("package:")]


def parse_awake_state(power_output):
    """Best-effort screen/awake state from ``dumpsys power``.

    Returns ``True`` (interactive/screen on), ``False`` (asleep/screen off), or
    ``None`` when it can't be determined. Different Android versions expose this
    as ``mWakefulness=Awake`` or ``Display Power: state=ON``, so both are tried.
    """
    if not power_output:
        return None
    for line in power_output.splitlines():
        line = line.strip()
        if line.startswith("mWakefulness="):
            return line.split("=", 1)[1].strip().lower() == "awake"
    low = power_output.lower()
    if "display power: state=on" in low:
        return True
    if "display power: state=off" in low:
        return False
    return None


def parse_adbd_root(id_output):
    """Return ``True`` when ``adb shell id`` shows uid 0 (adbd running as root)."""
    if not id_output:
        return False
    return "uid=0(" in id_output or id_output.strip().startswith("uid=0")