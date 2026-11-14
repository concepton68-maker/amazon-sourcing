"""Client Amazon Selling Partner API (SP-API) — usage privé sur VOTRE compte vendeur.

Données OBSERVÉES : catalogue, offres / Buy Box, frais, restrictions de vente.

Authentification : Login with Amazon (LWA) via refresh token. Depuis 2023 la
signature AWS SigV4 n'est plus requise. Un refresh token est propre à une
RÉGION (NA, EU, FE) : un vendeur présent sur les trois doit autoriser
l'application dans chacune.

Variables d'environnement :
  SPAPI_CLIENT_ID, SPAPI_CLIENT_SECRET, SPAPI_SELLER_ID
  SPAPI_REFRESH_TOKEN_EU / _NA / _FE   (ou SPAPI_REFRESH_TOKEN pour toutes)

Limites par défaut (doc Amazon, novembre 2026) — appliquées par couple vendeur/app :
  getItemOffers 0,5 req/s · getMyFeesEstimateForASIN 1 req/s ·
  getListingsRestrictions 5 req/s · Catalog Items 2 req/s.
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Optional

import requests

from ..marketplaces import SPAPI_ENDPOINTS, Marketplace
from ..profit import FraisAmazon
from .base import ErreurFournisseur, InfosCatalogue, InfosOffres, InfosRestrictions

LWA_URL = "https://api.amazon.com/auth/o2/token"

# Identifiants vendeur d'Amazon Retail tels que couramment observés dans les offres.
# À confirmer sur vos propres réponses API ; Keepa fournit aussi la présence d'Amazon.
AMAZON_RETAIL_SELLER_IDS = {
    "US": "ATVPDKIKX0DER",
    "UK": "A3P5ROKL5A1OLE",
    "DE": "A3JWKAKR8XB7XF",
    "FR": "A1X6FK5RDHNB96",
    "IT": "A11IL2BZBX6P9V",
    "ES": "A1AT7YVPFBWXBL",
}

_TYPES_FRAIS = {
    "ReferralFee": "commission",
    "FBAFees": "fba",
    "FBAPerUnitFulfillmentFee": "fba",
    "FBAPerOrderFulfillmentFee": "fba",
    "FBAWeightBasedFee": "fba",
    "VariableClosingFee": "cloture",
}


class ClientSPAPI:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        seller_id: Optional[str] = None,
        refresh_tokens: Optional[dict[str, str]] = None,
        session: Optional[requests.Session] = None,
        max_tentatives: int = 5,
    ):
        self.client_id = client_id or os.environ.get("SPAPI_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("SPAPI_CLIENT_SECRET")
        self.seller_id = seller_id or os.environ.get("SPAPI_SELLER_ID")
        if refresh_tokens is None:
            defaut = os.environ.get("SPAPI_REFRESH_TOKEN")
            refresh_tokens = {
                r: os.environ.get(f"SPAPI_REFRESH_TOKEN_{r}") or defaut
                for r in ("NA", "EU", "FE")
            }
        self.refresh_tokens = {k: v for k, v in refresh_tokens.items() if v}
        if not (self.client_id and self.client_secret and self.refresh_tokens):
            raise ErreurFournisseur(
                "Identifiants SP-API manquants (SPAPI_CLIENT_ID, SPAPI_CLIENT_SECRET, SPAPI_REFRESH_TOKEN_<REGION>)."
            )
        self.session = session or requests.Session()
        self.max_tentatives = max_tentatives
        self._jetons: dict[str, tuple[str, float]] = {}

    # ------------------------------------------------------------------ bas niveau
    def _jeton(self, region: str) -> str:
        jeton, expire = self._jetons.get(region, ("", 0.0))
        if jeton and time.time() < expire - 60:
            return jeton
        refresh = self.refresh_tokens.get(region)
        if not refresh:
            raise ErreurFournisseur(f"Pas de refresh token SP-API pour la région {region}.")
        r = self.session.post(
            LWA_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=30,
        )
        if r.status_code != 200:
            raise ErreurFournisseur(f"Échec authentification LWA ({r.status_code}) : {r.text[:300]}")
        data = r.json()
        self._jetons[region] = (data["access_token"], time.time() + int(data.get("expires_in", 3600)))
        return data["access_token"]

    def _appel(self, mp: Marketplace, methode: str, chemin: str, params=None, json=None) -> dict[str, Any]:
        url = SPAPI_ENDPOINTS[mp.region] + chemin
        attente = 2.0
        for tentative in range(1, self.max_tentatives + 1):
            r = self.session.request(
                methode,
                url,
                params=params,
                json=json,
                headers={"x-amz-access-token": self._jeton(mp.region), "content-type": "application/json"},
                timeout=30,
            )
            if r.status_code == 429 and tentative < self.max_tentatives:
                time.sleep(attente)  # limite de débit atteinte : on patiente
                attente *= 2
                continue
            if r.status_code >= 400:
                raise ErreurFournisseur(f"SP-API {methode} {chemin} -> {r.status_code} : {r.text[:300]}")
            return r.json()
        raise ErreurFournisseur(f"SP-API {chemin} : limite de débit dépassée après {self.max_tentatives} tentatives.")

    # ------------------------------------------------------------------ catalogue
    def rechercher_asins(self, mp: Marketplace, code: str) -> list[str]:
        code = code.strip()
        if len(code) == 10 and code[0].upper() == "B":
            return [code.upper()]
        type_id = {12: "UPC", 13: "EAN", 14: "GTIN"}.get(len(code), "EAN")
        if len(code) == 10 or (len(code) == 13 and code.startswith(("978", "979"))):
            type_id = "ISBN" if len(code) == 10 else "EAN"
        data = self._appel(
            mp, "GET", "/catalog/2022-04-01/items",
            params={"identifiers": code, "identifiersType": type_id,
                    "marketplaceIds": mp.marketplace_id, "includedData": "summaries"},
        )
        return [it["asin"] for it in data.get("items", []) if it.get("asin")]

    def catalogue(self, mp: Marketplace, asin: str) -> InfosCatalogue:
        data = self._appel(
            mp, "GET", f"/catalog/2022-04-01/items/{asin}",
            params={"marketplaceIds": mp.marketplace_id,
                    "includedData": "summaries,salesRanks,attributes,relationships,dimensions,identifiers"},
        )
        return parser_catalogue(asin, mp, data)

    # ------------------------------------------------------------------ recherche par mots-clés [RM-AMZ-084]
    def rechercher(self, mp: Marketplace, mots: str, taille: int = 20) -> list[InfosCatalogue]:
        data = self._appel(mp, "GET", "/catalog/2022-04-01/items",
                           params={"marketplaceIds": mp.marketplace_id, "keywords": mots, "pageSize": str(min(taille, 20)),
                                   "includedData": "summaries,salesRanks"})
        return [parser_catalogue(it.get("asin"), mp, it) for it in data.get("items", []) or [] if it.get("asin")]

    # ------------------------------------------------------------------ historique de nuit [RM-AMZ-086, 087]
    def rechercher_page(self, mp: Marketplace, mots: str, jeton: Optional[str] = None
                        ) -> tuple[list[InfosCatalogue], Optional[str]]:
        """Une page (20 au plus) d'une recherche par mots-clés ; jeton de la page suivante ou None."""
        params = {"marketplaceIds": mp.marketplace_id, "keywords": mots, "pageSize": "20",
                  "includedData": "summaries,salesRanks"}
        if jeton:
            params["pageToken"] = jeton
        data = self._appel(mp, "GET", "/catalog/2022-04-01/items", params=params)
        items = [parser_catalogue(it.get("asin"), mp, it) for it in data.get("items", []) or [] if it.get("asin")]
        return items, (data.get("pagination") or {}).get("nextToken")

    def catalogue_par_paquet(self, mp: Marketplace, asins: list[str]) -> dict[str, InfosCatalogue]:
        """Fiches de 20 ASIN au plus (`searchCatalogItems` par identifiants, « maxItems »: 20)."""
        if not asins:
            return {}
        data = self._appel(mp, "GET", "/catalog/2022-04-01/items", params={
            "identifiers": ",".join(asins[:20]), "identifiersType": "ASIN", "marketplaceIds": mp.marketplace_id,
            "includedData": "summaries,salesRanks,identifiers", "pageSize": "20"})
        return {it["asin"]: parser_catalogue(it["asin"], mp, it) for it in data.get("items", []) or [] if it.get("asin")}

    def offres_par_paquet(self, mp: Marketplace, asins: list[str]) -> dict[str, InfosOffres]:
        """Offres de 20 ASIN au plus (`getItemOffersBatch`). Un ASIN en erreur est absent du résultat."""
        if not asins:
            return {}
        corps = {"requests": [{"uri": f"/products/pricing/v0/items/{a}/offers", "method": "GET",
                               "MarketplaceId": mp.marketplace_id, "ItemCondition": "New"} for a in asins[:20]]}
        data = self._appel(mp, "POST", "/batches/products/pricing/v0/itemOffers", json=corps)
        out = {}
        for r in data.get("responses", []) or []:
            asin = (r.get("request") or {}).get("Asin")
            code = (r.get("status") or {}).get("statusCode")
            if asin and code == 200 and isinstance(r.get("body"), dict) and "payload" in r["body"]:
                out[asin] = parser_offres(mp, r["body"])
        return out

    # ------------------------------------------------------------------ offres
    def offres(self, mp: Marketplace, asin: str) -> InfosOffres:
        data = self._appel(
            mp, "GET", f"/products/pricing/v0/items/{asin}/offers",
            params={"MarketplaceId": mp.marketplace_id, "ItemCondition": "New"},
        )
        return parser_offres(mp, data)

    # ------------------------------------------------------------------ frais
    def frais(self, mp: Marketplace, asin: str, prix_vente: float) -> FraisAmazon:
        corps = {
            "FeesEstimateRequest": {
                "MarketplaceId": mp.marketplace_id,
                "IsAmazonFulfilled": True,
                "PriceToEstimateFees": {
                    "ListingPrice": {"CurrencyCode": mp.devise, "Amount": round(prix_vente, 2)},
                    "Shipping": {"CurrencyCode": mp.devise, "Amount": 0},
                },
                "Identifier": str(uuid.uuid4()),
            }
        }
        data = self._appel(mp, "POST", f"/products/fees/v0/items/{asin}/feesEstimate", json=corps)
        return parser_frais(data)

    # ------------------------------------------------------------------ restrictions
    def restrictions(self, mp: Marketplace, asin: str) -> InfosRestrictions:
        if not self.seller_id:
            return InfosRestrictions(autorise=None, motifs=["SPAPI_SELLER_ID non défini : restrictions non vérifiées."])
        data = self._appel(
            mp, "GET", "/listings/2021-08-01/restrictions",
            params={"asin": asin, "sellerId": self.seller_id,
                    "marketplaceIds": mp.marketplace_id, "conditionType": "new_new"},
        )
        return parser_restrictions(data)


    # ------------------------------------------------------------------ finances
    def page_transactions(self, mp: Marketplace, posted_after=None, posted_before=None,
                          next_token: Optional[str] = None, commande: Optional[str] = None) -> dict:
        """Une page de `GET /finances/2024-06-19/transactions` [RM-AMZ-016]. Rôle « Finance and Accounting ».
        Jamais de paramètre donnant accès aux données d'acheteurs [RM-AMZ-022]."""
        params: dict[str, str] = {}
        if commande:
            params.update(relatedIdentifierName="ORDER_ID", relatedIdentifierValue=commande)
        else:
            params.update(postedAfter=posted_after.isoformat(), postedBefore=posted_before.isoformat())
        if next_token:
            params["nextToken"] = next_token
        return self._appel(mp, "GET", "/finances/2024-06-19/transactions", params=params)

    # ------------------------------------------------------------------ places du vendeur [RM-AMZ-080]
    def participations(self, mp: Marketplace) -> list[str]:
        """Identifiants des places où le vendeur participe (`GET /sellers/v1/marketplaceParticipations`)."""
        data = self._appel(mp, "GET", "/sellers/v1/marketplaceParticipations")
        out = []
        for x in data.get("payload", []) or []:
            if (x.get("participation") or {}).get("isParticipating", True):
                mid = (x.get("marketplace") or {}).get("id")
                if mid:
                    out.append(mid)
        return out

    # ------------------------------------------------------------------ test de la connexion [RM-AMZ-079]
    def tester(self, mp: Marketplace) -> list[dict]:
        """Essaie chaque accès séparément ; renvoie une ligne par étape, sans aucun secret."""
        from datetime import datetime, timedelta, timezone
        etapes: list[dict] = []

        def ligne(etape, ok, statut=None, message="", requete=None):
            etapes.append({"etape": etape, "ok": ok, "statut": statut, "message": message[:300], "requete": requete})

        try:
            jeton = self._jeton(mp.region)
            ligne("IDENTIFICATION", True, 200)
        except ErreurFournisseur as e:
            ligne("IDENTIFICATION", False, None, str(e))
            for x in ("COMPTE", "CATALOGUE", "OFFRES", "STOCK", "FINANCES"):
                ligne(x, None)
            return etapes
        base = SPAPI_ENDPOINTS[mp.region]

        def essai(etape, chemin, params, resume=None):
            try:
                r = self.session.get(base + chemin, params=params, timeout=30,
                                     headers={"x-amz-access-token": jeton, "content-type": "application/json"})
            except requests.RequestException as e:
                ligne(etape, False, None, f"réseau : {e}")
                return None
            ok = r.status_code < 400
            msg = r.text if not ok else (resume(r.json()) if resume else "")
            ligne(etape, ok, r.status_code, msg, r.headers.get("x-amzn-RequestId"))
            return r.json() if ok else None

        compte = essai("COMPTE", "/sellers/v1/marketplaceParticipations", {})
        if compte is None:  # diagnostic : le même jeton ailleurs (autre région, serveurs d'essai Sandbox)
            for region, hote in list(SPAPI_ENDPOINTS.items()) + [
                    (f"SANDBOX_{r}", h.replace("https://", "https://sandbox.")) for r, h in SPAPI_ENDPOINTS.items()]:
                if hote == base:
                    continue
                try:
                    r = self.session.get(hote + "/sellers/v1/marketplaceParticipations", params={}, timeout=30,
                                         headers={"x-amz-access-token": jeton, "content-type": "application/json"})
                    if r.status_code < 400:
                        ligne(f"AILLEURS_{region}", True, r.status_code, "")
                except requests.RequestException:
                    pass
        cat = essai("CATALOGUE", "/catalog/2022-04-01/items",
                    {"marketplaceIds": mp.marketplace_id, "keywords": "gourde", "pageSize": "1"})
        asin = ((cat or {}).get("items") or [{}])[0].get("asin")
        if asin:
            essai("OFFRES", f"/products/pricing/v0/items/{asin}/offers",
                  {"MarketplaceId": mp.marketplace_id, "ItemCondition": "New"})
        else:
            ligne("OFFRES", None, None, "aucun ASIN pour tester")
        essai("STOCK", "/fba/inventory/v1/summaries",
              {"granularityType": "Marketplace", "granularityId": mp.marketplace_id, "marketplaceIds": mp.marketplace_id})
        maintenant = datetime.now(timezone.utc)
        essai("FINANCES", "/finances/2024-06-19/transactions",
              {"postedAfter": (maintenant - timedelta(days=7)).isoformat(timespec="seconds"),
               "postedBefore": (maintenant - timedelta(minutes=5)).isoformat(timespec="seconds")})
        return etapes

    # ------------------------------------------------------------------ stock [RM-AMZ-045]
    def page_inventaire(self, mp: Marketplace, next_token: Optional[str] = None) -> dict:
        """Une page de `GET /fba/inventory/v1/summaries`, photo complète (sans startDateTime). Rôle Amazon Fulfillment."""
        params = {"details": "true", "granularityType": "Marketplace", "granularityId": mp.marketplace_id,
                  "marketplaceIds": mp.marketplace_id}
        if next_token:
            params["nextToken"] = next_token
        return self._appel(mp, "GET", "/fba/inventory/v1/summaries", params=params)

    # ------------------------------------------------------------------ rapports (Reports API 2021-06-30)
    def rapport(self, mp: Marketplace, type_rapport: str, debut=None, fin=None, options: Optional[dict] = None,
                attendre=time.sleep, delai_max: float = 900) -> str:
        """Demande un rapport, attend qu'il soit prêt, le télécharge et le décompresse. Non testé sur un vrai compte."""
        import gzip
        corps: dict[str, Any] = {"reportType": type_rapport, "marketplaceIds": [mp.marketplace_id]}
        if debut:
            corps["dataStartTime"] = debut.isoformat()
        if fin:
            corps["dataEndTime"] = fin.isoformat()
        if options:
            corps["reportOptions"] = options
        rid = self._appel(mp, "POST", "/reports/2021-06-30/reports", json=corps)["reportId"]
        ecoule, pause = 0.0, 15.0
        while True:
            etat = self._appel(mp, "GET", f"/reports/2021-06-30/reports/{rid}")
            statut = etat.get("processingStatus")
            if statut == "DONE":
                break
            if statut == "CANCELLED":
                # Modèle officiel Reports 2021-06-30 : « automatic cancellation if there is no data to return » ;
                # l'outil n'annule jamais lui-même un rapport → rapport vide.
                return ""
            if statut == "FATAL":
                raise ErreurFournisseur(f"Rapport {type_rapport} : {statut}")
            if ecoule >= delai_max:
                raise ErreurFournisseur(f"Rapport {type_rapport} : délai dépassé")
            attendre(pause)
            ecoule += pause
        doc = self._appel(mp, "GET", f"/reports/2021-06-30/documents/{etat['reportDocumentId']}")
        r = self.session.get(doc["url"], timeout=120)
        if r.status_code != 200:
            raise ErreurFournisseur(f"Téléchargement du rapport {type_rapport} : {r.status_code}")
        brut = gzip.decompress(r.content) if doc.get("compressionAlgorithm") == "GZIP" else r.content
        for enc in ("utf-8-sig", "cp1252"):
            try:
                return brut.decode(enc)
            except UnicodeDecodeError:
                continue
        raise ErreurFournisseur("Rapport illisible")

    # ------------------------------------------------------------------ envois entrants (Inbound v0)
    def envois_fermes(self, mp: Marketplace, depuis, jusqua) -> list:
        """Envois CLOSED et leurs articles : QuantityShipped / QuantityReceived [RM-AMZ-057]. Non testé sur un vrai compte."""
        from ..remboursements import LigneEnvoi
        out, jeton = [], None
        while True:
            params = {"MarketplaceId": mp.marketplace_id, "ShipmentStatusList": "CLOSED",
                      "LastUpdatedAfter": depuis.isoformat(), "LastUpdatedBefore": jusqua.isoformat(),
                      "QueryType": "NEXT_TOKEN" if jeton else "DATE_RANGE"}
            if jeton:
                params["NextToken"] = jeton
            corps = self._appel(mp, "GET", "/fba/inbound/v0/shipments", params=params).get("payload", {})
            for env in corps.get("ShipmentData", []) or []:
                sid = env.get("ShipmentId")
                items = self._appel(mp, "GET", f"/fba/inbound/v0/shipments/{sid}/items",
                                    params={"MarketplaceId": mp.marketplace_id}).get("payload", {})
                for it in items.get("ItemData", []) or []:
                    out.append(LigneEnvoi(sid, env.get("ShipmentStatus", ""), mp.code, it.get("SellerSKU"),
                                          it.get("FulfillmentNetworkSKU", ""), int(it.get("QuantityShipped") or 0),
                                          int(it.get("QuantityReceived") or 0)))
            jeton = corps.get("NextToken")
            if not jeton:
                return out


