"""Historique maison et suivi de marché — [RM-AMZ-086 à 090].

Chaque nuit, par compte : liste de suivi, produits analysés, familles suivies → un relevé par produit, place et jour
(prix de la Buy Box, offres, présence d'Amazon, classement). L'historique d'un compte ne sert qu'à ce compte
(politique d'usage SP-API 4.3, 4.4, 4.6) ; jamais mis en commun, jamais vendu.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from .exploration import RAYONS

PARIS = ZoneInfo("Europe/Paris")
FAMILLES = dict(RAYONS)                 # code → mots-clés (rayons de l'outil)
PLAFOND = 20_000                        # produits par compte et par nuit [RM-AMZ-086]
MAX_FAMILLE = 1_000                     # « maximum number of items … paged through is 1,000 »
PAQUET = 20                             # « maxItems »: 20 (getItemOffersBatch, searchCatalogItems)
JOURS_ANALYSES = 90
PAUSE_RECHERCHE = 0.6                   # sous 2 requêtes/s
PAUSE_CATALOGUE = 0.6                   # sous 2 requêtes/s
PAUSE_OFFRES = 10.5                     # sous 0,1 requête/s
ANS_CONSERVATION = 3                    # [RM-AMZ-088]
RELEVES_MIN = 7                         # en dessous : « historique court » [RM-AMZ-089]
SUIVI, ANALYSE, FAMILLE = "SUIVI", "ANALYSE", "FAMILLE"


@dataclass(frozen=True)
class Releve:
    marketplace: str
    asin: str
    jour: date
    prix_buybox: Optional[Decimal] = None
    nb_fba: Optional[int] = None
    nb_fbm: Optional[int] = None
    amazon_vend: Optional[bool] = None
    buybox_amazon: Optional[bool] = None
    prix_bas_fba: Optional[Decimal] = None
    bsr: Optional[int] = None
    categorie: Optional[str] = None
    buybox_moi: Optional[bool] = None        # [RM-AMZ-118] vous détenez la Buy Box


@dataclass(frozen=True)
class ProduitMarche:
    marketplace: str
    asin: str
    titre: Optional[str] = None
    marque: Optional[str] = None
    famille: Optional[str] = None


def jour_paris(maintenant: datetime) -> date:
    return maintenant.astimezone(PARIS).date()


def limite_conservation(jour: date) -> date:
    """Relevés antérieurs à cette date : effacés [RM-AMZ-088]."""
    try:
        return jour.replace(year=jour.year - ANS_CONSERVATION)
    except ValueError:                  # 29 février
        return jour.replace(year=jour.year - ANS_CONSERVATION, day=28)


def _dec(x) -> Optional[Decimal]:
    return None if x is None else Decimal(str(x))


# ------------------------------------------------------------------ périmètre [RM-AMZ-086]
def perimetre(suivis: list[str], analyses: list[str], familles: dict[str, list[str]],
              plafond: int = PLAFOND) -> list[tuple[str, str, Optional[str]]]:
    """[(asin, origine, famille)] sans doublon, dans l'ordre de priorité, plafonné."""
    out, vus = [], set()
    groupes = [(SUIVI, None, suivis), (ANALYSE, None, analyses)] + [(FAMILLE, f, l) for f, l in familles.items()]
    for origine, fam, asins in groupes:
        for a in asins:
            if len(out) >= plafond:
                return out
            if a and a not in vus:
                vus.add(a)
                out.append((a, origine, fam))
    return out


