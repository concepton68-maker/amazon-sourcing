"""Remboursements FBA : vérifier ce qu'Amazon a versé — [RM-AMZ-054 à 059].

L'outil détecte des écarts et prépare un dossier ; il ne dépose JAMAIS de réclamation (aucune API ne le permet).
Colonnes des rapports : référence officielle des rapports FBA (notes `docs/recherches/notes/remboursements/`).
Points NON documentés, traités avec prudence :
- signe des colonnes `Lost` / `Damaged` / `Found` du Ledger synthèse → valeurs absolues ;
- codes de motif du Ledger et valeurs de `reason` → jamais utilisés ;
- remboursements sans numéro de commande : on ne sait pas s'ils couvrent un envoi entrant ou une perte en
  entrepôt → ils sont imputés d'abord aux envois entrants, puis aux pertes (choix de l'outil).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional

from .lots import Lot, VenteReelle

PERTE, RETOUR, ENVOI = "PERTE_ENTREPOT", "RETOUR_NON_RESTITUE", "ENVOI_INCOMPLET"
DETECTE, DOSSIER_ENVOYE, REMBOURSE, REFUSE, CLOS = "DETECTE", "DOSSIER_ENVOYE", "REMBOURSE", "REFUSE", "CLOS"
SUIVIS = (DETECTE, DOSSIER_ENVOYE, REMBOURSE, REFUSE, CLOS)

# Délais chiffrés par l'annonce officielle du 15/10/2025 (pas la page de politique) [RM-AMZ-058]
DELAI_PERTE = 60
RETOUR_DEBUT, RETOUR_FIN = 45, 105
SOURCE_DELAIS = "annonce Amazon du 15/10/2025"

_PAYS_VERS_PLACE = {"GB": "UK"}


def lire_tsv(texte: str) -> list[dict]:
    texte = texte.lstrip("﻿")
    return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(io.StringIO(texte), delimiter="\t")]


def _entier(v) -> int:
    try:
        return int(Decimal(str(v or "0").replace(",", ".")))
    except InvalidOperation:
        return 0


def _dec(v) -> Optional[Decimal]:
    try:
        return Decimal(str(v).replace(",", ".")) if v not in (None, "") else None
    except InvalidOperation:
        return None


def _jour(v) -> Optional[date]:
    v = (v or "").strip()
    for f in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(v[:10], f).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
    except ValueError:
        return None


@dataclass
class LigneLedger:
    jour: date
    marketplace: str
    fnsku: str
    asin: Optional[str]
    msku: Optional[str]
    perdus: int
    abimes: int
    retrouves: int


def parser_ledger_synthese(texte: str) -> list[LigneLedger]:
    """`GET_LEDGER_SUMMARY_VIEW_DATA` (agrégé par pays) : colonnes Date, FNSKU, ASIN, MSKU, Lost, Damaged, Found, Location."""
    out = []
    for r in lire_tsv(texte):
        j = _jour(r.get("Date"))
        if not j or not r.get("FNSKU"):
            continue
        pays = (r.get("Location") or "").upper()
        out.append(LigneLedger(j, _PAYS_VERS_PLACE.get(pays, pays), r["FNSKU"], r.get("ASIN") or None,
                               r.get("MSKU") or None, abs(_entier(r.get("Lost"))), abs(_entier(r.get("Damaged"))),
                               abs(_entier(r.get("Found")))))
    return out


@dataclass
class RemboursementVerse:
    reimbursement_id: str
    jour: Optional[date]
    case_id: Optional[str]
    commande: Optional[str]
    sku: Optional[str]
    fnsku: Optional[str]
    asin: Optional[str]
    devise: Optional[str]
    montant: Optional[Decimal]
    quantite: int


def parser_remboursements(texte: str) -> list[RemboursementVerse]:
    """`GET_FBA_REIMBURSEMENTS_DATA` (18 colonnes documentées)."""
    out = []
    for r in lire_tsv(texte):
        if not r.get("reimbursement-id"):
            continue
        out.append(RemboursementVerse(r["reimbursement-id"], _jour(r.get("approval-date")), r.get("case-id") or None,
                                      r.get("amazon-order-id") or None, r.get("sku") or None, r.get("fnsku") or None,
                                      r.get("asin") or None, r.get("currency-unit") or None, _dec(r.get("amount-total")),
                                      _entier(r.get("quantity-reimbursed-total"))))
    return out


@dataclass
class RetourClient:
    jour: Optional[date]
    commande: str
    sku: Optional[str]
    asin: Optional[str]
    fnsku: Optional[str]
    quantite: int


def parser_retours(texte: str) -> list[RetourClient]:
    """`GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA`."""
    return [RetourClient(_jour(r.get("return-date")), r["order-id"], r.get("sku") or None, r.get("asin") or None,
                         r.get("fnsku") or None, _entier(r.get("quantity")))
            for r in lire_tsv(texte) if r.get("order-id")]


@dataclass
class LigneEnvoi:
    envoi: str
    statut: str
    marketplace: str
    sku: Optional[str]
    fnsku: str
    expedie: int
    recu: int
    cloture_le: Optional[date] = None


@dataclass
class Cas:
    cle: str
    type: str
    marketplace: str
    asin: Optional[str]
    sku: Optional[str]
    fnsku: Optional[str]
    commande: Optional[str]
    unites: Optional[int]
    valeur_achat: Optional[Decimal]
    devise: str
    detecte_le: date
    echeance: Optional[date]
    statut: str = DETECTE
    case_id: Optional[str] = None
    montant_verse: Optional[Decimal] = None
    faits: dict = field(default_factory=dict)


def _cout(lots: list[Lot], asin: Optional[str], mp: str) -> tuple[Optional[Decimal], Optional[str]]:
    l = [x for x in lots if x.asin == asin and x.marketplace == mp]
    if not l:
        return None, None
    d = sorted(l, key=lambda x: (x.date_achat, x.cree_le))[-1].prevision
    return d.cout_achat, d.devise


def detecter(ledger: Iterable[LigneLedger], verses: Iterable[RemboursementVerse], retours: Iterable[RetourClient],
             ventes: Iterable[VenteReelle], envois: Iterable[LigneEnvoi], lots: Iterable[Lot],
             aujourd_hui: date, devise_par_defaut: str = "EUR",
             asins_par_sku: Optional[dict[str, str]] = None) -> list[Cas]:
    """[RM-AMZ-055, 056, 057, 058] `asins_par_sku` (photo de stock) retrouve l'ASIN d'un envoi pour sa valeur d'achat."""
    asins_par_sku = asins_par_sku or {}
    lots, verses = list(lots), list(verses)
    sans_commande: dict[str, int] = {}
    for v in verses:
        if not v.commande and v.fnsku:
            sans_commande[v.fnsku] = sans_commande.get(v.fnsku, 0) + v.quantite
    cas: list[Cas] = []

    def nouveau(cle, typ, mp, asin, sku, fnsku, commande, unites, echeance, faits):
        cout, dev = _cout(lots, asin, mp)
        cas.append(Cas(cle, typ, mp, asin, sku, fnsku, commande, unites,
                       None if cout is None or unites is None else cout * unites, dev or devise_par_defaut,
                       aujourd_hui, echeance, faits=faits))

    # 1. Envois entrants incomplets (imputés en premier) [RM-AMZ-057]
    for e in envois:
        if e.statut != "CLOSED" or e.expedie <= e.recu:
            continue
        manque = e.expedie - e.recu
        deja = min(manque, sans_commande.get(e.fnsku, 0))
        sans_commande[e.fnsku] = sans_commande.get(e.fnsku, 0) - deja
        if manque - deja > 0:
            nouveau(f"{ENVOI}:{e.envoi}:{e.fnsku}", ENVOI, e.marketplace, asins_par_sku.get(e.sku or ""), e.sku, e.fnsku, None, manque - deja, None,
                    {"envoi": e.envoi, "expedie": e.expedie, "recu": e.recu, "deja_rembourse": deja})

    # 2. Pertes et dommages en entrepôt [RM-AMZ-055]
    groupes: dict[tuple[str, str], list[LigneLedger]] = {}
    for l in ledger:
        groupes.setdefault((l.marketplace, l.fnsku), []).append(l)
    for (mp, fnsku), lignes in groupes.items():
        perdus = sum(l.perdus + l.abimes for l in lignes)
        retrouves = sum(l.retrouves for l in lignes)
        net = perdus - retrouves
        deja = min(max(net, 0), sans_commande.get(fnsku, 0))
        if net - deja <= 0:
            continue
        derniere = max((l.jour for l in lignes if l.perdus + l.abimes > 0), default=None)
        ex = lignes[0]
        nouveau(f"{PERTE}:{mp}:{fnsku}", PERTE, mp, ex.asin, ex.msku, fnsku, None, net - deja,
                None if derniere is None else derniere + timedelta(days=DELAI_PERTE),
                {"perdus_abimes": perdus, "retrouves": retrouves, "deja_rembourse": deja})

    # 3. Remboursé au client sans retour [RM-AMZ-056]
    retournes = {(r.commande, r.asin) for r in retours}
    commandes_remboursees = {v.commande for v in verses if v.commande}
    for v in ventes:
        if v.quantite != 0 or not v.commande or v.retours.valeur <= 0:
            continue
        if aujourd_hui - v.jour < timedelta(days=RETOUR_DEBUT):
            continue
        if (v.commande, v.asin) in retournes or v.commande in commandes_remboursees:
            continue
        nouveau(f"{RETOUR}:{v.commande}:{v.asin}", RETOUR, v.marketplace, v.asin, None, None, v.commande, None,
                v.jour + timedelta(days=RETOUR_FIN), {"rembourse_au_client_le": v.jour.isoformat(),
                                                       "montant_rembourse_client": str(v.retours.valeur)})
    return sorted(cas, key=lambda c: (c.echeance or date.max, c.cle))


