"""Fournisseurs et bons de commande — [RM-AMZ-049 à 053]. Fonctions pures : aucun accès au stockage."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable, Optional

from .lots import Lot, Prevision, VenteReelle, rattacher_fifo
from .money import dec

BROUILLON, ENVOYE, RECU, ANNULE = "BROUILLON", "ENVOYE", "RECU", "ANNULE"


class ErreurAchat(ValueError):
    """Le code (premier argument) est traduit par l'interface."""


def _maintenant() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Fournisseur:
    id: str
    compte_id: str
    nom: str
    devise: str = "EUR"
    delai_jours: int = 7
    courriel: Optional[str] = None
    # fiche [RM-AMZ-100]
    pays: Optional[str] = None
    site: Optional[str] = None
    categories: tuple = ()
    port_unitaire: Optional[Decimal] = None
    revente: str = "A_VERIFIER"          # AUTORISEE / INTERDITE / A_VERIFIER
    revente_source: Optional[str] = None
    connexion: str = "AUCUNE"            # FICHIER / API / AUCUNE
    notes: Optional[str] = None
    reference: Optional[str] = None      # code de l'annuaire [RM-AMZ-101]
    colonnes: Optional[dict] = None      # colonnes mémorisées du fichier de prix [RM-AMZ-102]


REVENTES = ("AUTORISEE", "INTERDITE", "A_VERIFIER")
CONNEXIONS = ("FICHIER", "API", "AUCUNE")


def modifier_fiche(f: Fournisseur, **champs) -> Fournisseur:
    """[RM-AMZ-100] Contrôle des champs de la fiche ; renvoie la fiche modifiée."""
    autorises = {"delai_jours", "courriel", "pays", "site", "categories", "port_unitaire", "revente", "revente_source",
                 "connexion", "notes", "colonnes"}
    inconnus = set(champs) - autorises
    if inconnus:
        raise ErreurAchat("CHAMP_INCONNU")
    if "revente" in champs and champs["revente"] not in REVENTES:
        raise ErreurAchat("REVENTE_INVALIDE")
    if "connexion" in champs and champs["connexion"] not in CONNEXIONS:
        raise ErreurAchat("CONNEXION_INVALIDE")
    if "delai_jours" in champs and not (isinstance(champs["delai_jours"], int) and 0 <= champs["delai_jours"] <= 365):
        raise ErreurAchat("DELAI_INVALIDE")
    if champs.get("port_unitaire") is not None:
        p = dec(champs["port_unitaire"])
        if not (0 <= p <= 1000):
            raise ErreurAchat("PORT_INVALIDE")
        champs["port_unitaire"] = p
    for k in ("courriel", "pays", "site", "revente_source", "notes"):
        if k in champs:
            v = (champs[k] or "").strip() or None
            if v and len(v) > (2000 if k == "notes" else 300):
                raise ErreurAchat("TEXTE_TROP_LONG")
            champs[k] = v
    if champs.get("courriel") and "@" not in champs["courriel"]:
        raise ErreurAchat("COURRIEL_INVALIDE")
    if champs.get("site") and not champs["site"].startswith(("https://", "http://")):
        raise ErreurAchat("SITE_INVALIDE")
    if "categories" in champs:
        champs["categories"] = tuple(dict.fromkeys(str(c) for c in champs["categories"] or ()))
    return replace(f, **champs)


def depuis_reference(compte_id: str, ref, existants: Iterable[Fournisseur] = ()) -> Fournisseur:
    """[RM-AMZ-101] Ajout en un clic depuis l'annuaire : les informations vérifiées sont recopiées."""
    f = nouveau_fournisseur(compte_id, ref.nom, existants=existants)
    return replace(f, pays=ref.pays, site=ref.site, categories=tuple(ref.categories), revente=ref.revente,
                   revente_source=ref.source or None, connexion=ref.connexion, notes=ref.note, reference=ref.code)


def analysable(f: Fournisseur) -> bool:
    """[RM-AMZ-100] Revente sur Amazon interdite : catalogue non analysé."""
    return f.revente != "INTERDITE"


