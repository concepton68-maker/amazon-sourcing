"""Synchronisation de nuit des ventes et frais réels — [RM-AMZ-017, 018].

Une synchronisation par compte et par région Amazon (Europe, Amérique du Nord, Extrême-Orient).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional

from .finances import avertissements_ligne, normaliser_transactions, vers_vente
from .marketplaces import Marketplace

RECUL = timedelta(days=7)          # relecture des 7 derniers jours (publications tardives, délai de 48 h)
MARGE_FIN = timedelta(minutes=5)   # la borne de fin doit précéder la requête de plus de 2 minutes
MAX_FENETRE = timedelta(days=180)  # au-delà, Amazon renvoie une réponse vide
PREMIERE_SYNCHRO = timedelta(days=179)
PAUSE_PAGES = 2.0                  # 0,5 requête par seconde


def fenetres(dernier: Optional[datetime], maintenant: datetime) -> list[tuple[datetime, datetime]]:
    """[RM-AMZ-018] Découpe [dernier − 7 j, maintenant − 5 min] en tranches de 180 jours au plus."""
    fin = maintenant - MARGE_FIN
    debut = (dernier - RECUL) if dernier else fin - PREMIERE_SYNCHRO
    out = []
    while debut < fin:
        b = min(debut + MAX_FENETRE, fin)
        out.append((debut, b))
        debut = b
    return out


@dataclass
class RapportSync:
    lignes: int = 0
    ventes: int = 0
    pages: int = 0
    sans_produit: list[str] = field(default_factory=list)       # frais de compte non imputés à un lot
    types_inconnus: dict[str, int] = field(default_factory=dict)
    avertissements: dict[str, int] = field(default_factory=dict)
    curseur: Optional[datetime] = None


def synchroniser(compte_id: str, mp: Marketplace, client, depot, maintenant: datetime,
                 dernier: Optional[datetime] = None, classement: Optional[dict] = None,
                 attendre: Callable[[float], None] = time.sleep) -> RapportSync:
    r = RapportSync()
    for debut, fin in fenetres(dernier, maintenant):
        jeton = None
        while True:
            if r.pages:
                attendre(PAUSE_PAGES)
            page = client.page_transactions(mp, debut, fin, jeton)
            r.pages += 1
            n = normaliser_transactions(page, classement)
            for t, k in n.types_inconnus.items():
                r.types_inconnus[t] = r.types_inconnus.get(t, 0) + k
            for a in n.avertissements:
                r.avertissements[a] = r.avertissements.get(a, 0) + 1
            for ligne in n.lignes:
                r.lignes += 1
                for a in avertissements_ligne(ligne):
                    r.avertissements[a] = r.avertissements.get(a, 0) + 1
                v = vers_vente(ligne, compte_id)
                if v is None:
                    r.sans_produit.append(ligne.id_externe)
                    continue
                depot.ajouter_vente(compte_id, v, id_externe=ligne.id_externe)
                r.ventes += 1
            jeton = page.get("payload", page).get("nextToken")
            if not jeton:            # une page vide n'arrête pas la lecture, seule l'absence de jeton
                break
        r.curseur = fin
    return r