def appliquer_suivi(detectes: list[Cas], existants: list[Cas], verses: Iterable[RemboursementVerse]) -> list[Cas]:
    """[RM-AMZ-059] Garder le suivi des cas déjà connus ; un cas qui disparaît après un remboursement passe à REMBOURSÉ."""
    verses = list(verses)
    par_cle = {c.cle: c for c in existants}
    sortie = []
    for c in detectes:
        ancien = par_cle.pop(c.cle, None)
        sortie.append(c if ancien is None else replace(c, statut=ancien.statut, case_id=ancien.case_id,
                                                       detecte_le=ancien.detecte_le, montant_verse=ancien.montant_verse))
    for c in par_cle.values():                    # n'apparaît plus dans la détection
        if c.statut in (REMBOURSE, REFUSE, CLOS):
            sortie.append(c)
            continue
        lies = [v for v in verses if (c.case_id and v.case_id == c.case_id) or (c.commande and v.commande == c.commande)
                or (c.fnsku and not v.commande and v.fnsku == c.fnsku)]
        montant = sum((v.montant or Decimal(0) for v in lies), Decimal(0)) if lies else None
        sortie.append(replace(c, statut=REMBOURSE if lies else CLOS, montant_verse=montant))
    return sortie


def changer_suivi(c: Cas, statut: str, case_id: Optional[str] = None) -> Cas:
    if statut not in SUIVIS or statut == DETECTE:
        raise ValueError("STATUT_INVALIDE")
    if statut == DOSSIER_ENVOYE and not (case_id or c.case_id):
        raise ValueError("NUMERO_DE_CAS_REQUIS")
    return replace(c, statut=statut, case_id=(case_id or c.case_id))


