"""Dépôt des données métier, cloisonné par compte — [RM-AMZ-014].

Toute lecture ou écriture exige le compte demandeur. Un compte ne voit jamais les
données d'un autre (politique d'usage SP-API 4.4 et 4.6). Quand l'autorisation
Amazon d'un compte est retirée, ses données sont supprimées à la purge suivante,
au plus tard 30 jours après le retrait (politique de protection des données).

`DepotMemoire` sert aux tests et au mode démo ; `db.DepotPostgres` a la même interface.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
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
            del self._revocations[c]
        return purges
