"""Envoi FBA par l'API Fulfillment Inbound v2024-03-20, partie 1 — [RM-AMZ-137 à 139].

Faits sourcés : docs/recherches/2026-11-14-envoi-fba-api-inbound.md (modèle officiel et guides lus le 14/11/2026).
Aucune étape qui engage des frais (placement, transport) dans cette partie.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Callable, Optional

BASE = "/inbound/fba/2024-03-20"
PROPRIETAIRES = ("SELLER", "AMAZON", "NONE")
BROUILLON, EN_COURS, PLAN_CREE, EMBALLAGE_CONFIRME, CARTONS_ENVOYES, ANNULE, ERREUR = (
    "BROUILLON", "EN_COURS", "PLAN_CREE", "EMBALLAGE_CONFIRME", "CARTONS_ENVOYES", "ANNULE", "ERREUR")
PAUSE_ECRITURE = 0.5            # 2 requêtes par seconde au plus
ATTENTE_MAX_OPERATION = 600.0   # 10 minutes


class ErreurEnvoi(ValueError):
    """args = (code, détail)"""


def _maintenant() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class EnvoiFBA:
    id: str
    compte_id: str
    nom: str
    marketplace: str
    lignes: list                    # [{"msku", "quantite", "asin"?}]
    proprietaire_etiquette: str = "SELLER"
    proprietaire_preparation: str = "NONE"
    statut: str = BROUILLON
    plan_id: Optional[str] = None
    donnees: dict = field(default_factory=dict)   # options d'emballage, problèmes, cartons, dernière opération
    cree_le: datetime = field(default_factory=_maintenant)
    maj: datetime = field(default_factory=_maintenant)


# ------------------------------------------------------------------------------------------- brouillon
def adresse_expedition(societe: dict) -> dict:
    """[RM-AMZ-137] AddressInput : addressLine1, city, countryCode, name, phoneNumber, postalCode obligatoires."""
    s = societe or {}
    champs = {"name": s.get("raison_sociale"), "addressLine1": s.get("expedition_rue"),
              "postalCode": s.get("expedition_cp"), "city": s.get("expedition_ville"),
              "countryCode": (s.get("expedition_pays") or "").upper() or None, "phoneNumber": s.get("telephone")}
    manquants = [k for k, v in champs.items() if not v]
    if manquants:
        raise ErreurEnvoi("ADRESSE_INCOMPLETE", ",".join(manquants))
    bornes = {"name": 50, "city": 30, "phoneNumber": 20}
    for k, n in bornes.items():
        if len(champs[k]) > n:
            raise ErreurEnvoi("ADRESSE_TROP_LONGUE", k)
    if len(champs["countryCode"]) != 2 or not champs["countryCode"].isalpha():
        raise ErreurEnvoi("PAYS_INVALIDE", "countryCode")
    if s.get("courriel"):
        champs["email"] = s["courriel"]
    return champs


def nouveau_brouillon(compte_id: str, nom: str, marketplace: str, lignes: list, etiquette: str = "SELLER",
                      preparation: str = "NONE") -> EnvoiFBA:
    """[RM-AMZ-137]"""
    nom = " ".join((nom or "").split())
    if not nom or len(nom) > 40:
        raise ErreurEnvoi("NOM_INVALIDE", "nom")
    if etiquette not in PROPRIETAIRES or preparation not in PROPRIETAIRES:
        raise ErreurEnvoi("PROPRIETAIRE_INVALIDE", "proprietaire")
    propres, vus = [], set()
    for l in lignes or []:
        msku = str(l.get("msku") or "").strip()
        q = l.get("quantite")
        if not msku or len(msku) > 255 or msku in vus:
            raise ErreurEnvoi("SKU_INVALIDE", msku)
        if isinstance(q, bool) or not isinstance(q, int) or not (1 <= q <= 500_000):
            raise ErreurEnvoi("QUANTITE_INVALIDE", msku)
        vus.add(msku)
        propres.append({"msku": msku, "quantite": q, "asin": l.get("asin")})
    if not propres:
        raise ErreurEnvoi("ENVOI_VIDE", "lignes")
    return EnvoiFBA(str(uuid.uuid4()), compte_id, nom, marketplace, propres, etiquette, preparation)


def corps_plan(e: EnvoiFBA, marketplace_id: str, adresse: dict) -> dict:
    return {"name": e.nom, "destinationMarketplaces": [marketplace_id], "sourceAddress": adresse,
            "items": [{"msku": l["msku"], "quantity": l["quantite"], "labelOwner": e.proprietaire_etiquette,
                       "prepOwner": e.proprietaire_preparation} for l in e.lignes]}


# ------------------------------------------------------------------------------------------ cartons
def controler_cartons(e: EnvoiFBA, cartons: list) -> list:
    """[RM-AMZ-139] Cartons par groupe ; chaque SKU d'un groupe placé en totalité ; poids dans les limites."""
    groupes = {g["id"]: g for g in e.donnees.get("groupes", [])}
    if not groupes:
        raise ErreurEnvoi("EMBALLAGE_NON_CONFIRME", "groupes")
    par_groupe: dict[str, dict] = {gid: {} for gid in groupes}
    propres = []
    for c in cartons or []:
        gid = c.get("groupe")
        if gid not in groupes:
            raise ErreurEnvoi("GROUPE_INCONNU", str(gid))
        try:
            dims = [float(c[k]) for k in ("longueur", "largeur", "hauteur")]
            poids, n = float(c["poids"]), int(c["nombre"])
        except (KeyError, TypeError, ValueError):
            raise ErreurEnvoi("CARTON_INVALIDE", str(gid)) from None
        if min(dims) <= 0 or poids <= 0 or not (1 <= n <= 10_000):
            raise ErreurEnvoi("CARTON_INVALIDE", str(gid))
        g = groupes[gid]
        if g.get("poids_min") is not None and poids < g["poids_min"]:
            raise ErreurEnvoi("POIDS_HORS_LIMITES", str(gid))
        if g.get("poids_max") is not None and poids > g["poids_max"]:
            raise ErreurEnvoi("POIDS_HORS_LIMITES", str(gid))
        contenu = {str(k): int(v) for k, v in (c.get("contenu") or {}).items() if int(v) > 0}
        if not contenu:
            raise ErreurEnvoi("CARTON_VIDE", str(gid))
        for msku, q in contenu.items():
            if msku not in g["mskus"]:
                raise ErreurEnvoi("SKU_HORS_GROUPE", msku)
            par_groupe[gid][msku] = par_groupe[gid].get(msku, 0) + q * n
        propres.append({"groupe": gid, "longueur": dims[0], "largeur": dims[1], "hauteur": dims[2], "poids": poids,
                        "nombre": n, "contenu": contenu})
    quantites = {l["msku"]: l["quantite"] for l in e.lignes}
    for gid, g in groupes.items():
        for msku in g["mskus"]:
            if par_groupe[gid].get(msku, 0) != quantites.get(msku):
                raise ErreurEnvoi("QUANTITES_CARTONS", msku)
    return propres


