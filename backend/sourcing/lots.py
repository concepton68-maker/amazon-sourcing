"""Lots d'achat : prévision figée, ventes réelles, écart expliqué.

[RM-AMZ-011] La prévision d'un lot est figée à sa création ; une correction crée une nouvelle version.
[RM-AMZ-012] Les ventes sont rattachées aux lots du même compte, produit et place de marché,
             premier entré premier sorti.
[RM-AMZ-013] L'écart prévu / réel est décomposé en causes dont la somme égale l'écart total.

Tous les montants unitaires de la prévision sont HT et dans la devise de la place de marché.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional

from .money import Montant, Nombre, dec


@dataclass(frozen=True)
class Prevision:
    """Ce que l'on attendait par unité au moment de l'achat."""
    devise: str
    prix_vente_ht: Decimal
    frais_amazon: Decimal          # frais + TVA non récupérable sur frais
    cout_achat: Decimal            # coût d'achat net
    retours: Decimal = Decimal(0)  # provision retours
    stockage: Decimal = Decimal(0)
    autres: Decimal = Decimal(0)   # envoi, préparation…
    sources: tuple[str, ...] = ()  # d'où viennent les chiffres (sp-api, keepa, saisi…)

    @property
    def profit(self) -> Decimal:
        return self.prix_vente_ht - self.frais_amazon - self.cout_achat - self.retours - self.stockage - self.autres

    @property
    def roi(self) -> Optional[Decimal]:
        return self.profit / self.cout_achat if self.cout_achat > 0 else None

    @classmethod
    def creer(cls, devise: str, prix_vente_ht: Nombre, frais_amazon: Nombre, cout_achat: Nombre,
              retours: Nombre = 0, stockage: Nombre = 0, autres: Nombre = 0, sources: Iterable[str] = ()) -> "Prevision":
        return cls(devise.upper(), dec(prix_vente_ht), dec(frais_amazon), dec(cout_achat),
                   dec(retours), dec(stockage), dec(autres), tuple(sources))


@dataclass(frozen=True)
class Lot:
    compte_id: str
    asin: str
    marketplace: str
    quantite: int
    date_achat: date
    prevision: Prevision
    fournisseur: Optional[str] = None
    designation: Optional[str] = None   # nom du produit, pour l'affichage
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    remplace: Optional[str] = None  # id de la version précédente
    motif: Optional[str] = None     # motif de la correction (versions > 1)
    cree_le: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if self.quantite <= 0:
            raise ValueError("quantité de lot non positive")


def corriger_prevision(lot: Lot, nouvelle: Prevision, motif: str) -> Lot:
    """[RM-AMZ-011] Nouvelle version ; l'ancienne reste inchangée et consultable."""
    if not motif.strip():
        raise ValueError("une correction de prévision exige un motif")
    return replace(lot, prevision=nouvelle, id=str(uuid.uuid4()), version=lot.version + 1, remplace=lot.id, motif=motif.strip(),
                   cree_le=datetime.now(timezone.utc))


@dataclass(frozen=True)
class VenteReelle:
    """Une ligne de vente telle que payée par Amazon (montants totaux de la ligne, HT)."""
    compte_id: str
    asin: str
    marketplace: str
    jour: date
    quantite: int
    chiffre_affaires_ht: Montant
    frais_amazon: Montant
    retours: Montant
    stockage: Montant
    autres: Montant
    commande: Optional[str] = None   # identifiant de commande Amazon (jamais de donnée d'acheteur)
    differe: bool = False            # [RM-AMZ-023] montant pas encore libéré par Amazon

    @property
    def net(self) -> Montant:
        return self.chiffre_affaires_ht - self.frais_amazon - self.retours - self.stockage - self.autres


@dataclass
class Allocation:
    vente: VenteReelle
    quantite: int
    part_fixe: Optional[Decimal] = None  # ajustement sans quantité : part de la commande portée par le lot

    @property
    def part(self) -> Decimal:
        if self.part_fixe is not None:
            return self.part_fixe
        return Decimal(self.quantite) / Decimal(self.vente.quantite)


@dataclass
class ResultatLot:
    lot: Lot
    allocations: list[Allocation] = field(default_factory=list)

    def _somme(self, attr: str) -> Montant:
        total = Montant.zero(self.lot.prevision.devise)
        for a in self.allocations:
            total = total + getattr(a.vente, attr) * a.part
        return total

    @property
    def quantite_vendue(self) -> int:
        return sum(a.quantite for a in self.allocations)

    @property
    def chiffre_affaires(self) -> Montant: return self._somme("chiffre_affaires_ht")
    @property
    def frais_amazon(self) -> Montant: return self._somme("frais_amazon")
    @property
    def retours(self) -> Montant: return self._somme("retours")
    @property
    def stockage(self) -> Montant: return self._somme("stockage")
    @property
    def autres(self) -> Montant: return self._somme("autres")

    @property
    def cout(self) -> Montant:
        return Montant(self.lot.prevision.cout_achat * self.quantite_vendue, self.lot.prevision.devise)

    @property
    def profit_reel(self) -> Montant:
        return self.chiffre_affaires - self.frais_amazon - self.retours - self.stockage - self.autres - self.cout

    @property
    def roi_reel(self) -> Optional[Decimal]:
        c = self.cout.valeur
        return self.profit_reel.valeur / c if c > 0 else None

    @property
    def a_encaisser(self) -> Montant:
        """[RM-AMZ-023] Part du net encore différée par Amazon (incluse dans le profit)."""
        total = Montant.zero(self.lot.prevision.devise)
        for a in self.allocations:
            if a.vente.differe:
                total = total + a.vente.net * a.part
        return total


