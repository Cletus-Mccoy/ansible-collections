from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kadans.android_adb.plugins.module_utils.adb import adb_shell
from ansible_collections.kadans.android_adb.plugins.module_utils.parsing import parse_getprop, extract_device_info
import shutil


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            device=dict(type="str", required=False),
        ),
        supports_check_mode=True
    )

    adb_path = shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH")

    device = module.params.get("device")

    try:
        output = adb_shell(adb_path, "getprop", device=device)
        props = parse_getprop(output)
        info = extract_device_info(props)

        module.exit_json(
            changed=False,
            android_device_info=info
        )

    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    run_module()


if __name__ == '__main__':
    main()