def synchroniser_remboursements(compte_id: str, mp, client, depot, aujourd_hui: date) -> list[Cas]:
    """Synchro de nuit : rapports Ledger synthèse, Remboursements, Retours ; envois fermés ; détection ; suivi gardé."""
    debut = datetime.combine(aujourd_hui - timedelta(days=540), datetime.min.time())
    fin = datetime.combine(aujourd_hui, datetime.min.time())
    ledger = parser_ledger_synthese(client.rapport(mp, "GET_LEDGER_SUMMARY_VIEW_DATA", debut, fin,
                                                   {"aggregateByLocation": "COUNTRY", "aggregatedByTimePeriod": "MONTHLY"}))
    verses = parser_remboursements(client.rapport(mp, "GET_FBA_REIMBURSEMENTS_DATA", debut, fin))
    retours = parser_retours(client.rapport(mp, "GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA",
                                            fin - timedelta(days=180), fin))
    envois = client.envois_fermes(mp, fin - timedelta(days=180), fin)
    depot.enregistrer_verses(compte_id, verses)
    tous = depot.verses(compte_id)
    _, photos = depot.photo_stock(compte_id)
    detectes = detecter(ledger, tous, retours, depot.ventes(compte_id), envois, depot.lots(compte_id), aujourd_hui,
                        mp.devise, {p.sku: p.asin for p in photos if p.asin})
    cas = appliquer_suivi(detectes, depot.cas_remboursement(compte_id), tous)
    depot.enregistrer_cas(compte_id, cas)
    return cas
