"""Tests des règles RM-AMZ du lot 1 non couvertes par test_sourcing.py."""
import dataclasses
import unittest
from datetime import date
from decimal import Decimal

from sourcing.analyse import Fournisseurs, analyser_asin
from sourcing.depot import AccesRefuse, DepotMemoire
from sourcing.lots import (Lot, Prevision, VenteReelle, corriger_prevision, decomposer_ecart,
                           prevision_depuis_analyse, rattacher_fifo)
from sourcing.marketplaces import get_marketplace
from sourcing.money import DeviseDifferente, Montant, TauxChange, convertir
from sourcing.profit import FraisAmazon, ParametresCout, calculer_rentabilite
from sourcing.providers.base import Historique, InfosCatalogue
from sourcing.providers.demo import FournisseurDemo

FR = get_marketplace("FR")
E = lambda v: Montant.de(v, "EUR")  # noqa: E731


def vente(q, ca, frais, retours=0, stockage=0, autres=0, jour=date(2026, 10, 1), compte="c1", asin="B0X"):
    return VenteReelle(compte, asin, "FR", jour, q, E(ca), E(frais), E(retours), E(stockage), E(autres))


def lot(q, cout, jour, compte="c1", asin="B0X", prix=20, frais=7):
    return Lot(compte, asin, "FR", q, jour, Prevision.creer("EUR", prix, frais, cout))


class TestTVA(unittest.TestCase):
    def test_taux_reduit(self):
        """[RM-AMZ-003] Un taux réduit par produit remplace le taux standard du pays."""
        r = calculer_rentabilite(FR, 10.55, FraisAmazon(1.0, 2.0), ParametresCout(4.0), taux_tva_vente=0.055)
        self.assertAlmostEqual(r.prix_vente_ht, 10.0)
        self.assertAlmostEqual(r.profit_net, 3.0)
        self.assertIn(("HYP_TVA_COLLECTEE", 0.055), [(h.code, h.params.get("taux")) for h in r.hypotheses])


class TestAnalyse(unittest.TestCase):
    def setUp(self):
        d = FournisseurDemo()
        self.f = Fournisseurs([d], d, d, d, d)

    def test_scenario_prudent(self):
        """[RM-AMZ-007] Recalcul au prix moyen 90 j seulement s'il est plus bas de plus de 2 %."""
        a = analyser_asin(FR, "B0DEMO0001", ParametresCout(8.5), self.f)  # 23,50 < 24,90 × 0,98
        self.assertIsNotNone(a.rentabilite_prudente)
        self.assertAlmostEqual(a.rentabilite_prudente.prix_vente, 23.50)
        self.assertLess(a.rentabilite_prudente.profit_net, a.rentabilite.profit_net)
        a = analyser_asin(FR, "B0DEMO0001", ParametresCout(8.5), self.f, prix_vente_force=23.60)  # écart < 2 %
        self.assertIsNone(a.rentabilite_prudente)

    def test_alertes(self):
        """[RM-AMZ-009] Buy Box Amazon, Amazon en stock, pic de prix, lot, prix instable."""
        a = analyser_asin(FR, "B0DEMO0002", ParametresCout(15), self.f)
        codes = {x.code for x in a.alertes}
        self.assertTrue({"A_AMAZON_BUYBOX", "A_AMAZON_EN_STOCK"} <= codes)

        class Pic(FournisseurDemo):
            def catalogue(self, mp, asin):
                return InfosCatalogue(asin, "X", "M", "C", 1000, nb_unites_lot=6)

            def historique(self, mp, asin):
                return Historique(prix_buybox_moy90=18.0, prix_buybox_min90=15.0, prix_buybox_max90=25.0,
                                  ventes_mois_estimees=100)
        p = Pic()
        a = analyser_asin(FR, "B0DEMO0001", ParametresCout(8.5), Fournisseurs([p], p, p, p, p))
        alertes = {x.code: x.params for x in a.alertes}
        self.assertIn("A_PIC_PRIX", alertes)
        self.assertEqual(alertes["A_LOT_MULTIPLE"], {"n": 6})
        self.assertIn("A_PRIX_INSTABLE", alertes)


