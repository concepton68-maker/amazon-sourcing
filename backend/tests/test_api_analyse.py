"""Écran « Analyse produit » : API et messages codés [RM-AMZ-027, 028, 029]."""
import json
import pathlib
import re
import unittest

from fastapi.testclient import TestClient

from sourcing import messages
from sourcing.analyse import PASSER, Fournisseurs, analyser_asin
from sourcing.api import creer_app
from sourcing.depot import DepotMemoire
from sourcing.marketplaces import get_marketplace
from sourcing.profit import ParametresCout
from sourcing.providers.demo import FournisseurDemo

C = "00000000-0000-4000-8000-0000000000bb"
FR_JSON = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "src" / "i18n" / "fr.json"


def demo():
    d = FournisseurDemo()
    return Fournisseurs([d], d, d, d, d)


def client(depot=None):
    return TestClient(creer_app(depot or DepotMemoire(), C, servir_interface=False, fournisseurs=demo()))


def codes_emis() -> set[str]:
    """Tous les codes de message présents dans le code Python (m("CODE", ...))."""
    racine = pathlib.Path(__file__).resolve().parents[1] / "sourcing"
    out = set()
    for f in racine.rglob("*.py"):
        out |= set(re.findall(r'\bm\(\s*"([A-Z_]+)"', f.read_text(encoding="utf-8")))
        out |= set(re.findall(r'"(R_(?:APPROBATION_REQUISE|VENTE_NON_AUTORISEE))"', f.read_text(encoding="utf-8")))
    return out


class TestMessages(unittest.TestCase):
    def test_messages_codes(self):
        """[RM-AMZ-027] Tout code émis a sa traduction, pour la ligne de commande ET pour l'interface."""
        emis = codes_emis()
        self.assertGreater(len(emis), 20)
        fr_web = json.loads(FR_JSON.read_text(encoding="utf-8"))
        for code in sorted(emis):
            with self.subTest(code=code):
                self.assertIn(code, messages.FR)
                self.assertIn(f"msg.{code}", fr_web)
        r = analyser_asin(get_marketplace("FR"), "B0DEMO0001", ParametresCout(8.5), demo())
        for x in r.raisons + r.alertes + r.non_verifie + r.rentabilite.hypotheses:
            self.assertRegex(x.code, r"^[A-Z_]+$")
            self.assertNotIn(x.code, messages.texte_fr(x))   # se traduit sans retomber sur le code

    def test_verdict_sur_codes(self):
        """[RM-AMZ-027] Le verdict découle des codes : approbation requise → PASSER."""
        r = analyser_asin(get_marketplace("FR"), "B0DEMO0002", ParametresCout(15), demo())
        self.assertEqual(r.verdict, PASSER)
        self.assertIn("R_APPROBATION_REQUISE", {x.code for x in r.raisons})


class TestApiAnalyse(unittest.TestCase):
    def test_api_analyse(self):
        """[RM-AMZ-028] EAN → analyse complète, montants et messages codés."""
        j = client().post("/api/analyse", json={"code": "3700000000017", "marketplace": "FR", "prix_achat": 8.5})
        self.assertEqual(j.status_code, 200)
        (a,) = j.json()["analyses"]
        self.assertEqual((a["asin"], a["verdict"], a["devise"], a["origine_prix"]), ("B0DEMO0001", "ACHETER", "EUR", "BUYBOX"))
        self.assertAlmostEqual(a["rentabilite"]["profit"], 4.36)
        self.assertAlmostEqual(a["rentabilite"]["prix_achat_max"], 9.89)
        self.assertEqual(a["raisons"][0]["code"], "R_TOUT_OK")
        self.assertTrue(a["jeton_analyse"])

    def test_api_analyse_introuvable(self):
        """[RM-AMZ-028] Code inconnu : « introuvable », jamais une analyse inventée ; entrées invalides refusées."""
        cl = client()
        r = cl.post("/api/analyse", json={"code": "0000000000000", "marketplace": "FR", "prix_achat": 8})
        self.assertEqual((r.status_code, r.json()["detail"]), (404, "PRODUIT_INTROUVABLE"))
        self.assertEqual(cl.post("/api/analyse", json={"code": "x", "marketplace": "ZZ", "prix_achat": 8}).json()["detail"],
                         "PLACE_INCONNUE")
        self.assertEqual(cl.post("/api/analyse", json={"code": "x", "prix_achat": 0}).status_code, 422)

    def test_api_creer_lot_depuis_analyse(self):
        """[RM-AMZ-029] Lot créé avec la prévision de l'analyse gardée côté serveur ; quantité > 0."""
        d = DepotMemoire()
        cl = client(d)
        a = cl.post("/api/analyse", json={"code": "B0DEMO0001", "prix_achat": 8.5}).json()["analyses"][0]
        self.assertEqual(cl.post("/api/lots", json={"jeton_analyse": a["jeton_analyse"], "quantite": 0}).status_code, 422)
        self.assertEqual(cl.post("/api/lots", json={"jeton_analyse": "inconnu", "quantite": 5}).json()["detail"],
                         "ANALYSE_EXPIREE")
        r = cl.post("/api/lots", json={"jeton_analyse": a["jeton_analyse"], "quantite": 30, "fournisseur": "Grossiste A",
                                       "prevision": {"cout_achat": 0.01}})   # chiffres du navigateur ignorés
        self.assertEqual(r.status_code, 201)
        (lot,) = d.lots(C)
        self.assertEqual((lot.quantite, lot.fournisseur, lot.designation), (30, "Grossiste A", "Gourde inox 750 ml (démo)"))
        self.assertAlmostEqual(float(lot.prevision.cout_achat), 8.5)
        self.assertAlmostEqual(float(lot.prevision.profit), a["rentabilite"]["profit"], places=2)
        again = cl.post("/api/lots", json={"jeton_analyse": a["jeton_analyse"], "quantite": 30})
        self.assertEqual((again.status_code, again.json()["detail"]), (409, "ANALYSE_DEJA_UTILISEE"))
        self.assertEqual(len(d.lots(C)), 1)
        liste = cl.get("/api/lots").json()["lots"]
        self.assertEqual(liste[0]["id"], r.json()["id"])


if __name__ == "__main__":
    unittest.main()
