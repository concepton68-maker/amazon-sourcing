"""D'Amazon vers les fournisseurs [RM-AMZ-109 à 112]."""
import io
import unittest

from fastapi.testclient import TestClient

from sourcing import correspondance as CO
from sourcing.analyse import Fournisseurs
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.marketplaces import get_marketplace
from sourcing.providers.demo import FournisseurDemo
from sourcing.providers.spapi import parser_catalogue

FR = get_marketplace("FR")


def client():
    d, c = construire()
    demo = FournisseurDemo()
    return d, c, demo, TestClient(creer_app(d, c, servir_interface=False, traitement_en_fond=False,
                                            fournisseurs=Fournisseurs([demo], demo, demo, demo, demo)))


def fournisseur(cl, nom, csv, port=None, revente=None):
    fid = cl.post("/api/fournisseurs", json={"nom": nom}).json()["id"]
    champs = {k: v for k, v in (("port_unitaire", port), ("revente", revente)) if v is not None}
    if champs:
        cl.put(f"/api/fournisseurs/{fid}", json=champs)
    f = cl.post(f"/api/fournisseurs/{fid}/fichier", files={"fichier": ("t.csv", io.BytesIO(csv.encode()), "text/csv")}).json()
    cl.post(f"/api/fournisseurs/{fid}/catalogue", json={"fichier_id": f["fichier_id"], "colonnes": f["colonnes"]})
    return fid


class TestCorrespondance(unittest.TestCase):
    def test_codes_normalises(self):
        """[RM-AMZ-109] Zéros de tête et espaces ignorés ; texte refusé ; codes lus dans le catalogue Amazon."""
        self.assertEqual(CO.normaliser("0 012345 678905"), CO.normaliser("12345678905"))
        self.assertEqual(CO.normaliser("00012345678905"), "12345678905")
        self.assertIsNone(CO.normaliser("B0DEMO0001"))
        self.assertIsNone(CO.normaliser("000"))
        c = parser_catalogue("B0X", FR, {"identifiers": [{"marketplaceId": FR.marketplace_id, "identifiers": [
            {"identifierType": "EAN", "identifier": "3700000000017"}, {"identifierType": "UPC", "identifier": "012345678905"},
            {"identifierType": "SKU", "identifier": "abc"}]}]})
        self.assertEqual(c.codes, ("3700000000017", "012345678905"))

    def test_ou_l_acheter(self):
        """[RM-AMZ-110] Offres de tous les fournisseurs, profit décroissant ; revente interdite listée, non calculée."""
        d, c, demo, cl = client()
        fournisseur(cl, "Cher", "EAN;Prix HT\n3700000000017;12,00\n")
        fournisseur(cl, "Moins cher", "EAN;Prix HT\n03700000000017;8,00\n", port=0.2)
        fournisseur(cl, "Interdit", "EAN;Prix HT\n3700000000017;5,00\n", revente="INTERDITE")
        fournisseur(cl, "Autre", "EAN;Prix HT\n3700000000024;5,00\n")
        j = cl.get("/api/produits/FR/B0DEMO0001/ou-acheter").json()
        noms = [o["fournisseur"] for o in j["offres"]]
        self.assertEqual(noms, ["Moins cher", "Cher", "Interdit"])
        self.assertGreater(j["offres"][0]["profit"], j["offres"][1]["profit"])
        self.assertFalse(j["offres"][2]["calcule"])
        self.assertNotIn("profit", j["offres"][2])
        self.assertEqual(cl.get("/api/produits/FR/B0INCONNU1/ou-acheter").json()["offres"], [])

    def test_correspondance_amazon_d_abord(self):
        """[RM-AMZ-111] Candidats (suivis, sondage) → codes → catalogues → liste, origine « correspondance »."""
        d, c, demo, cl = client()
        fid = fournisseur(cl, "Grossiste C", "EAN;Prix HT\n3700000000017;8,00\n3700000000024;9,00\n9999999999994;1\n")
        cl.post(f"/api/fournisseurs/{fid}/analyse", json={})                   # analyse du catalogue : autre origine
        d.ajouter_suivi(c, "FR", "B0DEMO0001")
        d.enregistrer_exploration(c, {"place": "FR", "le": "2026-11-14T00:00:00+00:00", "rayons": [
            {"code": "JOUETS", "produits": [{"asin": "B0DEMO0002", "statut": "AUTORISE"}]}]})
        pauses = []
        bilan = CO.executer(c, FR, Fournisseurs([demo], demo, demo, demo, demo), d, None, "assujetti",
                            attendre=pauses.append)
        self.assertEqual((bilan["correspondances"], bilan["fournisseurs"]), (2, 1))
        self.assertTrue(pauses)
        ops = d.opportunites(c)
        corr = [o for o in ops if o.origine == f"CORRESPONDANCE:{fid}"]
        self.assertEqual(sorted(o.asin for o in corr), ["B0DEMO0001", "B0DEMO0002"])
        self.assertTrue(any(o.origine == f"FOURNISSEUR:{fid}" for o in ops))              # intacte
        CO.executer(c, FR, Fournisseurs([demo], demo, demo, demo, demo), d, None, "assujetti", attendre=lambda s: None)
        self.assertEqual(len([o for o in d.opportunites(c) if o.origine == f"CORRESPONDANCE:{fid}"]), 2)  # remplacée

    def test_correspondance_api(self):
        """[RM-AMZ-112] Lancement, bilan relu ; sans source : refus."""
        d, c, demo, cl = client()
        fournisseur(cl, "Grossiste D", "EAN;Prix HT\n3700000000017;8,00\n")
        d.ajouter_suivi(c, "FR", "B0DEMO0001")
        import sourcing.correspondance as mod
        ancien, mod.PAUSE_CATALOGUE = mod.PAUSE_CATALOGUE, 0
        try:
            self.assertEqual(cl.post("/api/correspondance").status_code, 202)
        finally:
            mod.PAUSE_CATALOGUE = ancien
        j = cl.get("/api/correspondance").json()
        self.assertFalse(j["en_cours"])
        self.assertEqual(j["bilan"]["correspondances"], 1)
        self.assertEqual(TestClient(creer_app(d, c, servir_interface=False, fournisseurs=Fournisseurs())).post(
            "/api/correspondance").status_code, 503)


if __name__ == "__main__":
    unittest.main()
