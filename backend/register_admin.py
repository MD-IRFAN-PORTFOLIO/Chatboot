import urllib.request
import urllib.error
import json

url = "http://127.0.0.1:8000/admin/register"
data = json.dumps({"username": "new_admin", "password": "password123"}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    response = urllib.request.urlopen(req)
    print("Success: Registered new admin 'new_admin' with password 'password123'")
except urllib.error.HTTPError as e:
    resp_body = e.read().decode()
    if e.code == 400 and "Username already registered" in resp_body:
        print("Admin user 'new_admin' already exists.")
    else:
        print(f"Failed: {e.code} - {resp_body}")
