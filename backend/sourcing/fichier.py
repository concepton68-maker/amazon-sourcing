"""Lecture d'un fichier fournisseur — [RM-AMZ-030 à 033].

Aucune donnée de ce fichier ne part vers un moteur IA (D-AMZ-008).
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Optional

from .messages import Message, m

MAX_LIGNES = 20_000
MAX_OCTETS = 10 * 1024 * 1024
ROLES = ("code", "prix", "designation", "colisage", "minimum")
OBLIGATOIRES = ("code", "prix")

# [RM-AMZ-031] synonymes d'en-têtes, comparés sans accents ni ponctuation.
SYNONYMES: dict[str, tuple[str, ...]] = {
    "code": ("ean", "ean13", "gtin", "codebarre", "codebarres", "barcode", "upc", "asin", "isbn", "refean", "codeean"),
    "prix": ("prix", "prixht", "puht", "pu", "prixunitaire", "prixachat", "tarif", "tarifht", "price", "unitprice",
             "cost", "netprice", "prixnet"),
    "designation": ("designation", "designationarticle", "libelle", "description", "produit", "article", "nom",
                    "title", "productname", "name"),
    "colisage": ("colisage", "pcb", "unitesparcarton", "uc", "carton", "casepack", "packsize", "qteparcarton"),
    "minimum": ("mini", "minicde", "minimum", "minimumcommande", "moq", "qtemin", "minorder"),
}


class FichierInvalide(ValueError):
    """Le code (premier argument) est traduit par l'interface."""


def _norme(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


@dataclass
class Table:
    entetes: list[str]
    lignes: list[list[str]]


def lire(contenu: bytes, nom: str) -> Table:
    """[RM-AMZ-030]"""
    if len(contenu) > MAX_OCTETS:
        raise FichierInvalide("FICHIER_TROP_GROS")
    if nom.lower().endswith(".xlsx"):
        from openpyxl import load_workbook
        try:
            ws = load_workbook(io.BytesIO(contenu), read_only=True, data_only=True).active
        except Exception:
            raise FichierInvalide("FICHIER_ILLISIBLE") from None
        rangs = [["" if v is None else str(v).strip() for v in r] for r in ws.iter_rows(values_only=True)]
    elif nom.lower().endswith((".csv", ".txt")):
        for enc in ("utf-8-sig", "cp1252"):
            try:
                texte = contenu.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise FichierInvalide("FICHIER_ILLISIBLE")
        premiere = texte.splitlines()[0] if texte.strip() else ""
        sep = max(";,\t", key=premiere.count) if premiere else ";"
        rangs = [[c.strip() for c in r] for r in csv.reader(io.StringIO(texte), delimiter=sep)]
    else:
        raise FichierInvalide("FORMAT_NON_GERE")
    rangs = [r for r in rangs if any(c for c in r)]
    if len(rangs) < 2:
        raise FichierInvalide("FICHIER_VIDE")
    if len(rangs) - 1 > MAX_LIGNES:
        raise FichierInvalide("TROP_DE_LIGNES")
    entetes = rangs[0]
    largeur = len(entetes)
    return Table(entetes, [(r + [""] * largeur)[:largeur] for r in rangs[1:]])


def proposer_colonnes(entetes: list[str]) -> dict[str, Optional[int]]:
    """[RM-AMZ-031] Index de colonne par rôle ; None quand rien ne correspond ou que deux colonnes concourent."""
    normes = [_norme(e) for e in entetes]
    out: dict[str, Optional[int]] = {}
    for role, syn in SYNONYMES.items():
        exacts = [i for i, n in enumerate(normes) if n in syn]
        if len(exacts) == 1:
            out[role] = exacts[0]
            continue
        if len(exacts) > 1:
            out[role] = None
            continue
        partiels = [i for i, n in enumerate(normes) if n and any(s in n for s in syn if len(s) >= 3)]
        out[role] = partiels[0] if len(partiels) == 1 else None
    pris = [v for v in out.values() if v is not None]
    for role, v in out.items():           # une même colonne ne sert pas deux rôles
        if v is not None and pris.count(v) > 1:
            out[role] = None
    return out


def lire_prix(brut: str) -> Optional[Decimal]:
    """[RM-AMZ-032] « 1 234,56 € », « 1.234,56 », « 1,234.56 », « 12.5 » → Decimal ; sinon None."""
    s = re.sub(r"[^\d,.\-]", "", str(brut).replace(" ", "").replace(" ", ""))
    if not s or s in "-.,":
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if len(s.split(",")[-1]) != 3 or s.count(",") == 1 else s.replace(",", "")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def cle_gs1_valide(code: str) -> Optional[bool]:
    """Clé de contrôle EAN-8 / UPC-A / EAN-13 / GTIN-14 (pondération 3-1 depuis la droite). None si non applicable.
    Source : spécifications générales GS1 (non lue) → avertissement seulement [RM-AMZ-032]."""
    if not code.isdigit() or len(code) not in (8, 12, 13, 14):
        return None
    chiffres = [int(c) for c in code]
    somme = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(chiffres[:-1])))
    return (10 - somme % 10) % 10 == chiffres[-1]


