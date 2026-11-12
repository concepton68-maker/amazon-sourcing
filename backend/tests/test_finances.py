"""Tests du lot 2 : ventes et frais réels (RM-AMZ-016 à 023).

Les réponses ci-dessous sont construites avec les seuls noms de champs lus dans la documentation
v2024-06-19 (transactionId, transactionStatus, postedDate, totalAmount, marketplaceDetails,
relatedIdentifiers, items, breakdowns, contexts). Les valeurs et les types de frais autres que
Principal / Tax sont FICTIFS.
"""
import inspect
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sourcing import finances
from sourcing.depot import DepotMemoire
from sourcing.finances import LigneFinanciere, normaliser_transactions, vers_vente
from sourcing.lots import Lot, Prevision, rattacher_fifo
from sourcing.marketplaces import get_marketplace
from sourcing.providers import spapi
from sourcing.sync import MAX_FENETRE, fenetres, synchroniser

FR = get_marketplace("FR")
COMPTE = "compte-1"


def eur(v):
    return {"currencyCode": "EUR", "currencyAmount": v}


def transaction(tid, montants, statut="RELEASED", jour="2026-10-05", commande="111-1", asin="B0X", qte=1,
                description="Order Payment"):
    return {
        "transactionId": tid, "transactionType": "Shipment", "transactionStatus": statut,
        "description": description, "postedDate": f"{jour}T10:00:00Z",
        "totalAmount": eur(sum(montants.values())),
        "marketplaceDetails": {"marketplaceId": FR.marketplace_id, "marketplaceName": "Amazon.fr"},
        "relatedIdentifiers": [{"relatedIdentifierName": "ORDER_ID", "relatedIdentifierValue": commande}],
        "items": [{"description": "article", "totalAmount": eur(sum(montants.values())),
                   "breakdowns": [{"breakdownType": k, "breakdownAmount": eur(v)} for k, v in montants.items()],
                   "contexts": [{"contextType": "ProductContext", "asin": asin, "sku": "SKU-1",
                                 "quantityShipped": qte}]}],
    }


VENTE = transaction("T1", {"Principal": 20.75, "Tax": 4.15, "FraisFictifA": -3.74, "FraisFictifB": -4.15})
CLASSEMENT = {"FraisFictifA": "frais_amazon", "FraisFictifB": "frais_amazon"}


