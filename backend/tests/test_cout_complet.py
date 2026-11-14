"""Coût complet par unité [RM-AMZ-095 à 099]."""
import unittest
from datetime import date

from sourcing import frais_fba as FF
from sourcing.analyse import Fournisseurs, analyser_asin
from sourcing.marketplaces import get_marketplace
from sourcing.profit import FraisAmazon, ParametresCout, calculer_rentabilite
from sourcing.providers.base import InfosCatalogue, InfosOffres, InfosRestrictions
from sourcing.providers.spapi import parser_catalogue

FR, US = get_marketplace("FR"), get_marketplace("US")
NOV = date(2026, 11, 14)


class Faux:
    def __init__(self, dims=(20.0, 10.0, 5.0), poids=0.4, groupe=None, fba=4.0):
        self.cat = InfosCatalogue("B0TEST0001", "Produit", None, "Cat", 1000, dimensions_cm=dims, poids_kg=poids,
                                  groupe_affichage=groupe)
        self.fba = fba

    def catalogue(self, mp, asin):
        return self.cat

    def offres(self, mp, asin):
        return InfosOffres(30.0, False, False, 3, 0, 30.0)

    def frais(self, mp, asin, prix):
        return FraisAmazon(commission=round(prix * 0.15, 2), fba=self.fba, source="sp-api")

    def restrictions(self, mp, asin):
        return InfosRestrictions(autorise=True)


def analyse(f, mp=FR, **k):
    return analyser_asin(mp, "B0TEST0001", ParametresCout(8.0, port_fournisseur=0.5, placement=0.3, envoi_entrepot=0.4),
                         Fournisseurs([f], f, f, f, None), jour=k.pop("jour", NOV), **k)


