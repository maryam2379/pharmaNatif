class Response :
    def __init__(self, statut_code, texte, headers=None):
        self.statut_code = statut_code
        self.texte = texte
        self.headers = headers if headers else {}

r = Response(200, "hello")
print(r.statut_code)
print(r.texte)
print(r.headers)
r2 = Response(404, "erreur")
print(r2.statut_code)