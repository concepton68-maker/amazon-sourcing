"""Référentiel des places de marché Amazon.

Sources : documentation SP-API « Marketplace IDs » et « SP-API Endpoints »
(developer-docs.amazon.com), documentation Keepa (paramètre `domain`).

Les taux de TVA / GST sont les TAUX STANDARD du pays. Certaines catégories
(livres, alimentation, enfants...) ont des taux réduits : le taux est donc
toujours surchargeable par produit. À vérifier avant toute décision d'achat.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Marketplace:
    code: str                 # code court utilisé dans l'outil (FR, DE, US...)
    nom: str
    domaine: str              # amazon.fr ...
    marketplace_id: str       # identifiant SP-API
    region: str               # NA / EU / FE (endpoint SP-API)
    devise: str
    taux_tva_standard: float  # 0.20 = 20 % ; 0 si prix affichés hors taxe
    prix_ttc: bool            # True si les prix Amazon affichés incluent la TVA/GST
    keepa_domain: Optional[int]  # None = non couvert par Keepa (à notre connaissance)


SPAPI_ENDPOINTS = {
    "NA": "https://sellingpartnerapi-na.amazon.com",
    "EU": "https://sellingpartnerapi-eu.amazon.com",
    "FE": "https://sellingpartnerapi-fe.amazon.com",
}

_MARKETPLACES = [
    # --- Amérique du Nord / Sud (endpoint NA) ---
    # US / CA : taxes de vente ajoutées au moment du paiement, prix affichés HT.
    Marketplace("US", "États-Unis", "amazon.com", "ATVPDKIKX0DER", "NA", "USD", 0.0, False, 1),
    Marketplace("CA", "Canada", "amazon.ca", "A2EUQ1WTGCTBG2", "NA", "CAD", 0.0, False, 6),
    Marketplace("MX", "Mexique", "amazon.com.mx", "A1AM78C64UM0Y8", "NA", "MXN", 0.16, True, 11),
    Marketplace("BR", "Brésil", "amazon.com.br", "A2Q3Y263D00KWC", "NA", "BRL", 0.0, True, 12),  # domaine Keepa .com.br (doc officielle keepa.com/api-docs) — n° 12 à confirmer au 1er appel
    # --- Europe / Moyen-Orient / Afrique / Inde (endpoint EU) ---
    Marketplace("UK", "Royaume-Uni", "amazon.co.uk", "A1F83G8C2ARO7P", "EU", "GBP", 0.20, True, 2),
    Marketplace("DE", "Allemagne", "amazon.de", "A1PA6795UKMFR9", "EU", "EUR", 0.19, True, 3),
    Marketplace("FR", "France", "amazon.fr", "A13V1IB3VIYZZH", "EU", "EUR", 0.20, True, 4),
    Marketplace("IT", "Italie", "amazon.it", "APJ6JRA9NG5V4", "EU", "EUR", 0.22, True, 8),
    Marketplace("ES", "Espagne", "amazon.es", "A1RKKUPIHCS9HS", "EU", "EUR", 0.21, True, 9),
    Marketplace("NL", "Pays-Bas", "amazon.nl", "A1805IZSGTT6HS", "EU", "EUR", 0.21, True, None),
    Marketplace("BE", "Belgique", "amazon.com.be", "AMEN7PMS3EDWL", "EU", "EUR", 0.21, True, None),
    Marketplace("IE", "Irlande", "amazon.ie", "A28R8C7NBKEWEA", "EU", "EUR", 0.23, True, None),
    Marketplace("SE", "Suède", "amazon.se", "A2NODRKZP88ZB9", "EU", "SEK", 0.25, True, None),
    Marketplace("PL", "Pologne", "amazon.pl", "A1C3SOZRARQ6R3", "EU", "PLN", 0.23, True, None),
    Marketplace("TR", "Turquie", "amazon.com.tr", "A33AVAJ2PDY3EV", "EU", "TRY", 0.20, True, None),
    Marketplace("AE", "Émirats arabes unis", "amazon.ae", "A2VIGQ35RCS4UG", "EU", "AED", 0.05, True, None),
    Marketplace("SA", "Arabie saoudite", "amazon.sa", "A17E79C6D8DWNP", "EU", "SAR", 0.15, True, None),
    Marketplace("EG", "Égypte", "amazon.eg", "ARBP9OOSHTCHU", "EU", "EGP", 0.14, True, None),
    Marketplace("IN", "Inde", "amazon.in", "A21TJRUUN4KGV", "EU", "INR", 0.18, True, 10),
    Marketplace("ZA", "Afrique du Sud", "amazon.co.za", "AE08WJ6YKNBMC", "EU", "ZAR", 0.15, True, None),
    # --- Extrême-Orient (endpoint FE) ---
    Marketplace("JP", "Japon", "amazon.co.jp", "A1VC38T7YXB528", "FE", "JPY", 0.10, True, 5),
    Marketplace("AU", "Australie", "amazon.com.au", "A39IBJ37TRP1C6", "FE", "AUD", 0.10, True, None),
    Marketplace("SG", "Singapour", "amazon.sg", "A19VAU5U5O7RUS", "FE", "SGD", 0.09, True, None),
]

MARKETPLACES: dict[str, Marketplace] = {m.code: m for m in _MARKETPLACES}


def get_marketplace(code: str) -> Marketplace:
    code = code.strip().upper()
    if code == "GB":
        code = "UK"
    try:
        return MARKETPLACES[code]
    except KeyError:
        connus = ", ".join(sorted(MARKETPLACES))
        raise ValueError(f"Place de marché inconnue : {code}. Codes connus : {connus}") from None