class TestLots(unittest.TestCase):
    def test_lot_fige(self):
        """[RM-AMZ-011] Prévision non modifiable ; une correction crée une version liée, avec motif."""
        l = lot(10, 8, date(2026, 9, 1))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            l.quantite = 20
        with self.assertRaises(dataclasses.FrozenInstanceError):
            l.prevision.cout_achat = Decimal(1)
        with self.assertRaises(ValueError):
            corriger_prevision(l, Prevision.creer("EUR", 21, 7, 8), motif=" ")
        l2 = corriger_prevision(l, Prevision.creer("EUR", 21, 7, 8), motif="erreur de saisie du prix")
        self.assertEqual((l2.version, l2.remplace), (2, l.id))
        self.assertEqual(l.prevision.prix_vente_ht, Decimal(20))  # l'original n'a pas bougé

    def test_prevision_depuis_analyse(self):
        """[RM-AMZ-011] Le profit figé égale le profit calculé à l'analyse."""
        couts = ParametresCout(8.0, envoi_entrepot=0.5, preparation=0.3, taux_retours=0.05)
        r = calculer_rentabilite(FR, 24.0, FraisAmazon(3.0, 4.0), couts)
        p = prevision_depuis_analyse(r, couts, "EUR", ["sp-api"])
        self.assertAlmostEqual(float(p.profit), r.profit_net, places=2)

    def test_fifo(self):
        """[RM-AMZ-012] Premier entré premier sorti, même compte/produit/place ; surplus non rattaché."""
        ancien, recent = lot(5, 8, date(2026, 8, 1)), lot(10, 9, date(2026, 9, 1))
        autre_compte = lot(50, 1, date(2026, 7, 1), compte="c2")
        ventes = [vente(3, 60, 21, jour=date(2026, 10, 1)), vente(4, 80, 28, jour=date(2026, 10, 2)),
                  vente(9, 180, 63, jour=date(2026, 10, 3))]
        res, orphelines = rattacher_fifo([recent, ancien, autre_compte], ventes)
        self.assertEqual(res[ancien.id].quantite_vendue, 5)        # 3 + 2
        self.assertEqual(res[recent.id].quantite_vendue, 10)       # 2 + 8
        self.assertEqual(res[autre_compte.id].quantite_vendue, 0)  # jamais mélangé
        self.assertEqual(sum(o.quantite for o in orphelines), 1)
        # vente du 02/10 répartie 2/4 sur chaque lot : 40 € de CA chacun
        self.assertEqual(res[ancien.id].chiffre_affaires, E(60 + 40))
        self.assertEqual(res[ancien.id].profit_reel, E(100 - 35 - 40))  # CA − frais − 5 × 8

    def test_fifo_ignore_versions_remplacees(self):
        """[RM-AMZ-012] Seule la dernière version d'un lot reçoit des ventes."""
        l = lot(5, 8, date(2026, 8, 1))
        l2 = corriger_prevision(l, Prevision.creer("EUR", 20, 7, 7.5), motif="remise fournisseur")
        res, _ = rattacher_fifo([l, l2], [vente(2, 40, 14)])
        self.assertNotIn(l.id, res)
        self.assertEqual(res[l2.id].quantite_vendue, 2)

    def test_decomposition_ecart(self):
        """[RM-AMZ-013] Somme des causes = profit réel − profit prévu."""
        l = Lot("c1", "B0X", "FR", 10, date(2026, 9, 1), Prevision.creer("EUR", 20, 7, 8, retours=0.2, stockage=0.1))
        res, _ = rattacher_fifo([l], [vente(10, 180, 72, retours=6, stockage=4)])
        e = decomposer_ecart(res[l.id])
        self.assertEqual(e.prix, Decimal(-20))         # 180 − 200
        self.assertEqual(e.frais_amazon, Decimal(-2))  # 70 − 72
        self.assertEqual(e.retours, Decimal(-4))       # 2 − 6
        self.assertEqual(e.stockage, Decimal(-3))      # 1 − 4
        self.assertEqual(e.total, e.profit_reel - e.profit_prevu)
        self.assertEqual(e.causes_par_ordre()[0][0], "prix")


class TestIsolation(unittest.TestCase):
    def test_isolation_comptes(self):
        """[RM-AMZ-014] Aucun accès croisé ; purge des comptes révoqués sous 30 jours."""
        d = DepotMemoire()
        a, b = lot(5, 8, date(2026, 8, 1), compte="A"), lot(5, 8, date(2026, 8, 1), compte="B")
        d.ajouter_lot("A", a)
        d.ajouter_lot("B", b)
        with self.assertRaises(AccesRefuse):
            d.ajouter_lot("A", b)
        with self.assertRaises(AccesRefuse):
            d.lot("A", b.id)
        self.assertEqual([l.id for l in d.lots("A")], [a.id])
        with self.assertRaises(AccesRefuse):
            d.ajouter_vente("A", vente(1, 20, 7, compte="B"))
        limite = d.revoquer("A", date(2026, 11, 1))
        self.assertEqual(limite, date(2026, 12, 1))
        self.assertEqual(d.purger(date(2026, 11, 2)), ["A"])
        self.assertEqual(d.lots("A"), [])
        self.assertEqual(len(d.lots("B")), 1)


class TestDevises(unittest.TestCase):
    def test_conversion_datee(self):
        """[RM-AMZ-015] Pas d'addition entre devises ; conversion avec taux daté et sourcé."""
        with self.assertRaises(DeviseDifferente):
            _ = E(10) + Montant.de(10, "USD")
        with self.assertRaises(ValueError):
            TauxChange("EUR", "USD", Decimal("1.08"), date(2026, 11, 11), source=" ")
        t = TauxChange("EUR", "USD", Decimal("1.08"), date(2026, 11, 11), source="[SOURCE À CHOISIR]")
        c = convertir(E("8.50"), t)
        self.assertEqual(c.montant, Montant.de("9.18", "USD"))
        self.assertEqual((c.origine, c.taux.jour), (E("8.50"), date(2026, 11, 11)))
        with self.assertRaises(DeviseDifferente):
            convertir(Montant.de(1, "GBP"), t)
        self.assertEqual(str(Montant.de("0.005", "EUR")), "0.01 EUR")


if __name__ == "__main__":
    unittest.main()