class TestNormalisation(unittest.TestCase):
    def test_normalisation_transaction(self):
        """[RM-AMZ-016] Champs v2024 lus : place, commande, produit, quantité, montants."""
        n = normaliser_transactions({"payload": {"transactions": [VENTE]}}, CLASSEMENT)
        (l,) = n.lignes
        self.assertEqual((l.id_externe, l.marketplace, l.commande, l.asin, l.quantite, l.jour),
                         ("T1#0", "FR", "111-1", "B0X", 1, date(2026, 10, 5)))
        self.assertEqual(l.montants["vente"], Decimal("20.75"))
        self.assertEqual(l.montants["frais_amazon"], Decimal("-7.89"))
        self.assertEqual(l.net, Decimal("12.86"))
        v = vers_vente(l, COMPTE)
        self.assertEqual((v.chiffre_affaires_ht.valeur, v.frais_amazon.valeur), (Decimal("20.75"), Decimal("7.89")))

    def test_types_inconnus_signales(self):
        """[RM-AMZ-021] Type inconnu : compté en « autres » ET signalé, jamais ignoré."""
        n = normaliser_transactions({"transactions": [VENTE]})   # sans table : FraisFictifA/B inconnus
        (l,) = n.lignes
        self.assertEqual(n.types_inconnus, {"FraisFictifA": 1, "FraisFictifB": 1})
        self.assertEqual(l.montants["autres"], Decimal("-7.89"))
        self.assertEqual(l.net, Decimal("12.86"))               # le profit ne dépend pas du classement
        self.assertIn("TYPES_FRAIS_INCONNUS", finances.avertissements_ligne(l))

    def test_pas_de_double_comptage(self):
        """[RM-AMZ-021] Une ventilation qui a des sous-ventilations n'est pas additionnée elle-même."""
        t = transaction("T2", {})
        t["items"][0]["breakdowns"] = [
            {"breakdownType": "Principal", "breakdownAmount": eur(20)},
            {"breakdownType": "Groupe", "breakdownAmount": eur(-5),
             "breakdowns": [{"breakdownType": "FraisFictifA", "breakdownAmount": eur(-3)},
                            {"breakdownType": "FraisFictifB", "breakdownAmount": eur(-2)}]}]
        (l,) = normaliser_transactions({"transactions": [t]}, CLASSEMENT).lignes
        self.assertEqual(l.montants["frais_amazon"], Decimal(-5))
        self.assertEqual(l.net, Decimal(15))

    def test_tva_separee_ou_signalee(self):
        """[RM-AMZ-020] Taxe ventilée : hors chiffre d'affaires ; absente en UE : avertissement."""
        (l,) = normaliser_transactions({"transactions": [VENTE]}, CLASSEMENT).lignes
        self.assertTrue(l.tva_separee)
        self.assertEqual(vers_vente(l, COMPTE).chiffre_affaires_ht.valeur, Decimal("20.75"))
        self.assertNotIn("TVA_NON_SEPAREE", finances.avertissements_ligne(l))
        sans = transaction("T3", {"Principal": 24.90, "FraisFictifA": -3.74})
        (l2,) = normaliser_transactions({"transactions": [sans]}, CLASSEMENT).lignes
        self.assertIn("TVA_NON_SEPAREE", finances.avertissements_ligne(l2))

    def test_montant_differe(self):
        """[RM-AMZ-023] Différé : dans le profit, et affiché à part « à encaisser »."""
        t = transaction("T4", {"Principal": 20, "FraisFictifA": -8}, statut="DEFERRED")
        (l,) = normaliser_transactions({"transactions": [t]}, CLASSEMENT).lignes
        v = vers_vente(l, COMPTE)
        self.assertTrue(v.differe)
        lot = Lot(COMPTE, "B0X", "FR", 5, date(2026, 9, 1), Prevision.creer("EUR", 20, 8, 7))
        res, _ = rattacher_fifo([lot], [v])
        self.assertEqual(res[lot.id].a_encaisser.valeur, Decimal(12))
        self.assertEqual(res[lot.id].profit_reel.valeur, Decimal(5))   # 20 − 8 − 7

    def test_aucune_donnee_acheteur(self):
        """[RM-AMZ-022] Ni demande ni stockage de données d'acheteur."""
        source = inspect.getsource(spapi) + inspect.getsource(finances)
        for interdit in ("BUYER", "RECIPIENT", "buyerInfo", "shippingAddress"):
            self.assertNotIn(interdit, source.replace("[RM-AMZ-022]", ""))
        t = dict(VENTE, buyerName="Personne Fictive", shippingAddress={"city": "X"})
        (l,) = normaliser_transactions({"transactions": [t]}, CLASSEMENT).lignes
        champs = " ".join(str(v) for v in vars(l).values())
        self.assertNotIn("Personne Fictive", champs)


class TestAjustements(unittest.TestCase):
    def test_ajustement_rattache_a_la_commande(self):
        """[RM-AMZ-019] Remboursement ultérieur : ajouté, imputé aux retours du lot de la commande d'origine."""
        rembourse = transaction("T9", {"Principal": -20.75, "FraisFictifA": 3.0}, jour="2026-11-02",
                                description="Refund Order", qte=0)
        orphelin = transaction("T10", {"Principal": -10}, jour="2026-11-02", commande="999-9", qte=0)
        n = normaliser_transactions({"transactions": [VENTE, rembourse, orphelin]}, CLASSEMENT)
        ventes = [vers_vente(l, COMPTE) for l in n.lignes]
        a = Lot(COMPTE, "B0X", "FR", 1, date(2026, 8, 1), Prevision.creer("EUR", 20.75, 7.89, 8))
        res, orphelines = rattacher_fifo([a], ventes)
        r = res[a.id]
        self.assertEqual(r.quantite_vendue, 1)
        self.assertEqual(r.retours.valeur, Decimal("20.75"))
        self.assertEqual(r.frais_amazon.valeur, Decimal("4.89"))   # 7,89 prélevés − 3,00 rendus
        self.assertEqual(r.chiffre_affaires.valeur, Decimal("20.75"))  # la vente n'est pas écrasée
        self.assertEqual(len(orphelines), 1)
        self.assertEqual(orphelines[0].vente.commande, "999-9")


