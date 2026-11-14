"""D'Amazon vers les fournisseurs — [RM-AMZ-109 à 112].

Clé commune : le code-barres. Un produit Amazon donne ses codes (catalogue), on les cherche dans tous les
catalogues fournisseurs du compte, chaque correspondance est analysée avec le prix et le port du fournisseur.
"""
from __future__ import annotations

import threading
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from . import achats as A
from .analyse import Seuils
from .fichier import LigneFournisseur

PAQUET = 20                 # « maxItems »: 20 (searchCatalogItems par identifiants)
PAUSE_CATALOGUE = 0.6       # sous 2 requêtes/s
JOURS_ANALYSES = 90


def normaliser(code) -> Optional[str]:
    """[RM-AMZ-109] Chiffres seulement, zéros de tête retirés ; None si ce n'est pas un code numérique."""
    c = "".join(ch for ch in str(code or "") if not ch.isspace())
    if not c.isdigit():
        return None
    c = c.lstrip("0")
    return c or None


def index_catalogues(depot, compte_id: str) -> dict[str, list[tuple]]:
    """Code normalisé → [(fournisseur, ligne)] sur tous les catalogues du compte."""
    idx: dict[str, list[tuple]] = {}
    for f in depot.fournisseurs(compte_id):
        cat = depot.catalogue(compte_id, f.id)
        if not cat:
            continue
        for l in cat[1]:
            n = normaliser(l.code)
            if n:
                idx.setdefault(n, []).append((f, l))
    return idx


def offres_pour(codes, idx) -> list[tuple]:
    vus, out = set(), []
    for c in codes:
        for f, l in idx.get(normaliser(c) or "", []):
            if (f.id, l.code) not in vus:
                vus.add((f.id, l.code))
                out.append((f, l))
    return out


def _parametres_fournisseur(parametres, f):
    if parametres is None or f.port_unitaire is None:
        return parametres
    return replace(parametres, port_fournisseur=float(f.port_unitaire))


def ou_acheter(mp, asin: str, fx, depot, compte_id: str, parametres, regime: str) -> dict:
    """[RM-AMZ-110] Toutes les offres de vos fournisseurs pour ce produit, profit décroissant."""
    from .traitement import _ligne
    cat = None
    for src in fx.catalogue:
        try:
            cat = src.catalogue(mp, asin)
            break
        except Exception:
            continue
    codes = list(cat.codes) if cat and cat.codes else []
    offres = offres_pour(codes, index_catalogues(depot, compte_id))
    lignes = []
    seuils = parametres.seuils() if parametres else Seuils()
    for f, l in offres:
        base = {"fournisseur_id": f.id, "fournisseur": f.nom, "revente": f.revente, "code": l.code,
                "designation": l.designation, "prix_unitaire": float(l.prix_unitaire), "colisage": l.colisage,
                "minimum": l.minimum, "delai_jours": f.delai_jours,
                "port_unitaire": None if f.port_unitaire is None else float(f.port_unitaire)}
        if not A.analysable(f):
            lignes.append({**base, "calcule": False})
            continue
        r = _ligne(l, mp, asin, fx, regime, seuils, False, _parametres_fournisseur(parametres, f))
        lignes.append({**base, "calcule": True, "unites_lot": r.unites_lot,
                       "cout_achat": None if r.cout_achat is None else float(r.cout_achat), "prix_vente": r.prix_vente,
                       "profit": r.profit, "roi": r.roi, "marge": r.marge, "verdict": r.verdict,
                       "vendabilite": r.vendabilite, "remarques": [x.to_dict() for x in r.lignes]})
    lignes.sort(key=lambda x: (not x["calcule"], x.get("profit") is None, -(x.get("profit") or 0)))
    return {"asin": asin, "codes": codes, "offres": lignes}


