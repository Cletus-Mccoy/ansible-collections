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