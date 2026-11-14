"""Connexions aux sources saisies sur le site [RM-AMZ-072 à 074]."""
import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from sourcing import connexions as CX
from sourcing.analyse import Fournisseurs
from sourcing.api import creer_app
from sourcing.demo_donnees import construire

CLE = "11" * 32
SP = {"client_id": "id-test", "client_secret": "secret-test", "refresh_token": "jeton-test", "region": "EU"}


class TestConnexions(unittest.TestCase):
    def test_connexions_chiffrees(self):
        """Chiffré lié au compte et à la source ; jamais renvoyé ; sans clé de serveur : refus."""
        cle = bytes.fromhex(CLE)
        ch = CX.chiffrer(cle, "C1", "SPAPI", SP)
        self.assertNotIn(b"secret-test", ch)
        self.assertEqual(CX.dechiffrer(cle, "C1", "SPAPI", ch), SP)
        with self.assertRaises(Exception):
            CX.dechiffrer(cle, "C2", "SPAPI", ch)          # copié vers un autre compte : illisible
        with self.assertRaises(CX.ConnexionInvalide) as e:
            CX.chiffrer(None, "C1", "SPAPI", SP)
        self.assertEqual(e.exception.args[0], "CHIFFREMENT_NON_CONFIGURE")
        for brut, champ in (({**SP, "region": "XX"}, "region"), ({**SP, "client_id": " "}, "client_id"),
                            ({"cle": "a" * 2001}, "cle"), ({"autre": 1}, "champs")):
            with self.subTest(brut=str(brut)[:30]):
                with self.assertRaises(CX.ConnexionInvalide) as e:
                    CX.valider("KEEPA" if "cle" in brut or "autre" in brut else "SPAPI", brut)
                self.assertEqual(e.exception.args[1], champ)
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False))
        with mock.patch.dict(os.environ, {"AMZ_CLE_CHIFFREMENT": ""}):
            r = cl.put("/api/connexions/KEEPA", json={"cle": "k"})
            self.assertEqual((r.status_code, r.json()["detail"]["code"]), (503, "CHIFFREMENT_NON_CONFIGURE"))
        with mock.patch.dict(os.environ, {"AMZ_CLE_CHIFFREMENT": CLE}):
            self.assertEqual(cl.put("/api/connexions/SPAPI", json=SP).status_code, 200)
            j = cl.get("/api/connexions").json()
            self.assertTrue(j["chiffrement"])
            self.assertNotIn("secret-test", str(j))
            sp = next(x for x in j["sources"] if x["source"] == "SPAPI")
            self.assertIsNotNone(sp["enregistree_le"])
            # identifiant vendeur facultatif, ajouté plus tard sans retaper le reste
            self.assertEqual(cl.put("/api/connexions/SPAPI", json={"seller_id": "A2VENDEUR"}).status_code, 200)
            self.assertEqual(CX.dechiffrer(bytes.fromhex(CLE), c, "SPAPI", d.connexions(c)["SPAPI"].chiffre)["seller_id"], "A2VENDEUR")
            # remplacement : seul le jeton change, le reste est gardé
            self.assertEqual(cl.put("/api/connexions/SPAPI", json={"client_id": "", "client_secret": "", "refresh_token": "jeton-2",
                                                                    "region": "EU"}).status_code, 200)
            ch = d.connexions(c)["SPAPI"].chiffre
            self.assertEqual(CX.dechiffrer(bytes.fromhex(CLE), c, "SPAPI", ch), {**SP, "refresh_token": "jeton-2", "seller_id": "A2VENDEUR"})
            self.assertEqual(cl.put("/api/connexions/KEEPA", json={"cle": ""}).json()["detail"]["code"], "CHAMP_OBLIGATOIRE")
            self.assertEqual(cl.delete("/api/connexions/SPAPI").json()["retiree"], True)
            self.assertEqual(cl.delete("/api/connexions/SPAPI").status_code, 404)

    def test_sources_du_compte(self):
        """[RM-AMZ-073] Sans rien : « aucune source » ; avec une clé Keepa du compte : la source existe."""
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False, fournisseurs=Fournisseurs()))
        demande = {"code": "B07XJ8C8F5", "marketplace": "FR", "prix_achat": 8.5}
        self.assertEqual(cl.post("/api/analyse", json=demande).json()["detail"], "SOURCE_NON_CONFIGUREE")
        with mock.patch.dict(os.environ, {"AMZ_CLE_CHIFFREMENT": CLE}):
            cl.put("/api/connexions/KEEPA", json={"cle": "cle-de-test"})
            with mock.patch("sourcing.providers.keepa.ClientKeepa.produit", side_effect=RuntimeError("appel réseau interdit"),
                            create=True), mock.patch("sourcing.api.resoudre_asins", return_value=[]) as r:
                rep = cl.post("/api/analyse", json=demande)
            self.assertEqual(rep.json()["detail"], "PRODUIT_INTROUVABLE")   # la source du compte a été utilisée
            fx = r.call_args.args[2]
            self.assertEqual(type(fx.catalogue[0]).__name__, "ClientKeepa")

    def test_tester_connexion(self):
        """[RM-AMZ-079] Une ligne par accès, refus d'Amazon détaillé, aucun secret renvoyé."""
        class R:
            def __init__(self, code, corps, rid="REQ-1"):
                self.status_code, self._c, self.headers, self.text = code, corps, {"x-amzn-RequestId": rid}, str(corps)
            def json(self):
                return self._c

        class Session:
            def post(self, url, data, timeout):
                return R(200, {"access_token": "acces", "expires_in": 3600})
            def get(self, url, params, timeout, headers):
                if "/catalog/" in url:
                    return R(200, {"items": [{"asin": "B0TEST"}]})
                if "/pricing/" in url or "/finances/" in url:
                    return R(403, {"errors": [{"code": "Unauthorized", "message": "Access to requested resource is denied."}]}, "REQ-403")
                return R(200, {})
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False))
        with mock.patch.dict(os.environ, {"AMZ_CLE_CHIFFREMENT": CLE}), \
                mock.patch("sourcing.providers.spapi.requests.Session", Session):
            self.assertEqual(cl.post("/api/connexions/SPAPI/test", json={}).status_code, 404)
            cl.put("/api/connexions/SPAPI", json=SP)
            j = cl.post("/api/connexions/SPAPI/test", json={"marketplace": "FR"}).json()
            self.assertEqual(cl.post("/api/connexions/SPAPI/test", json={"marketplace": "US"}).json()["detail"], "REGION_DIFFERENTE")
        etat = {e["etape"]: e["ok"] for e in j["etapes"]}
        self.assertEqual(etat, {"IDENTIFICATION": True, "COMPTE": True, "CATALOGUE": True, "OFFRES": False, "STOCK": True,
                                "FINANCES": False})
        offres = next(e for e in j["etapes"] if e["etape"] == "OFFRES")
        self.assertEqual((offres["statut"], offres["requete"]), (403, "REQ-403"))
        self.assertIn("denied", offres["message"])
        for secret in ("secret-test", "jeton-test", "acces"):
            self.assertNotIn(secret, str(j))

    def test_diagnostic_autre_region(self):
        """[RM-AMZ-079] Compte refusé en Europe mais accepté ailleurs (ex. Sandbox) : signalé."""
        class R:
            def __init__(self, code, corps=None):
                self.status_code, self._c, self.headers, self.text = code, corps or {}, {}, str(corps)
            def json(self):
                return self._c

        class Session:
            def post(self, url, data, timeout):
                return R(200, {"access_token": "acces", "expires_in": 3600})
            def get(self, url, params, timeout, headers):
                return R(200) if url.startswith("https://sandbox.sellingpartnerapi-eu") else R(403, {"errors": []})
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False))
        with mock.patch.dict(os.environ, {"AMZ_CLE_CHIFFREMENT": CLE}), \
                mock.patch("sourcing.providers.spapi.requests.Session", Session):
            cl.put("/api/connexions/SPAPI", json=SP)
            j = cl.post("/api/connexions/SPAPI/test", json={}).json()
        self.assertIn("AILLEURS_SANDBOX_EU", [e["etape"] for e in j["etapes"] if e["ok"]])
        for secret in ("secret-test", "jeton-test", "acces"):
            self.assertNotIn(secret, str(j))


if __name__ == "__main__":
    unittest.main()
