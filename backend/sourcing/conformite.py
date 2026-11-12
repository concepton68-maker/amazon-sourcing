"""Conformité Europe — [RM-AMZ-060 à 067], D-AMZ-022.

L'outil ne décide jamais si le vendeur est producteur ni de quelle filière relève un produit : il range ce que le vendeur
déclare, cite le texte lu (note `docs/recherches/notes/conformite/conformite_ue.md`, lue le 12/11/2026) et signale ce qui
manque. Toutes les alertes sont des avertissements ; aucun produit n'est jamais déclaré « conforme ».
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Optional

from .messages import Message, m

# [RM-AMZ-060] Places de l'Union européenne (pays = code de la place).
PLACES_UE = ("DE", "FR", "IT", "ES", "NL", "BE", "IE", "SE", "PL")
FILIERES = ("EMBALLAGES", "EEE", "PILES", "AUTRE")
ROLES = ("OUI", "NON", "A_DETERMINER")
CE = ("OUI", "NON_CONCERNE", "A_DETERMINER")
DATE_LECTURE = "2026-11-12"


class SaisieInvalide(ValueError):
    """args = (code, champ)."""


@dataclass(frozen=True)
class Texte:
    code: str
    reference: str          # article tel qu'affiché
    url: str
    verifie: bool
    note: str = ""          # code de réserve éventuel


# [RM-AMZ-067] Bibliothèque : seulement ce qui a été lu (note conformite_ue.md).
_P = "https://publications.europa.eu/resource/celex/"
TEXTES: dict[str, Texte] = {t.code: t for t in (
    Texte("RSGP_19", "Règl. (UE) 2023/988 art. 19", _P + "32023R0988", True, "VERSION_JO"),
    Texte("RSGP_16", "Règl. (UE) 2023/988 art. 16", _P + "32023R0988", True, "VERSION_JO"),
    Texte("SURV_4", "Règl. (UE) 2019/1020 art. 4", _P + "32019R1020", True, "VERSION_JO"),
    Texte("FR_L541_10_13", "Code de l'environnement L541-10-13",
          "https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006074220/LEGISCTA000006176693/", True, "CITATION_PARTIELLE"),
    Texte("FR_L541_10_9", "Code de l'environnement L541-10-9",
          "https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006074220/LEGISCTA000006176693/", True, "CITATION_PARTIELLE"),
    Texte("FR_L541_9_3", "Code de l'environnement L541-9-3",
          "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000041556010", True, "ANNEXE_NON_LUE"),
    Texte("DE_VERPACKDG_6", "VerpackDG §6", "https://www.gesetze-im-internet.de/verpackdg/", True),
    Texte("DE_ELEKTROG_6", "ElektroG §6", "https://www.gesetze-im-internet.de/elektrog_2015/__6.html", True),
    Texte("DE_BATTDG_4", "BattDG §4", "https://www.gesetze-im-internet.de/battdg/__4.html", True),
    Texte("UE_EMB_44", "Règl. (UE) 2025/40 art. 44", _P + "32025R0040", True, "VERSION_JO"),
    Texte("UE_PILES_55", "Règl. (UE) 2023/1542 art. 55", _P + "32023R1542", True, "VERSION_JO"),
    Texte("CE_30", "Règl. (CE) 765/2008 art. 30", _P + "32008R0765", True, "VERSION_JO"),
    Texte("AMAZON_DE_EPR", "Amazon : EPR Allemagne (n° LUCID à 13 chiffres)", "https://sell.amazon.de/", True, "PAGE_AMAZON"),
)}

_COURRIEL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------ enregistrements du compte [RM-AMZ-061]
@dataclass(frozen=True)
class Enregistrement:
    pays: str
    filiere: str
    numero: str
    intitule: Optional[str] = None      # filière AUTRE seulement
    mandataire: Optional[str] = None

    @property
    def cle(self) -> str:
        return f"{self.pays}:{self.filiere}:{self.intitule or ''}"


def _texte_court(v, champ: str, maxi: int, obligatoire: bool = False) -> Optional[str]:
    if v is None:
        v = ""
    if not isinstance(v, str):
        raise SaisieInvalide("SAISIE_INVALIDE", champ)
    v = v.strip()
    if not v:
        if obligatoire:
            raise SaisieInvalide("CHAMP_OBLIGATOIRE", champ)
        return None
    if len(v) > maxi:
        raise SaisieInvalide("TROP_LONG", champ)
    return v


def nouvel_enregistrement(pays: str, filiere: str, numero, intitule=None, mandataire=None) -> Enregistrement:
    if pays not in PLACES_UE:
        raise SaisieInvalide("PAYS_HORS_CHAMP", "pays")
    if filiere not in FILIERES:
        raise SaisieInvalide("FILIERE_INCONNUE", "filiere")
    num = _texte_court(numero, "numero", 64, obligatoire=True)
    intit = _texte_court(intitule, "intitule", 80, obligatoire=(filiere == "AUTRE"))
    if filiere != "AUTRE":
        intit = None
    return Enregistrement(pays, filiere, num, intit, _texte_court(mandataire, "mandataire", 200))


def avertissements_enregistrement(e: Enregistrement) -> list[Message]:
    """[RM-AMZ-061] Format LUCID : page Amazon DE, pas la loi → avertissement seulement."""
    if e.pays == "DE" and e.filiere == "EMBALLAGES" and not re.fullmatch(r"\d{13}", e.numero.replace(" ", "")):
        return [m("C_LUCID_FORMAT", texte="AMAZON_DE_EPR")]
    return []


# ------------------------------------------------------------------ fiche produit [RM-AMZ-062, 064, 065, 066]
@dataclass(frozen=True)
class Coordonnees:
    nom: Optional[str] = None
    adresse: Optional[str] = None
    courriel: Optional[str] = None

    def complete(self) -> bool:
        return bool(self.nom and self.adresse and self.courriel)


@dataclass(frozen=True)
class Fiche:
    asin: str
    fabricant: Coordonnees = Coordonnees()
    fabricant_hors_ue: Optional[bool] = None
    responsable: Coordonnees = Coordonnees()
    avertissements_ok: bool = False
    producteur: str = "A_DETERMINER"
    filieres: tuple[str, ...] = ()
    intitule_autre: Optional[str] = None
    numeros_producteur: dict[str, str] = field(default_factory=dict)   # "PAYS:FILIERE" -> numéro du producteur
    triman_ok: bool = False
    marquage_ce: str = "A_DETERMINER"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["filieres"] = list(self.filieres)
        return d


def _coord(brut, champ: str) -> Coordonnees:
    if brut is None:
        return Coordonnees()
    if not isinstance(brut, dict) or set(brut) - {"nom", "adresse", "courriel"}:
        raise SaisieInvalide("SAISIE_INVALIDE", champ)
    courriel = _texte_court(brut.get("courriel"), f"{champ}.courriel", 254)
    if courriel and not _COURRIEL.match(courriel):
        raise SaisieInvalide("COURRIEL_INVALIDE", f"{champ}.courriel")
    return Coordonnees(_texte_court(brut.get("nom"), f"{champ}.nom", 200),
                       _texte_court(brut.get("adresse"), f"{champ}.adresse", 400), courriel)


_CHAMPS_FICHE = {"fabricant", "fabricant_hors_ue", "responsable", "avertissements_ok", "producteur", "filieres",
                 "intitule_autre", "numeros_producteur", "triman_ok", "marquage_ce"}


def valider_fiche(asin: str, brut: dict) -> Fiche:
    """[RM-AMZ-062, 064, 066] Refuse champ inconnu ou valeur hors liste ; ne suppose rien."""
    if not isinstance(brut, dict) or set(brut) - _CHAMPS_FICHE:
        raise SaisieInvalide("SAISIE_INVALIDE", "fiche")
    hors_ue = brut.get("fabricant_hors_ue")
    if hors_ue is not None and not isinstance(hors_ue, bool):
        raise SaisieInvalide("SAISIE_INVALIDE", "fabricant_hors_ue")
    for b in ("avertissements_ok", "triman_ok"):
        if not isinstance(brut.get(b, False), bool):
            raise SaisieInvalide("SAISIE_INVALIDE", b)
    producteur = brut.get("producteur", "A_DETERMINER")
    if producteur not in ROLES:
        raise SaisieInvalide("SAISIE_INVALIDE", "producteur")
    ce = brut.get("marquage_ce", "A_DETERMINER")
    if ce not in CE:
        raise SaisieInvalide("SAISIE_INVALIDE", "marquage_ce")
    filieres = brut.get("filieres", [])
    if not isinstance(filieres, list) or any(f not in FILIERES for f in filieres):
        raise SaisieInvalide("FILIERE_INCONNUE", "filieres")
    filieres = tuple(f for f in FILIERES if f in filieres)
    intitule = _texte_court(brut.get("intitule_autre"), "intitule_autre", 80, obligatoire="AUTRE" in filieres)
    numeros = brut.get("numeros_producteur", {}) or {}
    if not isinstance(numeros, dict):
        raise SaisieInvalide("SAISIE_INVALIDE", "numeros_producteur")
    propres = {}
    for cle, num in numeros.items():
        pays, _, fil = str(cle).partition(":")
        if pays not in PLACES_UE or fil not in FILIERES:
            raise SaisieInvalide("SAISIE_INVALIDE", f"numeros_producteur.{cle}")
        n = _texte_court(num, f"numeros_producteur.{cle}", 64)
        if n:
            propres[f"{pays}:{fil}"] = n
    return Fiche(asin, _coord(brut.get("fabricant"), "fabricant"), hors_ue, _coord(brut.get("responsable"), "responsable"),
                 bool(brut.get("avertissements_ok", False)), producteur, filieres,
                 intitule if "AUTRE" in filieres else None, propres, bool(brut.get("triman_ok", False)), ce)


# ------------------------------------------------------------------ vérification [RM-AMZ-063 à 067]
_TEXTE_NUMERO = {
    ("FR", "EMBALLAGES"): "FR_L541_10_13", ("FR", "EEE"): "FR_L541_10_13", ("FR", "PILES"): "FR_L541_10_13",
    ("FR", "AUTRE"): "FR_L541_10_13",
    ("DE", "EMBALLAGES"): "DE_VERPACKDG_6", ("DE", "EEE"): "DE_ELEKTROG_6", ("DE", "PILES"): "DE_BATTDG_4",
}
_TEXTE_UE = {"EMBALLAGES": "UE_EMB_44", "PILES": "UE_PILES_55"}


def texte_numero(pays: str, filiere: str) -> Optional[str]:
    """[RM-AMZ-065] Texte qui demande un numéro, ou None si le pays n'a pas été recherché pour cette filière."""
    return _TEXTE_NUMERO.get((pays, filiere)) or _TEXTE_UE.get(filiere)