# ====================================================================== parseurs
# Séparés du client pour être testables sans accès réseau.

def _montant(obj: Optional[dict]) -> Optional[float]:
    if not obj:
        return None
    v = obj.get("Amount", obj.get("amount"))
    return None if v is None else float(v)


_CM = {"centimeters": 1.0, "millimeters": 0.1, "meters": 100.0, "inches": 2.54}
_KG = {"kilograms": 1.0, "grams": 0.001, "pounds": 0.45359237, "ounces": 0.028349523125}


def _longueur_cm(d: Optional[dict]) -> Optional[float]:
    if not d or d.get("value") is None or str(d.get("unit", "")).lower() not in _CM:
        return None
    return round(float(d["value"]) * _CM[str(d["unit"]).lower()], 2)


def _poids_kg(d: Optional[dict]) -> Optional[float]:
    if not d or d.get("value") is None or str(d.get("unit", "")).lower() not in _KG:
        return None
    return round(float(d["value"]) * _KG[str(d["unit"]).lower()], 4)


def parser_catalogue(asin: str, mp: Marketplace, data: dict) -> InfosCatalogue:
    info = InfosCatalogue(asin=asin)
    for s in data.get("summaries", []):
        if s.get("marketplaceId") in (None, mp.marketplace_id):
            info.titre = s.get("itemName")
            info.marque = s.get("brand") or s.get("brandName")
            bc = s.get("browseClassification") or {}
            info.categorie = bc.get("displayName")
            info.classification = s.get("itemClassification")
            break
    for sr in data.get("salesRanks", []):
        if sr.get("marketplaceId") not in (None, mp.marketplace_id):
            continue
        if sr.get("displayGroupRanks"):
            info.groupe_affichage = sr["displayGroupRanks"][0].get("websiteDisplayGroup")
        rangs = sr.get("displayGroupRanks") or sr.get("classificationRanks") or []
        if rangs:
            info.bsr = int(rangs[0]["rank"])
            if not info.categorie:
                info.categorie = rangs[0].get("title")
        break
    for rel in data.get("relationships", []) or []:            # [RM-AMZ-082]
        if rel.get("marketplaceId") not in (None, mp.marketplace_id):
            continue
        enfants = {a for r in rel.get("relationships", []) or [] if r.get("type") == "VARIATION"
                   for a in r.get("childAsins", []) or []}
        if enfants:
            info.nb_variantes = len(enfants)
    for idm in data.get("identifiers", []) or []:                 # [RM-AMZ-109] codes-barres
        if idm.get("marketplaceId") not in (None, mp.marketplace_id):
            continue
        info.codes = tuple(dict.fromkeys(str(x.get("identifier")) for x in idm.get("identifiers", []) or []
                                         if x.get("identifierType") in ("EAN", "UPC", "GTIN", "ISBN")
                                         and x.get("identifier")))
        break
    for dm in data.get("dimensions", []) or []:                   # [RM-AMZ-096] colis
        if dm.get("marketplaceId") not in (None, mp.marketplace_id):
            continue
        pk = dm.get("package") or {}
        cotes = [_longueur_cm(pk.get(k)) for k in ("length", "width", "height")]
        if all(c is not None for c in cotes):
            info.dimensions_cm = tuple(cotes)
        info.poids_kg = _poids_kg(pk.get("weight"))
        break
    attrs = data.get("attributes") or {}
    for cle in ("number_of_items", "item_package_quantity"):
        vals = attrs.get(cle)
        if vals:
            try:
                info.nb_unites_lot = int(vals[0]["value"])
                break
            except (KeyError, ValueError, TypeError):
                pass
    return info


