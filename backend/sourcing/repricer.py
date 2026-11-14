"""Prix plancher envoyé au repricer gratuit d'Amazon (Automate Pricing) — [RM-AMZ-122 à 124].

Rien n'est envoyé sans validation du vendeur. Débit sous 5 requêtes/s (getListingsItem, patchListingsItem).
"""
from __future__ import annotations

import time
from typing import Optional

from .analyse import analyser_asin
from .marketplaces import get_marketplace

PAUSE = 0.25


def client_offres(fx):
    return next((s for s in fx.catalogue if hasattr(s, "lire_offre")), None)


def plancher_de(mp, asin: str, cout_unitaire: float, fx, parametres) -> Optional[float]:
    a = analyser_asin(mp, asin, parametres.couts(cout_unitaire), fx, parametres.regime(mp.code), parametres.seuils(),
                      **parametres.options_cout())
    return a.prix_plancher


def preparer(lignes: list[dict], fx, parametres, attendre=time.sleep) -> list[dict]:
    """[RM-AMZ-123] Proposition par SKU : prix actuel, plancher, maximum par défaut, règles du vendeur."""
    cl = client_offres(fx)
    regles_cache: dict = {}
    out = []
    for l in lignes:
        mp = get_marketplace(l["marketplace"])
        base = {"sku": l["sku"], "asin": l.get("asin"), "marketplace": mp.code, "devise": mp.devise}
        try:
            o = cl.lire_offre(mp, l["sku"])
            attendre(PAUSE)
            plancher = plancher_de(mp, l["asin"], float(l["cout_unitaire"]), fx, parametres) if l.get("cout_unitaire") else None
            cle = (mp.code, o["type_produit"])
            if o["type_produit"] and cle not in regles_cache:
                regles_cache[cle] = cl.regles_prix(mp, o["type_produit"])
                attendre(PAUSE)
            regles = regles_cache.get(cle, [])
            regle = o["regle"] or next((r["id"] for r in regles if "COMPETITIVE" in r["id"]), regles[0]["id"] if regles else None)
            out.append({**base, "type_produit": o["type_produit"], "prix": o["prix"], "plancher": plancher,
                        "minimum": plancher, "maximum": round(plancher * 2, 2) if plancher else None,
                        "regles": regles, "regle": regle, "actuel": {"minimum": o["minimum"], "maximum": o["maximum"],
                                                                     "regle": o["regle"]}})
        except Exception as e:
            out.append({**base, "erreur": f"{type(e).__name__}: {str(e)[:200]}"})
    return out


def envoyer(lignes: list[dict], fx, attendre=time.sleep) -> list[dict]:
    """[RM-AMZ-123] Remplace l'offre en gardant tout ce qu'elle contient (dont le prix) ; min, max, règle posés."""
    cl = client_offres(fx)
    out = []
    for l in lignes:
        mp = get_marketplace(l["marketplace"])
        try:
            mini, maxi = float(l["minimum"]), float(l["maximum"])
            if not (0 < mini <= maxi) or not l.get("regle"):
                out.append({"sku": l["sku"], "statut": "REFUSE", "probleme": "VALEURS_INVALIDES"})
                continue
            o = cl.lire_offre(mp, l["sku"])
            attendre(PAUSE)
            if not o["offre"] or not o["type_produit"]:
                out.append({"sku": l["sku"], "statut": "REFUSE", "probleme": "OFFRE_INTROUVABLE"})
                continue
            offre = dict(o["offre"])
            offre.setdefault("marketplace_id", mp.marketplace_id)
            offre.setdefault("currency", mp.devise)
            offre.setdefault("audience", "ALL")
            offre["minimum_seller_allowed_price"] = [{"schedule": [{"value_with_tax": round(mini, 2)}]}]
            offre["maximum_seller_allowed_price"] = [{"schedule": [{"value_with_tax": round(maxi, 2)}]}]
            offre["automated_pricing_merchandising_rule_plan"] = [{"merchandising_rule": {"rule_id": l["regle"]}}]
            r = cl.remplacer_offre(mp, l["sku"], o["type_produit"], offre)
            attendre(PAUSE)
            out.append({"sku": l["sku"], "statut": r.get("status", "?"),
                        "problemes": [i.get("message") for i in r.get("issues", []) or []]})
        except Exception as e:
            out.append({"sku": l["sku"], "statut": "ERREUR", "probleme": f"{type(e).__name__}: {str(e)[:200]}"})
    return out


def alertes(lignes_stock, fx, parametres, attendre=time.sleep) -> list[dict]:
    """[RM-AMZ-124] SKU en stock dont le prix actuel est sous le plancher."""
    cl = client_offres(fx)
    out = []
    if cl is None:
        return out
    for l in lignes_stock:
        if l.cout_unitaire is None or not l.photo.asin or not l.photo.sku:
            continue
        mp = get_marketplace(l.photo.marketplace)
        try:
            o = cl.lire_offre(mp, l.photo.sku)
            attendre(PAUSE)
            p = plancher_de(mp, l.photo.asin, float(l.cout_unitaire), fx, parametres)
        except Exception:
            continue
        if o["prix"] is not None and p is not None and o["prix"] < p:
            out.append({"marketplace": mp.code, "sku": l.photo.sku, "asin": l.photo.asin, "prix": o["prix"], "plancher": p})
    return out
