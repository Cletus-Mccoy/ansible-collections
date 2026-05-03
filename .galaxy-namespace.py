#!/usr/bin/env python3
"""
Detect the Galaxy namespace owned by the token, then:
  - update galaxy.yml namespace field
  - git mv the namespace subfolder if it differs from the current name
  - print the namespace for use in the Makefile
"""
import json, os, re, subprocess, sys, urllib.request, urllib.error

token = sys.argv[1]
repo_root = os.path.dirname(os.path.abspath(__file__))
headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

# --- 1. Fetch namespaces and find the one this token owns ---
github_user = os.environ.get("GITHUB_USERNAME", "").lower()
namespace = None

offset, limit = 0, 100
while True:
    url = f"https://galaxy.ansible.com/api/v3/namespaces/?limit={limit}&offset={offset}"
    req = urllib.request.Request(url, headers=headers)
    data = json.loads(urllib.request.urlopen(req).read())
    for ns in data["data"]:
        for user in ns.get("users", []):
            if user["name"].lower() == github_user:
                namespace = ns["name"]
                break
        if namespace:
            break
    if namespace or not data["links"].get("next"):
        break
    offset += limit

if not namespace:
    print(
        f"No Galaxy namespace found for GitHub user '{github_user}'.\n"
        "Log in at https://galaxy.ansible.com with your GitHub account to create one, then re-run.",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"Found Galaxy namespace: {namespace}")

# --- 2. Find the collection subfolder (namespace/collection_name) ---
# Walk repo_root looking for a galaxy.yml
collection_dir = None
for ns_dir in os.listdir(repo_root):
    ns_path = os.path.join(repo_root, ns_dir)
    if not os.path.isdir(ns_path) or ns_dir.startswith("."):
        continue
    for col_dir in os.listdir(ns_path):
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

# --- 3. Rename namespace folder if it differs ---
if current_ns != namespace:
    old_ns_path = os.path.join(repo_root, current_ns)
    new_ns_path = os.path.join(repo_root, namespace)
    new_col_path = os.path.join(new_ns_path, collection_name)
    print(f"Renaming {current_ns}/{collection_name} -> {namespace}/{collection_name}")
    subprocess.run(["git", "-C", repo_root, "mv", f"{current_ns}", f"{namespace}"], check=True)
    subprocess.run(
        ["git", "-C", repo_root, "commit", "-m",
         f"Rename namespace folder {current_ns} -> {namespace}"],
        check=True,
    )
    collection_dir = new_col_path

# --- 4. Update galaxy.yml namespace field if needed ---
galaxy_yml = os.path.join(collection_dir, "galaxy.yml")
with open(galaxy_yml) as f:
    content = f.read()

new_content = re.sub(r"^namespace:.*", f"namespace: {namespace}", content, flags=re.MULTILINE)
if new_content != content:
    print(f"Updating galaxy.yml namespace: {namespace}")
    with open(galaxy_yml, "w") as f:
        f.write(new_content)
    subprocess.run(["git", "-C", repo_root, "add", galaxy_yml], check=True)
    subprocess.run(
        ["git", "-C", repo_root, "commit", "-m", f"Update galaxy.yml namespace to {namespace}"],
        check=True,
    )

# Print namespace for Makefile capture
print(namespace)
