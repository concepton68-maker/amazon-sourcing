"""Paramètres du compte [RM-AMZ-042, 043, 044]."""
import unittest

from fastapi.testclient import TestClient

from sourcing.analyse import Fournisseurs
from sourcing.api import creer_app
from sourcing.depot import DepotMemoire
from sourcing.parametres import ParametreInvalide, Parametres, valider
from sourcing.providers.demo import FournisseurDemo

C = "00000000-0000-4000-8000-0000000000dd"


def client():
    d = FournisseurDemo()
    depot = DepotMemoire()
    return TestClient(creer_app(depot, C, servir_interface=False, fournisseurs=Fournisseurs([d], d, d, d, d),
                                traitement_en_fond=False)), depot


class TestParametres(unittest.TestCase):
    def test_parametres_bornes_et_defauts(self):
        """[RM-AMZ-042] Défauts de l'outil ; champ inconnu, type faux, hors bornes : refusés avec le champ."""
        p = valider({})
        self.assertEqual((p.roi_min, p.profit_min, p.regime("FR"), p.regime("US")), (0.30, 3.0, "assujetti", "hors_taxe"))
        self.assertEqual(valider({"tva": {"US": "assujetti"}}).regime("US"), "hors_taxe")   # place HT : toujours HT
        for brut, code, champ in [({"inconnu": 1}, "PARAMETRE_INCONNU", "inconnu"),
                                  ({"roi_min": "30"}, "PARAMETRE_INVALIDE", "roi_min"),
                                  ({"roi_min": True}, "PARAMETRE_INVALIDE", "roi_min"),
                                  ({"retours": 1.5}, "PARAMETRE_HORS_BORNES", "retours"),
                                  ({"profit_min": -1}, "PARAMETRE_HORS_BORNES", "profit_min"),
                                  ({"tva": {"FR": "autre"}}, "REGIME_TVA_INCONNU", "tva.FR"),
                                  ({"tva": {"ZZ": "assujetti"}}, "PLACE_INCONNUE", "tva.ZZ")]:
            with self.subTest(brut=brut), self.assertRaises(ParametreInvalide) as e:
                valider(brut)
            self.assertEqual(e.exception.args, (code, champ))
        cl, _ = client()
        r = cl.put("/api/parametres", json={"retours": 2})
        self.assertEqual((r.status_code, r.json()["detail"]), (422, {"code": "PARAMETRE_HORS_BORNES", "champ": "retours"}))
        self.assertEqual(cl.get("/api/parametres").json()["roi_min"], 0.30)

    def test_parametres_versions(self):
        """[RM-AMZ-043] Chaque enregistrement ajoute une version ; les anciennes restent intactes."""
        cl, depot = client()
        cl.put("/api/parametres", json={"roi_min": 0.4})
        r = cl.put("/api/parametres", json={"roi_min": 0.5, "tva": {"DE": "non_assujetti"}}).json()
        self.assertEqual((r["versions"], r["roi_min"], r["tva"]["DE"], r["tva"]["FR"]), (2, 0.5, "non_assujetti", "assujetti"))
        v = depot.versions_parametres(C)
        self.assertEqual([x[1]["roi_min"] for x in v], [0.4, 0.5])

    def test_parametres_appliques_a_l_analyse(self):
        """[RM-AMZ-044] Seuils, coûts et régime du compte appliqués ; le formulaire prime pour une analyse."""
        cl, _ = client()
        avant = cl.post("/api/analyse", json={"code": "B0DEMO0001", "prix_achat": 8.5}).json()["analyses"][0]
        self.assertEqual(avant["verdict"], "ACHETER")
        cl.put("/api/parametres", json={"roi_min": 0.6, "envoi": 1.0, "tva": {"FR": "non_assujetti"}})
        apres = cl.post("/api/analyse", json={"code": "B0DEMO0001", "prix_achat": 8.5}).json()["analyses"][0]
        self.assertEqual(apres["rentabilite"]["regime_tva"], "non_assujetti")
        self.assertIn("R_ROI_SOUS_SEUIL", [m["code"] for m in apres["raisons"]])
        self.assertAlmostEqual(apres["rentabilite"]["autres"], 1.0)
        force = cl.post("/api/analyse", json={"code": "B0DEMO0001", "prix_achat": 8.5, "regime_tva": "assujetti"}).json()
        self.assertEqual(force["analyses"][0]["rentabilite"]["regime_tva"], "assujetti")
        f = cl.post("/api/sourcing/fichiers", files={"fichier": ("f.csv", b"EAN;Prix\n3700000000017;8,5\n", "text/csv")}).json()
        tid = cl.post(f"/api/sourcing/fichiers/{f['fichier_id']}/traitements", json={"colonnes": f["colonnes"]}).json()["traitement_id"]
        (ligne,) = cl.get(f"/api/sourcing/traitements/{tid}").json()["resultats"]
        self.assertIn("R_ROI_SOUS_SEUIL", [m["code"] for m in ligne["raisons"]])   # le sourcing suit aussi les seuils


if __name__ == "__main__":
    unittest.main()
