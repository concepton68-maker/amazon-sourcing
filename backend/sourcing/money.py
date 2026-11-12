"""Montants et conversions de devises — [RM-AMZ-015].

Chaque montant porte sa devise. Additionner deux devises différentes est une
erreur. Une conversion exige un taux daté dont la source est connue.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Union

Nombre = Union[Decimal, int, str, float]
CENTIME = Decimal("0.01")


def dec(x: Nombre) -> Decimal:
    """Convertit sans perte d'arrondi binaire (un float passe par sa représentation texte)."""
    if isinstance(x, Decimal):
        return x
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(x)


class DeviseDifferente(ValueError):
    pass


@dataclass(frozen=True)
class Montant:
    valeur: Decimal
    devise: str

    @classmethod
    def de(cls, valeur: Nombre, devise: str) -> "Montant":
        return cls(dec(valeur), devise.upper())

    @classmethod
    def zero(cls, devise: str) -> "Montant":
        return cls(Decimal(0), devise.upper())

    def _meme_devise(self, autre: "Montant") -> None:
        if self.devise != autre.devise:
            raise DeviseDifferente(f"{self.devise} et {autre.devise} : conversion explicite requise")

    def __add__(self, autre: "Montant") -> "Montant":
        self._meme_devise(autre)
        return Montant(self.valeur + autre.valeur, self.devise)

    def __sub__(self, autre: "Montant") -> "Montant":
        self._meme_devise(autre)
        return Montant(self.valeur - autre.valeur, self.devise)

    def __mul__(self, k: Nombre) -> "Montant":
        return Montant(self.valeur * dec(k), self.devise)

    __rmul__ = __mul__

    def __truediv__(self, k: Nombre) -> "Montant":
        return Montant(self.valeur / dec(k), self.devise)

    def __neg__(self) -> "Montant":
        return Montant(-self.valeur, self.devise)

    def arrondi(self) -> "Montant":
        return Montant(self.valeur.quantize(CENTIME, rounding=ROUND_HALF_UP), self.devise)

    def __str__(self) -> str:
        return f"{self.arrondi().valeur} {self.devise}"


@dataclass(frozen=True)
class TauxChange:
    """1 unité de `de` = `taux` unités de `vers`, au `jour` indiqué, selon `source`."""
    de: str
    vers: str
    taux: Decimal
    jour: date
    source: str

    def __post_init__(self):
        if self.taux <= 0:
            raise ValueError("taux de change non positif")
        if not self.source.strip():
            raise ValueError("un taux de change doit indiquer sa source")


@dataclass(frozen=True)
class MontantConverti:
    montant: Montant
    origine: Montant
    taux: TauxChange


def convertir(m: Montant, taux: TauxChange) -> MontantConverti:
    if m.devise == taux.vers:
        raise ValueError("montant déjà dans la devise cible")
    if m.devise != taux.de:
        raise DeviseDifferente(f"taux {taux.de}→{taux.vers} inapplicable à {m.devise}")
    return MontantConverti(Montant(m.valeur * taux.taux, taux.vers), m, taux)