def candidats(depot, compte_id: str, mp_code: str, maintenant: datetime) -> list[str]:
    """[RM-AMZ-111] Autorisés du sondage, liste de suivi, familles relevées, analysés depuis 90 jours."""
    out: list[str] = []
    ex = depot.exploration(compte_id)
    if ex and ex.get("place") == mp_code:
        out += [p["asin"] for r in ex.get("rayons", []) for p in r.get("produits", []) if p.get("statut") == "AUTORISE"]
    out += depot.suivis(compte_id, mp_code)
    out += [p.asin for p in depot.produits_marche(compte_id, mp_code) if p.famille]
    out += depot.asins_analyses(compte_id, mp_code, maintenant - timedelta(days=JOURS_ANALYSES))
    return list(dict.fromkeys(a for a in out if a))


def executer(compte_id: str, mp, fx, depot, parametres, regime: str,
             progression: Callable[..., None] = lambda f, t, phase="": None,
             attendre: Callable[[float], None] = time.sleep, maintenant: Optional[datetime] = None) -> dict:
    """[RM-AMZ-111] Amazon d'abord : codes par paquets, correspondances analysées, rangées par fournisseur."""
    from .traitement import _ligne, opportunite
    maintenant = maintenant or datetime.now(timezone.utc)
    asins = candidats(depot, compte_id, mp.code, maintenant)
    idx = index_catalogues(depot, compte_id)
    paquet_src = next((s for s in fx.catalogue if hasattr(s, "catalogue_par_paquet")), None)
    trouves: list[tuple] = []                       # (asin, fournisseur, ligne)
    for i in range(0, len(asins), PAQUET):
        progression(i, len(asins), "CODES")
        morceau = asins[i:i + PAQUET]
        try:
            fiches = paquet_src.catalogue_par_paquet(mp, morceau) if paquet_src else {}
        except Exception:
            fiches = {}
        attendre(PAUSE_CATALOGUE)
        for a in morceau:
            c = fiches.get(a)
            for f, l in offres_pour(c.codes if c else (), idx):
                trouves.append((a, f, l))
    par_f: dict[str, list] = {}
    seuils = parametres.seuils() if parametres else Seuils()
    analysables = [(a, f, l) for a, f, l in trouves if A.analysable(f)]
    for k, (a, f, l) in enumerate(analysables):                      # [RM-AMZ-114] rangés au fil de l'eau
        progression(k, len(analysables), "ANALYSE")
        r = _ligne(LigneFournisseur(l.numero, l.code, l.prix_unitaire, l.designation, l.colisage, l.minimum), mp, a,
                   fx, regime, seuils, False, _parametres_fournisseur(parametres, f))
        par_f.setdefault(f.id, []).append(r)
        origine = (f"CORRESPONDANCE:{f.id}", f"{f.nom} · correspondance Amazon")
        depot.enregistrer_opportunites(compte_id, origine[0], origine[1], mp.code,
                                       [opportunite(origine, mp.code, x) for x in par_f[f.id] if x.statut == "ANALYSEE"])
    progression(len(analysables), len(analysables), "ANALYSE")
    return {"le": maintenant.isoformat(), "candidats": len(asins), "correspondances": len(trouves),
            "fournisseurs": len(par_f), "catalogues": len({f.id for _, f, _ in trouves})}


class Correspondances:
    """[RM-AMZ-112] Une à la fois par compte, en arrière-plan ; dernier bilan gardé en mémoire."""

    def __init__(self, en_fond: bool = True):
        self.en_cours: dict[str, tuple] = {}
        self.bilans: dict[str, dict] = {}
        self.en_fond = en_fond
        self._verrou = threading.Lock()

    def lancer(self, compte_id: str, mp, fx, depot, parametres, regime: str, attendre=time.sleep) -> bool:
        with self._verrou:
            if compte_id in self.en_cours:
                return False
            self.en_cours[compte_id] = (0, 0, "CODES")

        def travail():
            try:
                self.bilans[compte_id] = executer(compte_id, mp, fx, depot, parametres, regime,
                                                  lambda f, t, phase="": self.en_cours.__setitem__(compte_id, (f, t, phase)), attendre)
            except Exception as e:
                self.bilans[compte_id] = {"erreur": f"{type(e).__name__}: {str(e)[:200]}"}
            finally:
                self.en_cours.pop(compte_id, None)
        if self.en_fond:
            threading.Thread(target=travail, daemon=True).start()
        else:
            travail()
        return True