def corps_cartons(e: EnvoiFBA, cartons: list) -> dict:
    par_g: dict[str, list] = {}
    for c in cartons:
        par_g.setdefault(c["groupe"], []).append({
            "contentInformationSource": "BOX_CONTENT_PROVIDED",
            "dimensions": {"length": c["longueur"], "width": c["largeur"], "height": c["hauteur"], "unitOfMeasurement": "CM"},
            "weight": {"value": c["poids"], "unit": "KG"}, "quantity": c["nombre"],
            "items": [{"msku": m, "quantity": q, "labelOwner": e.proprietaire_etiquette,
                       "prepOwner": e.proprietaire_preparation} for m, q in c["contenu"].items()]})
    return {"packageGroupings": [{"packingGroupId": g, "boxes": b} for g, b in par_g.items()]}


# --------------------------------------------------------------------------------------- appels Amazon
class Inbound:
    """[RM-AMZ-138] Appels Fulfillment Inbound via le client SP-API du compte (`_appel`)."""

    def __init__(self, client, mp, attendre: Optional[Callable[[float], None]] = None):
        self.c, self.mp = client, mp
        self.attendre = attendre or (lambda s: time.sleep(s))

    def _ecrire(self, methode: str, chemin: str, corps=None) -> dict:
        r = self.c._appel(self.mp, methode, BASE + chemin, json=corps)
        self.attendre(PAUSE_ECRITURE)
        return r

    def operation(self, operation_id: str) -> dict:
        """Attente croissante (2 → 30 s), 10 minutes au plus ; renvoie l'état final et les problèmes."""
        ecoule, pause = 0.0, 2.0
        while True:
            r = self.c._appel(self.mp, "GET", f"{BASE}/operations/{operation_id}")
            if r.get("operationStatus") in ("SUCCESS", "FAILED"):
                return r
            if ecoule >= ATTENTE_MAX_OPERATION:
                raise ErreurEnvoi("OPERATION_TROP_LONGUE", operation_id)
            self.attendre(pause)
            ecoule += pause
            pause = min(pause * 2, 30.0)

    def _lister(self, chemin: str, cle: str) -> list:
        out, jeton = [], None
        while True:
            params = {"pageSize": 20}
            if jeton:
                params["paginationToken"] = jeton
            r = self.c._appel(self.mp, "GET", BASE + chemin, params=params)
            out += r.get(cle, [])
            jeton = (r.get("pagination") or {}).get("nextToken")
            if not jeton:
                return out

    def creer_plan(self, corps: dict) -> tuple[str, dict]:
        r = self._ecrire("POST", "/inboundPlans", corps)
        return r["inboundPlanId"], self.operation(r["operationId"])

    def options_emballage(self, plan_id: str) -> tuple[dict, list]:
        r = self._ecrire("POST", f"/inboundPlans/{plan_id}/packingOptions")
        op = self.operation(r["operationId"])
        if op.get("operationStatus") != "SUCCESS":
            return op, []
        return op, self._lister(f"/inboundPlans/{plan_id}/packingOptions", "packingOptions")

    def articles_groupe(self, plan_id: str, groupe_id: str) -> list:
        return self._lister(f"/inboundPlans/{plan_id}/packingGroups/{groupe_id}/items", "items")

    def confirmer_emballage(self, plan_id: str, option_id: str) -> dict:
        r = self._ecrire("POST", f"/inboundPlans/{plan_id}/packingOptions/{option_id}/confirmation")
        return self.operation(r["operationId"])

    def envoyer_cartons(self, plan_id: str, corps: dict) -> dict:
        r = self._ecrire("POST", f"/inboundPlans/{plan_id}/packingInformation", corps)
        return self.operation(r["operationId"])

    def annuler(self, plan_id: str) -> dict:
        r = self._ecrire("PUT", f"/inboundPlans/{plan_id}/cancellation")
        return self.operation(r["operationId"])


def problemes(op: dict) -> list[dict]:
    return [{"code": p.get("code"), "message": p.get("message"), "gravite": p.get("severity")}
            for p in op.get("operationProblems") or []]


def resume_options(options: list) -> list[dict]:
    """Options d'emballage lisibles : groupes, frais et remises tels que rendus, poids mini et maxi."""
    out = []
    for o in options:
        poids = None
        for conf in o.get("supportedConfigurations") or []:
            w = (conf.get("boxRequirements") or {}).get("weight")
            if w:
                poids = w
                break
        out.append({"id": o.get("packingOptionId"), "statut": o.get("status"), "expiration": o.get("expiration"),
                    "groupes": list(o.get("packingGroups") or []), "frais": o.get("fees") or [],
                    "remises": o.get("discounts") or [], "poids": poids})
    return out


def avec(e: EnvoiFBA, **champs) -> EnvoiFBA:
    return replace(e, maj=_maintenant(), **champs)
