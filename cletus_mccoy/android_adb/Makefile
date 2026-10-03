-include .env
-include ../../.env
export

VENV        := $(HOME)/.venv/ansible
PYTHON      := $(VENV)/bin/python3
PYTEST      := $(VENV)/bin/pytest
GALAXY      := $(VENV)/bin/ansible-galaxy
ANSIBLETEST := $(VENV)/bin/ansible-test
CHANGELOG   := $(VENV)/bin/antsibull-changelog
COLLECTION  := $(shell pwd)
INSTALL_PATH:= $(HOME)/.ansible/collections
GITHUB_REPO ?= ansible-collections

export PATH := $(HOME)/.local/platform-tools:$(PATH)
export ANSIBLE_COLLECTIONS_PATH := $(INSTALL_PATH)

# Current version from galaxy.yml
VERSION := $(shell grep '^version:' galaxy.yml | awk '{print $$2}')

.PHONY: install test test-unit test-integration sanity changelog-lint clean build publish release

install:
	$(GALAXY) collection install "$(COLLECTION)" --force

test-unit:
	$(PYTEST) -v

# ansible-test sanity (what CI runs). Needs a Linux filesystem: on /mnt/c every
# file looks executable, which fails the shebang test.
sanity:
	$(ANSIBLETEST) sanity --venv --python 3.12

# Validate changelogs/fragments/*.yml (pip install antsibull-changelog)
changelog-lint:
	$(CHANGELOG) lint



# Main test target: unit tests and orchestrated integration tests
test: test-unit integration-orchestrator

# Run orchestrated integration tests (recommended for full-sequence validation)
integration-orchestrator: install
	ANSIBLE_CONFIG=../../ansible.cfg ansible-playbook -i tests/integration/inventory tests/integration/orchestrator.yml -e @tests/integration/integration_config.yml

# Legacy/manual integration test target (deprecated)
test-integration:
	@echo "[DEPRECATED] Use 'make integration-orchestrator' for integration tests."
	@echo "This target is kept for reference only."

clean:
	rm -rf tests/output
	rm -f cletus_mccoy-android_adb-*.tar.gz

build:
	$(GALAXY) collection build --force

# Publish to Ansible Galaxy (token from .env or env)
publish: build
ifndef GALAXY_TOKEN
	$(error GALAXY_TOKEN is not set — add it to .env)
endif
	@$(PYTHON) ../../.galaxy-namespace.py "$(GALAXY_TOKEN)"
	@$(GALAXY) collection publish *-android_adb-$(VERSION).tar.gz --token $(GALAXY_TOKEN)

# Tag, push, and publish — Usage: make release VERSION=0.2.0
release:
ifndef VERSION
	$(error VERSION is not set — Usage: make release VERSION=0.2.0)
endif
ifndef GITHUB_TOKEN
	$(error GITHUB_TOKEN is not set — add it to .env)
endif
	@echo "Releasing cletus_mccoy.android_adb v$(VERSION)..."
	sed -i 's/^version: .*/version: $(VERSION)/' galaxy.yml
	$(CHANGELOG) release --version $(VERSION)
	git -C ../.. add cletus_mccoy/android_adb/galaxy.yml cletus_mccoy/android_adb/changelogs cletus_mccoy/android_adb/CHANGELOG.md
	git -C ../.. commit -m "Release cletus_mccoy.android_adb v$(VERSION)"
	git -C ../.. tag -a "cletus_mccoy.android_adb/v$(VERSION)" -m "cletus_mccoy.android_adb v$(VERSION)"
	git -C ../.. push
	git -C ../.. push --tags
	$(MAKE) publish
	# GitHub Release (shows in the repo sidebar and notifies watchers); needs the gh CLI
	-gh release create "cletus_mccoy.android_adb/v$(VERSION)" -R Cletus-Mccoy/ansible-collections \
		--verify-tag --latest --title "android_adb v$(VERSION)" \
		--notes "See the [changelog](https://github.com/Cletus-Mccoy/ansible-collections/blob/main/cletus_mccoy/android_adb/CHANGELOG.md#v$(subst .,-,$(VERSION))). Install: ansible-galaxy collection install cletus_mccoy.android_adb:==$(VERSION)"
	@echo "Released cletus_mccoy.android_adb v$(VERSION)"