def nouveau_fournisseur(compte_id: str, nom: str, devise: str = "EUR", delai_jours: int = 7,
                        courriel: Optional[str] = None, existants: Iterable[Fournisseur] = ()) -> Fournisseur:
    """[RM-AMZ-049]"""
    nom = " ".join((nom or "").split())
    if not nom or len(nom) > 120:
        raise ErreurAchat("NOM_FOURNISSEUR_INVALIDE")
    if any(f.nom.lower() == nom.lower() for f in existants):
        raise ErreurAchat("FOURNISSEUR_EXISTE")
    if not (isinstance(delai_jours, int) and 0 <= delai_jours <= 365):
        raise ErreurAchat("DELAI_INVALIDE")
    devise = (devise or "").upper()
    if len(devise) != 3 or not devise.isalpha():
        raise ErreurAchat("DEVISE_INVALIDE")
    courriel = (courriel or "").strip() or None
    if courriel and ("@" not in courriel or len(courriel) > 254):
        raise ErreurAchat("COURRIEL_INVALIDE")
    return Fournisseur(str(uuid.uuid4()), compte_id, nom, devise, delai_jours, courriel)


@dataclass(frozen=True)
class LigneBon:
    id: str
    asin: str
    marketplace: str
    designation: Optional[str]
    quantite: int
    prix_unitaire: Decimal
    prevision: Prevision                 # figée à l'ajout de la ligne [RM-AMZ-050]
    quantite_recue: Optional[int] = None
    lot_id: Optional[str] = None


@dataclass(frozen=True)
class BonCommande:
    id: str
    compte_id: str
    numero: int
    fournisseur_id: str
    statut: str = BROUILLON
    lignes: tuple[LigneBon, ...] = ()
    cree_le: datetime = field(default_factory=_maintenant)
    envoye_le: Optional[datetime] = None
    recu_le: Optional[date] = None
    annule_le: Optional[datetime] = None

    @property
    def reference(self) -> str:
        return f"BC-{self.numero:04d}"

    @property
    def montant(self) -> Decimal:
        return sum((l.prix_unitaire * l.quantite for l in self.lignes), Decimal(0))


def nouveau_bon(compte_id: str, numero: int, fournisseur: Fournisseur) -> BonCommande:
    if fournisseur.compte_id != compte_id:
        raise ErreurAchat("FOURNISSEUR_INCONNU")
    return BonCommande(str(uuid.uuid4()), compte_id, numero, fournisseur.id)


def prevision_au_prix(base: Prevision, prix_unitaire: Decimal) -> Prevision:
    """Prévision d'une ligne : celle d'une analyse ou du dernier lot, au prix d'achat de la ligne."""
    return replace(base, cout_achat=dec(prix_unitaire))


def ajouter_ligne(bon: BonCommande, asin: str, marketplace: str, quantite: int, prix_unitaire, prevision: Prevision,
                  designation: Optional[str] = None, devise_fournisseur: Optional[str] = None) -> BonCommande:
    """[RM-AMZ-050]"""
    if bon.statut != BROUILLON:
        raise ErreurAchat("BON_NON_MODIFIABLE")
    prix = dec(prix_unitaire)
    if not isinstance(quantite, int) or quantite <= 0:
        raise ErreurAchat("QUANTITE_INVALIDE")
    if prix <= 0:
        raise ErreurAchat("PRIX_INVALIDE")
    if devise_fournisseur and prevision.devise != devise_fournisseur:
        raise ErreurAchat("DEVISE_DIFFERENTE")
    l = LigneBon(str(uuid.uuid4()), asin, marketplace, designation, quantite, prix, prevision_au_prix(prevision, prix))
    return replace(bon, lignes=bon.lignes + (l,))


def retirer_ligne(bon: BonCommande, ligne_id: str) -> BonCommande:
    if bon.statut != BROUILLON:
        raise ErreurAchat("BON_NON_MODIFIABLE")
    if not any(l.id == ligne_id for l in bon.lignes):
        raise ErreurAchat("LIGNE_INCONNUE")
    return replace(bon, lignes=tuple(l for l in bon.lignes if l.id != ligne_id))


