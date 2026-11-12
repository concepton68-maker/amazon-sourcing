import unittest

from sourcing.analyse import ACHETER, PASSER, Fournisseurs, analyser_asin
from sourcing.marketplaces import get_marketplace
from sourcing.profit import FraisAmazon, ParametresCout, calculer_rentabilite
from sourcing.providers import keepa, spapi
from sourcing.providers.demo import FournisseurDemo

FR, US = get_marketplace("FR"), get_marketplace("US")


class TestRentabilite(unittest.TestCase):
    def test_assujetti_fr(self):
        r = calculer_rentabilite(FR, 24.0, FraisAmazon(3.0, 4.0), ParametresCout(8.0), "assujetti")
        self.assertAlmostEqual(r.prix_vente_ht, 20.0)
        self.assertAlmostEqual(r.profit_net, 5.0)       # 20 - 8 - 7
        self.assertAlmostEqual(r.roi, 0.625)
        # ROI 30 % : (20 - 7) / 1.3 = 10
        self.assertAlmostEqual(r.prix_achat_max_pour_roi, 10.0)

    def test_assujetti_achat_ttc(self):
        r = calculer_rentabilite(FR, 24.0, FraisAmazon(3.0, 4.0), ParametresCout(9.6, prix_achat_ttc=True))
        self.assertAlmostEqual(r.cout_achat_net, 8.0)
        self.assertAlmostEqual(r.prix_achat_max_pour_roi, 12.0)   # 10 HT -> 12 TTC

    def test_non_assujetti(self):
        r = calculer_rentabilite(FR, 24.0, FraisAmazon(3.0, 4.0), ParametresCout(8.0), "non_assujetti")
        # 24 - 8*1.2 - 7 - 7*0.2 = 6.0
        self.assertAlmostEqual(r.profit_net, 6.0)
        self.assertAlmostEqual(r.prix_achat_max_pour_roi, round((24 - 7 - 1.4) / 1.3 / 1.2, 2))

    def test_us_sans_tva(self):
        r = calculer_rentabilite(US, 20.0, FraisAmazon(3.0, 5.0), ParametresCout(6.0), "assujetti")
        self.assertEqual(r.regime_tva, "hors_taxe")
        self.assertAlmostEqual(r.profit_net, 6.0)

    def test_autres_couts_et_retours(self):
        c = ParametresCout(8.0, envoi_entrepot=0.5, preparation=0.3, taux_retours=0.05)
        r = calculer_rentabilite(FR, 24.0, FraisAmazon(3.0, 4.0), c)
        self.assertAlmostEqual(r.profit_net, round(5.0 - 0.8 - 1.2, 2))


class TestParseursSPAPI(unittest.TestCase):
    def test_frais(self):
        data = {"payload": {"FeesEstimateResult": {"Status": "Success", "FeesEstimate": {
            "TotalFeesEstimate": {"CurrencyCode": "EUR", "Amount": 7.5},
            "FeeDetailList": [
                {"FeeType": "ReferralFee", "FinalFee": {"Amount": 3.0}},
                {"FeeType": "VariableClosingFee", "FinalFee": {"Amount": 0.0}},
                {"FeeType": "FBAFees", "FinalFee": {"Amount": 4.5}},
            ]}}}}
        f = spapi.parser_frais(data)
        self.assertEqual((f.commission, f.fba, f.source), (3.0, 4.5, "sp-api"))

    def test_offres(self):
        data = {"payload": {"Summary": {
            "NumberOfOffers": [{"condition": "new", "fulfillmentChannel": "Amazon", "OfferCount": 3},
                               {"condition": "new", "fulfillmentChannel": "Merchant", "OfferCount": 2}],
            "BuyBoxPrices": [{"condition": "New", "LandedPrice": {"Amount": 19.99}}],
            "LowestPrices": [{"condition": "new", "fulfillmentChannel": "Amazon", "LandedPrice": {"Amount": 19.5}}]},
            "Offers": [{"SellerId": "A1X6FK5RDHNB96", "IsBuyBoxWinner": True}]}}
        o = spapi.parser_offres(FR, data)
        self.assertEqual((o.nb_offres_fba, o.nb_offres_fbm, o.prix_buybox), (3, 2, 19.99))
        self.assertTrue(o.buybox_amazon)

    def test_restrictions(self):
        self.assertTrue(spapi.parser_restrictions({"restrictions": []}).autorise)
        r = spapi.parser_restrictions({"restrictions": [{"reasons": [
            {"reasonCode": "APPROVAL_REQUIRED", "message": "Approval required"}]}]})
        self.assertFalse(r.autorise)
        self.assertTrue(r.approbation_requise)

    def test_catalogue(self):
        data = {"summaries": [{"marketplaceId": FR.marketplace_id, "itemName": "X", "brand": "B"}],
                "salesRanks": [{"marketplaceId": FR.marketplace_id,
                                "displayGroupRanks": [{"title": "Cuisine", "rank": 1234}]}],
                "attributes": {"number_of_items": [{"value": 6}]}}
        c = spapi.parser_catalogue("B0X", FR, data)
        self.assertEqual((c.titre, c.marque, c.bsr, c.categorie, c.nb_unites_lot), ("X", "B", 1234, "Cuisine", 6))