def parser_offres(mp: Marketplace, data: dict) -> InfosOffres:
    p = data.get("payload", data)
    s = p.get("Summary", {})
    res = InfosOffres(nb_offres_fba=0, nb_offres_fbm=0)
    for n in s.get("NumberOfOffers", []):
        if str(n.get("condition", "")).lower() != "new":
            continue
        if n.get("fulfillmentChannel") == "Amazon":
            res.nb_offres_fba += int(n.get("OfferCount", 0))
        else:
            res.nb_offres_fbm += int(n.get("OfferCount", 0))
    for bb in s.get("BuyBoxPrices", []):
        if str(bb.get("condition", "")).lower() == "new":
            res.prix_buybox = _montant(bb.get("LandedPrice")) or _montant(bb.get("ListingPrice"))
            break
    for lp in s.get("LowestPrices", []):
        if str(lp.get("condition", "")).lower() == "new" and lp.get("fulfillmentChannel") == "Amazon":
            v = _montant(lp.get("LandedPrice")) or _montant(lp.get("ListingPrice"))
            if v is not None and (res.prix_plus_bas_fba is None or v < res.prix_plus_bas_fba):
                res.prix_plus_bas_fba = v
    amazon_id = AMAZON_RETAIL_SELLER_IDS.get(mp.code)
    offres = p.get("Offers", [])
    if amazon_id and offres:
        res.amazon_vend = any(o.get("SellerId") == amazon_id for o in offres)
        res.buybox_amazon = any(o.get("SellerId") == amazon_id and o.get("IsBuyBoxWinner") for o in offres)
    gagnant = next((o for o in offres if o.get("IsBuyBoxWinner")), None)      # [RM-AMZ-118]
    if gagnant and gagnant.get("SellerId"):
        res.vendeur_buybox = gagnant["SellerId"]
    if res.prix_buybox is None:
        for o in offres:
            if o.get("IsBuyBoxWinner"):
                res.prix_buybox = (_montant(o.get("ListingPrice")) or 0) + (_montant(o.get("Shipping")) or 0)
                break
    return res


