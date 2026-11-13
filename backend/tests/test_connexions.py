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
            # remplacement : seul le jeton change, le reste est gardé
            self.assertEqual(cl.put("/api/connexions/SPAPI", json={"client_id": "", "client_secret": "", "refresh_token": "jeton-2",
                                                                    "region": "EU"}).status_code, 200)
            ch = d.connexions(c)["SPAPI"].chiffre
            self.assertEqual(CX.dechiffrer(bytes.fromhex(CLE), c, "SPAPI", ch), {**SP, "refresh_token": "jeton-2"})
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


if __name__ == "__main__":
    unittest.main()
