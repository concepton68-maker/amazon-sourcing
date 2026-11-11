"""Client API Keepa — historique de prix et de rang (BSR).

Données HISTORIQUES (observées dans le passé) et ESTIMÉES (ventes mensuelles).
Variable d'environnement : KEEPA_API_KEY.

Coût : abonnement API séparé de l'abonnement Keepa classique, facturé en
« jetons par minute » (à partir de ~49 €/mois pour 20 jetons/min selon des
sources tierces ; à vérifier sur keepa.com). Une requête produit avec `stats`
coûte en général 1 jeton ; les options `offers`/`buybox` coûtent davantage.

Format Keepa : prix en centimes (entiers), -1 = pas de donnée. Les tableaux
`stats.current` / `stats.avg90` sont indexés par type de série :
  0 AMAZON · 1 NEW · 3 SALES (BSR) · 11 COUNT_NEW · 18 BUY_BOX_SHIPPING
"""
from __future__ import annotations

import os
from typing import Optional

import requests

from ..marketplaces import Marketplace
from .base import ErreurFournisseur, Historique, InfosCatalogue

API = "https://api.keepa.com"
AMAZON, NEW, SALES, COUNT_NEW, BUY_BOX = 0, 1, 3, 11, 18


class ClientKeepa:
    def __init__(self, cle: Optional[str] = None, session: Optional[requests.Session] = None):
        self.cle = cle or os.environ.get("KEEPA_API_KEY")
        if not self.cle:
            raise ErreurFournisseur("KEEPA_API_KEY manquante.")
        self.session = session or requests.Session()
        self.jetons_restants: Optional[int] = None
        self._cache: dict[tuple[str, str], dict] = {}

    def _domaine(self, mp: Marketplace) -> int:
        if mp.keepa_domain is None:
            raise ErreurFournisseur(f"Keepa ne couvre pas {mp.domaine} (à notre connaissance).")
        return mp.keepa_domain

    def _produits(self, mp: Marketplace, **params) -> list[dict]:
        r = self.session.get(
            f"{API}/product",
            params={"key": self.cle, "domain": self._domaine(mp), "stats": 90, **params},
            timeout=60,
        )
        if r.status_code == 429:
            raise ErreurFournisseur("Keepa : plus de jetons disponibles, réessayer dans une minute.")
        if r.status_code >= 400:
            raise ErreurFournisseur(f"Keepa -> {r.status_code} : {r.text[:300]}")
        data = r.json()
        self.jetons_restants = data.get("tokensLeft")
        return data.get("products") or []

    def _produit(self, mp: Marketplace, asin: str) -> dict:
        cle = (mp.code, asin)
        if cle not in self._cache:
            prods = self._produits(mp, asin=asin)
            if not prods:
                raise ErreurFournisseur(f"Keepa : ASIN {asin} introuvable sur {mp.domaine}.")
            self._cache[cle] = prods[0]
        return self._cache[cle]

    # -------------------------------------------------------------- interfaces
    def rechercher_asins(self, mp: Marketplace, code: str) -> list[str]:
        code = code.strip()
        if len(code) == 10 and code[0].upper() == "B":
            return [code.upper()]
        prods = self._produits(mp, code=code)
        for p in prods:
            self._cache[(mp.code, p["asin"])] = p
        return [p["asin"] for p in prods if p.get("asin")]

    def catalogue(self, mp: Marketplace, asin: str) -> InfosCatalogue:
        return parser_catalogue(self._produit(mp, asin))

    def historique(self, mp: Marketplace, asin: str) -> Historique:
        return parser_historique(self._produit(mp, asin))


# ====================================================================== parseurs

def _val(tab, idx) -> Optional[int]:
    if not tab or idx >= len(tab):
        return None
    v = tab[idx]
    return None if v is None or v < 0 else int(v)


def _prix(tab, idx) -> Optional[float]:
    v = _val(tab, idx)
    return None if v is None else v / 100.0


def parser_catalogue(p: dict) -> InfosCatalogue:
    stats = p.get("stats") or {}
    cat = None
    tree = p.get("categoryTree") or []
    if tree:
        cat = tree[0].get("name")
    return InfosCatalogue(
        asin=p.get("asin"),
        titre=p.get("title"),
        marque=p.get("brand"),
        categorie=cat,
        bsr=_val(stats.get("current"), SALES),
        nb_unites_lot=p.get("packageQuantity") or p.get("numberOfItems") or None,
    )


def parser_historique(p: dict) -> Historique:
    s = p.get("stats") or {}
    # minInInterval / maxInInterval = extrêmes sur la période `stats` (90 j) ;
    # min / max = extrêmes historiques (repli si les premiers sont absents).
    avg = s.get("avg90")
    mini = s.get("minInInterval") or s.get("min")
    maxi = s.get("maxInInterval") or s.get("max")

    def extremum(tab):
        # liste de [temps Keepa, valeur] par série (ou -1/None)
        if not tab or BUY_BOX >= len(tab) or not tab[BUY_BOX]:
            return None
        e = tab[BUY_BOX]
        return e[1] / 100.0 if isinstance(e, list) and len(e) == 2 and e[1] >= 0 else None

    oos = s.get("outOfStockPercentage90")
    amazon_stock = None
    if oos and len(oos) > AMAZON and oos[AMAZON] is not None and oos[AMAZON] >= 0:
        amazon_stock = round(1 - oos[AMAZON] / 100.0, 2)

    vendus = p.get("monthlySold")
    return Historique(
        prix_buybox_moy90=_prix(avg, BUY_BOX) or _prix(avg, NEW),
        prix_buybox_min90=extremum(mini),
        prix_buybox_max90=extremum(maxi),
        bsr_moy90=_val(avg, SALES),
        chutes_bsr_30j=s.get("salesRankDrops30"),
        chutes_bsr_90j=s.get("salesRankDrops90"),
        ventes_mois_estimees=vendus if isinstance(vendus, int) and vendus >= 0 else None,
        amazon_en_stock_pct90=amazon_stock,
        nb_offres_neuf_moy90=_val(avg, COUNT_NEW),
    )
