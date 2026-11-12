"""Normalisation des transactions de l'API Finances v2024-06-19 — [RM-AMZ-016, 017, 019, 020, 021, 023].

Champs utilisés (doc SP-API lue le 12/11/2026, notes `docs/recherches/notes/api-financiere/`) :
transactionId, transactionType, transactionStatus, description, postedDate, totalAmount,
marketplaceDetails.marketplaceId, relatedIdentifiers, items[].breakdowns / contexts (asin, sku, quantityShipped).

Points NON VÉRIFIÉS, gérés sans deviner :
- liste des `breakdownType` : non publiée → table de classement modifiable, inconnus signalés ;
- noms exacts des champs d'un identifiant lié (`relatedIdentifierName` / `relatedIdentifierValue`) ;
- montants UE TTC ou HT → RM-AMZ-020.

Convention Amazon : montant positif = crédit au vendeur, négatif = débit. Le NET d'une ligne est
toujours la somme de ses ventilations finales, quel que soit leur classement : un type mal classé
change la répartition entre causes, jamais le profit.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional

from .lots import VenteReelle
from .marketplaces import MARKETPLACES
from .money import Montant, dec

CATEGORIES = ("vente", "taxe", "frais_amazon", "retours", "stockage", "autres")

# Seuls ces deux noms sont attestés (ChargeType de la v0 : « Principal », « Tax »). Leur reprise en v2024
# n'est PAS vérifiée : à confirmer sur la première réponse réelle, puis compléter cette table.
CLASSEMENT_PAR_DEFAUT: dict[str, str] = {
    "Principal": "vente",
    "Tax": "taxe",
}

_MP_PAR_ID = {m.marketplace_id: m.code for m in MARKETPLACES.values()}


@dataclass
class LigneFinanciere:
    id_externe: str            # transactionId#rang — clé de rejouabilité [RM-AMZ-017]
    transaction_id: str
    type: Optional[str]
    description: Optional[str]
    statut: Optional[str]
    jour: date
    marketplace: Optional[str]
    commande: Optional[str]
    asin: Optional[str]
    sku: Optional[str]
    quantite: int
    devise: str
    montants: dict[str, Decimal]
    types_inconnus: list[str] = field(default_factory=list)
    tva_separee: bool = False
    empreinte: str = ""

    @property
    def net(self) -> Decimal:
        return sum((v for k, v in self.montants.items() if k != "taxe"), Decimal(0))


@dataclass
class ResultatNormalisation:
    lignes: list[LigneFinanciere]
    types_inconnus: dict[str, int]
    avertissements: list[str]


def _feuilles(breakdowns: Iterable[dict]) -> Iterable[dict]:
    """[RM-AMZ-021] Seules les ventilations sans sous-ventilation sont additionnées."""
    for b in breakdowns or []:
        enfants = b.get("breakdowns") or []
        if enfants:
            yield from _feuilles(enfants)
        else:
            yield b


def _montant(obj: Optional[dict]) -> tuple[Decimal, Optional[str]]:
    if not obj:
        return Decimal(0), None
    return dec(str(obj.get("currencyAmount", 0))), obj.get("currencyCode")


def _ident(liste: Iterable[dict], nom: str) -> Optional[str]:
    for r in liste or []:
        if r.get("relatedIdentifierName") == nom:
            return r.get("relatedIdentifierValue")
    return None


def _contexte_produit(contexts: Iterable[dict]) -> dict:
    for c in contexts or []:
        if c.get("asin") or c.get("sku"):
            return c
    return {}


def normaliser_transactions(reponse: dict, classement: Optional[dict[str, str]] = None) -> ResultatNormalisation:
    classement = {**CLASSEMENT_PAR_DEFAUT, **(classement or {})}
    corps = reponse.get("payload", reponse)
    lignes, inconnus, avert = [], {}, []
    for t in corps.get("transactions", []) or []:
        tid = t.get("transactionId")
        if not tid:
            avert.append("transaction sans transactionId ignorée (non rejouable)")
            continue
        posted = str(t.get("postedDate", ""))[:10]
        jour = date.fromisoformat(posted) if posted else None
        mp_id = (t.get("marketplaceDetails") or {}).get("marketplaceId") \
            or (t.get("sellingPartnerMetadata") or {}).get("marketplaceId")
        mp = _MP_PAR_ID.get(mp_id)
        if mp_id and not mp:
            avert.append(f"place de marché inconnue {mp_id} ({tid})")
        commande = _ident(t.get("relatedIdentifiers"), "ORDER_ID")
        _, devise_t = _montant(t.get("totalAmount"))
        items = [it for it in (t.get("items") or []) if it.get("breakdowns")]
        blocs = [(i, it.get("breakdowns"), _contexte_produit(it.get("contexts"))) for i, it in enumerate(items)] \
            or [(0, t.get("breakdowns"), _contexte_produit(
                c for it in (t.get("items") or []) for c in (it.get("contexts") or [])))]
        for rang, breakdowns, ctx in blocs:
            montants = {c: Decimal(0) for c in CATEGORIES}
            types_ligne, devise = [], devise_t
            for f in _feuilles(breakdowns):
                v, cur = _montant(f.get("breakdownAmount"))
                devise = devise or cur
                if cur and devise and cur != devise:
                    avert.append(f"devises mélangées dans {tid}")
                bt = f.get("breakdownType") or "(sans type)"
                cat = classement.get(bt)
                if cat not in CATEGORIES:
                    cat = "autres"
                    types_ligne.append(bt)
                    inconnus[bt] = inconnus.get(bt, 0) + 1
                montants[cat] += v
            if not devise:
                avert.append(f"transaction {tid} sans devise ignorée")
                continue
            q = int(ctx.get("quantityShipped") or 0)
            brut = json.dumps({"t": tid, "r": rang, "b": breakdowns, "s": t.get("transactionStatus")},
                              sort_keys=True, default=str)
            lignes.append(LigneFinanciere(
                id_externe=f"{tid}#{rang}", transaction_id=tid, type=t.get("transactionType"),
                description=t.get("description"), statut=t.get("transactionStatus"), jour=jour,
                marketplace=mp, commande=commande, asin=ctx.get("asin"), sku=ctx.get("sku"),
                quantite=q, devise=devise, montants=montants, types_inconnus=types_ligne,
                tva_separee=montants["taxe"] != 0, empreinte=hashlib.sha256(brut.encode()).hexdigest()))
    return ResultatNormalisation(lignes, inconnus, avert)


def vers_vente(ligne: LigneFinanciere, compte_id: str) -> Optional[VenteReelle]:
    """Ligne rattachable à un produit → vente réelle (montants positifs = coûts). Sinon None
    (frais de compte sans produit : affichés à part, pas imputés à un lot)."""
    if not ligne.asin or not ligne.marketplace or ligne.jour is None:
        return None
    m = ligne.montants
    vente, retours = m["vente"], -m["retours"]
    quantite = ligne.quantite if vente > 0 else 0
    if quantite == 0 and vente < 0:          # [RM-AMZ-019] remboursement : imputé aux retours, pas au prix
        retours, vente = retours - vente, Decimal(0)
    d = ligne.devise
    return VenteReelle(
        compte_id, ligne.asin, ligne.marketplace, ligne.jour, quantite,
        chiffre_affaires_ht=Montant(vente, d), frais_amazon=Montant(-m["frais_amazon"], d),
        retours=Montant(retours, d), stockage=Montant(-m["stockage"], d), autres=Montant(-m["autres"], d),
        commande=ligne.commande, differe=(ligne.statut == "DEFERRED"))


def avertissements_ligne(ligne: LigneFinanciere) -> list[str]:
    out = []
    if not ligne.tva_separee and ligne.marketplace and MARKETPLACES[ligne.marketplace].prix_ttc \
            and MARKETPLACES[ligne.marketplace].taux_tva_standard > 0:
        out.append("TVA_NON_SEPAREE")        # [RM-AMZ-020]
    if ligne.types_inconnus:
        out.append("TYPES_FRAIS_INCONNUS")   # [RM-AMZ-021]
    return out
