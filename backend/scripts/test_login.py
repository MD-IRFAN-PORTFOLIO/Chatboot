import urllib.request
import urllib.parse
import json

url = "http://127.0.0.1:8000/admin/login"
data = urllib.parse.urlencode({'username': 'new_admin', 'password': 'password123'}).encode('utf-8')
req = urllib.request.Request(url, data=data)
req.add_header('Content-Type', 'application/x-www-form-urlencoded')

try:
    response = urllib.request.urlopen(req)
    val = response.read().decode()
    print("Success: Logged in!", json.loads(val)['access_token'][:10] + "...")
except Exception as e:
    print("Failed login:", e)