def _a_numero(pays, filiere, fiche: Fiche, enregs: list[Enregistrement]) -> bool:
    if fiche.producteur == "NON":
        return bool(fiche.numeros_producteur.get(f"{pays}:{filiere}"))
    for e in enregs:
        if e.pays == pays and e.filiere == filiere and (filiere != "AUTRE" or
                                                         (e.intitule or "").casefold() == (fiche.intitule_autre or "").casefold()):
            return True
    return False


def alertes(fiche: Optional[Fiche], asin: str, places: list[str], enregs: list[Enregistrement]) -> list[Message]:
    places_ue = [p for p in PLACES_UE if p in places]
    if not places_ue:
        return []
    f = fiche or Fiche(asin)
    out: list[Message] = []
    if not f.fabricant.complete():
        out.append(m("C_FABRICANT_INCOMPLET", texte="RSGP_19"))
    if f.fabricant_hors_ue is None:
        out.append(m("C_ORIGINE_FABRICANT_A_PRECISER", texte="RSGP_19"))
    elif f.fabricant_hors_ue and not f.responsable.complete():
        out.append(m("C_RESPONSABLE_MANQUANT", texte="RSGP_16"))
    if not f.avertissements_ok:
        out.append(m("C_AVERTISSEMENTS_A_CONFIRMER", texte="RSGP_19"))
    if f.producteur == "A_DETERMINER":
        out.append(m("C_ROLE_A_DETERMINER"))
    if not f.filieres:
        out.append(m("C_FILIERES_A_DECLARER"))
    elif f.producteur != "A_DETERMINER":
        for pays in places_ue:
            for fil in f.filieres:
                t = texte_numero(pays, fil)
                if t is None:
                    out.append(m("C_OBLIGATION_NON_VERIFIEE", pays=pays, filiere=fil))
                elif not _a_numero(pays, fil, f, enregs):
                    out.append(m("C_ENREGISTREMENT_MANQUANT", pays=pays, filiere=fil, texte=t,
                                 qui="producteur" if f.producteur == "NON" else "compte"))
    if "FR" in places_ue and f.filieres and not f.triman_ok:
        out.append(m("C_TRIMAN_A_CONFIRMER", texte="FR_L541_9_3"))
    if f.marquage_ce == "A_DETERMINER":
        out.append(m("C_CE_A_DETERMINER", texte="CE_30"))
    return out


