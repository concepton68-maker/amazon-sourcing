"""Ce que je peux vendre [RM-AMZ-084, 085]."""
import unittest
import unittest.mock
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from sourcing import exploration as EX
from sourcing.analyse import Fournisseurs
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.marketplaces import get_marketplace
from sourcing.providers.base import InfosCatalogue, InfosRestrictions


class Faux:
    """Rayon A : 5 produits autorisés ; rayon B : 2 sur 5 ; rayon C : aucun ; rayon D : panne de recherche."""
    def rechercher(self, mp, mots, taille):
        if mots == "d":
            raise RuntimeError("429")
        return [InfosCatalogue(f"{mots.upper()}{k}", f"Produit {mots}{k}", None, "Rayon", 1000 - k) for k in range(5)]

    def restrictions(self, mp, asin):
        rayon, k = asin[0], int(asin[1:])
        if rayon == "A" or (rayon == "B" and k < 2):
            return InfosRestrictions(autorise=True)
        if rayon == "C" and k == 0:
            raise RuntimeError("panne")
        return InfosRestrictions(autorise=False, approbation_requise=(k % 2 == 0))


class TestExploration(unittest.TestCase):
    def test_sondage_rayons(self):
        """Statut par rayon (ouvert / partiel / fermé / inconnu), tri par classement, une panne n'arrête rien."""
        f = Faux()
        res = EX.sonder(get_marketplace("FR"), Fournisseurs([f], None, None, f, None), attendre=lambda s: None,
                        rayons=(("A", "a"), ("B", "b"), ("C", "c"), ("D", "d")), taille=5)
        self.assertEqual([r.statut for r in res], [EX.OUVERT, EX.PARTIEL, EX.FERME, EX.INCONNU])
        self.assertEqual([p.bsr for p in res[0].produits], sorted(p.bsr for p in res[0].produits))
        b = res[1]
        self.assertEqual((b.compte(EX.AUTORISE), b.compte(EX.APPROBATION), b.compte(EX.INTERDIT)), (2, 2, 1))
        self.assertEqual(res[2].compte(EX.INCONNU), 1)
        self.assertIn("429", res[3].erreur)
        j = EX.en_json(res, "FR", datetime(2026, 11, 14, tzinfo=timezone.utc))
        self.assertEqual((j["rayons"][1]["autorises"], j["rayons"][1]["testes"]), (2, 5))

    @unittest.mock.patch.object(EX, "PAUSE_RESTRICTIONS", 0)
    @unittest.mock.patch.object(EX, "PAUSE_RECHERCHE", 0)
    def test_exploration_api(self):
        """Lancement (démo), une seule à la fois, résultat relu ; sans source : refus."""
        d, c = construire()
        from sourcing.providers.demo import FournisseurDemo
        demo = FournisseurDemo()
        cl = TestClient(creer_app(d, c, servir_interface=False, traitement_en_fond=False,
                                  fournisseurs=Fournisseurs([demo], demo, demo, demo, demo)))
        self.assertIsNone(cl.get("/api/exploration").json()["resultat"])
        self.assertEqual(cl.post("/api/exploration").status_code, 202)
        j = cl.get("/api/exploration").json()
        self.assertFalse(j["en_cours"])
        self.assertEqual(len(j["resultat"]["rayons"]), len(EX.RAYONS))
        self.assertTrue(any(r["autorises"] for r in j["resultat"]["rayons"]))
        sans = TestClient(creer_app(d, c, servir_interface=False, fournisseurs=Fournisseurs()))
        self.assertEqual(sans.post("/api/exploration").json()["detail"], "SOURCE_NON_CONFIGUREE")


if __name__ == "__main__":
    unittest.main()


class TestDeblocages(unittest.TestCase):
    def ray(self, code, statut, autorises, approbation=0, produits=()):
        return {"code": code, "statut": statut, "autorises": autorises, "approbation": approbation,
                "produits": [{"asin": a, "statut": s} for a, s in produits]}

    def test_deblocages(self):
        """[RM-AMZ-113] Statut qui s'ouvre ou autorisés en plus ; inconnu jamais compté ; produits nouvellement autorisés."""
        ancien = {"place": "FR", "le": "2026-11-13", "rayons": [
            self.ray("SPORT", "FERME", 0, 14, [("B1", "APPROBATION")]), self.ray("JOUETS", "PARTIEL", 2),
            self.ray("AUTO", "PARTIEL", 3), self.ray("BEBE", "INCONNU", 0), self.ray("CUISINE", "OUVERT", 18)]}
        nouveau = {"place": "FR", "le": "2026-11-14", "rayons": [
            self.ray("SPORT", "PARTIEL", 1, 13, [("B1", "AUTORISE")]), self.ray("JOUETS", "PARTIEL", 5),
            self.ray("AUTO", "PARTIEL", 2), self.ray("BEBE", "OUVERT", 20), self.ray("CUISINE", "OUVERT", 18)]}
        n = EX.comparer(ancien, nouveau)
        self.assertEqual((n["rayons"], n["produits"], n["depuis"]), (["SPORT", "JOUETS"], ["B1"], "2026-11-13"))
        self.assertEqual(EX.comparer(None, nouveau)["rayons"], [])                 # premier sondage : rien de « nouveau »
        self.assertEqual(EX.comparer({**ancien, "place": "DE"}, nouveau)["rayons"], [])

    def test_deblocages_vus(self):
        """[RM-AMZ-113] Annoncés sur le tableau de bord jusqu'à « vu »."""
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False))
        EX.enregistrer(d, c, {"place": "FR", "le": "2026-11-13", "rayons": [self.ray("SPORT", "FERME", 0, 14)]})
        self.assertIsNone(cl.get("/api/tableau").json()["a_faire"]["deblocages"])
        EX.enregistrer(d, c, {"place": "FR", "le": "2026-11-14", "rayons": [self.ray("SPORT", "PARTIEL", 2, 12)]})
        self.assertEqual(cl.get("/api/tableau").json()["a_faire"]["deblocages"]["rayons"], ["SPORT"])
        self.assertTrue(cl.post("/api/exploration/vu").json()["vu"])
        self.assertIsNone(cl.get("/api/tableau").json()["a_faire"]["deblocages"])
