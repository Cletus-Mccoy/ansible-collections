#!/usr/bin/env python3
"""
Detect the Galaxy namespace owned by the token:
  1. POST /api/v3/auth/token/ to get a short-lived JWT
  2. GET /api/pulp/api/v3/users/?username=<me> to resolve username from JWT
  3. GET /api/v3/namespaces/?name=<derived> to confirm namespace
  4. git mv namespace folder and update galaxy.yml if name differs
"""
import json, os, re, subprocess, sys, urllib.request, urllib.error

token = sys.argv[1]
repo_root = os.path.dirname(os.path.abspath(__file__))

# --- 1. Exchange API token for a short-lived JWT ---
req = urllib.request.Request(
    "https://galaxy.ansible.com/api/v3/auth/token/",
    data=b"{}",
    headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
    method="POST",
)
jwt = json.loads(urllib.request.urlopen(req).read())["token"]
jwt_headers = {"Authorization": f"Token {jwt}", "Content-Type": "application/json"}

# --- 2. Resolve username from JWT via Pulp users endpoint ---
req = urllib.request.Request(
    "https://galaxy.ansible.com/api/pulp/api/v3/users/me/",
    headers=jwt_headers,
)
try:
    me = json.loads(urllib.request.urlopen(req).read())
    github_user = me["username"]
except urllib.error.HTTPError:
    # Fallback: try listing users filtered by known username from env
    github_user = os.environ.get("GITHUB_USERNAME", "")
    if not github_user:
        print("Could not resolve username from token. Set GITHUB_USERNAME in .env.", file=sys.stderr)
        sys.exit(1)

# Galaxy converts GitHub hyphens to underscores
candidate = github_user.lower().replace("-", "_")
print(f"Token owner: {github_user} → Galaxy namespace candidate: {candidate}")

# --- 3. Look up the namespace ---
req = urllib.request.Request(
    f"https://galaxy.ansible.com/api/v3/namespaces/?limit=10&name={candidate}",
    headers={"Authorization": f"Token {token}"},
)
data = json.loads(urllib.request.urlopen(req).read())
namespace = next((n["name"] for n in data["data"]), None)

if not namespace:
    print(
        f"No Galaxy namespace found for '{github_user}' (tried '{candidate}').\n"
        "Log in at https://galaxy.ansible.com with your GitHub account to create one.",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"Galaxy namespace: {namespace}")

# --- 4. Find collection subfolder containing galaxy.yml ---
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

# --- 5. Rename namespace folder if it differs ---
if current_ns != namespace:
    print(f"Renaming: {current_ns}/{collection_name} -> {namespace}/{collection_name}")
    subprocess.run(["git", "-C", repo_root, "mv", current_ns, namespace], check=True)
    subprocess.run(
        ["git", "-C", repo_root, "commit", "-m",
         f"Rename namespace folder {current_ns} -> {namespace}"],
        check=True,
    )
    collection_dir = os.path.join(repo_root, namespace, collection_name)

# --- 6. Update galaxy.yml namespace if needed ---
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
