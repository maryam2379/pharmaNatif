import json
import sys
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse


class Request:
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


class Response:
    def __init__(self, statut_code, texte, headers=None):
        self.statut_code = statut_code
        self.texte = texte
        self.headers = headers if headers else {}

    @classmethod
    def json(cls, data, statut_code=200, headers=None):
        texte = json.dumps(data, ensure_ascii=False)
        if headers is None:
            headers = {}
        else:
            headers = dict(headers)  # copie : on ne modifie pas le dictionnaire de l'appelant
        headers['Content-Type'] = 'application/json; charset=utf-8'
        return cls(statut_code, texte, headers)


#  fonction pour tester les routes

def echo(request):
    return f"Echo: {request.body.decode('utf-8')}"


def health(request):
    return "Server is healthy"


def about(request):
    return "This is a simple HTTP server implemented in Python."


def boom(request):
    return 1 / 0


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


route = {
    ("GET", "/health"): health,
    ("GET", "/about"): about,
    ("POST", "/echo"): echo,
    ("GET", "/boom"): boom,
    ("POST", "/cree"): cree,
    ("GET", "/mauvaise"): mauvaise,
    ("GET", "/api/test"): api_test,
    ("POST", "/verifier"): verifier,
}


def repondre_a(request):
 
    cle = (request.method, request.path)

    if cle in route:
        try:
            resultat = route[cle](request)
        except Exception:
            traceback.print_exc()
            return Response(500, "Internal Server Error")
        if isinstance(resultat, Response):
            return resultat
        return Response(200, str(resultat))

    methodes_autorisees = [m for (m, p) in route if p == request.path]
    if methodes_autorisees:
        return Response(405, "Method Not Allowed", {"Allow": ", ".join(methodes_autorisees)})
    return Response(404, "Page not found")

#  partie quigere le wsgi 

def application(environ, start_response):
   
    try:
        taille = int(environ.get('CONTENT_LENGTH') or 0)
    except ValueError:
        taille = 0
    corps_requete = environ['wsgi.input'].read(taille) if taille > 0 else b""
    chemin = environ.get('PATH_INFO', '/')
    query = environ.get('QUERY_STRING', '')
    raw_path = chemin + ('?' + query if query else '')

    request = Request(environ['REQUEST_METHOD'], raw_path, corps_requete)

    response = repondre_a(request)

    entetes = dict(response.headers)
    if 'content-type' not in {k.lower() for k in entetes}:
        entetes['Content-Type'] = 'text/html; charset=utf-8'


    try:
        phrase = HTTPStatus(response.statut_code).phrase
    except ValueError:
        phrase = "Unknown"
    statut = f"{response.statut_code} {phrase}"

    start_response(statut, list(entetes.items()))
    return [response.texte.encode('utf-8')]


# lapartie qui gere le serveur

class Handler(BaseHTTPRequestHandler):

    def construire_environ(self):

        parsed = urlparse(self.path)
        host, port = self.server.server_address[:2]

        environ = {
            'REQUEST_METHOD': self.command,
            'SCRIPT_NAME': '',
            'PATH_INFO': unquote(parsed.path),
            'QUERY_STRING': parsed.query,
            'CONTENT_TYPE': self.headers.get('Content-Type', ''),
            'CONTENT_LENGTH': self.headers.get('Content-Length', ''),
            'SERVER_NAME': str(host),
            'SERVER_PORT': str(port),
            'SERVER_PROTOCOL': self.request_version,
            'REMOTE_ADDR': self.client_address[0],
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': self.rfile,
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': True,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }

        
        for nom, valeur in self.headers.items():
            if nom.lower() in ('content-type', 'content-length'):
                continue
            environ['HTTP_' + nom.upper().replace('-', '_')] = valeur

        return environ

    def envoyer_erreur_500(self):
        corps = b"Internal Server Error"
        self.send_response(500)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def traiter(self):
        environ = self.construire_environ()
        reponse = {}
        ecrits = []

        def start_response(statut, entetes, exc_info=None):
            reponse['statut'] = statut
            reponse['entetes'] = list(entetes)
            return ecrits.append  # "write" exigé par la spec WSGI

        resultat = None
        try:
            resultat = application(environ, start_response)
            corps = b"".join(ecrits + list(resultat))
            if 'statut' not in reponse:
                raise RuntimeError("l'application n'a pas appelé start_response")
        except Exception:
            traceback.print_exc()
            self.envoyer_erreur_500()
            return
        finally:
            if hasattr(resultat, 'close'):
                resultat.close()

        code = int(reponse['statut'].split()[0])
        self.send_response(code)

        noms_envoyes = set()
        for nom, valeur in reponse['entetes']:
            self.send_header(nom, valeur)
            noms_envoyes.add(nom.lower())
        if 'content-length' not in noms_envoyes:
            self.send_header('Content-Length', str(len(corps)))  # octets, pas caractères
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        self.traiter()

    def do_POST(self):
        self.traiter()


if __name__ == '__main__':
    serveur = ThreadingHTTPServer(('localhost', 8000), Handler)
    print("Serveur lancé sur http://localhost:8000")
    serveur.serve_forever()