"""Tests de l'API de l'écran « Achats & lots » [RM-AMZ-024, 025, 026, D-AMZ-017]."""
import os
import re
import unittest
from datetime import date
from decimal import Decimal
from unittest import mock

from fastapi.testclient import TestClient

from sourcing import api
from sourcing.demo_donnees import construire
from sourcing.depot import DepotMemoire
from sourcing.lots import Lot, Prevision, VenteReelle
from sourcing.money import Montant

C = "00000000-0000-4000-8000-0000000000aa"
E = lambda v: Montant.de(v, "EUR")  # noqa: E731


def client(depot, compte=C):
    return TestClient(api.creer_app(depot, compte, servir_interface=False))


class TestApi(unittest.TestCase):
    def test_api_statut_lot(self):
        """[RM-AMZ-024] EN_VENTE tant qu'il reste des unités, ECOULE ensuite."""
        d = DepotMemoire()
        l = Lot(C, "B0X", "FR", 2, date(2026, 9, 1), Prevision.creer("EUR", 20, 7, 8), designation="X")
        d.ajouter_lot(C, l)
        d.ajouter_vente(C, VenteReelle(C, "B0X", "FR", date(2026, 10, 1), 1, E(20), E(7), E(0), E(0), E(0)), "a")
        self.assertEqual(client(d).get("/api/lots").json()["lots"][0]["statut"], "EN_VENTE")
        d.ajouter_vente(C, VenteReelle(C, "B0X", "FR", date(2026, 10, 2), 1, E(20), E(7), E(0), E(0), E(0)), "b")
        self.assertEqual(client(d).get("/api/lots").json()["lots"][0]["statut"], "ECOULE")

    def test_api_detail_lot(self):
        """[RM-AMZ-025] Comparaison par unité vendue ; écart des causes = profit réel − prévu ; lot entier à part."""
        d = DepotMemoire()
        l = Lot(C, "B0X", "FR", 10, date(2026, 9, 1), Prevision.creer("EUR", 20, 7, 8, retours=0.5))
        d.ajouter_lot(C, l)
        for i in range(4):
            d.ajouter_vente(C, VenteReelle(C, "B0X", "FR", date(2026, 10, 1 + i), 1, E(18), E(7.5), E(0), E(0), E(0)),
                            f"v{i}")
        j = client(d).get(f"/api/lots/{l.id}").json()
        lignes = {x["poste"]: x for x in j["comparatif"]}
        self.assertEqual((lignes["PRIX_VENTE_HT"]["prevu"], lignes["PRIX_VENTE_HT"]["reel"]), ("20.00", "18.00"))
        self.assertEqual(lignes["PRIX_VENTE_HT"]["ecart"], "-2.00")
        self.assertEqual(lignes["FRAIS_AMAZON"]["ecart"], "-0.50")      # plus de frais = moins bien
        self.assertEqual(lignes["RETOURS"]["ecart"], "0.50")            # moins de retours = mieux
        self.assertEqual(j["profit_prevu"], "18.00")                    # 4,5 × 4 unités vendues
        self.assertEqual(j["profit_prevu_lot_entier"], "45.00")         # 4,5 × 10
        somme = sum(Decimal(c["montant"]) for c in j["causes"])
        self.assertEqual(somme, Decimal(j["profit_reel"]) - Decimal(j["profit_prevu"]))
        self.assertEqual(Decimal(j["ecart"]), somme)

    def test_api_codes_sans_texte(self):
        """[RM-AMZ-026] Statuts, postes et causes sont des codes ; montants en chaînes décimales avec devise."""
        d, c = construire()
        cl = client(d, c)
        lots = cl.get("/api/lots").json()["lots"]
        self.assertEqual(len(lots), 4)
        code = re.compile(r"^[A-Z_]+$")
        for l in lots:
            self.assertRegex(l["statut"], code)
            self.assertEqual(l["devise"], "EUR")
            self.assertRegex(l["profit_reel"], r"^-?\d+\.\d{2}$")
            det = cl.get(f"/api/lots/{l['id']}").json()
            for x in det["comparatif"]:
                self.assertRegex(x["poste"], code)
            for x in det["causes"]:
                self.assertRegex(x["cause"], code)

    def test_api_lot_autre_compte_introuvable(self):
        """[RM-AMZ-014] Un lot d'un autre compte répond « introuvable », sans révéler qu'il existe."""
        d = DepotMemoire()
        autre = Lot("autre", "B0X", "FR", 1, date(2026, 9, 1), Prevision.creer("EUR", 1, 1, 1))
        d.ajouter_lot("autre", autre)
        r = client(d).get(f"/api/lots/{autre.id}")
        self.assertEqual((r.status_code, r.json()["detail"]), (404, "LOT_INTROUVABLE"))

    def test_refus_hors_mode_dev(self):
        """[D-AMZ-017] Sans authentification, l'application refuse de démarrer hors AMZ_MODE=dev."""
        with mock.patch.dict(os.environ, {"AMZ_MODE": "production"}):
            with self.assertRaises(SystemExit):
                api.app_depuis_environnement()


if __name__ == "__main__":
    unittest.main()
