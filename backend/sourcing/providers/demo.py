"""Fournisseur de démonstration : données FICTIVES pour tester l'outil sans clé API.

Aucune de ces valeurs ne correspond à un vrai produit.
"""
from __future__ import annotations

import hashlib

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
        if code.isdigit() and code.startswith("200") and len(code) == 13:   # catalogue généré, fictif
            p = _genere(code)
            _PRODUITS.setdefault(p["cat"].asin, p)
            return [p["cat"].asin]
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


# --------------------------------------------------------------------- catalogue généré (démo)
# Codes fictifs : préfixe 200 (plage GS1 « usage interne », jamais attribuée à une marque).

_NOMS = ["Boîte hermétique verre", "Moulin à épices", "Égouttoir pliable", "Couvercles silicone", "Planche bambou",
         "Thermos 500 ml", "Lampe de bureau LED", "Tapis de yoga", "Gourde sport 1 L", "Set de pinceaux",
         "Puzzle 500 pièces", "Câble HDMI 2 m", "Balance de cuisine", "Brosse à vaisselle", "Sac isotherme",
         "Porte-clés traceur", "Étui carte bancaire", "Chargeur USB-C", "Bougie parfumée", "Organiseur tiroir"]


def _h(code: str, k: int, n: int) -> int:
    return int(hashlib.sha256(f"{code}:{k}".encode()).hexdigest(), 16) % n


def _genere(code: str):
    asin = "B0GEN" + code[-5:]
    prix = round(9.99 + _h(code, 1, 3000) / 100, 2)
    nom = _NOMS[_h(code, 2, len(_NOMS))] + " (démo)"
    pack = 6 if _h(code, 3, 10) == 0 else 1
    restreint = _h(code, 4, 8) == 0
    amazon = _h(code, 5, 6) == 0
    nb_fba = 1 + _h(code, 6, 9)
    ventes = [8, 30, 60, 120, 250][_h(code, 7, 5)]
    moy = round(prix * (0.85 + _h(code, 8, 30) / 100), 2)
    return dict(
        cat=InfosCatalogue(asin, nom, "MarqueDemo", "Maison", 500 + _h(code, 9, 40000), pack),
        off=InfosOffres(prix, amazon, amazon, nb_fba, 1, prix),
        frais=FraisAmazon(commission=round(prix * 0.15, 2), fba=round(2.8 + _h(code, 10, 300) / 100, 2), source="démo"),
        restr=InfosRestrictions(autorise=not restreint, approbation_requise=restreint,
                                motifs=["APPROVAL_REQUIRED"] if restreint else []),
        hist=Historique(moy, round(moy * 0.9, 2), round(moy * 1.15, 2), 3000, ventes // 3, ventes, ventes,
                        0.8 if amazon else None, nb_fba),
    )

