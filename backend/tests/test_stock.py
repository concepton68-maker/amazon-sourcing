"""Stock et réapprovisionnement [RM-AMZ-045 à 048]."""
import unittest
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.depot import DepotMemoire
from sourcing.lots import Lot, Prevision, VenteReelle
from sourcing.marketplaces import get_marketplace
from sourcing.money import Montant
from sourcing.stock import PhotoStock, calculer, commandes_par_fournisseur, parser_inventaire, synchroniser_stock

C = "c"
J = date(2026, 11, 12)
E = lambda v: Montant.de(v, "EUR")  # noqa: E731

RESUME = {"asin": "B0X", "fnSku": "X001", "sellerSku": "SKU-1", "condition": "NewItem", "productName": "Produit X",
          "inventoryDetails": {"fulfillableQuantity": 10, "inboundWorkingQuantity": 2, "inboundShippedQuantity": 3,
                               "inboundReceivingQuantity": 1, "reservedQuantity": {"totalReservedQuantity": 4},
                               "unfulfillableQuantity": {"totalUnfulfillableQuantity": 1}}, "totalQuantity": 21}


def ventes(asin, mp, n, jour=date(2026, 11, 1)):
    return [VenteReelle(C, asin, mp, jour, 1, E(20), E(7), E(0), E(0), E(0)) for _ in range(n)]


class TestStock(unittest.TestCase):
    def test_inventaire_parse_et_photo(self):
        """[RM-AMZ-045] Champs officiels lus ; neuf seulement ; photo du jour remplacée, jamais doublée."""
        (p,) = parser_inventaire({"payload": {"inventorySummaries": [RESUME, dict(RESUME, condition="UsedGood")]}}, "FR")
        self.assertEqual((p.sku, p.asin, p.disponible, p.en_route, p.reserve, p.invendable), ("SKU-1", "B0X", 10, 6, 4, 1))
        d = DepotMemoire()
        d.enregistrer_photo_stock(C, J, [p])
        d.enregistrer_photo_stock(C, J, [PhotoStock("FR", "SKU-1", "B0X", "Produit X", 8, 0)])
        jour, photos = d.photo_stock(C)
        self.assertEqual((jour, len(photos), photos[0].disponible), (J, 1, 8))
        self.assertEqual(d.photo_stock("autre"), (None, []))

    def test_vitesse_et_couverture(self):
        """[RM-AMZ-046] Vitesse = vendus 30 j ÷ 30 ; couverture = (dispo + en route) ÷ vitesse ; sans vente : illimitée."""
        photos = [PhotoStock("FR", "A", "B0A", None, 20, 10), PhotoStock("FR", "B", "B0B", None, 5, 0)]
        v = ventes("B0A", "FR", 15) + ventes("B0A", "FR", 30, jour=date(2026, 9, 1)) + ventes("B0A", "DE", 50)
        a, b = sorted(calculer(photos, v, [], J), key=lambda l: l.photo.sku)
        self.assertEqual((a.vendus_30j, a.vitesse, a.couverture, a.rupture_le), (15, Decimal("0.5"), 60, date(2027, 1, 11)))
        self.assertEqual((b.vendus_30j, b.couverture, b.rupture_le, b.a_commander), (0, None, None, 0))
        self.assertEqual([x.code for x in b.alertes], ["S_SANS_VENTE"])

    def test_quantite_a_commander(self):
        """[RM-AMZ-047] ⌈vitesse × (fournisseur + réception + sécurité)⌉ − disponible − en route, jamais négatif."""
        photos = [PhotoStock("FR", "A", "B0A", None, 4, 2)]
        (l,) = calculer(photos, ventes("B0A", "FR", 30), [], J, 7, 10, 14)       # 1/j × 31 j − 6
        self.assertEqual(l.a_commander, 25)
        (l,) = calculer([PhotoStock("FR", "A", "B0A", None, 400, 0)], ventes("B0A", "FR", 30), [], J)
        self.assertEqual(l.a_commander, 0)

    def test_alertes_stock_et_commandes(self):
        """[RM-AMZ-048] Rupture / surstock selon les seuils ; commandes par fournisseur ; coût inconnu → pas de total."""
        lot = Lot(C, "B0A", "FR", 10, date(2026, 9, 1), Prevision.creer("EUR", 20, 7, 8.5), fournisseur="Grossiste A")
        photos = [PhotoStock("FR", "A", "B0A", None, 5, 0), PhotoStock("FR", "B", "B0B", None, 5, 0),
                  PhotoStock("FR", "C", "B0C", None, 900, 0)]
        v = ventes("B0A", "FR", 30) + ventes("B0B", "FR", 30) + ventes("B0C", "FR", 3)
        lignes = {l.photo.sku: l for l in calculer(photos, v, [lot], J, seuil_rupture=15, seuil_surstock=180)}
        self.assertEqual([x.code for x in lignes["A"].alertes], ["S_RUPTURE"])
        self.assertEqual([x.code for x in lignes["C"].alertes], ["S_SURSTOCK"])
        cmds = commandes_par_fournisseur(list(lignes.values()))
        par = {c.fournisseur: c for c in cmds}
        self.assertEqual((par["Grossiste A"].unites, par["Grossiste A"].montant), (26, Decimal("8.5") * 26))
        self.assertIsNone(par[None].montant)

    def test_synchro_stock_pages(self):
        """[RM-AMZ-045] Toutes les pages lues (jeton de page) ; une photo par place."""
        class Client:
            def page_inventaire(self, mp, jeton):
                if jeton is None:
                    return {"pagination": {"nextToken": "p2"}, "payload": {"inventorySummaries": [RESUME]}}
                return {"payload": {"inventorySummaries": [dict(RESUME, sellerSku="SKU-2")]}}
        d, pauses = DepotMemoire(), []
        n = synchroniser_stock(C, [get_marketplace("FR"), get_marketplace("DE")], Client(), d, J, pauses.append)
        self.assertEqual((n, len(d.photo_stock(C)[1]), pauses), (4, 4, [0.5, 0.5]))

    def test_api_stock_demo(self):
        """API : lignes triées par couverture croissante, commande suggérée pour le produit en rupture."""
        d, c = construire()
        j = TestClient(creer_app(d, c, servir_interface=False)).get("/api/stock").json()
        self.assertEqual(j["jour"], "2026-11-12")
        self.assertEqual(j["lignes"][0]["sku"], "GOURDE-750")
        self.assertIn("S_RUPTURE", [a["code"] for a in j["lignes"][0]["alertes"]])
        self.assertEqual(j["commandes"][0]["fournisseur"], "Grossiste A")
        self.assertEqual(j["compteurs"]["ruptures"], 1)


if __name__ == "__main__":
    unittest.main()
