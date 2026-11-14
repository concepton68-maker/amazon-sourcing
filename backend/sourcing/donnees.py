"""Écran « Données » : chaque jeu collecté, en lignes plates — [RM-AMZ-140].

Le tri, la recherche et les filtres se font à l'écran (jeux de quelques milliers de lignes au plus).
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from . import historique as H
from . import opportunites as OP

LIMITE = 20000

# colonne : (clé, type) ; types : texte, nombre, monnaie, pourcent, date, oui_non, liste
COLONNES = {
    "produits": [("titre", "texte"), ("asin", "texte"), ("code", "texte"), ("origine_nom", "liste"), ("marketplace", "liste"),
                 ("prix_achat", "monnaie"), ("cout_achat", "monnaie"), ("prix_vente", "monnaie"), ("profit", "monnaie"),
                 ("roi", "pourcent"), ("marge", "pourcent"), ("prix_achat_max", "monnaie"), ("bsr", "nombre"),
                 ("nb_vendeurs", "nombre"), ("amazon_vend", "oui_non"), ("vendabilite", "liste"), ("verdict", "liste"),
                 ("unites_lot", "nombre"), ("analyse_le", "date")],
    "marche": [("titre", "texte"), ("marque", "texte"), ("asin", "texte"), ("famille", "liste"), ("marketplace", "liste"),
               ("prix_buybox", "monnaie"), ("prix_moyen", "monnaie"), ("prix_variation", "pourcent"), ("bsr", "nombre"),
               ("bsr_moyen", "nombre"), ("jours_baisse_bsr", "nombre"), ("vendeurs", "nombre"), ("amazon_vend", "oui_non"),
               ("buybox_amazon", "oui_non"), ("part_buybox_amazon", "pourcent"), ("buybox_moi", "oui_non"),
               ("releves", "nombre"), ("jour", "date")],
    "releves": [("asin", "texte"), ("titre", "texte"), ("marketplace", "liste"), ("jour", "date"), ("prix_buybox", "monnaie"),
                ("prix_bas_fba", "monnaie"), ("bsr", "nombre"), ("categorie", "texte"), ("nb_fba", "nombre"),
                ("nb_fbm", "nombre"), ("amazon_vend", "oui_non"), ("buybox_amazon", "oui_non"), ("buybox_moi", "oui_non")],
    "autorisations": [("titre", "texte"), ("asin", "texte"), ("rayon", "liste"), ("statut", "liste"), ("bsr", "nombre"),
                      ("categorie", "texte")],
    "catalogues": [("designation", "texte"), ("code", "texte"), ("fournisseur", "liste"), ("prix_unitaire", "monnaie"),
                   ("colisage", "nombre"), ("minimum", "nombre"), ("devise", "liste")],
}


def _v(x):
    if isinstance(x, Decimal):
        return float(x)
    if isinstance(x, date):
        return x.isoformat()
    return x


def produits(depot, compte_id: str) -> list[dict]:
    cles = [k for k, _ in COLONNES["produits"]]
    out = []
    for o in OP.sans_doublon(depot.opportunites(compte_id)):
        d = {k: _v(getattr(o, k, None)) for k in cles}
        d["origine"] = o.origine
        d["titre"] = o.titre or o.designation
        out.append(d)
    return out


def _places(depot, compte_id: str) -> list[str]:
    from .marketplaces import MARKETPLACES
    return list(MARKETPLACES)


def marche(depot, compte_id: str, aujourd_hui: date) -> list[dict]:
    """[RM-AMZ-140] Dernier relevé et tendances 30 jours, par produit et place."""
    out = []
    for mp in _places(depot, compte_id):
        rel = depot.releves(compte_id, mp, None, aujourd_hui - timedelta(days=30))
        if not rel:
            continue
        fiches = {p.asin: p for p in depot.produits_marche(compte_id, mp)}
        par: dict[str, list] = {}
        for r in rel:
            par.setdefault(r.asin, []).append(r)
        for asin, serie in par.items():
            d = max(serie, key=lambda r: r.jour)
            t = H.tendances(serie, aujourd_hui, 30)
            f = fiches.get(asin)
            out.append({"asin": asin, "marketplace": mp, "titre": getattr(f, "titre", None), "marque": getattr(f, "marque", None),
                        "famille": getattr(f, "famille", None), "prix_buybox": _v(d.prix_buybox), "prix_moyen": _v(t["prix_moyen"]),
                        "prix_variation": t["prix_variation"], "bsr": d.bsr, "bsr_moyen": t["bsr_moyen"],
                        "jours_baisse_bsr": t["jours_baisse_bsr"],
                        "vendeurs": None if d.nb_fba is None and d.nb_fbm is None else (d.nb_fba or 0) + (d.nb_fbm or 0),
                        "amazon_vend": d.amazon_vend, "buybox_amazon": d.buybox_amazon,
                        "part_buybox_amazon": t["part_buybox_amazon"], "buybox_moi": d.buybox_moi,
                        "releves": t["releves"], "jour": d.jour.isoformat()})
            if len(out) >= LIMITE:
                return out
    return out


def releves(depot, compte_id: str, aujourd_hui: date, jours: int = 90) -> list[dict]:
    out = []
    for mp in _places(depot, compte_id):
        fiches = None
        for r in depot.releves(compte_id, mp, None, aujourd_hui - timedelta(days=jours)):
            if fiches is None:
                fiches = {p.asin: p.titre for p in depot.produits_marche(compte_id, mp)}
            out.append({"asin": r.asin, "titre": fiches.get(r.asin), "marketplace": mp, "jour": r.jour.isoformat(),
                        "prix_buybox": _v(r.prix_buybox), "prix_bas_fba": _v(r.prix_bas_fba), "bsr": r.bsr,
                        "categorie": r.categorie, "nb_fba": r.nb_fba, "nb_fbm": r.nb_fbm, "amazon_vend": r.amazon_vend,
                        "buybox_amazon": r.buybox_amazon, "buybox_moi": getattr(r, "buybox_moi", None)})
            if len(out) >= LIMITE:
                return out
    return out


def autorisations(depot, compte_id: str) -> list[dict]:
    ex = depot.exploration(compte_id) or {}
    return [{"titre": p.get("titre"), "asin": p.get("asin"), "rayon": r.get("code"), "statut": p.get("statut"),
             "bsr": p.get("bsr"), "categorie": p.get("categorie"), "marketplace": ex.get("place")}
            for r in ex.get("rayons", []) for p in r.get("produits", [])]


def catalogues(depot, compte_id: str) -> list[dict]:
    out = []
    for f in depot.fournisseurs(compte_id):
        cat = depot.catalogue(compte_id, f.id)
        if not cat:
            continue
        for l in cat[1]:
            out.append({"designation": l.designation, "code": l.code, "fournisseur": f.nom,
                        "prix_unitaire": _v(l.prix_unitaire), "colisage": l.colisage, "minimum": l.minimum, "devise": f.devise})
            if len(out) >= LIMITE:
                return out
    return out


def jeu(nom: str, depot, compte_id: str, aujourd_hui: date) -> dict:
    if nom not in COLONNES:
        raise KeyError(nom)
    lignes = {"produits": lambda: produits(depot, compte_id), "marche": lambda: marche(depot, compte_id, aujourd_hui),
              "releves": lambda: releves(depot, compte_id, aujourd_hui),
              "autorisations": lambda: autorisations(depot, compte_id),
              "catalogues": lambda: catalogues(depot, compte_id)}[nom]()
    return {"jeu": nom, "colonnes": [{"cle": k, "type": t} for k, t in COLONNES[nom]], "lignes": lignes,
            "tronque": len(lignes) >= LIMITE}
