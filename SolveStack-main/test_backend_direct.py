import urllib.request as r
import urllib.error as e

try:
    print(r.urlopen('http://localhost:8001/problems').read().decode())
except e.HTTPError as ex:
    print(ex.read().decode())
