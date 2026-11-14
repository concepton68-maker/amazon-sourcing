"""Dépôt des données métier, cloisonné par compte — [RM-AMZ-014].

Toute lecture ou écriture exige le compte demandeur. Un compte ne voit jamais les
données d'un autre (politique d'usage SP-API 4.4 et 4.6). Quand l'autorisation
Amazon d'un compte est retirée, ses données sont supprimées à la purge suivante,
au plus tard 30 jours après le retrait (politique de protection des données).

`DepotMemoire` sert aux tests et au mode démo ; `db.DepotPostgres` a la même interface.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from .lots import Lot, VenteReelle

DELAI_SUPPRESSION = timedelta(days=30)


class AccesRefuse(PermissionError):
    pass


class DepotMemoire:
    def __init__(self) -> None:
        self._comptes: set[str] = set()
        self._lots: dict[str, Lot] = {}
        self._ventes: dict[tuple[str, str], VenteReelle] = {}  # (compte, id_externe) -> vente
        self._revocations: dict[str, date] = {}
        self._appariements: dict[tuple[str, str, str], tuple[list[str], datetime]] = {}
        self._parametres: dict[str, list[tuple[dict, datetime]]] = {}
        self._stock: dict[tuple[str, str, str, date], object] = {}
        self._fournisseurs: dict[str, object] = {}
        self._bons: dict[str, object] = {}
        self._verses: dict[tuple[str, str], object] = {}
        self._cas: dict[tuple[str, str], object] = {}
        self._enregs: dict[tuple[str, str], object] = {}
        self._fiches: dict[tuple[str, str], object] = {}
        self._connexions: dict[tuple[str, str], object] = {}
        self._curseurs: dict[tuple[str, str], datetime] = {}
        self._journal: list[tuple[str, object]] = []
        self._explorations: dict[str, dict] = {}
        self._familles: dict[str, list[str]] = {}
        self._catalogues: dict[tuple[str, str], tuple[dict, list]] = {}
        self._opportunites: dict[tuple[str, str, str], list] = {}
        self._alertes_prix: dict[str, list] = {}
        self._suivis: dict[tuple[str, str, str], datetime] = {}
        self._releves: dict[tuple[str, str, str, date], object] = {}
        self._produits_marche: dict[tuple[str, str, str], object] = {}

    # -------------------------------------------------------------- écriture
    def creer_compte(self, compte_id: str, nom: str) -> None:
        if not nom.strip():
            raise ValueError("nom de compte vide")
        self._comptes.add(compte_id)

    def ajouter_lot(self, compte_id: str, lot: Lot) -> None:
        if lot.compte_id != compte_id:
            raise AccesRefuse("lot d'un autre compte")
        if lot.id in self._lots:
            raise ValueError("lot déjà enregistré (un lot ne se modifie pas)")
        self._lots[lot.id] = lot

    def ajouter_vente(self, compte_id: str, vente: VenteReelle, id_externe: Optional[str] = None) -> None:
        """Rejouable : une même ligne Amazon (`id_externe`) remplace la précédente au lieu de doubler."""
        if vente.compte_id != compte_id:
            raise AccesRefuse("vente d'un autre compte")
        self._ventes[(compte_id, id_externe or str(uuid.uuid4()))] = vente

    # -------------------------------------------------------------- lecture
    def lot(self, compte_id: str, lot_id: str) -> Lot:
        l = self._lots.get(lot_id)
        if l is None or l.compte_id != compte_id:
            raise AccesRefuse("lot introuvable pour ce compte")  # même message : ne révèle pas l'existence
        return l

    def lots(self, compte_id: str) -> list[Lot]:
        return sorted((l for l in self._lots.values() if l.compte_id == compte_id),
                      key=lambda l: (l.date_achat, l.cree_le))

    def ventes(self, compte_id: str) -> list[VenteReelle]:
        return sorted((v for (c, _), v in self._ventes.items() if c == compte_id), key=lambda v: v.jour)

    # -------------------------------------------------------------- appariements [RM-AMZ-034]
    def appariement(self, compte_id: str, marketplace: str, code: str) -> Optional[tuple[list[str], datetime]]:
        return self._appariements.get((compte_id, marketplace, code))

    def memoriser_appariement(self, compte_id: str, marketplace: str, code: str, asins: list[str],
                              quand: Optional[datetime] = None) -> None:
        self._appariements[(compte_id, marketplace, code)] = (list(asins), quand or datetime.now(timezone.utc))

    # -------------------------------------------------------------- paramètres [RM-AMZ-042, 043]
    def parametres(self, compte_id: str) -> Optional[dict]:
        v = self._parametres.get(compte_id)
        return dict(v[-1][0]) if v else None

    def versions_parametres(self, compte_id: str) -> list[tuple[int, dict, datetime]]:
        return [(i + 1, dict(x), q) for i, (x, q) in enumerate(self._parametres.get(compte_id, []))]

    def enregistrer_parametres(self, compte_id: str, valeurs: dict) -> int:
        self._parametres.setdefault(compte_id, []).append((dict(valeurs), datetime.now(timezone.utc)))
        return len(self._parametres[compte_id])

    # -------------------------------------------------------------- stock [RM-AMZ-045]
    def enregistrer_photo_stock(self, compte_id: str, jour: date, photos) -> None:
        """Remplace la photo du jour pour les SKU fournis (relancer la même nuit ne double rien)."""
        for p in photos:
            self._stock[(compte_id, p.marketplace, p.sku, jour)] = p

    def photo_stock(self, compte_id: str):
        """Dernière photo de chaque SKU : (jour, photos)."""
        dernier: dict[tuple[str, str], tuple[date, object]] = {}
        for (c, mp, sku, j), p in self._stock.items():
            if c == compte_id and ((mp, sku) not in dernier or j > dernier[(mp, sku)][0]):
                dernier[(mp, sku)] = (j, p)
        jour = max((j for j, _ in dernier.values()), default=None)
        return jour, [p for _, p in dernier.values()]

    # -------------------------------------------------------------- achats [RM-AMZ-049 à 051]
    def fournisseurs(self, compte_id: str) -> list:
        return sorted((f for f in self._fournisseurs.values() if f.compte_id == compte_id), key=lambda f: f.nom.lower())

    def enregistrer_fournisseur(self, compte_id: str, f) -> None:
        if f.compte_id != compte_id:
            raise AccesRefuse("fournisseur d'un autre compte")
        if any(x.nom.lower() == f.nom.lower() and x.id != f.id for x in self.fournisseurs(compte_id)):
            raise ValueError("FOURNISSEUR_EXISTE")
        self._fournisseurs[f.id] = f

    def bons(self, compte_id: str) -> list:
        return sorted((b for b in self._bons.values() if b.compte_id == compte_id), key=lambda b: -b.numero)

    def bon(self, compte_id: str, bon_id: str):
        b = self._bons.get(bon_id)
        if b is None or b.compte_id != compte_id:
            raise AccesRefuse("bon introuvable pour ce compte")
        return b

    def prochain_numero(self, compte_id: str) -> int:
        return max((b.numero for b in self.bons(compte_id)), default=0) + 1

    def enregistrer_bon(self, compte_id: str, bon) -> None:
        if bon.compte_id != compte_id:
            raise AccesRefuse("bon d'un autre compte")
        ancien = self._bons.get(bon.id)
        if ancien is not None and ancien.statut in ("RECU", "ANNULE"):
            raise ValueError("BON_DEFINITIF")
        self._bons[bon.id] = bon

    def receptionner(self, compte_id: str, bon, lots) -> None:
        """Bon reçu et lots créés ensemble."""
        for l in lots:
            self.ajouter_lot(compte_id, l)
        self.enregistrer_bon(compte_id, bon)

    # -------------------------------------------------------------- remboursements [RM-AMZ-054 à 059]
    def enregistrer_verses(self, compte_id: str, verses) -> None:
        for v in verses:
            self._verses[(compte_id, v.reimbursement_id)] = v

    def verses(self, compte_id: str) -> list:
        return [v for (c, _), v in self._verses.items() if c == compte_id]

    def enregistrer_cas(self, compte_id: str, cas) -> None:
        for x in cas:
            self._cas[(compte_id, x.cle)] = x

    def cas_remboursement(self, compte_id: str) -> list:
        return [x for (c, _), x in self._cas.items() if c == compte_id]

    # -------------------------------------------------------------- conformité [RM-AMZ-061, 062]
    def enregistrements(self, compte_id: str) -> list:
        return sorted((e for (c, _), e in self._enregs.items() if c == compte_id), key=lambda e: e.cle)

    def enregistrer_enregistrement(self, compte_id: str, e) -> None:
        self._enregs[(compte_id, e.cle)] = e

    def supprimer_enregistrement(self, compte_id: str, cle: str) -> bool:
        return self._enregs.pop((compte_id, cle), None) is not None

    def fiches(self, compte_id: str) -> dict:
        return {a: f for (c, a), f in self._fiches.items() if c == compte_id}

    def enregistrer_fiche(self, compte_id: str, fiche) -> None:
        self._fiches[(compte_id, fiche.asin)] = fiche

    # -------------------------------------------------------------- connexions [RM-AMZ-072]
    def connexions(self, compte_id: str) -> dict:
        return {s: x for (c, s), x in self._connexions.items() if c == compte_id}

    def enregistrer_connexion(self, compte_id: str, source: str, chiffre: bytes) -> None:
        from .connexions import Connexion
        self._connexions[(compte_id, source)] = Connexion(source, chiffre, datetime.now(timezone.utc))

    def supprimer_connexion(self, compte_id: str, source: str) -> bool:
        return self._connexions.pop((compte_id, source), None) is not None

    # -------------------------------------------------------------- envois FBA [RM-AMZ-137]
    def enregistrer_envoi_fba(self, compte_id: str, e) -> None:
        if e.compte_id != compte_id:
            raise AccesRefuse("envoi d'un autre compte")
        import copy
        self.__dict__.setdefault("_envois_fba", {})[e.id] = copy.deepcopy(e)

    def envois_fba(self, compte_id: str) -> list:
        import copy
        return sorted((copy.deepcopy(e) for e in self.__dict__.get("_envois_fba", {}).values() if e.compte_id == compte_id),
                      key=lambda e: e.cree_le, reverse=True)

    def envoi_fba(self, compte_id: str, envoi_id: str):
        e = self.__dict__.get("_envois_fba", {}).get(envoi_id)
        if e is None or e.compte_id != compte_id:
            return None
        import copy
        return copy.deepcopy(e)

    # -------------------------------------------------------------- envois de bons [RM-AMZ-131]
    def ajouter_envoi_bon(self, compte_id: str, t) -> None:
        l = self.__dict__.setdefault("_envois_bon", {}).setdefault(compte_id, [])
        if any(x.bon_id == t.bon_id and x.generation == t.generation for x in l):
            raise ValueError("GENERATION_EXISTE")
        l.append(t)

    def envois_bon(self, compte_id: str, bon_id: str) -> list:
        return sorted((x for x in self.__dict__.get("_envois_bon", {}).get(compte_id, []) if x.bon_id == bon_id),
                      key=lambda x: x.generation)

    # -------------------------------------------------------------- synchronisation de nuit [RM-AMZ-080]
    def curseur_synchro(self, compte_id: str, tache: str) -> Optional[datetime]:
        return self._curseurs.get((compte_id, tache))

    def enregistrer_curseur_synchro(self, compte_id: str, tache: str, curseur: Optional[datetime]) -> None:
        if curseur:
            self._curseurs[(compte_id, tache)] = curseur

    def journaliser_synchro(self, compte_id: str, r) -> None:
        self._journal.append((compte_id, r))

    def journal_synchro(self, compte_id: str) -> list:
        return [r for c, r in self._journal if c == compte_id]

    def etat_synchros(self) -> dict:
        """[RM-AMZ-081] Dernier passage par tâche, tous comptes confondus, sans aucune donnée de compte."""
        out: dict = {}
        for _, r in self._journal:
            if r.tache not in out or r.fin >= out[r.tache][0]:
                out[r.tache] = (r.fin, r.ok)
        return out

    # -------------------------------------------------------------- exploration [RM-AMZ-085]
    def enregistrer_exploration(self, compte_id: str, resultat: dict) -> None:
        self._explorations[compte_id] = resultat

    def exploration(self, compte_id: str) -> Optional[dict]:
        return self._explorations.get(compte_id)

    # -------------------------------------------------------------- catalogues fournisseurs [RM-AMZ-102]
    def enregistrer_catalogue(self, compte_id: str, fournisseur_id: str, meta: dict, lignes: list) -> None:
        if fournisseur_id not in self._fournisseurs or self._fournisseurs[fournisseur_id].compte_id != compte_id:
            raise AccesRefuse("fournisseur d'un autre compte")
        self._catalogues[(compte_id, fournisseur_id)] = (dict(meta, maj=datetime.now(timezone.utc)), list(lignes))

    def catalogue(self, compte_id: str, fournisseur_id: str) -> Optional[tuple[dict, list]]:
        return self._catalogues.get((compte_id, fournisseur_id))

    # -------------------------------------------------------------- produits rentables [RM-AMZ-105]
    def enregistrer_opportunites(self, compte_id: str, origine: str, origine_nom: str, marketplace: str, ops) -> None:
        self._opportunites[(compte_id, origine, marketplace)] = list(ops)

    def enregistrer_alertes_prix(self, compte_id: str, alertes: list[dict]) -> None:
        """[RM-AMZ-124] Remplace les alertes du compte."""
        self._alertes_prix[compte_id] = [dict(a) for a in alertes]

    def alertes_prix(self, compte_id: str) -> list[dict]:
        return list(self._alertes_prix.get(compte_id, []))

    def vider_opportunites(self, compte_id: str, origine: str, marketplace: str) -> None:
        self._opportunites.pop((compte_id, origine, marketplace), None)

    def ajouter_opportunites(self, compte_id: str, origine: str, marketplace: str, ops) -> None:
        """[RM-AMZ-116] Ajout au fil de l'eau (même produit : remplacé)."""
        l = self._opportunites.setdefault((compte_id, origine, marketplace), [])
        cles = {(o.code, o.asin) for o in ops}
        l[:] = [o for o in l if (o.code, o.asin) not in cles] + list(ops)

    def opportunites(self, compte_id: str) -> list:
        return [o for (c, _, _), l in self._opportunites.items() if c == compte_id for o in l]

    # -------------------------------------------------------------- historique et suivi de marché [RM-AMZ-086 à 090]
    def familles_suivies(self, compte_id: str) -> list[str]:
        return list(self._familles.get(compte_id, []))

    def enregistrer_familles(self, compte_id: str, codes: list[str]) -> None:
        self._familles[compte_id] = list(dict.fromkeys(codes))

    def suivis(self, compte_id: str, marketplace: Optional[str] = None) -> list[str]:
        l = sorted(((q, mp, a) for (c, mp, a), q in self._suivis.items()
                    if c == compte_id and (marketplace is None or mp == marketplace)), reverse=True)
        return [a for _, _, a in l]

    def ajouter_suivi(self, compte_id: str, marketplace: str, asin: str) -> None:
        self._suivis.setdefault((compte_id, marketplace, asin), datetime.now(timezone.utc))

    def retirer_suivi(self, compte_id: str, marketplace: str, asin: str) -> bool:
        return self._suivis.pop((compte_id, marketplace, asin), None) is not None

    def asins_analyses(self, compte_id: str, marketplace: str, depuis: datetime) -> list[str]:
        l = sorted(((q, asins) for (c, mp, _), (asins, q) in self._appariements.items()
                    if c == compte_id and mp == marketplace and q >= depuis), key=lambda x: x[0], reverse=True)
        return list(dict.fromkeys(a for _, asins in l for a in asins))

    def enregistrer_releves(self, compte_id: str, releves) -> None:
        for r in releves:
            self._releves[(compte_id, r.marketplace, r.asin, r.jour)] = r

    def releves(self, compte_id: str, marketplace: str, asins: Optional[list[str]] = None,
                depuis: Optional[date] = None) -> list:
        ens = None if asins is None else set(asins)
        return sorted((r for (c, mp, a, j), r in self._releves.items()
                       if c == compte_id and mp == marketplace and (ens is None or a in ens)
                       and (depuis is None or j >= depuis)), key=lambda r: (r.asin, r.jour))

    def purger_releves(self, compte_id: str, avant: date) -> int:
        vieux = [k for k in self._releves if k[0] == compte_id and k[3] < avant]
        for k in vieux:
            del self._releves[k]
        return len(vieux)

    def enregistrer_produits_marche(self, compte_id: str, produits) -> None:
        for p in produits:
            k = (compte_id, p.marketplace, p.asin)
            old = self._produits_marche.get(k)
            if old is not None:   # on garde ce qui est connu quand le nouveau relevé ne le donne pas
                from dataclasses import replace
                p = replace(p, titre=p.titre or old.titre, marque=p.marque or old.marque,
                            famille=p.famille or old.famille)
            self._produits_marche[k] = p

    def produits_marche(self, compte_id: str, marketplace: str, asins: Optional[list[str]] = None,
                        famille: Optional[str] = None) -> list:
        ens = None if asins is None else set(asins)
        return [p for (c, mp, a), p in self._produits_marche.items()
                if c == compte_id and mp == marketplace and (ens is None or a in ens)
                and (famille is None or p.famille == famille)]

    # -------------------------------------------------------------- retrait d'autorisation
    def revoquer(self, compte_id: str, jour: date) -> date:
        """Enregistre le retrait (la première date compte) ; renvoie la date limite de suppression."""
        self._revocations.setdefault(compte_id, jour)
        return self._revocations[compte_id] + DELAI_SUPPRESSION

    def echeance_suppression(self, compte_id: str) -> Optional[date]:
        j = self._revocations.get(compte_id)
        return None if j is None else j + DELAI_SUPPRESSION

    def purger(self, aujourd_hui: date) -> list[str]:
        """Supprime toutes les données des comptes révoqués au plus tard aujourd'hui."""
        purges = sorted(c for c, j in self._revocations.items() if j <= aujourd_hui)
        for c in purges:
            self._lots = {k: l for k, l in self._lots.items() if l.compte_id != c}
            self._ventes = {k: v for k, v in self._ventes.items() if k[0] != c}
            self._comptes.discard(c)
            self._appariements = {k: v for k, v in self._appariements.items() if k[0] != c}
            self._parametres.pop(c, None)
            self._stock = {k: v for k, v in self._stock.items() if k[0] != c}
            self._fournisseurs = {k: v for k, v in self._fournisseurs.items() if v.compte_id != c}
            self._bons = {k: v for k, v in self._bons.items() if v.compte_id != c}
            self._verses = {k: v for k, v in self._verses.items() if k[0] != c}
            self._cas = {k: v for k, v in self._cas.items() if k[0] != c}
            self._enregs = {k: v for k, v in self._enregs.items() if k[0] != c}
            self._fiches = {k: v for k, v in self._fiches.items() if k[0] != c}
            self._connexions = {k: v for k, v in self._connexions.items() if k[0] != c}
            self._curseurs = {k: v for k, v in self._curseurs.items() if k[0] != c}
            self._journal = [x for x in self._journal if x[0] != c]
            self._explorations.pop(c, None)
            self._familles.pop(c, None)
            self._catalogues = {k: v for k, v in self._catalogues.items() if k[0] != c}
            self._opportunites = {k: v for k, v in self._opportunites.items() if k[0] != c}
            self._alertes_prix.pop(c, None)
            self._suivis = {k: v for k, v in self._suivis.items() if k[0] != c}
            self._releves = {k: v for k, v in self._releves.items() if k[0] != c}
            self._produits_marche = {k: v for k, v in self._produits_marche.items() if k[0] != c}
            del self._revocations[c]
        return purges
