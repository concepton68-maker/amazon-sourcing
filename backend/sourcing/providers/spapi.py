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
                    "includedData": "summaries,salesRanks,attributes"},
        )
        return parser_catalogue(asin, mp, data)

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


# ====================================================================== parseurs
# Séparés du client pour être testables sans accès réseau.

def _montant(obj: Optional[dict]) -> Optional[float]:
    if not obj:
        return None
    v = obj.get("Amount", obj.get("amount"))
    return None if v is None else float(v)


def parser_catalogue(asin: str, mp: Marketplace, data: dict) -> InfosCatalogue:
    info = InfosCatalogue(asin=asin)
    for s in data.get("summaries", []):
        if s.get("marketplaceId") in (None, mp.marketplace_id):
            info.titre = s.get("itemName")
            info.marque = s.get("brand") or s.get("brandName")
            bc = s.get("browseClassification") or {}
            info.categorie = bc.get("displayName")
            break
    for sr in data.get("salesRanks", []):
        if sr.get("marketplaceId") not in (None, mp.marketplace_id):
            continue
        rangs = sr.get("displayGroupRanks") or sr.get("classificationRanks") or []
        if rangs:
            info.bsr = int(rangs[0]["rank"])
            if not info.categorie:
                info.categorie = rangs[0].get("title")
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
    return res
