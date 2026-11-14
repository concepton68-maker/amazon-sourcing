"""Comparaison entre pays européens [RM-AMZ-117]."""
import unittest

from fastapi.testclient import TestClient

from sourcing import multipays as MP
from sourcing.analyse import Fournisseurs
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.marketplaces import MARKETPLACES
from sourcing.parametres import Parametres
from sourcing.providers.demo import FournisseurDemo


class Inscrit(FournisseurDemo):
    def participations(self, mp):
        return [MARKETPLACES[c].marketplace_id for c in ("FR", "DE", "SE", "UK", "US")]

    def offres(self, mp, asin):
        o = super().offres(mp, asin)
        if mp.code == "DE":
            from dataclasses import replace
            return replace(o, prix_buybox=o.prix_buybox + 5)
        if mp.code == "SE":
            raise RuntimeError("panne")
        return o


class TestMultiPays(unittest.TestCase):
    def test_comparaison_pays(self):
        """[RM-AMZ-117] Places inscrites seulement ; euros triés par profit ; autres devises à part ; panne isolée ; EFN rappelé."""
        f = Inscrit()
        fx = Fournisseurs([f], f, f, f, f)
        self.assertEqual([m.code for m in MP.places_europe(fx)], ["FR", "DE", "SE", "UK"])
        r = MP.comparer("3700000000017", 8.5, fx, Parametres())
        self.assertEqual([x["marketplace"] for x in r], ["DE", "FR", "UK", "SE"])
        self.assertGreater(r[0]["profit"], r[1]["profit"])
        self.assertIn("erreur", r[3])
        self.assertEqual(r[0]["hypotheses"][0]["code"], "HYP_STOCK_PAYS")
        self.assertEqual(r[1]["hypotheses"], [])                                     # France : pas de rappel
        self.assertEqual(r[2]["hypotheses"][0]["code"], "HYP_STOCK_PAYS_UK")
        self.assertEqual(r[2]["devise"], "GBP")
        demo = FournisseurDemo()
        self.assertTrue(all(m.devise == "EUR" for m in MP.places_europe(Fournisseurs([demo], demo, demo, demo, demo))))
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False, fournisseurs=fx))
        j = cl.post("/api/analyse/pays", json={"code": "3700000000017", "prix_achat": 8.5}).json()
        self.assertEqual(j["pays"][0]["marketplace"], "DE")


if __name__ == "__main__":
    unittest.main()
