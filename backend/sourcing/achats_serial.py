"""Sérialisation des lignes de bon (stockage JSON)."""
from __future__ import annotations

from decimal import Decimal

from .achats import LigneBon
from .lots import Prevision


def ligne_vers_dict(l: LigneBon) -> dict:
    p = l.prevision
    return {"id": l.id, "asin": l.asin, "marketplace": l.marketplace, "designation": l.designation,
            "quantite": l.quantite, "prix_unitaire": str(l.prix_unitaire), "quantite_recue": l.quantite_recue,
            "lot_id": l.lot_id, "prevision": {"devise": p.devise, "prix_vente_ht": str(p.prix_vente_ht),
            "frais_amazon": str(p.frais_amazon), "cout_achat": str(p.cout_achat), "retours": str(p.retours),
            "stockage": str(p.stockage), "autres": str(p.autres), "sources": list(p.sources)}}


def ligne_depuis_dict(d: dict) -> LigneBon:
    p = d["prevision"]
    prev = Prevision(p["devise"], Decimal(p["prix_vente_ht"]), Decimal(p["frais_amazon"]), Decimal(p["cout_achat"]),
                     Decimal(p["retours"]), Decimal(p["stockage"]), Decimal(p["autres"]), tuple(p["sources"]))
    return LigneBon(d["id"], d["asin"], d["marketplace"], d.get("designation"), d["quantite"],
                    Decimal(d["prix_unitaire"]), prev, d.get("quantite_recue"), d.get("lot_id"))
