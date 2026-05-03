#!/usr/bin/env python3
"""Ensure a Galaxy namespace exists, creating it if not."""
import json, sys, urllib.request, urllib.error

token, namespace = sys.argv[1], sys.argv[2]
headers = {
    "Authorization": f"Token {token}",
    "Content-Type": "application/json",
}

check_url = f"https://galaxy.ansible.com/api/v1/namespaces/?name={namespace}"
req = urllib.request.Request(check_url, headers=headers)
res = json.loads(urllib.request.urlopen(req).read())

if res["count"] > 0:
    print(f"Namespace '{namespace}' already exists.")
    sys.exit(0)

print(f"Namespace '{namespace}' not found, creating...")
data = json.dumps({"name": namespace}).encode()
req = urllib.request.Request(
    "https://galaxy.ansible.com/api/v1/namespaces/",
    data=data,
    headers=headers,
)
try:
    res = json.loads(urllib.request.urlopen(req).read())
    print(f"Created namespace '{namespace}' (id={res['id']}).")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"Failed to create namespace: {body}", file=sys.stderr)
    sys.exit(1)