class TestCoutComplet(unittest.TestCase):
    def test_detail_cout_complet(self):
        """[RM-AMZ-095, 098] Chaque ligne séparée ; profit = prix HT − somme des lignes ; port et placement comptés."""
        r = calculer_rentabilite(FR, 30.0, FraisAmazon(4.5, 4.0, carburant=0.08, source="sp-api"),
                                 ParametresCout(8.0, port_fournisseur=0.5, placement=0.3, envoi_entrepot=0.4,
                                                preparation=0.2, stockage_estime=0.1, taux_retours=0.01))
        d = r.detail
        self.assertEqual((d["port_fournisseur"], d["placement"], d["carburant"], d["retours"]), (0.5, 0.3, 0.08, 0.3))
        total = sum(v for k, v in d.items())
        self.assertAlmostEqual(r.profit_net, round(r.prix_vente_ht - total, 2), places=2)

    def test_gabarit(self):
        """[RM-AMZ-096] Standard : ≤ 45 × 34 × 26 cm (dans n'importe quel ordre), ≤ 11,9 kg, volumétrique ≤ 7,96 kg."""
        self.assertEqual(FF.gabarit((26, 45, 34), 11.9), "STANDARD")
        self.assertEqual(FF.gabarit((46, 10, 10), 1), FF.HORS_GABARIT)
        self.assertEqual(FF.gabarit((40, 30, 20), 12), FF.HORS_GABARIT)
        self.assertEqual(FF.gabarit((45, 34, 26), 1), "STANDARD")             # 45×34×26/5000 = 7,956 ≤ 7,96
        self.assertIsNone(FF.gabarit((10, 10, 10), None))
        self.assertIsNone(FF.gabarit(None, 1))

    def test_stockage_calcule(self):
        """[RM-AMZ-096] Volume × tarif × durée, mois par mois (oct.–déc. plus cher), catégorie selon le groupe Amazon."""
        v = 20 * 10 * 5 / 1e6                                                  # 0,001 m³
        s = FF.stockage("FR", (20.0, 10.0, 5.0), 0.4, None, date(2026, 9, 10), 2)  # sept. + oct.
        self.assertAlmostEqual(s["montant"], round(v * (27.54 + 52.20), 4))
        s = FF.stockage("FR", (20.0, 10.0, 5.0), 0.4, "apparel_display_on_website", date(2026, 12, 1), 1.5)
        self.assertAlmostEqual(s["montant"], round(v * (29.23 + 0.5 * 19.99), 4))   # déc. + ½ janv.
        self.assertEqual(FF.stockage("FR", (50.0, 40.0, 30.0), 3.0, None, NOV, 1)["categorie"], FF.HORS_GABARIT)
        self.assertIsNone(FF.stockage("UK", (20.0, 10.0, 5.0), 0.4, None, NOV, 1))  # £/ft³ : pas dans cette version
        a = analyse(Faux(), duree_stock_mois=2)
        self.assertAlmostEqual(a.rentabilite.detail["stockage"], round(v * 52.20 * 2, 2))
        self.assertIn("HYP_STOCKAGE_CALCULE", {x.code for x in a.rentabilite.hypotheses})
        # lecture des dimensions du colis dans le catalogue (pouces, livres)
        c = parser_catalogue("B0X", FR, {"dimensions": [{"marketplaceId": FR.marketplace_id, "package": {
            "length": {"unit": "inches", "value": 10}, "width": {"unit": "centimeters", "value": 5},
            "height": {"unit": "millimeters", "value": 30}, "weight": {"unit": "pounds", "value": 1}}}],
            "salesRanks": [{"marketplaceId": FR.marketplace_id, "displayGroupRanks": [
                {"websiteDisplayGroup": "apparel_display_on_website", "title": "Vêtements", "rank": 12}]}]})
        self.assertEqual((c.dimensions_cm, c.poids_kg, c.groupe_affichage),
                         ((25.4, 5.0, 3.0), 0.4536, "apparel_display_on_website"))

    def test_stockage_sans_dimensions(self):
        """[RM-AMZ-096] Sans dimensions : le stockage saisi reste, et c'est dit."""
        f = Faux(dims=None)
        a = analyser_asin(FR, "B0TEST0001", ParametresCout(8.0, stockage_estime=0.25), Fournisseurs([f], f, f, f, None),
                          duree_stock_mois=2, jour=NOV)
        self.assertEqual(a.rentabilite.detail["stockage"], 0.25)
        self.assertIn("HYP_STOCKAGE_SAISI", {x.code for x in a.rentabilite.hypotheses})

    def test_supplement_carburant(self):
        """[RM-AMZ-097] 2 % des frais FBA dès le 2/11/2026 sur les 10 sites ; retiré si « déjà inclus » ; hors champ : rien."""
        self.assertEqual(FF.taux_carburant("FR", date(2026, 11, 2)), 0.02)
        self.assertIsNone(FF.taux_carburant("FR", date(2026, 11, 1)))
        self.assertIsNone(FF.taux_carburant("US", NOV))
        a = analyse(Faux(fba=4.0))
        self.assertEqual(a.rentabilite.detail["carburant"], 0.08)
        self.assertIn("HYP_CARBURANT", {x.code for x in a.rentabilite.hypotheses})
        b = analyse(Faux(fba=4.0), carburant_inclus=True)
        self.assertEqual(b.rentabilite.detail["carburant"], 0.0)
        self.assertIn("HYP_CARBURANT_INCLUS", {x.code for x in b.rentabilite.hypotheses})
        self.assertAlmostEqual(b.rentabilite.profit_net - a.rentabilite.profit_net, 0.08, places=2)

    def test_frais_non_inclus_signales(self):
        """[RM-AMZ-099] Faible stock, retours au-delà du seuil, stock ancien : toujours signalés en zone euro."""
        a = analyse(Faux(), duree_stock_mois=1)
        self.assertIn("HYP_FRAIS_NON_INCLUS", {x.code for x in a.rentabilite.hypotheses})


if __name__ == "__main__":
    unittest.main()