class ClientFactice:
    def __init__(self, pages):
        self.pages, self.appels = pages, []

    def page_transactions(self, mp, debut, fin, jeton):
        self.appels.append((debut, fin, jeton))
        return self.pages[jeton]


class TestSync(unittest.TestCase):
    MAINTENANT = datetime(2026, 11, 12, 3, 0, tzinfo=timezone.utc)

    def test_fenetre_sync(self):
        """[RM-AMZ-018] Recul de 7 jours, fin à −5 min, tranches de 180 jours, page vide non bloquante."""
        dernier = datetime(2026, 11, 11, 3, 0, tzinfo=timezone.utc)
        (f,) = fenetres(dernier, self.MAINTENANT)
        self.assertEqual(f, (dernier - timedelta(days=7), self.MAINTENANT - timedelta(minutes=5)))
        longues = fenetres(datetime(2025, 1, 1, tzinfo=timezone.utc), self.MAINTENANT)
        self.assertTrue(all(b - a <= MAX_FENETRE for a, b in longues))
        self.assertEqual(longues[-1][1], self.MAINTENANT - timedelta(minutes=5))
        c = ClientFactice({None: {"payload": {"transactions": [], "nextToken": "p2"}},
                           "p2": {"payload": {"transactions": [VENTE]}}})
        pauses = []
        r = synchroniser(COMPTE, FR, c, DepotMemoire(), self.MAINTENANT, dernier, CLASSEMENT, pauses.append)
        self.assertEqual((r.pages, r.ventes), (2, 1))
        self.assertEqual(pauses, [2.0])                         # 0,5 requête par seconde
        self.assertEqual(r.curseur, self.MAINTENANT - timedelta(minutes=5))

    def test_sync_rejouable(self):
        """[RM-AMZ-017] Rejouer les mêmes transactions ne double rien ; un statut mis à jour remplace."""
        d = DepotMemoire()
        c = ClientFactice({None: {"transactions": [VENTE]}})
        for _ in range(2):
            synchroniser(COMPTE, FR, c, d, self.MAINTENANT, None, CLASSEMENT, lambda s: None)
        self.assertEqual(len(d.ventes(COMPTE)), 1)
        libere = dict(VENTE, transactionStatus="DEFERRED")
        synchroniser(COMPTE, FR, ClientFactice({None: {"transactions": [libere]}}), d, self.MAINTENANT,
                     None, CLASSEMENT, lambda s: None)
        (v,) = d.ventes(COMPTE)
        self.assertTrue(v.differe)

    def test_frais_sans_produit_mis_a_part(self):
        """Un frais de compte sans produit n'est imputé à aucun lot, il est listé à part."""
        t = transaction("T20", {"FraisFictifC": -39}, asin=None)
        t["items"][0]["contexts"] = []
        r = synchroniser(COMPTE, FR, ClientFactice({None: {"transactions": [t]}}), DepotMemoire(),
                         self.MAINTENANT, None, None, lambda s: None)
        self.assertEqual((r.ventes, r.sans_produit), (0, ["T20#0"]))


class TestParcoursDemo(unittest.TestCase):
    def test_parcours_demo(self):
        """Parcours de bout en bout (analyse → lot → synchro → écart) : la somme des causes égale l'écart."""
        from sourcing.demo_parcours import executer
        sortie = executer()
        self.assertIn("DONNÉES FICTIVES", sortie)
        self.assertIn("FraisInconnuX", sortie)
        self.assertIn("Total", sortie)


if __name__ == "__main__":
    unittest.main()
