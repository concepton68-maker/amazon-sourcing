"""Synchronisation de nuit — [RM-AMZ-080].

Pour chaque compte ayant une connexion SP-API : ventes et frais, photo du stock, remboursements, sondage des rayons,
historique de marché [RM-AMZ-090]. Tâches indépendantes,
journalisées ; le curseur des ventes n'avance qu'en cas de réussite. Aucun secret dans le journal.
"""
from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from .marketplaces import MARKETPLACES
from .remboursements import synchroniser_remboursements
from .stock import synchroniser_stock
from .sync import synchroniser

TACHES = ("VENTES", "STOCK", "REMBOURSEMENTS", "PRIX", "EXPLORATION", "HISTORIQUE", "CORRESPONDANCE")


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


class Arret(BaseException):
    """[RM-AMZ-136] Arrêt demandé pendant une attente. Hérite de BaseException pour traverser les
    « except Exception » des boucles qui comptent les erreurs sans s'arrêter."""


def places_actives(depot, compte_id: str, places: list) -> list:
    """[RM-AMZ-133] Places où le compte a du stock (dernière photo), des ventes ou des lots."""
    codes = set()
    try:
        _, photos = depot.photo_stock(compte_id)
        codes |= {p.marketplace for p in photos or []}
    except Exception:
        pass
    codes |= {v.marketplace for v in depot.ventes(compte_id)}
    codes |= {l.marketplace for l in depot.lots(compte_id)}
    return [m for m in places if m.code in codes]


