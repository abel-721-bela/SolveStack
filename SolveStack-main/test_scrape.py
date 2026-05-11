import urllib.request
import urllib.error
import json

req = urllib.request.Request(
    'http://127.0.0.1:8001/scrape/all', 
    data=b'', 
    headers={'Content-Type': 'application/json'}
)

try:
    res = urllib.request.urlopen(req)
    print(res.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}:\n{e.read().decode()}")
except Exception as e:
    print(f"Other Error: {e}")
