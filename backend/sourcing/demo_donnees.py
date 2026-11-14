"""Jeu de données FICTIF pour le mode démo de l'interface : quatre lots et leurs ventes simulées,
passées par la vraie chaîne (normalisation Amazon → synchro → dépôt)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from .depot import DepotMemoire
from .lots import Lot, Prevision
from .marketplaces import get_marketplace
from .stock import PhotoStock
from .sync import synchroniser

COMPTE_DEMO = "00000000-0000-4000-8000-000000000001"
CLASSEMENT = {"Commission": "frais_amazon", "FraisFBA": "frais_amazon", "Stockage": "stockage"}


def _eur(v):
    return {"currencyCode": "EUR", "currencyAmount": round(v, 2)}


def _tx(tid, jour, asin, commande, montants, qte=1, statut="RELEASED", mp="FR"):
    return {"transactionId": tid, "transactionType": "Shipment", "transactionStatus": statut,
            "postedDate": f"{jour}T10:00:00Z", "marketplaceDetails": {"marketplaceId": get_marketplace(mp).marketplace_id},
            "relatedIdentifiers": [{"relatedIdentifierName": "ORDER_ID", "relatedIdentifierValue": commande}],
            "items": [{"breakdowns": [{"breakdownType": k, "breakdownAmount": _eur(v)} for k, v in montants.items()],
                       "contexts": [{"contextType": "ProductContext", "asin": asin, "quantityShipped": qte}]}]}


def _ventes(prefixe, asin, n, prix_ht, frais, debut, mp="FR", baisse=None, differe_dernieres=0):
    out = []
    for i in range(n):
        p, f = prix_ht, frais
        if baisse and i >= baisse[0]:
            p, f = baisse[1], baisse[2]
        j = date.fromordinal(debut.toordinal() + i)
        out.append(_tx(f"{prefixe}{i}", j.isoformat(), asin, f"{prefixe}-C{i}",
                       {"Principal": p, "Tax": p * 0.2, "Commission": -f * 0.45, "FraisFBA": -f * 0.55},
                       statut="DEFERRED" if i >= n - differe_dernieres else "RELEASED", mp=mp))
    return out


class _AmazonSimule:
    def __init__(self, transactions):
        self.t = transactions

    def page_transactions(self, mp, debut, fin, jeton):
        return {"payload": {"transactions": self.t}}


def construire() -> tuple[DepotMemoire, str]:
    d = DepotMemoire()
    c = COMPTE_DEMO
    d.creer_compte(c, "Compte démo")
    lots = [
        Lot(c, "B0DEMO0001", "FR", 80, date(2026, 8, 12), Prevision.creer("EUR", 20.75, 7.89, 8.50, retours=0.20),
            "Grossiste A", "Gourde inox 750 ml"),
        Lot(c, "B0DEMO0003", "DE", 60, date(2026, 9, 5), Prevision.creer("EUR", 20.92, 8.05, 9.80, retours=0.25),
            "Grossiste B", "Lampe frontale LED"),
        Lot(c, "B0DEMO0004", "FR", 70, date(2026, 8, 20), Prevision.creer("EUR", 14.99, 6.10, 6.40, retours=0.36,
            stockage=0.05), "Grossiste B", "Puzzle 1000 pièces"),
        Lot(c, "B0DEMO0005", "IT", 40, date(2026, 9, 28), Prevision.creer("EUR", 32.70, 11.40, 14.20, retours=0.40),
            "Grossiste A", "Set de couteaux 5 pièces"),
    ]
    for l in lots:
        d.ajouter_lot(c, l)
    tx = []
    tx += _ventes("G", "B0DEMO0001", 64, 20.75, 7.89, date(2026, 8, 20), differe_dernieres=3)
    tx += _ventes("L", "B0DEMO0003", 41, 20.92, 8.05, date(2026, 9, 12), mp="DE", baisse=(12, 17.92, 7.70))
    tx += _ventes("P", "B0DEMO0004", 52, 14.99, 6.10, date(2026, 8, 28))
    tx += [_tx(f"PR{i}", "2026-10-25", "B0DEMO0004", f"P-C{i}", {"Principal": -14.99, "Commission": 0.45}, qte=0)
           for i in range(5)]
    tx += [_tx("PS1", "2026-10-31", "B0DEMO0004", "P-C1", {"Stockage": -18.5}, qte=0)]
    tx += _ventes("K", "B0DEMO0005", 18, 32.70, 11.62, date(2026, 10, 5), mp="IT")
    # remboursements clients anciens : l'un sans retour (cas), l'autre retourné (pas de cas)
    tx += [_tx("GR1", "2026-09-15", "B0DEMO0001", "G-C5", {"Principal": -20.75, "Commission": 0.60}, qte=0),
           _tx("GR2", "2026-09-16", "B0DEMO0001", "G-C6", {"Principal": -20.75, "Commission": 0.60}, qte=0)]
    synchroniser(c, get_marketplace("FR"), _AmazonSimule(tx), d, datetime(2026, 11, 12, 3, tzinfo=timezone.utc),
                 classement=CLASSEMENT, attendre=lambda s: None)
    # fournisseurs et bons (fictifs) [RM-AMZ-049, 050]
    from . import achats as A
    fa = A.nouveau_fournisseur(c, "Grossiste A", "EUR", 6)
    fb = A.nouveau_fournisseur(c, "Grossiste B", "EUR", 9, existants=[fa])
    fm = A.nouveau_fournisseur(c, "MarqueDemo", "EUR", 4, existants=[fa, fb])
    for f in (fa, fb, fm):
        d.enregistrer_fournisseur(c, f)
    envoye = A.nouveau_bon(c, d.prochain_numero(c), fm)
    envoye = A.ajouter_ligne(envoye, "B0DEMO0005", "IT", 20, "14.20", lots[3].prevision, "Set de couteaux 5 pièces", "EUR")
    envoye = A.envoyer(envoye, datetime(2026, 11, 4, 9, tzinfo=timezone.utc))
    d.enregistrer_bon(c, envoye)
    brouillon = A.nouveau_bon(c, d.prochain_numero(c), fb)
    brouillon = A.ajouter_ligne(brouillon, "B0DEMO0004", "FR", 30, "6.10", lots[2].prevision, "Puzzle 1000 pièces", "EUR")
    d.enregistrer_bon(c, brouillon)
    # remboursements FBA (fictifs) [RM-AMZ-054 à 059]
    from . import remboursements as RB
    verses = [RB.RemboursementVerse("R-1001", date(2026, 9, 2), "C-55501", None, "PUZZLE-1000", "X-PUZZLE", "B0DEMO0004",
                                    "EUR", Decimal("12.80"), 2),
              RB.RemboursementVerse("R-1002", date(2026, 10, 20), None, None, "LAMPE-LED", "X-LAMPE", "B0DEMO0003",
                                    "EUR", Decimal("9.80"), 1)]
    ledger = [RB.LigneLedger(date(2026, 10, 1), "DE", "X-LAMPE", "B0DEMO0003", "LAMPE-LED", 3, 1, 1)]
    retours = [RB.RetourClient(date(2026, 9, 25), "G-C6", "GOURDE-750", "B0DEMO0001", "X-GOURDE", 1)]
    envois = [RB.LigneEnvoi("FBA-DEMO1", "CLOSED", "IT", "COUTEAUX-5", "X-COUTEAUX", 40, 37)]
    d.enregistrer_verses(c, verses)
    asins = {"COUTEAUX-5": "B0DEMO0005", "LAMPE-LED": "B0DEMO0003", "GOURDE-750": "B0DEMO0001"}
    cas = RB.detecter(ledger, verses, retours, d.ventes(c), envois, d.lots(c), date(2026, 11, 12), "EUR", asins)
    d.enregistrer_cas(c, RB.appliquer_suivi(cas, [], verses))
    # conformité (fictive) [RM-AMZ-061 à 066] : un dossier presque complet, un à moitié, les autres vides
    from . import conformite as CF
    d.enregistrer_enregistrement(c, CF.nouvel_enregistrement("FR", "EMBALLAGES", "FR000000_01DEMO"))
    d.enregistrer_enregistrement(c, CF.nouvel_enregistrement("DE", "EMBALLAGES", "0000000000001"))
    fab = {"nom": "Fabricant Démo SAS", "adresse": "1 rue de l'Exemple, 75000 Paris", "courriel": "contact@exemple.invalid"}
    d.enregistrer_fiche(c, CF.valider_fiche("B0DEMO0001", {
        "fabricant": fab, "fabricant_hors_ue": False, "avertissements_ok": True, "producteur": "OUI",
        "filieres": ["EMBALLAGES"], "triman_ok": True, "marquage_ce": "NON_CONCERNE"}))
    d.enregistrer_fiche(c, CF.valider_fiche("B0DEMO0003", {
        "fabricant": {"nom": "Demo Lights Ltd", "adresse": "Shenzhen", "courriel": "sales@exemple.invalid"},
        "fabricant_hors_ue": True, "producteur": "OUI", "filieres": ["EMBALLAGES", "EEE", "PILES"],
        "marquage_ce": "OUI"}))
    jour = date(2026, 11, 12)
    d.enregistrer_photo_stock(c, jour, [
        PhotoStock("FR", "GOURDE-750", "B0DEMO0001", "Gourde inox 750 ml", 3, 0),
        PhotoStock("DE", "LAMPE-LED", "B0DEMO0003", "Lampe frontale LED", 19, 0),
        PhotoStock("FR", "PUZZLE-1000", "B0DEMO0004", "Puzzle 1000 pièces", 18, 0, invendable=2),
        PhotoStock("IT", "COUTEAUX-5", "B0DEMO0005", "Set de couteaux 5 pièces", 22, 12),
        PhotoStock("FR", "BOUGIE-VIEILLE", "B0DEMO0099", "Bougie parfumée", 37, 0),
    ])
    return d, c


def historique_demo(d, c: str, jour: date) -> None:
    """Historique FICTIF de 40 jours pour l'écran « Marché » en démonstration [RM-AMZ-089]."""
    import math

    from .historique import ProduitMarche, Releve
    produits = [("B0DEMO0001", "Gourde inox 750 ml (démo)", None, 24.9, 4200, True),
                ("B0DEMO0011", "Boîte hermétique verre (démo)", "CUISINE", 14.5, 2100, True),
                ("B0DEMO0012", "Moulin à épices (démo)", "CUISINE", 19.9, 8800, False),
                ("B0DEMO0013", "Planche bambou (démo)", "CUISINE", 12.9, 15500, False)]
    d.enregistrer_familles(c, ["CUISINE"])
    d.enregistrer_produits_marche(c, [ProduitMarche("FR", a, ti, "MarqueDemo", f) for a, ti, f, *_ in produits])
    for k, (a, _, f, prix, bsr, suivi) in enumerate(produits):
        if suivi:
            d.ajouter_suivi(c, "FR", a)
        d.enregistrer_releves(c, [Releve(
            "FR", a, date.fromordinal(jour.toordinal() - n),
            Decimal(str(round(prix * (1 + 0.06 * math.sin((n + k) / 5) - 0.002 * n * (k - 1)), 2))),
            3 + (n + k) % 3, k % 2, k == 2 and n % 3 == 0, k == 2 and n % 6 == 0, None,
            int(bsr * (1 + 0.25 * math.sin((n * (k + 2)) / 3))), "Cuisine") for n in range(40)])
