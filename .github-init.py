#!/usr/bin/env python3
import json, os, subprocess, sys, urllib.request, urllib.error

token, repo_name = sys.argv[1], sys.argv[2]
repo_root = os.path.dirname(os.path.abspath(__file__))
headers = {"Authorization": f"token {token}", "User-Agent": "ansible-collections", "Content-Type": "application/json"}

req = urllib.request.Request("https://api.github.com/user", headers=headers)
user = json.loads(urllib.request.urlopen(req).read())["login"]
print(f"GitHub user: {user}")

data = json.dumps({"name": repo_name, "description": "Ansible collections by Kasper Daems", "private": False}).encode()
req = urllib.request.Request("https://api.github.com/user/repos", data=data, headers=headers)
try:
    res = json.loads(urllib.request.urlopen(req).read())
    print(f"Created: {res['html_url']}")
except urllib.error.HTTPError as e:
    body = json.loads(e.read())
    if "already exists" in body.get("errors", [{}])[0].get("message", ""):
        print(f"Repo already exists: https://github.com/{user}/{repo_name}")
    else:
        print(f"Error: {body['message']}", file=sys.stderr)
        sys.exit(1)

remote_url = f"https://{token}@github.com/{user}/{repo_name}.git"
existing = subprocess.run(["git", "-C", repo_root, "remote", "get-url", "origin"], capture_output=True)
if existing.returncode != 0:
    subprocess.run(["git", "-C", repo_root, "remote", "add", "origin", remote_url], check=True)
else:
    subprocess.run(["git", "-C", repo_root, "remote", "set-url", "origin", remote_url], check=True)

subprocess.run(["git", "-C", repo_root, "push", "-u", "origin", "main"], check=True)
print(f"Repo live at https://github.com/{user}/{repo_name}")
