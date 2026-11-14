"""Historique maison et suivi de marché [RM-AMZ-086 à 090]."""
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

from fastapi.testclient import TestClient

from sourcing import historique as H
from sourcing import synchro_nuit as SN
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.depot import DepotMemoire
from sourcing.marketplaces import get_marketplace
from sourcing.providers.base import InfosCatalogue, InfosOffres
from sourcing.providers.spapi import ClientSPAPI

C = "00000000-0000-4000-8000-0000000000c2"
FR = get_marketplace("FR")
NUIT = datetime(2026, 11, 14, 3, 15, tzinfo=timezone.utc)
RIEN = lambda s: None  # noqa: E731


class Faux:
    """Catalogue simulé : 3 pages de 20 par famille (1 parent par page) ; paquets d'offres comptés."""
    def __init__(self, panne_offres=None):
        self.paquets_offres, self.paquets_catalogue, self.pages, self.panne = [], [], 0, panne_offres

    def participations(self, mp):
        return [FR.marketplace_id]

    def rechercher_page(self, mp, mots, jeton=None):
        self.pages += 1
        p = int(jeton or 0)
        items = [InfosCatalogue(f"{mots[:2].upper()}{p:02d}{k:06d}", f"{mots} {k}", "M", "Cat", 100 * p + k + 1,
                                classification="VARIATION_PARENT" if k == 0 else "BASE_PRODUCT") for k in range(20)]
        return items, (str(p + 1) if p < 2 else None)

    def catalogue_par_paquet(self, mp, asins):
        assert len(asins) <= 20
        self.paquets_catalogue.append(list(asins))
        return {a: InfosCatalogue(a, "T " + a, None, "Cat", 5000) for a in asins}

    def offres_par_paquet(self, mp, asins):
        assert len(asins) <= 20
        self.paquets_offres.append(list(asins))
        if self.panne and self.panne(asins):
            raise RuntimeError("429")
        return {a: InfosOffres(12.5, False, a.endswith("1"), 3, 1, 12.9) for a in asins if not a.endswith("7")}

    # tâches de nuit hors historique
    def page_transactions(self, *a):
        return {"payload": {"transactions": []}}

    def page_inventaire(self, *a):
        return {"payload": {"inventorySummaries": []}}

    def rapport(self, *a, **k):
        return ""

    def envois_fermes(self, *a):
        return []

    def rechercher(self, mp, mots, taille=20):
        return []

    def restrictions(self, mp, asin):
        return None