def parser_frais(data: dict) -> FraisAmazon:
    p = data.get("payload", data)
    r = p.get("FeesEstimateResult", {})
    if r.get("Status") not in (None, "Success"):
        err = r.get("Error") or {}
        raise ErreurFournisseur(f"Estimation des frais refusée : {err.get('Message') or err}")
    est = r.get("FeesEstimate", {})
    frais = FraisAmazon(commission=0.0, source="sp-api")
    for d in est.get("FeeDetailList", []):
        montant = _montant(d.get("FinalFee")) or _montant(d.get("FeeAmount")) or 0.0
        champ = _TYPES_FRAIS.get(d.get("FeeType"), "autres")
        setattr(frais, champ, getattr(frais, champ) + montant)
    if frais.total_ht == 0 and est.get("TotalFeesEstimate"):
        frais.autres = _montant(est["TotalFeesEstimate"]) or 0.0
    return frais


def parser_restrictions(data: dict) -> InfosRestrictions:
    restr = data.get("restrictions", [])
    if not restr:
        return InfosRestrictions(autorise=True)
    res = InfosRestrictions(autorise=False)
    for r in restr:
        for raison in r.get("reasons", []):
            code = raison.get("reasonCode", "")
            if code == "APPROVAL_REQUIRED":
                res.approbation_requise = True
            res.motifs.append(f"{code} : {raison.get('message', '')}".strip(" :"))
            for l in raison.get("links", []) or []:                      # [RM-AMZ-120] tels quels
                url = l.get("resource")
                if url and url.startswith("https://") and not any(x["url"] == url for x in res.liens):
                    res.liens.append({"titre": l.get("title") or None, "url": url})
    return res

