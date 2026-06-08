import urllib.request, json

BASE = "http://127.0.0.1:5173"

def api(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

# 1. Login
status, data = api("POST", "/api/auth/login", body={"username": "yyz", "password": "123456"})
print(f"Login: {status}")
if "access_token" not in data:
    print(f"FAIL: {data}")
    exit()
token = data["access_token"]
print(f"Token OK: {token[:30]}...")

# 2. Admin check
status, data = api("GET", "/api/admin/check", token=token)
print(f"Admin check: {status} {data}")
