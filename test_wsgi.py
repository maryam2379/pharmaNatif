from wsgiref.simple_server import make_server

def application(environ, start_response):
    for cle,valeur in environ.items():
        print(f"{cle}: {valeur}")
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b"hello world"]

serveur = make_server('localhost', 8001, application)
serveur.serve_forever()