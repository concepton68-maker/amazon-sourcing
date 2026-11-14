"""Sérialisation des lignes de bon (stockage JSON)."""
from __future__ import annotations

from decimal import Decimal

from .achats import LigneBon
from .lots import Prevision


def prevision_vers_dict(p: Prevision) -> dict:
    return {"devise": p.devise, "prix_vente_ht": str(p.prix_vente_ht), "frais_amazon": str(p.frais_amazon),
            "cout_achat": str(p.cout_achat), "retours": str(p.retours), "stockage": str(p.stockage),
            "autres": str(p.autres), "sources": list(p.sources)}


def prevision_depuis_dict(p: dict) -> Prevision:
    return Prevision(p["devise"], Decimal(p["prix_vente_ht"]), Decimal(p["frais_amazon"]), Decimal(p["cout_achat"]),
                     Decimal(p["retours"]), Decimal(p["stockage"]), Decimal(p["autres"]), tuple(p["sources"]))


def ligne_vers_dict(l: LigneBon) -> dict:
    d = {"id": l.id, "asin": l.asin, "marketplace": l.marketplace, "designation": l.designation,
         "quantite": l.quantite, "prix_unitaire": str(l.prix_unitaire), "quantite_recue": l.quantite_recue,
         "lot_id": l.lot_id, "prevision": prevision_vers_dict(l.prevision)}
    if l.code:
        d["code"] = l.code
    if l.unites_lot != 1:
        d["unites_lot"] = l.unites_lot
    return d


def ligne_depuis_dict(d: dict) -> LigneBon:
    return LigneBon(d["id"], d["asin"], d["marketplace"], d.get("designation"), d["quantite"],
                    Decimal(d["prix_unitaire"]), prevision_depuis_dict(d["prevision"]), d.get("quantite_recue"),
                    d.get("lot_id"), d.get("code"), d.get("unites_lot", 1))
