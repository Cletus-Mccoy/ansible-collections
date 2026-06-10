-include .env
export

PYTHON      := python3
GITHUB_REPO ?= ansible-collections
BRANCH      ?= main

.PHONY: repo-init release git-fetch git-push

# Create GitHub repo and push — run once after git init
repo-init:
ifndef GITHUB_TOKEN
	$(error GITHUB_TOKEN is not set — add it to .env)
endif
	$(PYTHON) .github-init.py "$(GITHUB_TOKEN)" "$(GITHUB_REPO)"

# Git fetch using the token from .env (token is never embedded in the remote URL
# or passed as a process argument — it is fed to git via a transient helper).
git-fetch:
ifndef GITHUB_TOKEN
	$(error GITHUB_TOKEN is not set — add it to .env)
endif
	git -c credential.helper='!f(){ echo username=x-access-token; echo "password=$$GITHUB_TOKEN"; }; f' fetch origin

# Git push — Usage: make git-push [BRANCH=main]
git-push:
ifndef GITHUB_TOKEN
	$(error GITHUB_TOKEN is not set — add it to .env)
endif
	git -c credential.helper='!f(){ echo username=x-access-token; echo "password=$$GITHUB_TOKEN"; }; f' push origin $(BRANCH)

# Release a collection — Usage: make release COLLECTION=cletus_mccoy/android_adb VERSION=0.2.0
release:
ifndef COLLECTION
	$(error COLLECTION is not set — Usage: make release COLLECTION=cletus_mccoy/android_adb VERSION=0.2.0)
endif
ifndef VERSION
	$(error VERSION is not set — Usage: make release COLLECTION=cletus_mccoy/android_adb VERSION=0.2.0)
endif
	$(MAKE) -C "$(COLLECTION)" release VERSION=$(VERSION)