@dataclass(frozen=True)
class LigneProduit:
    asin: str
    designation: Optional[str]
    places: tuple[str, ...]          # toutes les places où le produit est (lots, stock)
    couvert: bool                    # au moins une place UE [RM-AMZ-060]
    alertes: tuple[Message, ...]

    @property
    def statut(self) -> str:
        """[RM-AMZ-067] Jamais « conforme »."""
        if not self.couvert:
            return "NON_COUVERT"
        return "A_COMPLETER" if self.alertes else "RIEN_DE_SIGNALE"


def produits_a_verifier(lots, photos) -> dict[str, tuple[Optional[str], set[str]]]:
    """[RM-AMZ-060] Produits ayant un lot ou du stock, avec leurs places et une désignation."""
    out: dict[str, tuple[Optional[str], set[str]]] = {}
    for l in lots:
        nom, places = out.get(l.asin, (None, set()))
        places.add(l.marketplace)
        out[l.asin] = (nom or getattr(l, "designation", None), places)
    for p in photos:
        if not p.asin:
            continue
        nom, places = out.get(p.asin, (None, set()))
        places.add(p.marketplace)
        out[p.asin] = (nom or p.designation, places)
    return out


def verifier(lots, photos, fiches: dict[str, Fiche], enregs: list[Enregistrement]) -> list[LigneProduit]:
    lignes = []
    for asin, (nom, places) in produits_a_verifier(lots, photos).items():
        al = alertes(fiches.get(asin), asin, sorted(places), enregs)
        couvert = any(p in PLACES_UE for p in places)
        lignes.append(LigneProduit(asin, nom, tuple(sorted(places)), couvert, tuple(al)))
    ordre = {"A_COMPLETER": 0, "RIEN_DE_SIGNALE": 1, "NON_COUVERT": 2}
    lignes.sort(key=lambda x: (ordre[x.statut], -len(x.alertes), x.asin))
    return lignes


# ------------------------------------------------------------------ sérialisation (dépôt)
def fiche_depuis_dict(asin: str, d: dict) -> Fiche:
    d = dict(d)
    d.pop("asin", None)
    return valider_fiche(asin, d)
