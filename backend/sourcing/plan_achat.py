"""Plan d'achat : des produits rentables vers les bons de commande — [RM-AMZ-125, 126]."""
from __future__ import annotations

import math
from typing import Optional

from . import achats as A
from .achats_serial import prevision_depuis_dict

ORIGINES_FOURNISSEUR = ("FOURNISSEUR:", "CORRESPONDANCE:")


def fournisseur_de(origine: str) -> Optional[str]:
    for p in ORIGINES_FOURNISSEUR:
        if origine.startswith(p):
            return origine[len(p):]
    return None


def quantite_proposee(minimum: Optional[int], colisage: Optional[int], unites_lot: int) -> int:
    """[RM-AMZ-126] En lots vendus sur Amazon : max(minimum, colisage) arrondi au colisage, puis au lot."""
    col = colisage if colisage and colisage > 0 else 1
    unites = max(minimum or 1, col, 1)
    unites = math.ceil(unites / col) * col
    return max(1, math.ceil(unites / max(1, unites_lot)))


def _ligne_catalogue(depot, compte_id: str, fid: str, code: str):
    cat = depot.catalogue(compte_id, fid)
    if not cat:
        return None
    return next((l for l in cat[1] if str(l.code) == str(code)), None)


def ajouter(depot, compte_id: str, choix: list[dict]) -> dict:
    """[RM-AMZ-125] `choix` : [{origine, marketplace, code, asin, quantite?}] ; un brouillon par fournisseur."""
    ops = {(o.origine, o.marketplace, o.code, o.asin): o for o in depot.opportunites(compte_id)}
    fournisseurs = {f.id: f for f in depot.fournisseurs(compte_id)}
    brouillons: dict[str, A.BonCommande] = {}
    for b in sorted(depot.bons(compte_id), key=lambda b: b.numero):
        if b.statut == A.BROUILLON:
            brouillons[b.fournisseur_id] = b                  # le plus récent l'emporte
    modifies: dict[str, A.BonCommande] = {}
    ajoutees, deja, refus = 0, 0, []
    for c in choix:
        cle = (c.get("origine"), c.get("marketplace"), c.get("code"), c.get("asin"))
        o = ops.get(cle)
        if o is None:
            refus.append({"asin": cle[3], "code": cle[2], "motif": "INTROUVABLE"})
            continue
        fid = fournisseur_de(o.origine)
        f = fournisseurs.get(fid) if fid else None
        if f is None:
            refus.append({"asin": o.asin, "code": o.code, "motif": "FOURNISSEUR_REQUIS"})
            continue
        if not A.analysable(f):
            refus.append({"asin": o.asin, "code": o.code, "motif": "REVENTE_INTERDITE"})
            continue
        if not o.prevision:
            refus.append({"asin": o.asin, "code": o.code, "motif": "PREVISION_ABSENTE"})
            continue
        bon = modifies.get(f.id) or brouillons.get(f.id)
        if bon is None:
            bon = A.nouveau_bon(compte_id, depot.prochain_numero(compte_id), f)
            depot.enregistrer_bon(compte_id, bon)             # numéro réservé tout de suite
            brouillons[f.id] = bon
        if any(l.asin == o.asin and l.marketplace == o.marketplace and (l.code or o.code) == o.code for l in bon.lignes):
            deja += 1
            continue
        k = max(1, o.unites_lot or 1)
        q = c.get("quantite")
        if q is None:
            lc = _ligne_catalogue(depot, compte_id, f.id, o.code)
            q = quantite_proposee(getattr(lc, "minimum", None), getattr(lc, "colisage", None), k)
        prev = prevision_depuis_dict(o.prevision)
        prix = prev.cout_achat if o.cout_achat is None else o.cout_achat
        try:
            bon = A.ajouter_ligne(bon, o.asin, o.marketplace, q, prix, prev, o.titre or o.designation, f.devise,
                                  code=o.code, unites_lot=k)
        except A.ErreurAchat as e:
            refus.append({"asin": o.asin, "code": o.code, "motif": e.args[0]})
            continue
        modifies[f.id] = bon
        ajoutees += 1
    for b in modifies.values():
        depot.enregistrer_bon(compte_id, b)
    return {"ajoutees": ajoutees, "deja": deja, "refus": refus, "bons": [b.id for b in modifies.values()]}
