# TODO for android_adb Collection

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