@dataclass
class LigneFournisseur:
    numero: int                 # numéro de ligne dans le fichier (en-tête = 1)
    code: str
    prix_unitaire: Decimal
    designation: Optional[str] = None
    colisage: Optional[int] = None
    minimum: Optional[int] = None
    avertissements: list[Message] = field(default_factory=list)


@dataclass
class Preparation:
    lignes: list[LigneFournisseur]
    rejets: list[tuple[int, Message]]
    doublons: list[tuple[int, str]]


def _entier(brut: str) -> Optional[int]:
    p = lire_prix(brut)
    return int(p) if p is not None and p == int(p) and p > 0 else None


def preparer(table: Table, colonnes: dict[str, Optional[int]], prix_par_carton: bool = False) -> Preparation:
    """[RM-AMZ-032, 033]"""
    for r in OBLIGATOIRES:
        if colonnes.get(r) is None:
            raise FichierInvalide("COLONNE_OBLIGATOIRE_MANQUANTE")
    for r, i in colonnes.items():
        if i is not None and not (0 <= i < len(table.entetes)):
            raise FichierInvalide("COLONNE_INVALIDE")
    val = lambda row, r: row[colonnes[r]].strip() if colonnes.get(r) is not None else ""  # noqa: E731
    lignes, rejets, doublons, vus = [], [], [], set()
    for k, row in enumerate(table.lignes, start=2):
        code = re.sub(r"\s", "", val(row, "code"))
        if re.fullmatch(r"\d+(\.0+)?", code):          # Excel : 3700000000017.0
            code = code.split(".")[0]
        if not code:
            rejets.append((k, m("L_CODE_ABSENT")))
            continue
        if not val(row, "prix"):
            rejets.append((k, m("L_PRIX_ABSENT")))
            continue
        prix = lire_prix(val(row, "prix"))
        if prix is None or prix <= 0:
            rejets.append((k, m("L_PRIX_INVALIDE", valeur=val(row, "prix"))))
            continue
        colisage = _entier(val(row, "colisage"))
        if prix_par_carton:
            if not colisage:
                rejets.append((k, m("L_COLISAGE_ABSENT")))
                continue
            prix = prix / colisage
        if code in vus:
            doublons.append((k, code))
            continue
        vus.add(code)
        av = []
        if code.isdigit() and len(code) < 13 and len(code) not in (8, 12):   # zéros de tête perdus par un tableur
            code = code.zfill(13)
            av.append(m("L_ZEROS_AJOUTES"))
        if cle_gs1_valide(code) is False:
            av.append(m("L_CLE_INVALIDE"))
        lignes.append(LigneFournisseur(k, code, prix, val(row, "designation") or None, colisage,
                                       _entier(val(row, "minimum")), av))
    return Preparation(lignes, rejets, doublons)
