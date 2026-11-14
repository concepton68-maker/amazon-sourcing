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
# partie 2 [RM-AMZ-142 à 146]
REPARTITION_PROPOSEE, TRANSPORT_PROPOSE, REPARTITION_CONFIRMEE, TRANSPORT_CONFIRME = (
    "REPARTITION_PROPOSEE", "TRANSPORT_PROPOSE", "REPARTITION_CONFIRMEE", "TRANSPORT_CONFIRME")
COLIS = "GROUND_SMALL_PARCEL"
PARTENAIRE, PROPRE = "AMAZON_PARTNERED_CARRIER", "USE_YOUR_OWN_CARRIER"
PAGES_ETIQUETTES = ("PackageLabel_A4_4", "PackageLabel_A4_2")
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


    # ---------------------------------------------------------------- partie 2 [RM-AMZ-142 à 146]
    def options_repartition(self, plan_id: str) -> tuple[dict, list]:
        r = self._ecrire("POST", f"/inboundPlans/{plan_id}/placementOptions", {})
        op = self.operation(r["operationId"])
        if op.get("operationStatus") != "SUCCESS":
            return op, []
        return op, self._lister(f"/inboundPlans/{plan_id}/placementOptions", "placementOptions")

    def envoi(self, plan_id: str, shipment_id: str) -> dict:
        return self.c._appel(self.mp, "GET", f"{BASE}/inboundPlans/{plan_id}/shipments/{shipment_id}")

    def options_transport(self, plan_id: str, placement_id: str, envois: list, pret_le: str, contact: Optional[dict]) -> tuple[dict, list]:
        confs = [{"shipmentId": s, "readyToShipWindow": {"start": f"{pret_le}T00:00:00Z"},
                  **({"contactInformation": contact} if contact else {})} for s in envois]
        r = self._ecrire("POST", f"/inboundPlans/{plan_id}/transportationOptions",
                         {"placementOptionId": placement_id, "shipmentTransportationConfigurations": confs})
        op = self.operation(r["operationId"])
        if op.get("operationStatus") != "SUCCESS":
            return op, []
        out, jeton = [], None
        while True:                                     # toutes les pages, 20 au plus chacune [RM-AMZ-143]
            params = {"placementOptionId": placement_id, "pageSize": 20}
            if jeton:
                params["paginationToken"] = jeton
            p = self.c._appel(self.mp, "GET", f"{BASE}/inboundPlans/{plan_id}/transportationOptions", params=params)
            out += p.get("transportationOptions", [])
            jeton = (p.get("pagination") or {}).get("nextToken")
            if not jeton:
                return op, out

    def fenetres(self, plan_id: str, shipment_id: str) -> tuple[dict, list]:
        r = self._ecrire("POST", f"/inboundPlans/{plan_id}/shipments/{shipment_id}/deliveryWindowOptions")
        op = self.operation(r["operationId"])
        if op.get("operationStatus") != "SUCCESS":
            return op, []
        return op, self._lister(f"/inboundPlans/{plan_id}/shipments/{shipment_id}/deliveryWindowOptions", "deliveryWindowOptions")

    def confirmer_repartition(self, plan_id: str, placement_id: str) -> dict:
        r = self._ecrire("POST", f"/inboundPlans/{plan_id}/placementOptions/{placement_id}/confirmation")
        return self.operation(r["operationId"])

    def confirmer_fenetre(self, plan_id: str, shipment_id: str, fenetre_id: str) -> dict:
        r = self._ecrire("POST", f"/inboundPlans/{plan_id}/shipments/{shipment_id}/deliveryWindowOptions/{fenetre_id}/confirmation")
        return self.operation(r["operationId"])

    def confirmer_transport(self, plan_id: str, choix: dict, contact: Optional[dict]) -> dict:
        sel = [{"shipmentId": s, "transportationOptionId": o, **({"contactInformation": contact} if contact else {})}
               for s, o in choix.items()]
        r = self._ecrire("POST", f"/inboundPlans/{plan_id}/transportationOptions/confirmation", {"transportationSelections": sel})
        return self.operation(r["operationId"])

    def cartons_envoi(self, plan_id: str, shipment_id: str) -> list:
        return self._lister(f"/inboundPlans/{plan_id}/shipments/{shipment_id}/boxes", "boxes")

    def etiquettes(self, confirmation_id: str, box_ids: list, page: str) -> bytes:
        """[RM-AMZ-145] getLabels v0 ; l'adresse ne vaut que 15 s : téléchargée aussitôt."""
        p = {"PageType": page, "LabelType": "UNIQUE", "PackageLabelsToPrint": ",".join(box_ids)}
        r = self.c._appel(self.mp, "GET", f"/fba/inbound/v0/shipments/{confirmation_id}/labels", params=p)
        url = (r.get("payload") or {}).get("DownloadURL")
        if not url:
            raise ErreurEnvoi("ETIQUETTES_ABSENTES", confirmation_id)
        d = self.c.session.get(url, timeout=60)
        if d.status_code != 200:
            raise ErreurEnvoi("ETIQUETTES_TELECHARGEMENT", str(d.status_code))
        return d.content

    def suivi(self, plan_id: str, shipment_id: str, numeros: dict) -> dict:
        corps = {"trackingDetails": {"spdTrackingDetail": {"spdTrackingItems": [
            {"boxId": b, "trackingId": n} for b, n in numeros.items()]}}}
        r = self._ecrire("PUT", f"/inboundPlans/{plan_id}/shipments/{shipment_id}/trackingDetails", corps)
        return self.operation(r["operationId"])