def envoyer(bon: BonCommande, quand: Optional[datetime] = None) -> BonCommande:
    if bon.statut != BROUILLON:
        raise ErreurAchat("TRANSITION_INTERDITE")
    if not bon.lignes:
        raise ErreurAchat("BON_VIDE")
    return replace(bon, statut=ENVOYE, envoye_le=quand or _maintenant())


def annuler(bon: BonCommande, quand: Optional[datetime] = None) -> BonCommande:
    if bon.statut not in (BROUILLON, ENVOYE):
        raise ErreurAchat("TRANSITION_INTERDITE")
    return replace(bon, statut=ANNULE, annule_le=quand or _maintenant())


def recevoir(bon: BonCommande, quantites: dict[str, int], jour: date,
             fournisseur: Fournisseur) -> tuple[BonCommande, list[Lot]]:
    """[RM-AMZ-051] Une seule réception ; chaque ligne reçue devient un lot lié au bon."""
    if bon.statut != ENVOYE:
        raise ErreurAchat("TRANSITION_INTERDITE")
    ids = {l.id for l in bon.lignes}
    if set(quantites) - ids:
        raise ErreurAchat("LIGNE_INCONNUE")
    lignes, lots = [], []
    for l in bon.lignes:
        q = quantites.get(l.id, 0)
        if not isinstance(q, int) or q < 0 or q > l.quantite:
            raise ErreurAchat("QUANTITE_RECUE_INVALIDE")
        lot_id = None
        if q > 0:
            lot = Lot(bon.compte_id, l.asin, l.marketplace, q, jour, l.prevision, fournisseur=fournisseur.nom,
                      designation=l.designation, bon_commande=bon.id)
            lots.append(lot)
            lot_id = lot.id
        lignes.append(replace(l, quantite_recue=q, lot_id=lot_id))
    return replace(bon, statut=RECU, recu_le=jour, lignes=tuple(lignes)), lots


@dataclass
class Bilan:
    fournisseur: Fournisseur
    lots: int = 0
    achete_12_mois: Decimal = Decimal(0)
    roi_prevu: Optional[Decimal] = None
    roi_reel: Optional[Decimal] = None
    delai_reel_jours: Optional[float] = None


def bilans(fournisseurs: Iterable[Fournisseur], lots: Iterable[Lot], ventes: Iterable[VenteReelle],
           bons: Iterable[BonCommande], aujourd_hui: date) -> list[Bilan]:
    """[RM-AMZ-052] Pondération par le coût ; « — » (None) sans données."""
    lots = list(lots)
    res, _ = rattacher_fifo(lots, ventes)
    sortie = []
    for f in fournisseurs:
        b = Bilan(f)
        siens = [r for r in res.values() if r.lot.fournisseur == f.nom]
        b.lots = len(siens)
        b.achete_12_mois = sum((r.lot.prevision.cout_achat * r.lot.quantite for r in siens
                                if r.lot.date_achat > aujourd_hui - timedelta(days=365)), Decimal(0))
        cout_total = sum((r.lot.prevision.cout_achat * r.lot.quantite for r in siens), Decimal(0))
        if cout_total > 0:
            b.roi_prevu = sum((r.lot.prevision.roi or Decimal(0)) * r.lot.prevision.cout_achat * r.lot.quantite
                              for r in siens) / cout_total
        vendus = [r for r in siens if r.quantite_vendue > 0 and r.roi_reel is not None]
        poids = sum((r.cout.valeur for r in vendus), Decimal(0))
        if poids > 0:
            b.roi_reel = sum((r.roi_reel * r.cout.valeur for r in vendus), Decimal(0)) / poids
        delais = [(x.recu_le - x.envoye_le.date()).days for x in bons
                  if x.fournisseur_id == f.id and x.statut == RECU and x.envoye_le and x.recu_le]
        b.delai_reel_jours = round(sum(delais) / len(delais), 1) if delais else None
        sortie.append(b)
    return sorted(sortie, key=lambda b: -b.achete_12_mois)