class TestParseurKeepa(unittest.TestCase):
    def test_historique(self):
        avg = [-1] * 19
        avg[keepa.SALES], avg[keepa.BUY_BOX], avg[keepa.COUNT_NEW] = 5000, 2350, 4
        mini = [None] * 19
        mini[keepa.BUY_BOX] = [123, 2190]
        p = {"asin": "B0X", "monthlySold": 100, "stats": {
            "avg90": avg, "minInInterval": mini, "salesRankDrops30": 40,
            "outOfStockPercentage90": [80] + [0] * 18}}
        h = keepa.parser_historique(p)
        self.assertEqual((h.prix_buybox_moy90, h.prix_buybox_min90, h.bsr_moy90), (23.5, 21.9, 5000))
        self.assertEqual((h.ventes_mois_estimees, h.chutes_bsr_30j, h.nb_offres_neuf_moy90), (100, 40, 4))
        self.assertAlmostEqual(h.amazon_en_stock_pct90, 0.2)


class TestAnalyse(unittest.TestCase):
    def setUp(self):
        d = FournisseurDemo()
        self.f = Fournisseurs([d], d, d, d, d)

    def test_bon_produit(self):
        a = analyser_asin(FR, "B0DEMO0001", ParametresCout(8.5), self.f)
        self.assertEqual(a.verdict, ACHETER)

    def test_produit_restreint(self):
        a = analyser_asin(FR, "B0DEMO0002", ParametresCout(15), self.f)
        self.assertEqual(a.verdict, PASSER)

    def test_sans_sources_ne_dit_jamais_acheter(self):
        a = analyser_asin(FR, "B0DEMO0001", ParametresCout(1), Fournisseurs(), prix_vente_force=30)
        self.assertNotEqual(a.verdict, ACHETER)
        self.assertTrue(a.non_verifie)

    def test_prix_retenu(self):
        """[RM-AMZ-001] saisi > Buy Box > FBA le plus bas > moyenne 90 j ; sinon rien."""
        a = analyser_asin(FR, "B0DEMO0001", ParametresCout(8.5), self.f, prix_vente_force=30)
        self.assertEqual((a.prix_vente_retenu, a.origine_prix), (30, "saisi"))
        a = analyser_asin(FR, "B0DEMO0001", ParametresCout(8.5), self.f)
        self.assertEqual(a.prix_vente_retenu, 24.90)
        self.assertIn("Buy Box", a.origine_prix)
        a = analyser_asin(FR, "B0DEMO0001", ParametresCout(8.5), Fournisseurs())
        self.assertIsNone(a.prix_vente_retenu)
        self.assertIsNone(a.rentabilite)


if __name__ == "__main__":
    unittest.main()