def produits_famille(client, mp, mots: str, attendre: Callable[[float], None],
                     maximum: int = MAX_FAMILLE) -> list:
    """Recherche page par page, parents de variantes écartés [RM-AMZ-082, 086]."""
    out, vus, jeton = [], set(), None
    for _ in range(maximum // PAQUET + 5):          # borne de sûreté
        items, jeton = client.rechercher_page(mp, mots, jeton)
        attendre(PAUSE_RECHERCHE)
        for c in items:
            if c.asin in vus or c.classification == "VARIATION_PARENT":
                continue
            vus.add(c.asin)
            out.append(c)
            if len(out) >= maximum:
                return out
        if not jeton:
            break
    return out


# ------------------------------------------------------------------ relevé [RM-AMZ-087]
def relever(client, mp, asins: list[str], connus: dict, jour: date, attendre: Callable[[float], None],
            enregistrer: Callable[[list[Releve]], None]) -> tuple[int, int]:
    """Relève par paquets de 20 et enregistre au fil de l'eau. Renvoie (relevés, paquets en erreur)."""
    fiches, erreurs, n = dict(connus), 0, 0
    moi = getattr(client, "seller_id", None)
    manquants = [a for a in asins if a not in fiches]
    for i in range(0, len(manquants), PAQUET):
        try:
            fiches.update(client.catalogue_par_paquet(mp, manquants[i:i + PAQUET]))
        except Exception:
            erreurs += 1
        attendre(PAUSE_CATALOGUE)
    for i in range(0, len(asins), PAQUET):
        paquet = asins[i:i + PAQUET]
        try:
            offres = client.offres_par_paquet(mp, paquet)
        except Exception:
            offres, erreurs = {}, erreurs + 1
        lot = []
        for a in paquet:
            o, c = offres.get(a), fiches.get(a)
            lot.append(Releve(mp.code, a, jour,
                              prix_buybox=_dec(o.prix_buybox) if o else None,
                              nb_fba=o.nb_offres_fba if o else None, nb_fbm=o.nb_offres_fbm if o else None,
                              amazon_vend=o.amazon_vend if o else None, buybox_amazon=o.buybox_amazon if o else None,
                              prix_bas_fba=_dec(o.prix_plus_bas_fba) if o else None,
                              bsr=c.bsr if c else None, categorie=c.categorie if c else None,
                              buybox_moi=(o.vendeur_buybox == moi) if (o and moi and o.vendeur_buybox) else None))
        enregistrer(lot)
        n += len(lot)
        attendre(PAUSE_OFFRES)
    return n, erreurs


def executer(compte_id: str, client, places: list, depot, maintenant: datetime,
             attendre: Callable[[float], None] = time.sleep, plafond: int = PLAFOND) -> str:
    """Tâche de nuit « HISTORIQUE » [RM-AMZ-090]. Familles : amazon.fr seulement dans cette version."""
    jour = jour_paris(maintenant)
    budget, morceaux = plafond, []
    for mp in places:
        if budget <= 0:
            break
        suivis = depot.suivis(compte_id, mp.code)
        analyses = depot.asins_analyses(compte_id, mp.code, maintenant - timedelta(days=JOURS_ANALYSES))
        fam_items, err_fam = {}, 0
        if mp.code == "FR":
            for code in depot.familles_suivies(compte_id):
                if code in FAMILLES:
                    try:
                        fam_items[code] = produits_famille(client, mp, FAMILLES[code], attendre)
                    except Exception:
                        err_fam += 1
        connus = {c.asin: c for l in fam_items.values() for c in l}
        fam_de = {c.asin: f for f, l in reversed(list(fam_items.items())) for c in l}
        cibles = perimetre(suivis, analyses, {f: [c.asin for c in l] for f, l in fam_items.items()}, budget)
        if not cibles:
            continue
        depot.enregistrer_produits_marche(compte_id, [
            ProduitMarche(mp.code, a, getattr(connus.get(a), "titre", None), getattr(connus.get(a), "marque", None),
                          fam_de.get(a)) for a, _, _ in cibles])
        n, err = relever(client, mp, [a for a, _, _ in cibles], connus, jour, attendre,
                         lambda lot: depot.enregistrer_releves(compte_id, lot))
        budget -= n
        morceaux.append(f"{mp.code} {n} produits" + (f", {err + err_fam} erreurs" if err + err_fam else ""))
    effaces = depot.purger_releves(compte_id, limite_conservation(jour))
    return "; ".join(morceaux or ["rien à relever"]) + (f" ; {effaces} anciens effacés" if effaces else "")


# ------------------------------------------------------------------ tendances [RM-AMZ-089]
def tendances(releves: list[Releve], jour: date, jours: int) -> dict:
    serie = sorted((r for r in releves if jour - timedelta(days=jours) < r.jour <= jour), key=lambda r: r.jour)
    prix = [r.prix_buybox for r in serie if r.prix_buybox is not None]
    bsr = [r.bsr for r in serie if r.bsr is not None]
    av = [r.amazon_vend for r in serie if r.amazon_vend is not None]
    abb = [r.buybox_amazon for r in serie if r.buybox_amazon is not None]
    bmoi = [r.buybox_moi for r in serie if getattr(r, "buybox_moi", None) is not None]
    vend = [(r.nb_fba or 0) + (r.nb_fbm or 0) for r in serie if r.nb_fba is not None or r.nb_fbm is not None]
    baisses = sum(1 for a, b in zip(bsr, bsr[1:]) if b < a)
    part = lambda l: None if not l else round(sum(1 for x in l if x) / len(l), 2)  # noqa: E731
    return {
        "jours": jours, "releves": len(serie), "court": len(serie) < RELEVES_MIN,
        "prix_dernier": prix[-1] if prix else None,
        "prix_moyen": (sum(prix) / len(prix)).quantize(Decimal("0.01")) if prix else None,
        "prix_min": min(prix) if prix else None, "prix_max": max(prix) if prix else None,
        "prix_variation": round(float((prix[-1] - prix[0]) / prix[0]), 4) if len(prix) > 1 and prix[0] else None,
        "bsr_moyen": round(sum(bsr) / len(bsr)) if bsr else None, "bsr_dernier": bsr[-1] if bsr else None,
        "jours_baisse_bsr": baisses if len(bsr) > 1 else None,
        "part_amazon_vend": part(av), "part_buybox_amazon": part(abb), "part_buybox_moi": part(bmoi),
        "stabilite": round(float((max(prix) - min(prix)) / (sum(prix) / len(prix))), 4) if len(prix) > 1 else None,
        "vendeurs_moyen": round(sum(vend) / len(vend), 1) if vend else None,
    }
