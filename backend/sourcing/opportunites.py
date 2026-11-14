"""Liste des produits rentables — [RM-AMZ-105 à 108]. Fonctions pures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

VENDABLE, NON_VENDABLE, PROBABLE, PROBABLE_NON, INCONNU = (
    "VENDABLE", "NON_VENDABLE", "PROBABLEMENT_VENDABLE", "PROBABLEMENT_NON_VENDABLE", "INCONNU")
NIVEAUX = (VENDABLE, PROBABLE, PROBABLE_NON, NON_VENDABLE, INCONNU)
TRIS = ("profit", "roi", "marge", "prix_vente", "prix_achat", "rotation", "bsr")


def vendabilite(restrictions) -> tuple[str, Optional[str]]:
    """[RM-AMZ-106] Réponse d'Amazon pour CE produit : seule source d'un niveau « sûr »."""
    if restrictions is None or restrictions.autorise is None:
        return INCONNU, None
    if restrictions.autorise:
        return VENDABLE, None
    return NON_VENDABLE, "APPROBATION" if restrictions.approbation_requise else "INTERDIT"


@dataclass
class Opportunite:
    origine: str                     # « FOURNISSEUR:<id> » ou « FICHIER:<nom> »
    origine_nom: str
    marketplace: str
    code: str
    asin: str
    titre: Optional[str] = None
    designation: Optional[str] = None
    prix_achat: Optional[float] = None       # prix unitaire fournisseur
    unites_lot: int = 1
    cout_achat: Optional[float] = None       # coût du listing (lot compris)
    prix_vente: Optional[float] = None
    profit: Optional[float] = None
    roi: Optional[float] = None
    marge: Optional[float] = None
    prix_achat_max: Optional[float] = None
    verdict: Optional[str] = None
    vendabilite: str = INCONNU
    motif: Optional[str] = None
    bsr: Optional[int] = None
    nb_vendeurs: Optional[int] = None
    amazon_vend: Optional[bool] = None
    analyse_le: Optional[datetime] = None
    rotation: Optional[int] = None           # [RM-AMZ-108] calculée à la lecture, jamais stockée
    historique_court: bool = True
    extra: dict = field(default_factory=dict)


@dataclass
class Criteres:
    tri: str = "profit"
    decroissant: bool = True
    vendabilites: Optional[set] = None       # None = tous
    roi_min: Optional[float] = None
    profit_min: Optional[float] = None
    marge_min: Optional[float] = None
    origine: Optional[str] = None
    verdict: Optional[str] = None
    amazon_absent: bool = False


def filtrer_trier(ops: list[Opportunite], c: Criteres) -> list[Opportunite]:
    """[RM-AMZ-107] Une valeur absente ne passe jamais un seuil ; elle est toujours classée en dernier."""
    if c.tri not in TRIS:
        raise ValueError("TRI_INCONNU")

    def garde(o: Opportunite) -> bool:
        if c.vendabilites is not None and o.vendabilite not in c.vendabilites:
            return False
        for seuil, v in ((c.roi_min, o.roi), (c.profit_min, o.profit), (c.marge_min, o.marge)):
            if seuil is not None and (v is None or v < seuil):
                return False
        if c.origine and o.origine != c.origine:
            return False
        if c.verdict and o.verdict != c.verdict:
            return False
        if c.amazon_absent and o.amazon_vend is not False:
            return False
        return True
    gardes = [o for o in ops if garde(o)]
    avec = [o for o in gardes if getattr(o, c.tri) is not None]
    sans = [o for o in gardes if getattr(o, c.tri) is None]
    avec.sort(key=lambda o: (getattr(o, c.tri), o.asin), reverse=c.decroissant)
    return avec + sans


def _date(o: Opportunite) -> datetime:
    from datetime import timezone
    d = o.analyse_le or datetime.min.replace(tzinfo=timezone.utc)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def sans_doublon(ops: list[Opportunite]) -> list[Opportunite]:
    """[RM-AMZ-105] Même fournisseur, même code, même ASIN, même place : le plus récent seulement."""
    def cle(o):
        f = o.origine.split(":", 1)[1] if o.origine.startswith(("FOURNISSEUR:", "CORRESPONDANCE:")) else o.origine
        return (f, o.marketplace, o.code, o.asin)
    garde: dict = {}
    for o in ops:
        k = cle(o)
        if k not in garde or _date(o) > _date(garde[k]):
            garde[k] = o
    return list(garde.values())
