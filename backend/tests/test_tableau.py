"""Tableau de bord [RM-AMZ-091 à 094]."""
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from sourcing import tableau as TB
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.historique import Releve
from sourcing.lots import Lot, Prevision, VenteReelle
from sourcing.money import Montant
from sourcing.remboursements import Cas
from sourcing.stock import LigneStock, PhotoStock
from sourcing.synchro_nuit import ResultatTache

C = "00000000-0000-4000-8000-0000000000d1"
J = date(2026, 11, 14)


def vente(jour, q=1, ca=20, frais=5, dev="EUR", asin="B0X"):
    M = lambda v: Montant.de(v, dev)  # noqa: E731
    return VenteReelle(C, asin, "FR", jour, q, M(ca), M(frais), M(0), M(0), M(0))


def ligne(dispo, route, cout, dev="EUR", a_commander=0):
    return LigneStock(PhotoStock("FR", "S", "B0X", None, dispo, route), 0, Decimal(0), None, None, a_commander, None,
                      None if cout is None else Decimal(str(cout)), dev)


class TestTableau(unittest.TestCase):
    def test_tableau_chiffres(self):
        """[RM-AMZ-091] Ventes 30 j, variation, profit réel (FIFO), ROI réel, stock ; non rattachées à part."""
        lots = [Lot(C, "B0X", "FR", 3, date(2026, 9, 1), Prevision.creer("EUR", 20, 5, 8))]
        ventes = [vente(J), vente(J - timedelta(days=29), q=2, ca=40, frais=10),       # dans la fenêtre
                  vente(J - timedelta(days=30), q=1, ca=10, frais=0),                  # période précédente (lot épuisé)
                  vente(J - timedelta(days=5), asin="B0Y")]                            # non rattachée
        # FIFO : la vente la plus ancienne (J-30) consomme 1 unité, puis J-29 (2) ; J n'a plus de lot
        ch = TB.chiffres(lots, ventes, [ligne(4, 1, 8), ligne(2, 0, None)], J)
        e = ch["par_devise"]["EUR"]
        self.assertEqual(e["ventes"], Decimal(80))                                       # 20 + 40 + 20 (B0Y)
        self.assertEqual(e["variation_ventes"], Decimal(7))                              # (80 − 10) / 10
        self.assertEqual(e["profit"], Decimal(40 - 10 - 16))                            # J-29 seulement : 30 − 16
        self.assertEqual(e["roi"], Decimal(14) / Decimal(16))
        self.assertEqual(e["stock"], Decimal(40))                                        # (4 + 1) × 8
        self.assertEqual((ch["ventes_non_rattachees"], ch["unites_sans_cout"]), (2, 2))  # J et B0Y ; 2 unités

    def test_tableau_devises_separees(self):
        """[RM-AMZ-091] Aucune addition entre devises ; EUR principale ; sans période précédente : pas de variation."""
        ch = TB.chiffres([], [vente(J, dev="GBP", ca=15), vente(J, ca=20)], [], J)
        self.assertEqual(set(ch["par_devise"]), {"EUR", "GBP"})
        self.assertEqual((ch["par_devise"]["GBP"]["ventes"], ch["par_devise"]["EUR"]["ventes"]), (Decimal(15), Decimal(20)))
        self.assertIsNone(ch["par_devise"]["EUR"]["variation_ventes"])
        self.assertIsNone(ch["par_devise"]["EUR"]["roi"])
        self.assertEqual(ch["devise"], "EUR")
        self.assertEqual(TB.devise_principale(["USD", "GBP"]), "GBP")
        self.assertIsNone(TB.devise_principale([]))

    def test_tableau_serie(self):
        """[RM-AMZ-092] 30 jours, du plus ancien au plus récent, zéros les jours sans vente."""
        lots = [Lot(C, "B0X", "FR", 10, date(2026, 9, 1), Prevision.creer("EUR", 20, 5, 8))]
        ch = TB.chiffres(lots, [vente(J - timedelta(days=3)), vente(J - timedelta(days=3))], [], J)
        s = ch["serie"]
        self.assertEqual((len(s), s[0]["jour"], s[-1]["jour"]), (30, "2026-10-16", "2026-11-14"))
        self.assertEqual(s[-4]["profit"], Decimal(14))                                   # 2 × (15 − 8)
        self.assertEqual(sum(x["profit"] for x in s), Decimal(14))
        self.assertEqual(TB.chiffres([], [], [], J)["serie"], [])

    def test_tableau_a_faire(self):
        """[RM-AMZ-093] Recommandes, remboursements détectés (valeur), conformité, synchro (échecs nommés)."""
        cas = [Cas("k1", "PERDU", "FR", "B0X", None, None, None, 1, Decimal("5.5"), "EUR", J, None),
               Cas("k2", "PERDU", "FR", "B0X", None, None, None, 1, Decimal("2"), "EUR", J, None, statut="CLOS")]
        conf = [type("L", (), {"statut": "A_COMPLETER"})(), type("L", (), {"statut": "RIEN_DE_SIGNALE"})()]
        t = lambda h: datetime(2026, 11, 14, h, tzinfo=timezone.utc)  # noqa: E731
        journal = [ResultatTache("VENTES", t(3), t(3), False, "x"), ResultatTache("VENTES", t(4), t(4), True),
                   ResultatTache("STOCK", t(4), t(4), False, "403")]
        af = TB.a_faire([ligne(1, 0, 8, a_commander=3), ligne(1, 0, 8)], cas, conf, journal)
        self.assertEqual((af["recommander"], af["remboursements"], af["conformite"]), (1, 1, 1))
        self.assertEqual(af["valeur_remboursements"], {"EUR": Decimal("5.5")})
        self.assertEqual(af["synchro"]["echecs"], ["STOCK"])
        self.assertIsNone(TB.a_faire([], [], [], [])["synchro"])

    def test_tableau_mouvements(self):
        """[RM-AMZ-094] 5 plus fortes variations absolues sur 7 jours, ≥ 2 relevés ; API complète."""
        rel = []
        for k in range(7):
            rel += [Releve("FR", f"B0{k}", J - timedelta(days=6), Decimal(10)), Releve("FR", f"B0{k}", J, Decimal(10 + k - 3))]
        rel.append(Releve("FR", "SEUL", J, Decimal(5)))
        mv = TB.mouvements(rel, J)
        self.assertEqual([m["asin"] for m in mv], ["B00", "B06", "B01", "B05", "B02"])
        d, c = construire()
        j = TestClient(creer_app(d, c, servir_interface=False)).get("/api/tableau").json()
        self.assertEqual(j["devise"], "EUR")
        self.assertEqual(len(j["serie"]), 30)
        self.assertIn("recommander", j["a_faire"])


if __name__ == "__main__":
    unittest.main()
