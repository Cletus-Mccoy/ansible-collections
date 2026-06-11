# TODO for android_adb Collection

## Pre-existing integration-test failures (found 2026-06-12 on a rooted phh-Treble GSI)
These targets carry environment-dependent assumptions that break on a rooted
device. They were masked before because the orchestrator died early at adb_config
(a failed host is dropped from later plays). Unrelated to the 0.3.0 modules.
- [x] `adb_config` — asserted a `persist.*` set is *denied*; under root it succeeds
      (and is idempotent when the value already matches). FIXED: assert now accepts
      "denied-with-message (non-root) OR applied cleanly (root)".
- [x] `adb_install` — referenced an undefined `install_result` var and required
      `changed=true` (breaks on idempotent re-runs). FIXED: removed the bogus task;
      success = "not failed".
- [ ] `adb_intent` — assumes `am start -a com.example.INVALID_ACTION` exits non-zero;
      on this GSI's `am` an unresolvable action prints an error but exits 0, so the
      module does not "fail" → "Intent did not fail as expected" assertion fails.
      Fix: use a guaranteed-failing invocation (e.g. `-n pkg/.NoSuchActivity`) or make
      the assertion device-aware.
- [ ] Verify the orchestrator tail (`adb_logcat`, `adb_packages`, `adb_uninstall`)
      reaches green once `adb_intent` is fixed — these were never reached on this
      device (masked behind the earlier failures).
- [ ] Ties into existing item below: "Add adaptive test logic: detect device
      capabilities (root, settings put) and branch/skip accordingly."

## Immediate Tasks
- [ ] Replace all remaining stub integration tests with meaningful tests for each module
- [ ] Verify all module integration tests pass and cover basic functionality
- [ ] Review and update integration_config.yml for completeness and clarity
- [ ] Ensure all modules have correct argument specs and error handling
- [ ] Check for missing or incorrect shebang/interpreter lines in all modules
- [ ] Add a bootstrap task to ensure "Install unknown apps" is allowed for the shell/adb user before running integration tests

## Next Steps: Role Setup & Testing
- [ ] Create and document example roles using android_adb modules
- [ ] Write integration tests for each role
- [ ] Ensure roles work with variables from integration_config.yml
- [ ] Validate idempotency and error handling in roles

## Final Steps: Playbook Usage Testing
- [ ] Create example playbooks that import roles and use modules directly
- [ ] Test playbook execution with imported roles and direct module usage
- [ ] Document usage patterns and best practices in README
- [ ] Prepare for collection publishing (galaxy.yml, versioning, etc.)
- [ ] Uncomment tasks for pairing in test setup

## Additional TODO
- [ ] Document and support Android app configuration via Managed Configurations (app_restrictions.xml, EMM/enterprise, or custom config files in assets/runtime)
- [ ] Improve adb_install module to gracefully handle and report install failures (e.g., user restrictions, Play Protect, etc.)
- [ ] Implement a bootstrap playbook/task to:
    - Dismiss keyguard/lock screen (input keyevent 82, wm dismiss-keyguard)
    - Grant install permissions (settings put global verifier_verify_adb_installs 0, etc.)
    - Enable development/adb settings (settings put global development_settings_enabled 1, adb_enabled 1)
    - Set screen brightness (settings put system screen_brightness_mode 0, screen_brightness 120)
    - Document limitations (cannot bypass MDM, TV, SELinux, etc.)
- [ ] Add adaptive test logic: detect device capabilities (e.g., settings put, root access) and branch/skips tests accordingly
- [ ] Document device class matrix: consumer, TV, enterprise, rooted, non-root, and expected test coverage/limitations

---
Add/remove items as needed. Check off tasks as you complete them!