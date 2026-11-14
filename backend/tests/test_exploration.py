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
