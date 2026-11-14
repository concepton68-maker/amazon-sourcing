"""Tableau de bord — [RM-AMZ-091 à 094]. Calculs purs ; montants par devise, jamais additionnés entre devises."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from .lots import rattacher_fifo

JOURS = 30


def _fenetre(jour: date, j: date, decalage: int = 0) -> bool:
    fin = jour - timedelta(days=decalage)
    return fin - timedelta(days=JOURS) < j <= fin


def devise_principale(devises) -> Optional[str]:
    devises = sorted(set(devises))
    return "EUR" if "EUR" in devises else (devises[0] if devises else None)


def chiffres(lots, ventes, lignes_stock, jour: date) -> dict:
    """[RM-AMZ-091, 092] Par devise : ventes, variation, profit réel, ROI réel, stock ; série du profit par jour."""
    par: dict[str, dict] = {}

    def d(dev):
        return par.setdefault(dev, {"ventes": Decimal(0), "ventes_avant": Decimal(0), "profit": Decimal(0),
                                    "cout": Decimal(0), "stock": Decimal(0), "par_jour": {}})
    for v in ventes:
        dev = v.chiffre_affaires_ht.devise
        if _fenetre(jour, v.jour):
            d(dev)["ventes"] += v.chiffre_affaires_ht.valeur
        elif _fenetre(jour, v.jour, JOURS):
            d(dev)["ventes_avant"] += v.chiffre_affaires_ht.valeur
    res, orphelines = rattacher_fifo(lots, ventes)
    for r in res.values():
        dev = r.lot.prevision.devise
        for a in r.allocations:
            if not _fenetre(jour, a.vente.jour):
                continue
            cout = r.lot.prevision.cout_achat * a.quantite
            p = a.vente.net.valeur * a.part - cout
            x = d(dev)
            x["profit"] += p
            x["cout"] += cout
            x["par_jour"][a.vente.jour] = x["par_jour"].get(a.vente.jour, Decimal(0)) + p
    sans_cout = 0
    for l in lignes_stock:
        unites = l.photo.disponible + l.photo.en_route
        if l.cout_unitaire is None:
            sans_cout += unites
        elif unites:
            d(l.devise)["stock"] += l.cout_unitaire * unites
    principale = devise_principale(par)
    out = {}
    for dev, x in sorted(par.items()):
        out[dev] = {"ventes": x["ventes"], "profit": x["profit"], "stock": x["stock"],
                    "variation_ventes": (x["ventes"] - x["ventes_avant"]) / x["ventes_avant"] if x["ventes_avant"] else None,
                    "roi": x["profit"] / x["cout"] if x["cout"] else None}
    serie = []
    if principale:
        pj = par[principale]["par_jour"]
        serie = [{"jour": (jour - timedelta(days=k)).isoformat(),
                  "profit": pj.get(jour - timedelta(days=k), Decimal(0))} for k in range(JOURS - 1, -1, -1)]
    return {"devise": principale, "par_devise": out, "serie": serie,
            "ventes_non_rattachees": sum(1 for a in orphelines if _fenetre(jour, a.vente.jour)),
            "unites_sans_cout": sans_cout}


def a_faire(lignes_stock, cas, lignes_conformite, journal) -> dict:
    """[RM-AMZ-093] Nombres > 0 seulement (sauf la synchronisation, toujours présente)."""
    from .remboursements import DETECTE
    detectes = [c for c in cas if c.statut == DETECTE]
    valeur: dict[str, Decimal] = {}
    for c in detectes:
        if c.valeur_achat is not None:
            valeur[c.devise] = valeur.get(c.devise, Decimal(0)) + c.valeur_achat
    derniers: dict = {}
    for r in journal:
        if r.tache not in derniers or r.fin >= derniers[r.tache].fin:
            derniers[r.tache] = r
    synchro = None
    if derniers:
        synchro = {"le": max(r.fin for r in derniers.values()).isoformat(),
                   "echecs": sorted(t for t, r in derniers.items() if not r.ok)}
    out = {"recommander": sum(1 for l in lignes_stock if l.a_commander > 0),
           "remboursements": len(detectes), "valeur_remboursements": valeur,
           "conformite": sum(1 for l in lignes_conformite if l.statut == "A_COMPLETER"), "synchro": synchro}
    return out


def mouvements(releves, jour: date, n: int = 5) -> list[dict]:
    """[RM-AMZ-094] Plus fortes variations du prix de la Buy Box sur 7 jours (≥ 2 relevés)."""
    from .historique import tendances
    par: dict[str, list] = {}
    for r in releves:
        par.setdefault(r.asin, []).append(r)
    out = []
    for asin, rel in par.items():
        t = tendances(rel, jour, 7)
        if t["prix_variation"] is not None and t["releves"] >= 2:
            out.append({"asin": asin, "variation": t["prix_variation"], "prix": t["prix_dernier"], "bsr": t["bsr_dernier"]})
    out.sort(key=lambda x: (-abs(x["variation"]), x["asin"]))
    return out[:n]
