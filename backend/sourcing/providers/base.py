"""Interfaces des fournisseurs de données et structures communes.

Chaque champ porte implicitement sa nature :
- OBSERVÉ  : lu directement chez Amazon (offres, restrictions, frais SP-API)
- HISTORIQUE : séries Keepa (prix, BSR) -> observé dans le passé
- ESTIMÉ   : ventes mensuelles (déduites du BSR ou du badge « achetés le mois dernier »)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol

from ..marketplaces import Marketplace
from ..profit import FraisAmazon


@dataclass
class InfosCatalogue:
    asin: str
    titre: Optional[str] = None
    marque: Optional[str] = None
    categorie: Optional[str] = None
    bsr: Optional[int] = None
    nb_unites_lot: Optional[int] = None   # « Pack of 6 » -> 6 si connu
    classification: Optional[str] = None  # itemClassification du catalogue [RM-AMZ-082]
    nb_variantes: Optional[int] = None
    dimensions_cm: Optional[tuple] = None   # colis (catalogue « package ») [RM-AMZ-096]
    poids_kg: Optional[float] = None
    groupe_affichage: Optional[str] = None  # websiteDisplayGroup du classement des ventes
    codes: tuple = ()                       # EAN, UPC, GTIN, ISBN du catalogue [RM-AMZ-109]


@dataclass
class InfosOffres:
    prix_buybox: Optional[float] = None
    buybox_amazon: Optional[bool] = None     # Amazon détient la Buy Box ?
    amazon_vend: Optional[bool] = None       # Amazon présent sur le listing ?
    nb_offres_fba: Optional[int] = None
    nb_offres_fbm: Optional[int] = None
    prix_plus_bas_fba: Optional[float] = None
    vendeur_buybox: Optional[str] = None     # SellerId de l'offre IsBuyBoxWinner [RM-AMZ-118]


@dataclass
class InfosRestrictions:
    autorise: Optional[bool] = None          # None = inconnu
    approbation_requise: bool = False
    motifs: list[str] = field(default_factory=list)
    liens: list[dict] = field(default_factory=list)   # [RM-AMZ-120] liens de suite donnés par Amazon (titre, url)


@dataclass
class Historique:
    prix_buybox_moy90: Optional[float] = None
    prix_buybox_min90: Optional[float] = None
    prix_buybox_max90: Optional[float] = None
    bsr_moy90: Optional[int] = None
    chutes_bsr_30j: Optional[int] = None     # nombre de baisses de rang ≈ ventes (proxy)
    chutes_bsr_90j: Optional[int] = None
    ventes_mois_estimees: Optional[int] = None  # badge Amazon « bought in past month » via Keepa
    amazon_en_stock_pct90: Optional[float] = None
    nb_offres_neuf_moy90: Optional[int] = None


class FournisseurCatalogue(Protocol):
    def rechercher_asins(self, mp: Marketplace, code: str) -> list[str]:
        """EAN/UPC/ISBN -> liste d'ASIN (souvent 1, parfois plusieurs : lots, variantes)."""
    def catalogue(self, mp: Marketplace, asin: str) -> InfosCatalogue: ...


class FournisseurOffres(Protocol):
    def offres(self, mp: Marketplace, asin: str) -> InfosOffres: ...


class FournisseurFrais(Protocol):
    def frais(self, mp: Marketplace, asin: str, prix_vente: float) -> FraisAmazon: ...


class FournisseurRestrictions(Protocol):
    def restrictions(self, mp: Marketplace, asin: str) -> InfosRestrictions: ...


class FournisseurHistorique(Protocol):
    def historique(self, mp: Marketplace, asin: str) -> Historique: ...


class ErreurFournisseur(RuntimeError):
    pass
