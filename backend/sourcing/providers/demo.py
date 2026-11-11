"""Fournisseur de démonstration : données FICTIVES pour tester l'outil sans clé API.

Aucune de ces valeurs ne correspond à un vrai produit.
"""
from __future__ import annotations

from ..marketplaces import Marketplace
from ..profit import FraisAmazon
from .base import Historique, InfosCatalogue, InfosOffres, InfosRestrictions

_PRODUITS = {
    "B0DEMO0001": dict(
        cat=InfosCatalogue("B0DEMO0001", "Gourde inox 750 ml (démo)", "MarqueDemo", "Sports", 4200, 1),
        off=InfosOffres(24.90, False, False, 4, 1, 24.90),
        frais=FraisAmazon(commission=3.74, fba=4.15, source="sp-api"),
        restr=InfosRestrictions(autorise=True),
        hist=Historique(23.50, 21.90, 26.00, 5100, 40, 118, 100, None, 4),
    ),
    "B0DEMO0002": dict(
        cat=InfosCatalogue("B0DEMO0002", "Jouet de construction 500 pièces (démo)", "GrandeMarqueDemo", "Jeux et Jouets", 950, 1),
        off=InfosOffres(39.99, True, True, 9, 2, 40.50),
        frais=FraisAmazon(commission=6.00, fba=5.20, source="sp-api"),
        restr=InfosRestrictions(autorise=False, approbation_requise=True,
                                motifs=["APPROVAL_REQUIRED : approbation de la marque nécessaire (démo)"]),
        hist=Historique(34.50, 29.99, 41.99, 1300, 210, 640, 600, 0.92, 10),
    ),
}
_EAN = {"3700000000017": ["B0DEMO0001"], "3700000000024": ["B0DEMO0002"]}


class FournisseurDemo:
    def rechercher_asins(self, mp: Marketplace, code: str) -> list[str]:
        code = code.strip().upper()
        return [code] if code in _PRODUITS else _EAN.get(code, [])

    def catalogue(self, mp, asin):
        return _PRODUITS[asin]["cat"]

    def offres(self, mp, asin):
        return _PRODUITS[asin]["off"]

    def frais(self, mp, asin, prix_vente):
        f = _PRODUITS[asin]["frais"]
        # commission proportionnelle au prix demandé
        ratio = f.commission / _PRODUITS[asin]["off"].prix_buybox
        return FraisAmazon(commission=round(prix_vente * ratio, 2), fba=f.fba, source="démo")

    def restrictions(self, mp, asin):
        return _PRODUITS[asin]["restr"]

    def historique(self, mp, asin):
        return _PRODUITS[asin]["hist"]
