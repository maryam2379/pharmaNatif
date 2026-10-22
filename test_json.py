import json
from urllib.parse import parse_qs, urlparse

valide = '{"code": "123", "quantite": 2}'
resultat = json.loads(valide)
print(resultat)
print(type(resultat))
print(resultat["code"])
print(json.loads(b'{"code":"123"}'))
print(json.loads('{"nom": "Santé"}'.encode('utf-8')))
print(issubclass(json.JSONDecodeError, ValueError))
print(issubclass(UnicodeDecodeError, ValueError))

invalide = 'pas du json'
try:
    json.loads(invalide)
    
except Exception as e:
    print(type(e).__name__)
    print(e)

try :
    json.loads(b"")
except Exception as e:
    print(type(e).__name__)
    print(e)


try:
    json.loads(b'\x80\x81')

except Exception as e:
    print(type(e).__name__)
    print(e)


##############################################
class Request :
    def __init__(self, method, raw_path, body):
    
        self.method = method
        self.raw_path = raw_path
        parsed_url = urlparse(raw_path)
        self.path = parsed_url.path
        self.query_params = parse_qs(parsed_url.query)
        self.body = body

    def json(self):
        try:
            return json.loads(self.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None


r=Request("POST","/x",b'{"code": "123"}')
print(r.json())

r=Request("POST","/x",b"pas du json")
print(r.json())

r=Request("POST","/x",b"")
print(r.json())

r=Request("POST","/x", b'\x80\x81')
print(r.json())