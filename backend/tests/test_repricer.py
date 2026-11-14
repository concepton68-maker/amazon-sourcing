"""Prix plancher et repricer d'Amazon [RM-AMZ-122 à 124]."""
import unittest
from decimal import Decimal

from sourcing import repricer as RP
from sourcing.analyse import Fournisseurs, analyser_asin
from sourcing.marketplaces import get_marketplace
from sourcing.parametres import Parametres
from sourcing.prix_plancher import prix_plancher
from sourcing.profit import FraisAmazon, ParametresCout, calculer_rentabilite
from sourcing.providers.demo import FournisseurDemo
from sourcing.providers.spapi import parser_offre_vendeur, regles_depuis_schema
from sourcing.stock import LigneStock, PhotoStock

FR = get_marketplace("FR")
RIEN = lambda s: None  # noqa: E731


class Vendeur(FournisseurDemo):
    """Client simulé : une offre en ligne par SKU, deux règles de prix, PATCH enregistré."""
    def __init__(self, prix=24.9):
        self.patches, self.prix = [], prix

    def lire_offre(self, mp, sku):
        return {"type_produit": "BOTTLE", "prix": self.prix, "minimum": None, "maximum": None, "regle": None,
                "offre": {"marketplace_id": mp.marketplace_id, "currency": "EUR", "audience": "ALL",
                          "our_price": [{"schedule": [{"value_with_tax": self.prix}]}]}}

    def regles_prix(self, mp, type_produit):
        return [{"id": "1-CROSSBORDER_PRICING", "nom": "Global"}, {"id": "2-COMPETITIVE_BUYBOX", "nom": "Competitive"}]

    def remplacer_offre(self, mp, sku, type_produit, offre):
        self.patches.append((sku, type_produit, offre))
        return {"status": "ACCEPTED", "issues": []}


class TestRepricer(unittest.TestCase):
    def test_prix_plancher(self):
        """[RM-AMZ-122] Plus bas prix qui garde le profit minimum ; au plancher, profit ≈ minimum ; inatteignable : None."""
        frais = FraisAmazon(commission=3.74, fba=4.15, source="sp-api")
        couts = ParametresCout(8.5)
        p = prix_plancher(FR, 24.9, frais, couts, "assujetti", 3.0)
        prof = lambda x: calculer_rentabilite(FR, x, FraisAmazon(3.74 / 24.9 * x, 4.15, source="sp-api"), couts).profit_net  # noqa: E731
        self.assertGreaterEqual(prof(p), 2.995)
        self.assertLess(prof(p - 0.02), 3.0)
        self.assertIsNone(prix_plancher(FR, 24.9, frais, ParametresCout(500), "assujetti", 3.0))
        f = FournisseurDemo()
        a = analyser_asin(FR, "B0DEMO0001", ParametresCout(8.5), Fournisseurs([f], f, f, f, f))
        self.assertIsNotNone(a.prix_plancher)
        self.assertLess(a.prix_plancher, 24.9)

    def test_regles_prix_vendeur(self):
        """[RM-AMZ-123] Règles lues dans le schéma du type de produit ; offre du vendeur lue (prix, min, max, règle)."""
        schema = {"properties": {"purchasable_offer": {"items": {"properties": {"automated_pricing_merchandising_rule_plan": {
            "items": {"properties": {"merchandising_rule": {"properties": {"rule_id": {
                "enum": ["328182282407-COMPETITIVE_BUYBOX", "abc"], "enumNames": ["Competitive Price Rule by Amazon", "Ma règle"]}}}}}}}}}}}
        self.assertEqual(regles_depuis_schema(schema), [{"id": "328182282407-COMPETITIVE_BUYBOX", "nom": "Competitive Price Rule by Amazon"},
                                                        {"id": "abc", "nom": "Ma règle"}])
        self.assertEqual(regles_depuis_schema({"properties": {}}), [])
        o = parser_offre_vendeur(FR, {"summaries": [{"marketplaceId": FR.marketplace_id, "productType": "BOTTLE"}],
                                      "attributes": {"purchasable_offer": [{"marketplace_id": FR.marketplace_id,
                                          "our_price": [{"schedule": [{"value_with_tax": 24.9}]}],
                                          "minimum_seller_allowed_price": [{"schedule": [{"value_with_tax": 18}]}],
                                          "automated_pricing_merchandising_rule_plan": [{"merchandising_rule": {"rule_id": "abc"}}]}]}})
        self.assertEqual((o["type_produit"], o["prix"], o["minimum"], o["maximum"], o["regle"]), ("BOTTLE", 24.9, 18.0, None, "abc"))

    def test_envoi_repricer(self):
        """[RM-AMZ-123] Proposition (plancher, max = 2 × plancher, règle « compétitive ») ; envoi : prix gardé, min/max/règle posés."""
        v = Vendeur()
        fx = Fournisseurs([v], v, v, v, v)
        prop = RP.preparer([{"sku": "S1", "asin": "B0DEMO0001", "marketplace": "FR", "cout_unitaire": 8.5}], fx, Parametres(), RIEN)[0]
        self.assertEqual((prop["type_produit"], prop["regle"]), ("BOTTLE", "2-COMPETITIVE_BUYBOX"))
        self.assertEqual(prop["maximum"], round(prop["plancher"] * 2, 2))
        r = RP.envoyer([{"sku": "S1", "marketplace": "FR", "minimum": prop["minimum"], "maximum": prop["maximum"],
                         "regle": prop["regle"]}], fx, RIEN)
        self.assertEqual(r[0]["statut"], "ACCEPTED")
        sku, tp, offre = v.patches[0]
        self.assertEqual((sku, tp, offre["our_price"][0]["schedule"][0]["value_with_tax"]), ("S1", "BOTTLE", 24.9))
        self.assertEqual(offre["minimum_seller_allowed_price"][0]["schedule"][0]["value_with_tax"], prop["minimum"])
        self.assertEqual(offre["automated_pricing_merchandising_rule_plan"][0]["merchandising_rule"]["rule_id"], "2-COMPETITIVE_BUYBOX")
        mauvais = RP.envoyer([{"sku": "S1", "marketplace": "FR", "minimum": 30, "maximum": 20, "regle": "x"}], fx, RIEN)
        self.assertEqual(mauvais[0]["statut"], "REFUSE")
        self.assertEqual(len(v.patches), 1)                                     # rien envoyé pour la ligne invalide

    def test_alerte_sous_plancher(self):
        """[RM-AMZ-124] SKU dont le prix actuel est sous le plancher ; sans coût d'achat : ignoré."""
        bas, haut = Vendeur(prix=10.0), Vendeur(prix=30.0)
        l = LigneStock(PhotoStock("FR", "S1", "B0DEMO0001", None, 5, 0), 0, Decimal(0), None, None, 0, None, Decimal("8.5"), "EUR")
        sans = LigneStock(PhotoStock("FR", "S2", "B0DEMO0001", None, 5, 0), 0, Decimal(0), None, None, 0, None, None, "EUR")
        a = RP.alertes([l, sans], Fournisseurs([bas], bas, bas, bas, bas), Parametres(), RIEN)
        self.assertEqual([(x["sku"], x["prix"]) for x in a], [("S1", 10.0)])
        self.assertEqual(RP.alertes([l], Fournisseurs([haut], haut, haut, haut, haut), Parametres(), RIEN), [])


if __name__ == "__main__":
    unittest.main()
