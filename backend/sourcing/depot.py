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
            del self._revocations[c]
        return purges
