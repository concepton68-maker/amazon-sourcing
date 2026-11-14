"""Autorisations en masse et lien de demande [RM-AMZ-120, 121]."""
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from sourcing import eligibilite as EL
from sourcing.analyse import Fournisseurs
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.marketplaces import get_marketplace
from sourcing.providers.base import InfosRestrictions
from sourcing.providers.demo import FournisseurDemo
from sourcing.providers.spapi import parser_restrictions

FR = get_marketplace("FR")


class Lien(FournisseurDemo):
    def restrictions(self, mp, asin):
        if asin == "B0DEMO0002":
            return InfosRestrictions(autorise=False, approbation_requise=True, motifs=["APPROVAL_REQUIRED"],
                                     liens=[{"titre": "Request approval", "url": "https://sellercentral.amazon.fr/x?asin=B0DEMO0002"}])
        return super().restrictions(mp, asin)


class TestEligibilite(unittest.TestCase):
    def test_lien_demande(self):
        """[RM-AMZ-120] Lien de suite gardé tel quel (https seulement, sans doublon) ; jamais fabriqué."""
        r = parser_restrictions({"restrictions": [{"reasons": [{"reasonCode": "APPROVAL_REQUIRED", "message": "m", "links": [
            {"resource": "https://sellercentral.amazon.fr/hz/approvalrequest?asin=B0X", "verb": "GET", "title": "Demander"},
            {"resource": "https://sellercentral.amazon.fr/hz/approvalrequest?asin=B0X", "verb": "GET"},
            {"resource": "javascript:alert(1)", "verb": "GET"}]}]}]})
        self.assertEqual(r.liens, [{"titre": "Demander", "url": "https://sellercentral.amazon.fr/hz/approvalrequest?asin=B0X"}])
        self.assertEqual(parser_restrictions({"restrictions": [{"reasons": [{"reasonCode": "NOT_ELIGIBLE"}]}]}).liens, [])
        d, c = construire()
        f = Lien()
        cl = TestClient(creer_app(d, c, servir_interface=False, fournisseurs=Fournisseurs([f], f, f, f, f)))
        a = cl.post("/api/analyse", json={"code": "3700000000024", "prix_achat": 10}).json()["analyses"][0]
        self.assertEqual(a["liens_autorisation"][0]["titre"], "Request approval")

    def test_eligibilite_masse(self):
        """[RM-AMZ-121] Codes nettoyés sans doublon ; statut par code ; lien de demande ; pauses sous le plafond."""
        self.assertEqual(EL.lire_codes("3700000000017, 3700000000017\nb0demo0001;  x  ;3700000000024"),
                         ["3700000000017", "B0DEMO0001", "3700000000024"])
        f = Lien()
        fx = Fournisseurs([f], f, f, f, f)
        v, pauses = EL.Verifications(en_fond=False), []
        v.lancer("c", FR, fx, ["3700000000017", "3700000000024", "9999999999994"], attendre=pauses.append)
        r = {x["code"]: x for x in v.etats["c"]["resultats"]}
        self.assertEqual((r["3700000000017"]["statut"], r["3700000000024"]["statut"], r["9999999999994"]["statut"]),
                         ("AUTORISE", "APPROBATION", "INTROUVABLE"))
        self.assertTrue(r["3700000000024"]["liens"][0]["url"].startswith("https://"))
        self.assertEqual(pauses, [EL.PAUSE] * 3)
        self.assertFalse(v.etats["c"]["en_cours"])
        self.assertIn("APPROBATION;https://", EL.export_csv(v.etats["c"]))

    def test_eligibilite_api(self):
        """[RM-AMZ-121] Lancement, lecture, export ; sans code ou sans source : refus."""
        d, c = construire()
        f = Lien()
        with mock.patch.object(EL, "PAUSE", 0):
            cl = TestClient(creer_app(d, c, servir_interface=False, traitement_en_fond=False,
                                      fournisseurs=Fournisseurs([f], f, f, f, f)))
            self.assertEqual(cl.post("/api/eligibilite", json={"codes": "  ,; "}).status_code, 422)
            self.assertEqual(cl.post("/api/eligibilite", json={"codes": "3700000000017\n3700000000024"}).json()["codes"], 2)
            e = cl.get("/api/eligibilite").json()["etat"]
            self.assertEqual(len(e["resultats"]), 2)
            self.assertEqual(cl.get("/api/eligibilite/export.csv").status_code, 200)
        self.assertEqual(TestClient(creer_app(d, c, servir_interface=False, fournisseurs=Fournisseurs())).post(
            "/api/eligibilite", json={"codes": "3700000000017"}).status_code, 503)


if __name__ == "__main__":
    unittest.main()