def executer_compte(compte_id: str, client, region: str, depot, maintenant: datetime,
                    horloge: Callable[[], datetime] = None, attendre=None, taches: Optional[set] = None,
                    suivi: Optional[Callable] = None, detail: Optional[Callable] = None,
                    arret: Callable[[], bool] = lambda: False) -> list[ResultatTache]:
    """`taches` : sous-ensemble à exécuter (None = toutes) ; `suivi(tache, resultat|None)` : début et fin de chaque
    tâche, pour l'avancement réel [RM-AMZ-115]."""
    horloge = horloge or (lambda: datetime.now(maintenant.tzinfo))
    res: list[ResultatTache] = []
    voulues = [t for t in TACHES if taches is None or t in taches]
    t0 = horloge()
    try:
        places = places_du_vendeur(client, region)
    except Exception as e:  # sans les places, aucune tâche ne peut tourner
        res = [ResultatTache(t, t0, horloge(), False, "places : " + _message(e)) for t in voulues]
        for r in res:
            suivi and suivi(r.tache, r)
        return res
    if not places:
        res = [ResultatTache(t, t0, horloge(), False, "aucune place gérée où le vendeur participe") for t in voulues]
        for r in res:
            suivi and suivi(r.tache, r)
        return res
    principale = next((m for m in places if m.code == "FR"), places[0])
    dort = attendre or time.sleep

    def attente(s):                                                       # [RM-AMZ-136] chaque pause regarde l'arrêt
        if arret():
            raise Arret()
        dort(s)
    kw = {"attendre": attente}

    def tache(nom, f):
        if nom not in voulues:
            return
        if arret():                                                       # [RM-AMZ-136] tâche non faite
            r = ResultatTache(nom, horloge(), horloge(), False, "arrêtée")
            res.append(r)
            suivi and suivi(nom, r)
            return
        suivi and suivi(nom, None)
        d = horloge()
        try:
            msg = f() or ""
            r = ResultatTache(nom, d, horloge(), True, msg)
        except Arret:
            r = ResultatTache(nom, d, horloge(), False, "arrêtée")
        except Exception as e:
            r = ResultatTache(nom, d, horloge(), False, _message(e))
        res.append(r)
        suivi and suivi(nom, r)

    def ventes():
        r = synchroniser(compte_id, principale, client, depot, maintenant,
                         dernier=depot.curseur_synchro(compte_id, "VENTES"), **kw)
        depot.enregistrer_curseur_synchro(compte_id, "VENTES", r.curseur)   # seulement si réussi
        return f"{r.ventes} ventes"

    tache("VENTES", ventes)
    tache("STOCK", lambda: f"{synchroniser_stock(compte_id, places, client, depot, maintenant.date(), **kw)} lignes")
    def exploration():                                                    # [RM-AMZ-085] chaque nuit
        from .analyse import Fournisseurs
        from .exploration import en_json, enregistrer, sonder
        fr = next((m for m in places if m.code == "FR"), None)
        if fr is None:
            return "amazon.fr non ouvert : non sondé"
        f = Fournisseurs([client], client, client, client, None)
        r = enregistrer(depot, compte_id, en_json(sonder(fr, f, **kw), "FR", maintenant))
        n = r["nouveautes"]
        return f"sondage refait ; {len(n['rayons'])} rayons débloqués, {len(n['produits'])} produits autorisés en plus"

    def remboursements():                                                 # [RM-AMZ-133, 134]
        actives = places_actives(depot, compte_id, places)
        if not actives:
            return "aucune activité FBA : rien à vérifier"
        out = []
        for i, m in enumerate(actives, start=1):
            compteur = {"n": 0}

            class Suivi:                                                  # le client, avec l'avancement de ses rapports
                def __getattr__(self, nom):
                    return getattr(client, nom)

                def rapport(self, *a, **k):
                    compteur["n"] += 1
                    lib = f"{m.code} ({i}/{len(actives)}) · rapport {compteur['n']} sur 3"
                    detail and detail("REMBOURSEMENTS", lib)
                    dort, debut = k.pop("attendre", None) or attendre or time.sleep, time.monotonic()

                    def attente(s):                                   # [RM-AMZ-134] signe de vie pendant qu'Amazon prépare
                        if arret():
                            raise Arret()
                        dort(s)
                        minutes = int((time.monotonic() - debut) // 60)
                        detail and detail("REMBOURSEMENTS", f"{lib} · Amazon prépare le rapport ({minutes} min)")
                    return client.rapport(*a, attendre=attente, **k)
            out.append(f"{m.code} {len(synchroniser_remboursements(compte_id, m, Suivi(), depot, maintenant.date()))} cas")
        return "; ".join(out)
    tache("REMBOURSEMENTS", remboursements)
    def prix():                                                           # [RM-AMZ-124]
        from . import repricer as RP
        from .analyse import Fournisseurs
        from .parametres import valider
        from .stock import calculer as calculer_stock
        p = valider(depot.parametres(compte_id) or {})
        jour_photo, photos = depot.photo_stock(compte_id)
        if not photos:
            depot.enregistrer_alertes_prix(compte_id, [])
            return "aucun stock"
        lignes = calculer_stock(photos, depot.ventes(compte_id), depot.lots(compte_id), jour_photo or maintenant.date(),
                                p.delai_fournisseur, p.delai_reception, p.marge_securite, p.seuil_rupture, p.seuil_surstock)
        al = RP.alertes(lignes, Fournisseurs([client], client, client, client, None), p, **kw)
        depot.enregistrer_alertes_prix(compte_id, al)
        return f"{len(al)} SKU sous le prix plancher"

    tache("PRIX", prix)
    tache("EXPLORATION", exploration)

    def historique():                                                     # [RM-AMZ-090]
        from . import historique as H
        return H.executer(compte_id, client, places, depot, maintenant, **kw,
                          progression=lambda texte: detail and detail("HISTORIQUE", texte))

    tache("HISTORIQUE", historique)

    def correspondance():                                                 # [RM-AMZ-114]
        from . import correspondance as CO
        from .analyse import Fournisseurs
        from .parametres import valider
        fr = next((m for m in places if m.code == "FR"), None)
        if fr is None:
            return "amazon.fr non ouvert"
        p = valider(depot.parametres(compte_id) or {})
        b = CO.executer(compte_id, fr, Fournisseurs([client], client, client, client, None), depot, p,
                        p.regime(fr.code), maintenant=maintenant, **kw)
        return f"{b['candidats']} produits comparés, {b['correspondances']} trouvés"

    tache("CORRESPONDANCE", correspondance)
    return res


def client_spapi(v: dict):
    from .providers.spapi import ClientSPAPI
    return ClientSPAPI(client_id=v["client_id"], client_secret=v["client_secret"], seller_id=v.get("seller_id"),
                       refresh_tokens={v["region"]: v["refresh_token"]})


class SynchrosManuelles:
    """[RM-AMZ-115] Une exécution manuelle à la fois par compte ; état réel au fil de l'eau ; journal « manuel »."""

    def __init__(self, en_fond: bool = True):
        self.etats: dict[str, dict] = {}
        self.en_fond = en_fond
        self._verrou = threading.Lock()

    def lancer(self, compte_id: str, client, region: str, depot, taches: Optional[set] = None, attendre=None) -> bool:
        with self._verrou:
            if self.etats.get(compte_id, {}).get("en_cours"):
                return False
            voulues = [t for t in TACHES if taches is None or t in taches]
            etat = {"en_cours": True, "debut": datetime.now(timezone.utc).isoformat(), "taches": voulues,
                    "courante": None, "terminees": []}
            self.etats[compte_id] = etat

        def signe(_tache, texte):                                         # [RM-AMZ-134] détail et dernière nouvelle
            etat["detail"], etat["vu"] = texte, datetime.now(timezone.utc).isoformat()

        def suivi(tache, r):
            etat["detail"], etat["vu"] = None, datetime.now(timezone.utc).isoformat()
            if r is None:
                etat["debut_tache"] = etat["vu"]
            if r is None:
                etat["courante"] = tache
                return
            r = ResultatTache(r.tache, r.debut, r.fin, r.ok, ("manuel · " + r.message).strip(" ·"))
            depot.journaliser_synchro(compte_id, r)
            etat["terminees"].append({"tache": r.tache, "ok": r.ok, "message": r.message, "fin": r.fin.isoformat()})
            etat["courante"] = None

        def travail():
            try:
                executer_compte(compte_id, client, region, depot, datetime.now(timezone.utc), attendre=attendre,
                                taches=set(voulues), suivi=suivi, detail=signe, arret=lambda: bool(etat.get("arret")))
            except Exception as e:  # garde-fou : l'état ne reste jamais « en cours »
                etat["terminees"].append({"tache": etat.get("courante") or "?", "ok": False, "message": _message(e),
                                          "fin": datetime.now(timezone.utc).isoformat()})
            finally:
                etat["en_cours"], etat["courante"] = False, None
                etat["fin"] = datetime.now(timezone.utc).isoformat()
        if self.en_fond:
            threading.Thread(target=travail, daemon=True).start()
        else:
            travail()
        return True


    def arreter(self, compte_id: str) -> bool:
        """[RM-AMZ-136]"""
        e = self.etats.get(compte_id)
        if not e or not e.get("en_cours"):
            return False
        e["arret"] = True
        return True

def executer(comptes: list[tuple[str, dict]], depot, maintenant: datetime, fabrique: Optional[Callable] = None,
             attendre=None) -> dict[str, list[ResultatTache]]:
    """`comptes` : [(compte_id, identifiants SP-API déchiffrés)]. Journalise chaque tâche."""
    fabrique = fabrique or client_spapi
    tout = {}
    for compte_id, v in comptes:
        res = executer_compte(compte_id, fabrique(v), v["region"], depot, maintenant, attendre=attendre)
        for r in res:
            depot.journaliser_synchro(compte_id, r)
        tout[compte_id] = res
    return tout