def rattacher_fifo(lots: Iterable[Lot], ventes: Iterable[VenteReelle]) -> tuple[dict[str, ResultatLot], list[Allocation]]:
    """[RM-AMZ-012] Renvoie (résultats par id de lot, ventes non rattachées).

    Seule la dernière version de chaque lot compte. Les lots sont consommés par date d'achat
    croissante ; une vente peut être répartie sur plusieurs lots.
    """
    lots = list(lots)
    remplaces = {l.remplace for l in lots if l.remplace}
    actifs = [l for l in lots if l.id not in remplaces]
    resultats = {l.id: ResultatLot(l) for l in actifs}
    restant = {l.id: l.quantite for l in actifs}
    orphelines: list[Allocation] = []

    def cle(x):
        return (x.compte_id, x.asin, x.marketplace)

    par_commande: dict[tuple, list[tuple[str, int]]] = {}
    ventes = sorted(ventes, key=lambda v: v.jour)
    for v in ventes:                       # 1) ventes avec quantité, premier entré premier sorti
        if v.quantite <= 0:
            continue
        a_placer = v.quantite
        candidats = sorted((l for l in actifs if cle(l) == cle(v) and restant[l.id] > 0),
                           key=lambda l: (l.date_achat, l.cree_le))
        for l in candidats:
            if a_placer == 0:
                break
            if v.chiffre_affaires_ht.devise != l.prevision.devise:
                raise ValueError("devise de la vente différente de celle du lot")
            q = min(a_placer, restant[l.id])
            resultats[l.id].allocations.append(Allocation(v, q))
            restant[l.id] -= q
            a_placer -= q
            if v.commande:
                par_commande.setdefault(cle(v) + (v.commande,), []).append((l.id, q))
        if a_placer:
            orphelines.append(Allocation(v, a_placer))
    for v in ventes:                       # 2) [RM-AMZ-019] ajustements sans quantité : lots de la même commande
        if v.quantite > 0:
            continue
        repartition = par_commande.get(cle(v) + (v.commande,)) if v.commande else None
        if not repartition:
            orphelines.append(Allocation(v, 0, Decimal(1)))
            continue
        total = sum(q for _, q in repartition)
        for lot_id, q in repartition:
            resultats[lot_id].allocations.append(Allocation(v, 0, Decimal(q) / Decimal(total)))
    return resultats, orphelines


@dataclass(frozen=True)
class Ecart:
    """[RM-AMZ-013] Écart prévu / réel sur les unités vendues ; positif = gain par rapport au prévu."""
    devise: str
    quantite: int
    prix: Decimal
    frais_amazon: Decimal
    retours: Decimal
    stockage: Decimal
    autres: Decimal
    profit_prevu: Decimal
    profit_reel: Decimal
    roi_prevu: Optional[Decimal]
    roi_reel: Optional[Decimal]

    @property
    def total(self) -> Decimal:
        return self.prix + self.frais_amazon + self.retours + self.stockage + self.autres

    def causes_par_ordre(self) -> list[tuple[str, Decimal]]:
        causes = [("prix", self.prix), ("frais_amazon", self.frais_amazon), ("retours", self.retours),
                  ("stockage", self.stockage), ("autres", self.autres)]
        return sorted(causes, key=lambda c: abs(c[1]), reverse=True)


def decomposer_ecart(r: ResultatLot) -> Ecart:
    p, q = r.lot.prevision, r.quantite_vendue
    prix = r.chiffre_affaires.valeur - p.prix_vente_ht * q
    frais = p.frais_amazon * q - r.frais_amazon.valeur
    retours = p.retours * q - r.retours.valeur
    stockage = p.stockage * q - r.stockage.valeur
    autres = p.autres * q - r.autres.valeur
    return Ecart(p.devise, q, prix, frais, retours, stockage, autres,
                 profit_prevu=p.profit * q, profit_reel=r.profit_reel.valeur,
                 roi_prevu=p.roi, roi_reel=r.roi_reel)


def prevision_depuis_analyse(rentabilite, couts, devise: str, sources: Iterable[str]) -> Prevision:
    """Fige le résultat d'une analyse d'achat (profit.ResultatRentabilite + ParametresCout) en prévision unitaire."""
    retours = dec(couts.taux_retours) * dec(rentabilite.prix_vente)
    autres = dec(couts.envoi_entrepot) + dec(couts.preparation) + dec(couts.autres_couts)
    return Prevision.creer(
        devise,
        prix_vente_ht=rentabilite.prix_vente_ht,
        frais_amazon=dec(rentabilite.frais_amazon) + dec(rentabilite.tva_sur_frais_non_recuperable),
        cout_achat=rentabilite.cout_achat_net,
        retours=retours,
        stockage=couts.stockage_estime,
        autres=autres,
        sources=sources,
    )