class TestHistorique(unittest.TestCase):
    def test_perimetre_priorite_et_plafond(self):
        """[RM-AMZ-086] Suivis, puis analysés, puis familles ; sans doublon ; plafond appliqué dans cet ordre."""
        p = H.perimetre(["S1", "S2"], ["S2", "A1"], {"CUISINE": ["F1", "A1", "F2"], "JARDIN": ["G1"]}, plafond=5)
        self.assertEqual(p, [("S1", H.SUIVI, None), ("S2", H.SUIVI, None), ("A1", H.ANALYSE, None),
                             ("F1", H.FAMILLE, "CUISINE"), ("F2", H.FAMILLE, "CUISINE")])
        self.assertEqual(len(H.perimetre([f"X{i}" for i in range(30)], [], {})), 30)
        self.assertEqual(H.PLAFOND, 20_000)

    def test_familles_paginees_sans_parents(self):
        """[RM-AMZ-086] Pages suivies jusqu'au bout ou jusqu'au maximum ; parents de variantes écartés."""
        f = Faux()
        tout = H.produits_famille(f, FR, "cuisine", RIEN)
        self.assertEqual((len(tout), f.pages), (57, 3))                        # 3 pages × 19 (parents écartés)
        f = Faux()
        self.assertEqual(len(H.produits_famille(f, FR, "cuisine", RIEN, maximum=25)), 25)
        self.assertEqual(f.pages, 2)
        self.assertEqual(H.MAX_FAMILLE, 1000)

    def test_releve_par_paquets(self):
        """[RM-AMZ-087] Paquets de 20 ; fiches demandées seulement pour les produits inconnus ; pauses respectées."""
        f, d, pauses = Faux(), DepotMemoire(), []
        asins = [f"B0{k:08d}" for k in range(45)]
        connus = {a: InfosCatalogue(a, "connu", None, "Cat", 77) for a in asins[:5]}
        n, err = H.relever(f, FR, asins, connus, date(2026, 11, 14), pauses.append,
                           lambda lot: d.enregistrer_releves(C, lot))
        self.assertEqual((n, err), (45, 0))
        self.assertEqual([len(p) for p in f.paquets_offres], [20, 20, 5])
        self.assertEqual([len(p) for p in f.paquets_catalogue], [20, 20])     # 40 inconnus
        self.assertEqual(pauses.count(H.PAUSE_OFFRES), 3)
        r = {x.asin: x for x in d.releves(C, "FR")}
        self.assertEqual((r[asins[0]].bsr, r[asins[10]].bsr), (77, 5000))
        self.assertEqual((r[asins[1]].prix_buybox, r[asins[1]].amazon_vend, r[asins[1]].nb_fba), (Decimal("12.5"), True, 3))

    def test_releve_erreur_partielle(self):
        """[RM-AMZ-087] Produit ou paquet en erreur : relevé sans les champs manquants, jamais deviné."""
        f, d = Faux(panne_offres=lambda l: "B000000020" in l), DepotMemoire()
        asins = [f"B0{k:08d}" for k in range(25)]
        n, err = H.relever(f, FR, asins, {}, date(2026, 11, 14), RIEN, lambda lot: d.enregistrer_releves(C, lot))
        self.assertEqual((n, err), (25, 1))
        r = {x.asin: x for x in d.releves(C, "FR")}
        self.assertIsNone(r["B000000007"].prix_buybox)                        # absent du paquet
        self.assertEqual(r["B000000007"].bsr, 5000)                           # la fiche reste relevée
        self.assertIsNone(r["B000000022"].prix_buybox)                        # paquet entier en panne
        self.assertIsNone(r["B000000022"].nb_fba)

    def test_tendances(self):
        """[RM-AMZ-089] Prix, classement, jours de baisse du classement, parts Amazon, vendeurs, fenêtre glissante."""
        j = date(2026, 11, 14)
        rel = [H.Releve("FR", "X", j - timedelta(days=k), Decimal(str(10 + k % 3)), 2, k % 2, k < 4, k < 2, None,
                        1000 - 10 * ((9 - k) % 4)) for k in range(10)]
        rel.append(H.Releve("FR", "X", j - timedelta(days=40), Decimal("99"), bsr=1))   # hors fenêtre
        t = H.tendances(rel, j, 30)
        self.assertEqual((t["releves"], t["court"]), (10, False))
        self.assertEqual((t["prix_min"], t["prix_max"], t["prix_dernier"]), (Decimal("10"), Decimal("12"), Decimal("10")))
        self.assertEqual(t["prix_variation"], round((10 - 10) / 10, 4))
        self.assertEqual(t["prix_moyen"], Decimal("10.90"))
        self.assertEqual(t["part_amazon_vend"], 0.4)
        self.assertEqual(t["part_buybox_amazon"], 0.2)
        bsr = [r.bsr for r in sorted(rel[:10], key=lambda r: r.jour)]
        self.assertEqual(t["jours_baisse_bsr"], sum(1 for a, b in zip(bsr, bsr[1:]) if b < a))
        self.assertEqual(t["vendeurs_moyen"], 2.5)
        self.assertEqual(H.tendances(rel, j, 7)["releves"], 7)

    def test_historique_court(self):
        """[RM-AMZ-089] Moins de 7 relevés : « historique court » ; sans relevé : rien n'est inventé."""
        j = date(2026, 11, 14)
        t = H.tendances([H.Releve("FR", "X", j, Decimal("5"), bsr=10)], j, 30)
        self.assertTrue(t["court"])
        self.assertIsNone(t["jours_baisse_bsr"])
        self.assertIsNone(t["prix_variation"])
        vide = H.tendances([], j, 30)
        self.assertEqual((vide["releves"], vide["prix_moyen"], vide["part_amazon_vend"]), (0, None, None))

    def test_synchro_historique(self):
        """[RM-AMZ-090] Tâche « HISTORIQUE » journalisée : suivis + analysés + familles, une fois par produit."""
        d = DepotMemoire()
        d.creer_compte(C, "A")
        d.ajouter_suivi(C, "FR", "B0SUIVI001")
        d.memoriser_appariement(C, "FR", "3700000000017", ["B0ANALYSE1"], NUIT - timedelta(days=2))
        d.memoriser_appariement(C, "FR", "3700000000024", ["B0VIEUX001"], NUIT - timedelta(days=200))
        d.enregistrer_familles(C, ["CUISINE"])
        f = Faux()
        res = SN.executer([(C, {"region": "EU"})], d, NUIT, fabrique=lambda v: f, attendre=RIEN)[C]
        h = [r for r in res if r.tache == "HISTORIQUE"][0]
        self.assertTrue(h.ok, h.message)
        self.assertIn("FR 59 produits", h.message)                            # 1 + 1 + 57
        asins = {r.asin for r in d.releves(C, "FR")}
        self.assertIn("B0SUIVI001", asins)
        self.assertIn("B0ANALYSE1", asins)
        self.assertNotIn("B0VIEUX001", asins)                                  # analysé il y a plus de 90 jours
        self.assertEqual({r.jour for r in d.releves(C, "FR")}, {date(2026, 11, 14)})
        self.assertEqual(len(d.produits_marche(C, "FR", famille="CUISINE")), 57)
        self.assertIn("HISTORIQUE", d.etat_synchros())
        with mock.patch.object(H, "PLAFOND", 10):                              # plafond : suivis d'abord
            d2 = DepotMemoire()
            d2.creer_compte(C, "A")
            d2.ajouter_suivi(C, "FR", "B0SUIVI001")
            d2.enregistrer_familles(C, ["CUISINE"])
            msg = H.executer(C, Faux(), [FR], d2, NUIT, RIEN, plafond=10)
            self.assertIn("FR 10 produits", msg)
            self.assertIn("B0SUIVI001", {r.asin for r in d2.releves(C, "FR")})

    def test_api_marche(self):
        """[RM-AMZ-090] Familles choisies, suivi ajouté et retiré, liste et historique d'un produit."""
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False))
        self.assertEqual(cl.put("/api/marche/familles", json={"familles": ["INCONNUE"]}).status_code, 422)
        self.assertEqual(cl.put("/api/marche/familles", json={"familles": ["CUISINE"]}).json()["familles"], ["CUISINE"])
        self.assertEqual(cl.post("/api/marche/suivi", json={"asin": "trop-court"}).status_code, 422)
        self.assertEqual(cl.post("/api/marche/suivi", json={"asin": "b0test0001"}).status_code, 201)
        jour = H.jour_paris(datetime.now(timezone.utc))
        d.enregistrer_releves(c, [H.Releve("FR", "B0TEST0001", jour - timedelta(days=k), Decimal("20") + k, 2, 1,
                                           False, False, None, 500 + k) for k in range(3)])
        j = cl.get("/api/marche").json()
        self.assertEqual(j["suivis"], 1)
        p = j["produits"][0]
        self.assertEqual((p["asin"], p["prix"], p["bsr"], p["vendeurs"]), ("B0TEST0001", 20.0, 500, 3))
        self.assertTrue(p["tendance"]["court"])
        self.assertTrue([f for f in j["familles"] if f["code"] == "CUISINE"][0]["suivie"])
        self.assertEqual(cl.get("/api/marche?groupe=XYZ").status_code, 422)
        self.assertEqual(cl.get("/api/marche?groupe=CUISINE").status_code, 200)
        h = cl.get("/api/marche/produit/FR/B0TEST0001").json()
        self.assertEqual((len(h["releves"]), h["suivi"], h["tendances"]["7"]["releves"]), (3, True, 3))
        self.assertEqual(cl.delete("/api/marche/suivi/FR/B0TEST0001").status_code, 200)
        self.assertEqual(cl.delete("/api/marche/suivi/FR/B0TEST0001").status_code, 404)

    def test_spapi_paquets(self):
        """[RM-AMZ-087] Requête par lot conforme au modèle ; réponse en erreur ignorée ; page suivante lue."""
        cl = ClientSPAPI(client_id="x", client_secret="y", refresh_tokens={"EU": "z"})
        corps = {}

        def appel(mp, methode, chemin, params=None, json=None):
            if chemin.startswith("/batches"):
                corps.update(json)
                return {"responses": [
                    {"status": {"statusCode": 200}, "request": {"Asin": "B0A0000001"},
                     "body": {"payload": {"Summary": {"BuyBoxPrices": [{"condition": "New", "LandedPrice": {"Amount": 9.9}}],
                                                      "NumberOfOffers": [{"condition": "new", "fulfillmentChannel": "Amazon",
                                                                          "OfferCount": 2}]}, "Offers": []}}},
                    {"status": {"statusCode": 400}, "request": {"Asin": "B0A0000002"}, "body": {"errors": [{}]}}]}
            return {"items": [{"asin": "B0A0000003", "summaries": [{"marketplaceId": FR.marketplace_id, "itemName": "T"}]}],
                    "pagination": {"nextToken": "abc"}}
        cl._appel = appel
        o = cl.offres_par_paquet(FR, ["B0A0000001", "B0A0000002"])
        self.assertEqual(list(o), ["B0A0000001"])
        self.assertEqual((o["B0A0000001"].prix_buybox, o["B0A0000001"].nb_offres_fba), (9.9, 2))
        self.assertEqual(corps["requests"][0], {"uri": "/products/pricing/v0/items/B0A0000001/offers", "method": "GET",
                                                "MarketplaceId": FR.marketplace_id, "ItemCondition": "New"})
        items, jeton = cl.rechercher_page(FR, "cuisine")
        self.assertEqual(([i.asin for i in items], jeton), (["B0A0000003"], "abc"))


if __name__ == "__main__":
    unittest.main()
