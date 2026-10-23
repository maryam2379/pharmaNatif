from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer 
import traceback
import json
from urllib.parse import urlparse, parse_qs


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


class Response :
    def __init__(self, statut_code, texte, headers=None):
        self.statut_code = statut_code
        self.texte = texte
        self.headers = headers  if headers else {}


    @classmethod
    def json(cls, data, statut_code=200, headers=None):
        texte = json.dumps(data, ensure_ascii=False)
        if headers is None:
            headers = {}
        else :
            headers = dict(headers)  # Create a copy to avoid modifying the caller's dictionary
        headers['Content-Type'] = 'application/json; charset=utf-8'
        return cls(statut_code, texte, headers)
    

class Handler(BaseHTTPRequestHandler):

    def envoyer(self, response):
        corps=response.texte.encode('utf-8')
        self.send_response(response.statut_code)
        miniscule={k.lower(): v for k, v in response.headers.items()}
        if miniscule.get('content-type') is None:
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(response.texte.encode('utf-8'))))
        if response.headers:
            for header, value in response.headers.items():
                self.send_header(header, value )
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        self.traiter()


    def do_POST(self):
       self.traiter()

    def traiter(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        request = Request(self.command, self.path, body)
        print(request.query_params)
        print(request.body)
        
        if( (request.method, request.path) in route):
            try:
                resultat= route[(request.method, request.path)](request)
            except Exception :
                traceback.print_exc()
                self.envoyer(Response(500, "Internal Server Error "))
                return 
            if isinstance(resultat, Response):
                response = resultat
            else:
                response = Response(200, str(resultat))
            self.envoyer(response)
        else: 
            methode_auth=[method for (method, path) in route if path == request.path]
            if methode_auth:
                self.envoyer(Response(405, "Method Not Allowed", {"Allow": ", ".join(methode_auth)}))
                return
            self.envoyer(Response(404, "Page not found"))

def echo(request):
    return f"Echo: {request.body.decode('utf-8')}"

def health(request):
    return "Server is healthy"

def about(request):
    return "This is a simple HTTP server implemented in Python."

def boom(request):
    return 1/0

def cree(request):
    return Response(201, "Créé")

def mauvaise(request):
    return Response(400, "Mauvaise requête")

def api_test(request):
    return Response.json({"statut": "ok", "id": 5})

def verifier(request):
    data = request.json()
   
    if data is None or not isinstance(data, dict):
        return Response.json({"error": "Invalid JSON"}, statut_code=400)

    if "code" not in data or "quantite" not in data:
        return Response.json({"error": "Missing required fields"}, statut_code=400)
    return Response.json({"message": "Data is valid", "code": data["code"], "quantite": data["quantite"]})

route={ 
    ("GET", "/health"): health,
    ("GET", "/about"): about,
    ("POST", "/echo"): echo,
    ("GET", "/boom"): boom,
    ("POST", "/cree"): cree,
    ("GET", "/mauvaise"): mauvaise,
    ("GET", "/api/test"): api_test,
    ("POST", "/verifier"): verifier
}


serveur=ThreadingHTTPServer(('localhost', 8000), Handler)
serveur.serve_forever()
