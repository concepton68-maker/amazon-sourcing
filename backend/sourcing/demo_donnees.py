"""Jeu de données FICTIF pour le mode démo de l'interface : quatre lots et leurs ventes simulées,
passées par la vraie chaîne (normalisation Amazon → synchro → dépôt)."""
from __future__ import annotations

from datetime import date, datetime, timezone

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
    synchroniser(c, get_marketplace("FR"), _AmazonSimule(tx), d, datetime(2026, 11, 12, 3, tzinfo=timezone.utc),
                 classement=CLASSEMENT, attendre=lambda s: None)
    jour = date(2026, 11, 12)
    d.enregistrer_photo_stock(c, jour, [
        PhotoStock("FR", "GOURDE-750", "B0DEMO0001", "Gourde inox 750 ml", 3, 0),
        PhotoStock("DE", "LAMPE-LED", "B0DEMO0003", "Lampe frontale LED", 19, 0),
        PhotoStock("FR", "PUZZLE-1000", "B0DEMO0004", "Puzzle 1000 pièces", 18, 0, invendable=2),
        PhotoStock("IT", "COUTEAUX-5", "B0DEMO0005", "Set de couteaux 5 pièces", 22, 12),
        PhotoStock("FR", "BOUGIE-VIEILLE", "B0DEMO0099", "Bougie parfumée", 37, 0),
    ])
    return d, c