def montants(liste) -> list[dict]:
    """Frais ou remises tels que rendus (montant, devise, description) [RM-AMZ-142]."""
    return [{"montant": (x.get("value") or {}).get("amount"), "devise": (x.get("value") or {}).get("code"),
             "description": x.get("description"), "cible": x.get("target")} for x in liste or []]


def resume_repartition(options: list) -> list[dict]:
    return [{"id": o.get("placementOptionId"), "statut": o.get("status"), "expiration": o.get("expiration"),
             "envois": list(o.get("shipmentIds") or []), "frais": montants(o.get("fees")), "remises": montants(o.get("discounts"))}
            for o in options]


def resume_transport(options: list) -> dict:
    """Options colis seulement, par envoi [RM-AMZ-143]."""
    par: dict[str, list] = {}
    for o in options:
        if o.get("shippingMode") != COLIS:
            continue
        q = o.get("quote") or {}
        par.setdefault(o.get("shipmentId"), []).append({
            "id": o.get("transportationOptionId"), "transporteur": (o.get("carrier") or {}).get("name"),
            "code_transporteur": (o.get("carrier") or {}).get("alphaCode"), "solution": o.get("shippingSolution"),
            "devis": (q.get("cost") or {}).get("amount"), "devise": (q.get("cost") or {}).get("code"),
            "annulable_jusqu_au": q.get("voidableUntil"), "conditions": o.get("preconditions") or []})
    return par


def controler_transport(transports: dict, choix: dict) -> None:
    """Un choix par envoi, parmi les options rendues ; même transporteur pour tous les envois colis."""
    if set(choix) != set(transports):
        raise ErreurEnvoi("TRANSPORT_INCOMPLET", ",".join(sorted(set(transports) - set(choix))))
    vus = set()
    for s, oid in choix.items():
        o = next((x for x in transports[s] if x["id"] == oid), None)
        if o is None:
            raise ErreurEnvoi("TRANSPORT_INCONNU", s)
        vus.add((o["code_transporteur"] or o["transporteur"], o["solution"]))
    if len(vus) > 1:
        raise ErreurEnvoi("TRANSPORTEURS_DIFFERENTS", "transport")


def contact(societe: dict) -> Optional[dict]:
    s = societe or {}
    if not (s.get("raison_sociale") and s.get("telephone")):
        return None
    c = {"name": s["raison_sociale"][:50], "phoneNumber": s["telephone"]}
    if s.get("courriel"):
        c["email"] = s["courriel"]
    return c


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
