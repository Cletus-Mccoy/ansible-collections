-include .env
export

PYTHON      := python3
GITHUB_REPO ?= ansible-collections

.PHONY: repo-init release

# Create GitHub repo and push — run once after git init
repo-init:
ifndef GITHUB_TOKEN
	$(error GITHUB_TOKEN is not set — add it to .env)
endif
	$(PYTHON) .github-init.py "$(GITHUB_TOKEN)" "$(GITHUB_REPO)"

# Release a collection — Usage: make release COLLECTION=kadans/android_adb VERSION=0.2.0
release:
ifndef COLLECTION
	$(error COLLECTION is not set — Usage: make release COLLECTION=kadans/android_adb VERSION=0.2.0)
endif
ifndef VERSION
	$(error VERSION is not set — Usage: make release COLLECTION=kadans/android_adb VERSION=0.2.0)
endif
	$(MAKE) -C "$(COLLECTION)" release VERSION=$(VERSION)
