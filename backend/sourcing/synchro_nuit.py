"""Synchronisation de nuit — [RM-AMZ-080].

Pour chaque compte ayant une connexion SP-API : ventes et frais, photo du stock, remboursements. Tâches indépendantes,
journalisées ; le curseur des ventes n'avance qu'en cas de réussite. Aucun secret dans le journal.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from .marketplaces import MARKETPLACES
from .remboursements import synchroniser_remboursements
from .stock import synchroniser_stock
from .sync import synchroniser

TACHES = ("VENTES", "STOCK", "REMBOURSEMENTS")


@dataclass(frozen=True)
class ResultatTache:
    tache: str
    debut: datetime
    fin: datetime
    ok: bool
    message: str = ""


def _message(e: Exception) -> str:
    return f"{type(e).__name__}: {str(e)[:300]}"


def places_du_vendeur(client, region: str) -> list:
    """Places gérées par l'outil, dans la région, où le vendeur participe."""
    de_region = [m for m in MARKETPLACES.values() if m.region == region]
    ids = set(client.participations(de_region[0]))
    return [m for m in de_region if m.marketplace_id in ids]


def executer_compte(compte_id: str, client, region: str, depot, maintenant: datetime,
                    horloge: Callable[[], datetime] = None, attendre=None) -> list[ResultatTache]:
    horloge = horloge or (lambda: datetime.now(maintenant.tzinfo))
    res: list[ResultatTache] = []
    t0 = horloge()
    try:
        places = places_du_vendeur(client, region)
    except Exception as e:  # sans les places, aucune tâche ne peut tourner
        return [ResultatTache(t, t0, horloge(), False, "places : " + _message(e)) for t in TACHES]
    if not places:
        return [ResultatTache(t, t0, horloge(), False, "aucune place gérée où le vendeur participe") for t in TACHES]
    principale = next((m for m in places if m.code == "FR"), places[0])
    kw = {} if attendre is None else {"attendre": attendre}

    def tache(nom, f):
        d = horloge()
        try:
            msg = f() or ""
            res.append(ResultatTache(nom, d, horloge(), True, msg))
        except Exception as e:
            res.append(ResultatTache(nom, d, horloge(), False, _message(e)))

    def ventes():
        r = synchroniser(compte_id, principale, client, depot, maintenant,
                         dernier=depot.curseur_synchro(compte_id, "VENTES"), **kw)
        depot.enregistrer_curseur_synchro(compte_id, "VENTES", r.curseur)   # seulement si réussi
        return f"{r.ventes} ventes"

    tache("VENTES", ventes)
    tache("STOCK", lambda: f"{synchroniser_stock(compte_id, places, client, depot, maintenant.date(), **kw)} lignes")
    tache("REMBOURSEMENTS", lambda: "; ".join(
        f"{m.code} {len(synchroniser_remboursements(compte_id, m, client, depot, maintenant.date()))} cas" for m in places))
    return res


def executer(comptes: list[tuple[str, dict]], depot, maintenant: datetime, fabrique: Optional[Callable] = None,
             attendre=None) -> dict[str, list[ResultatTache]]:
    """`comptes` : [(compte_id, identifiants SP-API déchiffrés)]. Journalise chaque tâche."""
    if fabrique is None:
        from .providers.spapi import ClientSPAPI

        def fabrique(v):
            return ClientSPAPI(client_id=v["client_id"], client_secret=v["client_secret"],
                               refresh_tokens={v["region"]: v["refresh_token"]})
    tout = {}
    for compte_id, v in comptes:
        res = executer_compte(compte_id, fabrique(v), v["region"], depot, maintenant, attendre=attendre)
        for r in res:
            depot.journaliser_synchro(compte_id, r)
        tout[compte_id] = res
    return tout
