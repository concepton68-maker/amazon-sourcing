"""Liste des produits rentables [RM-AMZ-105 à 108]."""
import io
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from sourcing import opportunites as OP
from sourcing.analyse import Fournisseurs
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.historique import Releve, jour_paris
from sourcing.providers.base import InfosRestrictions
from sourcing.providers.demo import FournisseurDemo

CSV = "EAN;Libellé;Prix HT\n3700000000017;Gourde;8,50\n3700000000024;Jouet;15,00\n2000000000017;Boîte;3,20\n"


def client():
    d, c = construire()
    demo = FournisseurDemo()
    return d, c, TestClient(creer_app(d, c, servir_interface=False, traitement_en_fond=False,
                                      fournisseurs=Fournisseurs([demo], demo, demo, demo, demo)))


def charger(cl, nom="Grossiste O", texte=CSV):
    fid = cl.post("/api/fournisseurs", json={"nom": nom}).json()["id"]
    f = cl.post(f"/api/fournisseurs/{fid}/fichier", files={"fichier": ("t.csv", io.BytesIO(texte.encode()), "text/csv")}).json()
    cl.post(f"/api/fournisseurs/{fid}/catalogue", json={"fichier_id": f["fichier_id"], "colonnes": f["colonnes"]})
    cl.post(f"/api/fournisseurs/{fid}/analyse", json={})
    return fid


def op(asin, **k):
    return OP.Opportunite("FOURNISSEUR:x", "X", "FR", asin, asin, **k)


class TestOpportunites(unittest.TestCase):
    def test_vendabilite(self):
        """[RM-AMZ-106] « Sûr » seulement sur réponse d'Amazon pour le produit ; sinon inconnu."""
        self.assertEqual(OP.vendabilite(InfosRestrictions(autorise=True)), (OP.VENDABLE, None))
        self.assertEqual(OP.vendabilite(InfosRestrictions(autorise=False, approbation_requise=True)),
                         (OP.NON_VENDABLE, "APPROBATION"))
        self.assertEqual(OP.vendabilite(InfosRestrictions(autorise=False)), (OP.NON_VENDABLE, "INTERDIT"))
        self.assertEqual(OP.vendabilite(None), (OP.INCONNU, None))
        self.assertEqual(OP.vendabilite(InfosRestrictions(autorise=None)), (OP.INCONNU, None))

    def test_opportunites_gardees(self):
        """[RM-AMZ-105] L'analyse d'un catalogue alimente la liste (profit, ROI, marge, achat max, vendabilité)."""
        d, c, cl = client()
        charger(cl)
        j = cl.get("/api/opportunites").json()
        self.assertEqual(j["total"], 3)
        g = [p for p in j["produits"] if p["asin"] == "B0DEMO0001"][0]
        self.assertEqual((g["vendabilite"], g["verdict"], g["origine_nom"]), ("VENDABLE", "ACHETER", "Grossiste O"))
        self.assertIsNotNone(g["marge"])
        self.assertIsNotNone(g["prix_achat_max"])
        jouet = [p for p in j["produits"] if p["asin"] == "B0DEMO0002"][0]
        self.assertEqual((jouet["vendabilite"], jouet["motif"]), ("NON_VENDABLE", "APPROBATION"))

    def test_opportunites_remplacees(self):
        """[RM-AMZ-105] Nouvelle analyse de la même origine : remplace ; autre origine : s'ajoute."""
        d, c, cl = client()
        fid = charger(cl)
        f = cl.post(f"/api/fournisseurs/{fid}/fichier", files={"fichier": ("t.csv", io.BytesIO(
            "EAN;Prix HT\n3700000000017;8,50\n".encode()), "text/csv")}).json()
        cl.post(f"/api/fournisseurs/{fid}/catalogue", json={"fichier_id": f["fichier_id"], "colonnes": f["colonnes"]})
        cl.post(f"/api/fournisseurs/{fid}/analyse", json={})
        self.assertEqual(cl.get("/api/opportunites").json()["total"], 1)
        charger(cl, "Grossiste P2")
        j = cl.get("/api/opportunites").json()
        self.assertEqual((j["total"], len(j["origines"])), (4, 2))

    def test_tri_filtres(self):
        """[RM-AMZ-107] Tri dans les deux sens, valeurs absentes en dernier ; filtres cumulés ; rien caché par défaut."""
        ops = [op("A", profit=5.0, roi=0.5, marge=0.2, vendabilite=OP.VENDABLE, amazon_vend=False, verdict="ACHETER"),
               op("B", profit=9.0, roi=0.2, marge=0.3, vendabilite=OP.NON_VENDABLE, amazon_vend=True, verdict="PASSER"),
               op("C", profit=None, roi=None, vendabilite=OP.INCONNU),
               op("D", profit=1.0, roi=0.9, marge=0.1, vendabilite=OP.VENDABLE, amazon_vend=None)]
        self.assertEqual([o.asin for o in OP.filtrer_trier(ops, OP.Criteres())], ["B", "A", "D", "C"])
        self.assertEqual([o.asin for o in OP.filtrer_trier(ops, OP.Criteres("roi", False))], ["B", "A", "D", "C"])
        self.assertEqual([o.asin for o in OP.filtrer_trier(ops, OP.Criteres("roi"))], ["D", "A", "B", "C"])
        c = OP.Criteres(vendabilites={OP.VENDABLE}, roi_min=0.3)
        self.assertEqual([o.asin for o in OP.filtrer_trier(ops, c)], ["A", "D"])
        self.assertEqual([o.asin for o in OP.filtrer_trier(ops, OP.Criteres(amazon_absent=True))], ["A"])   # inconnu exclu
        self.assertEqual([o.asin for o in OP.filtrer_trier(ops, OP.Criteres(marge_min=0.15))], ["B", "A"])
        with self.assertRaises(ValueError):
            OP.filtrer_trier(ops, OP.Criteres("couleur"))
        d, c2, cl = client()
        charger(cl)
        j = cl.get("/api/opportunites?vendabilite=VENDABLE&tri=roi&ordre=desc").json()
        self.assertTrue(all(p["vendabilite"] == "VENDABLE" for p in j["produits"]))
        self.assertEqual(cl.get("/api/opportunites?vendabilite=PEUT_ETRE").status_code, 422)
        self.assertEqual(cl.get("/api/opportunites?tri=couleur").status_code, 422)

    def test_rotation_opportunites(self):
        """[RM-AMZ-108] Rotation affichée seulement avec au moins 7 relevés."""
        d, c, cl = client()
        charger(cl)
        jour = jour_paris(datetime.now(timezone.utc))
        d.enregistrer_releves(c, [Releve("FR", "B0DEMO0001", jour - timedelta(days=k), Decimal("24.9"),
                                         bsr=1000 + (50 if k % 2 else 0)) for k in range(10)])
        j = cl.get("/api/opportunites").json()
        g = [p for p in j["produits"] if p["asin"] == "B0DEMO0001"][0]
        self.assertFalse(g["historique_court"])
        self.assertEqual(g["rotation"], 5)
        autre = [p for p in j["produits"] if p["asin"] == "B0DEMO0002"][0]
        self.assertTrue(autre["historique_court"])
        self.assertIsNone(autre["rotation"])


if __name__ == "__main__":
    unittest.main()
