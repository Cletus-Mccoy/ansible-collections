# Contributing to cletus_mccoy.android_adb

Thank you for your interest in contributing!

## How to Contribute
- Fork the repository and create a feature branch.
- Make your changes with clear commit messages.
- Ensure all tests pass: `make test-unit`, `make sanity` (ansible-test; run it from a
  Linux filesystem, not `/mnt/c`), and integration tests if you have a device.
- Update or add documentation as needed. Options shared by all modules live in
  `plugins/doc_fragments/adb.py` and `adb_argument_spec()` in `plugins/module_utils/adb.py`.
- Add a changelog fragment in `changelogs/fragments/` (see
  [antsibull-changelog](https://github.com/ansible-community/antsibull-changelog/blob/main/docs/changelogs.md)),
  e.g. `changelogs/fragments/123-adb-shell-creates.yml`:
  ```yaml
  minor_changes:
    - adb_shell - add a ``creates`` option.
  ```
- Open a pull request describing your changes.

## Code Style
- Follow PEP8 for Python code.
- Use descriptive variable and function names.
- Keep module docstrings up to date.

## Reporting Issues
- Use [GitHub Issues](https://github.com/Cletus-Mccoy/ansible-collections/issues) to report bugs or request features.
- Include details: environment, steps to reproduce, expected/actual behavior, and logs if possible.

## Questions and feedback
- Ask questions and share how you use the collection in
  [GitHub Discussions](https://github.com/Cletus-Mccoy/ansible-collections/discussions).

## Communication
- Be respectful and constructive in all interactions.
- Maintainers will review PRs and issues as time permits.
