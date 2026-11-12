"""Stock et réapprovisionnement — [RM-AMZ-045 à 048]."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, Optional

from .lots import Lot, VenteReelle
from .marketplaces import MARKETPLACES
from .messages import Message, m

_MP_PAR_ID = {mp.marketplace_id: mp.code for mp in MARKETPLACES.values()}


@dataclass
class PhotoStock:
    """Une ligne de la photo de nuit [RM-AMZ-045]."""
    marketplace: str
    sku: str
    asin: Optional[str]
    designation: Optional[str]
    disponible: int
    en_route: int
    reserve: int = 0
    invendable: int = 0


def _q(d: dict, *cles) -> int:
    for k in cles:
        d = (d or {}).get(k) if isinstance(d, dict) else None
    return int(d or 0)


def parser_inventaire(reponse: dict, marketplace: str) -> list[PhotoStock]:
    """`getInventorySummaries` (details=true) → lignes. Champs lus dans la référence officielle (notes § 1)."""
    corps = reponse.get("payload", reponse)
    out = []
    for s in corps.get("inventorySummaries", []) or []:
        if s.get("condition") not in (None, "", "NewItem"):
            continue                                   # stock neuf seulement
        det = s.get("inventoryDetails") or {}
        out.append(PhotoStock(
            marketplace=marketplace, sku=s.get("sellerSku") or s.get("fnSku") or "", asin=s.get("asin"),
            designation=s.get("productName"),
            disponible=_q(det, "fulfillableQuantity"),
            en_route=_q(det, "inboundWorkingQuantity") + _q(det, "inboundShippedQuantity") + _q(det, "inboundReceivingQuantity"),
            reserve=_q(det, "reservedQuantity", "totalReservedQuantity"),
            invendable=_q(det, "unfulfillableQuantity", "totalUnfulfillableQuantity")))
    return [x for x in out if x.sku]


@dataclass
class LigneStock:
    photo: PhotoStock
    vendus_30j: int
    vitesse: Decimal                       # unités par jour
    couverture: Optional[int]              # jours ; None = illimitée
    rupture_le: Optional[date]
    a_commander: int
    fournisseur: Optional[str]
    cout_unitaire: Optional[Decimal]
    devise: str
    alertes: list[Message] = field(default_factory=list)


def calculer(photos: Iterable[PhotoStock], ventes: Iterable[VenteReelle], lots: Iterable[Lot], aujourd_hui: date,
             delai_fournisseur: int = 7, delai_reception: int = 10, marge_securite: int = 14,
             seuil_rupture: int = 15, seuil_surstock: int = 180) -> list[LigneStock]:
    """[RM-AMZ-046, 047, 048]"""
    debut = aujourd_hui - timedelta(days=30)
    vendus: dict[tuple[str, str], int] = {}
    for v in ventes:
        if debut < v.jour <= aujourd_hui and v.quantite > 0:
            vendus[(v.asin, v.marketplace)] = vendus.get((v.asin, v.marketplace), 0) + v.quantite
    dernier_lot: dict[tuple[str, str], Lot] = {}
    for l in sorted(lots, key=lambda l: (l.date_achat, l.cree_le)):
        dernier_lot[(l.asin, l.marketplace)] = l
    horizon = delai_fournisseur + delai_reception + marge_securite
    out = []
    for p in photos:
        cle = (p.asin, p.marketplace)
        n = vendus.get(cle, 0)
        vitesse = Decimal(n) / Decimal(30)
        stock = p.disponible + p.en_route
        if vitesse > 0:
            couverture = int(Decimal(stock) / vitesse)
            rupture = aujourd_hui + timedelta(days=couverture)
            a_commander = max(0, math.ceil(vitesse * horizon) - stock)
        else:
            couverture, rupture, a_commander = None, None, 0
        lot = dernier_lot.get(cle)
        alertes = []
        if couverture is not None and couverture < seuil_rupture:
            alertes.append(m("S_RUPTURE", jours=couverture))
        if stock > 0 and couverture is None:
            alertes.append(m("S_SANS_VENTE"))
        elif couverture is not None and couverture > seuil_surstock:
            alertes.append(m("S_SURSTOCK", jours=couverture))
        out.append(LigneStock(p, n, vitesse, couverture, rupture, a_commander,
                              lot.fournisseur if lot else None, lot.prevision.cout_achat if lot else None,
                              lot.prevision.devise if lot else MARKETPLACES[p.marketplace].devise, alertes))
    return sorted(out, key=lambda x: (x.couverture is None, x.couverture if x.couverture is not None else 0))


@dataclass
class CommandeSuggeree:
    fournisseur: Optional[str]
    lignes: int
    unites: int
    montant: Optional[Decimal]
    devise: str


def commandes_par_fournisseur(lignes: list[LigneStock]) -> list[CommandeSuggeree]:
    """[RM-AMZ-048] Regroupe les quantités à commander par fournisseur (et devise)."""
    groupes: dict[tuple, CommandeSuggeree] = {}
    for l in lignes:
        if l.a_commander <= 0:
            continue
        cle = (l.fournisseur, l.devise)
        g = groupes.setdefault(cle, CommandeSuggeree(l.fournisseur, 0, 0, Decimal(0), l.devise))
        g.lignes += 1
        g.unites += l.a_commander
        if g.montant is not None and l.cout_unitaire is not None:
            g.montant += l.cout_unitaire * l.a_commander
        else:
            g.montant = None                               # coût inconnu : jamais un total deviné
    return sorted(groupes.values(), key=lambda g: -(g.montant or 0))


def synchroniser_stock(compte_id: str, mps, client, depot, jour: date, attendre=None) -> int:
    """[RM-AMZ-045] Photo de nuit : toutes les pages, sans pause longue (le jeton de page expire en 30 s)."""
    import time
    attendre = attendre or time.sleep
    total = 0
    for mp in mps:
        jeton, photos = None, []
        while True:
            page = client.page_inventaire(mp, jeton)
            photos += parser_inventaire(page, mp.code)
            jeton = (page.get("pagination") or page.get("payload", {}).get("pagination") or {}).get("nextToken")
            if not jeton:
                break
            attendre(0.5)                                  # 2 requêtes par seconde
        depot.enregistrer_photo_stock(compte_id, jour, photos)
        total += len(photos)
    return total
