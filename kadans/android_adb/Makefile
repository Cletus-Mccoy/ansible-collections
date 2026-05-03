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
REPO_ROOT   := $(shell git -C "$(COLLECTION)" rev-parse --show-toplevel)
GITHUB_REPO ?= ansible-collections

export PATH := $(HOME)/.local/platform-tools:$(PATH)
export ANSIBLE_COLLECTIONS_PATH := $(INSTALL_PATH)

# Current version from galaxy.yml
VERSION := $(shell grep '^version:' galaxy.yml | awk '{print $$2}')

.PHONY: install test test-unit test-integration clean build publish release repo-init

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
	$(error GALAXY_TOKEN is not set — add it to $(REPO_ROOT)/.env)
endif
	$(GALAXY) collection publish kadans-android_adb-$(VERSION).tar.gz --token $(GALAXY_TOKEN)

# Create GitHub repo, set remote, and push — run once from repo root
repo-init:
ifndef GITHUB_TOKEN
	$(error GITHUB_TOKEN is not set — add it to $(REPO_ROOT)/.env)
endif
	@GITHUB_USER=$$($(PYTHON) -c "\
	import urllib.request, json; \
	req = urllib.request.Request('https://api.github.com/user', \
	  headers={'Authorization': 'token $(GITHUB_TOKEN)', 'User-Agent': 'ansible-collections'}); \
	print(json.loads(urllib.request.urlopen(req).read())['login'])") && \
	$(PYTHON) -c "\
	import urllib.request, json; \
	data = json.dumps({'name': '$(GITHUB_REPO)', 'description': 'Ansible collections by Kasper Daems', 'private': False}).encode(); \
	req = urllib.request.Request('https://api.github.com/user/repos', data=data, \
	  headers={'Authorization': 'token $(GITHUB_TOKEN)', 'Content-Type': 'application/json', 'User-Agent': 'ansible-collections'}); \
	res = json.loads(urllib.request.urlopen(req).read()); \
	print('Created: ' + res['html_url'])" && \
	git -C "$(REPO_ROOT)" remote add origin https://$(GITHUB_TOKEN)@github.com/$$GITHUB_USER/$(GITHUB_REPO).git && \
	git -C "$(REPO_ROOT)" push -u origin main && \
	echo "Repo live at https://github.com/$$GITHUB_USER/$(GITHUB_REPO)"

# Tag, push, and publish in one step — Usage: make release VERSION=0.2.0
release:
ifndef VERSION
	$(error VERSION is not set — Usage: make release VERSION=0.2.0)
endif
ifndef GITHUB_TOKEN
	$(error GITHUB_TOKEN is not set — add it to $(REPO_ROOT)/.env)
endif
	@echo "Releasing kadans.android_adb v$(VERSION)..."
	sed -i 's/^version: .*/version: $(VERSION)/' galaxy.yml
	git -C "$(REPO_ROOT)" add kadans/android_adb/galaxy.yml
	git -C "$(REPO_ROOT)" commit -m "Release kadans.android_adb v$(VERSION)"
	git -C "$(REPO_ROOT)" tag -a "kadans.android_adb/v$(VERSION)" -m "kadans.android_adb v$(VERSION)"
	git -C "$(REPO_ROOT)" push
	git -C "$(REPO_ROOT)" push --tags
	$(MAKE) publish
	@echo "Released kadans.android_adb v$(VERSION)"
