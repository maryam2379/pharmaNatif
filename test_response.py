import json


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
    
    

# Test A : la route passe ses propres en-têtes
r = Response.json({"x": 1}, 200, {"X-Test": "oui"})
print("A :", r.headers)

# Test B : la méthode modifie-t-elle le dictionnaire de l'appelant ?
mes_entetes = {"X-Test": "oui"}
Response.json({"x": 1}, 200, mes_entetes)
print("B :", mes_entetes)

# Test C : deux réponses sans en-têtes partagent-elles un dictionnaire ?
a = Response(200, "a")
a.headers["X-Perso"] = "oui"
b = Response(200, "b")
print("C :", b.headers)