#!/usr/bin/env python3
"""
Detect the Galaxy namespace for this account:
  1. Derive candidate name from GITHUB_USERNAME (lowercase, hyphens -> underscores)
  2. Confirm it exists via GET /api/v3/namespaces/?name=<candidate>
  3. git mv namespace folder and update galaxy.yml if name differs
"""
import json, os, re, shutil, subprocess, sys, urllib.request, urllib.error

token = sys.argv[1]
repo_root = os.path.dirname(os.path.abspath(__file__))

github_user = os.environ.get("GITHUB_USERNAME", "")
if not github_user:
    print("GITHUB_USERNAME is not set in .env", file=sys.stderr)
    sys.exit(1)

# Galaxy normalises GitHub usernames: lowercase, hyphens become underscores
candidate = github_user.lower().replace("-", "_")
print(f"Looking up Galaxy namespace '{candidate}' for GitHub user '{github_user}'...")

req = urllib.request.Request(
    f"https://galaxy.ansible.com/api/v3/namespaces/?limit=5&name={candidate}",
    headers={"Authorization": f"Token {token}"},
)
try:
    data = json.loads(urllib.request.urlopen(req).read())
except urllib.error.HTTPError as e:
    print(f"Galaxy API error: {e.code} {e.reason}", file=sys.stderr)
    sys.exit(1)

namespace = next((n["name"] for n in data["data"]), None)
if not namespace:
    print(
        f"No Galaxy namespace found for '{github_user}' (tried '{candidate}').\n"
        "Log in at https://galaxy.ansible.com with your GitHub account to create one.",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"Galaxy namespace: {namespace}")

# --- Find collection subfolder containing galaxy.yml ---
collection_dir = current_ns = collection_name = None
for ns_dir in sorted(os.listdir(repo_root)):
    ns_path = os.path.join(repo_root, ns_dir)
    if not os.path.isdir(ns_path) or ns_dir.startswith("."):
        continue
    for col_dir in sorted(os.listdir(ns_path)):
        col_path = os.path.join(ns_path, col_dir)
        if os.path.isfile(os.path.join(col_path, "galaxy.yml")):
            collection_dir = col_path
            current_ns = ns_dir
            collection_name = col_dir
            break
    if collection_dir:
        break

if not collection_dir:
    print("Could not find a collection with galaxy.yml under the repo root.", file=sys.stderr)
    sys.exit(1)

# --- Rename namespace folder if it differs ---
if current_ns != namespace:
    old_path = os.path.join(repo_root, current_ns)
    new_path = os.path.join(repo_root, namespace)
    print(f"Renaming: {current_ns}/{collection_name} -> {namespace}/{collection_name}")
    shutil.move(old_path, new_path)
    subprocess.run(["git", "-C", repo_root, "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", repo_root, "commit", "-m",
         f"Rename namespace folder {current_ns} -> {namespace}"],
        check=True,
    )
    collection_dir = os.path.join(repo_root, namespace, collection_name)

# --- Update galaxy.yml namespace if needed ---
galaxy_yml = os.path.join(collection_dir, "galaxy.yml")
with open(galaxy_yml) as f:
    content = f.read()

new_content = re.sub(r"^namespace:.*", f"namespace: {namespace}", content, flags=re.MULTILINE)
if new_content != content:
    print(f"Updating galaxy.yml: namespace -> {namespace}")
    with open(galaxy_yml, "w") as f:
        f.write(new_content)
    subprocess.run(["git", "-C", repo_root, "add", galaxy_yml], check=True)
    subprocess.run(
        ["git", "-C", repo_root, "commit", "-m", f"Update galaxy.yml namespace to {namespace}"],
        check=True,
    )

print(namespace)
