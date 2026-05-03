-include .env
-include ../../.env
export

VENV        := $(HOME)/.venv/ansible
PYTHON      := $(VENV)/bin/python3
PYTEST      := $(VENV)/bin/pytest
GALAXY      := $(VENV)/bin/ansible-galaxy
ANSIBLETEST := $(VENV)/bin/ansible-test
COLLECTION  := $(shell pwd)
INSTALL_PATH:= $(HOME)/.ansible/collections
GITHUB_REPO ?= ansible-collections

export PATH := $(HOME)/.local/platform-tools:$(PATH)
export ANSIBLE_COLLECTIONS_PATH := $(INSTALL_PATH)

# Current version from galaxy.yml
VERSION := $(shell grep '^version:' galaxy.yml | awk '{print $$2}')

.PHONY: install test test-unit test-integration clean build publish release

install:
	$(GALAXY) collection install "$(COLLECTION)" --force

test-unit:
	$(PYTEST) -v

test-integration: install
	$(ANSIBLETEST) integration adb_device_info adb_packages role_android_probe --python 3.12

test: test-unit test-integration

clean:
	rm -rf tests/output
	rm -f kadans-android_adb-*.tar.gz

build:
	$(GALAXY) collection build --force

# Publish to Ansible Galaxy (token from .env or env)
publish: build
ifndef GALAXY_TOKEN
	$(error GALAXY_TOKEN is not set — add it to .env)
endif
	$(PYTHON) ../../.galaxy-namespace.py "$(GALAXY_TOKEN)" kadans
	$(GALAXY) collection publish kadans-android_adb-$(VERSION).tar.gz --token $(GALAXY_TOKEN)

# Tag, push, and publish — Usage: make release VERSION=0.2.0
release:
ifndef VERSION
	$(error VERSION is not set — Usage: make release VERSION=0.2.0)
endif
ifndef GITHUB_TOKEN
	$(error GITHUB_TOKEN is not set — add it to .env)
endif
	@echo "Releasing kadans.android_adb v$(VERSION)..."
	sed -i 's/^version: .*/version: $(VERSION)/' galaxy.yml
	git -C ../.. add kadans/android_adb/galaxy.yml
	git -C ../.. commit -m "Release kadans.android_adb v$(VERSION)"
	git -C ../.. tag -a "kadans.android_adb/v$(VERSION)" -m "kadans.android_adb v$(VERSION)"
	git -C ../.. push
	git -C ../.. push --tags
	$(MAKE) publish
	@echo "Released kadans.android_adb v$(VERSION)"
