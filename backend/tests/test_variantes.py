"""Produit parent à variantes [RM-AMZ-082]."""
import unittest
from dataclasses import replace

from sourcing.analyse import ACHETER, Fournisseurs, analyser_asin
from sourcing.marketplaces import get_marketplace
from sourcing.profit import ParametresCout
from sourcing.providers.demo import FournisseurDemo
from sourcing.providers.spapi import parser_catalogue


class Parent(FournisseurDemo):
    def catalogue(self, mp, asin):
        return replace(super().catalogue(mp, asin), classification="VARIATION_PARENT", nb_variantes=7)


class TestVariantes(unittest.TestCase):
    def test_asin_parent(self):
        """Catalogue → classification et nombre de variantes ; l'analyse le signale et ne dit jamais « Acheter »."""
        fr = get_marketplace("FR")
        info = parser_catalogue("B0P", fr, {
            "summaries": [{"marketplaceId": fr.marketplace_id, "itemName": "Boxer", "itemClassification": "VARIATION_PARENT"}],
            "relationships": [{"marketplaceId": fr.marketplace_id, "relationships": [
                {"type": "VARIATION", "childAsins": ["B0C1", "B0C2", "B0C3"]}]}]})
        self.assertEqual((info.classification, info.nb_variantes), ("VARIATION_PARENT", 3))
        normal = analyser_asin(fr, "B0DEMO0001", ParametresCout(8.5), Fournisseurs([FournisseurDemo()], *[FournisseurDemo()] * 4))
        self.assertEqual(normal.verdict, ACHETER)
        d = Parent()
        r = analyser_asin(fr, "B0DEMO0001", ParametresCout(8.5), Fournisseurs([d], d, d, d, d))
        self.assertIn("A_ASIN_PARENT", [a.code for a in r.alertes])
        self.assertEqual(next(a for a in r.alertes if a.code == "A_ASIN_PARENT").params["n"], 7)
        self.assertNotEqual(r.verdict, ACHETER)


if __name__ == "__main__":
    unittest.main()
