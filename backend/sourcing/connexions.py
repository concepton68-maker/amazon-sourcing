"""Connexions aux sources (Amazon SP-API, Keepa) saisies par le vendeur — [RM-AMZ-072 à 074].

Les identifiants sont chiffrés (AES-256-GCM) avec la clé du serveur `AMZ_CLE_CHIFFREMENT` (64 caractères hexadécimaux) ;
le compte et la source sont liés au chiffré (données associées) : un chiffré copié vers un autre compte ne se déchiffre pas.
Ils ne sont jamais renvoyés par l'API.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SOURCES = {"SPAPI": ("client_id", "client_secret", "refresh_token", "region"), "KEEPA": ("cle",)}
REGIONS = ("EU", "NA", "FE")
MAX = 2000


class ConnexionInvalide(ValueError):
    """args = (code, champ)."""


@dataclass(frozen=True)
class Connexion:
    source: str
    chiffre: bytes
    maj: datetime


def cle_serveur() -> Optional[bytes]:
    brut = os.environ.get("AMZ_CLE_CHIFFREMENT", "").strip()
    try:
        cle = bytes.fromhex(brut)
    except ValueError:
        return None
    return cle if len(cle) == 32 else None


def valider(source: str, brut: dict) -> dict:
    """[RM-AMZ-072] Champs attendus, non vides, 2 000 caractères au plus ; région connue."""
    if source not in SOURCES:
        raise ConnexionInvalide("SOURCE_INCONNUE", "source")
    if not isinstance(brut, dict) or set(brut) != set(SOURCES[source]):
        raise ConnexionInvalide("SAISIE_INVALIDE", "champs")
    propre = {}
    for k in SOURCES[source]:
        v = brut[k]
        if not isinstance(v, str) or not v.strip():
            raise ConnexionInvalide("CHAMP_OBLIGATOIRE", k)
        if len(v) > MAX:
            raise ConnexionInvalide("TROP_LONG", k)
        propre[k] = v.strip()
    if source == "SPAPI" and propre["region"] not in REGIONS:
        raise ConnexionInvalide("SAISIE_INVALIDE", "region")
    return propre


def _aad(compte_id: str, source: str) -> bytes:
    return f"{compte_id}:{source}".encode()


def chiffrer(cle: Optional[bytes], compte_id: str, source: str, valeurs: dict) -> bytes:
    """[RM-AMZ-074] Sans clé : refus, jamais de clair."""
    if not cle:
        raise ConnexionInvalide("CHIFFREMENT_NON_CONFIGURE", "serveur")
    nonce = os.urandom(12)
    return nonce + AESGCM(cle).encrypt(nonce, json.dumps(valeurs).encode(), _aad(compte_id, source))


def dechiffrer(cle: bytes, compte_id: str, source: str, chiffre: bytes) -> dict:
    return json.loads(AESGCM(cle).decrypt(chiffre[:12], chiffre[12:], _aad(compte_id, source)))


def fournisseurs_du_compte(connexions: dict[str, dict]):
    """[RM-AMZ-073] Construit les sources à partir des identifiants déchiffrés du compte."""
    from .analyse import Fournisseurs
    from .providers.keepa import ClientKeepa
    from .providers.spapi import ClientSPAPI
    f = Fournisseurs()
    sp = connexions.get("SPAPI")
    if sp:
        c = ClientSPAPI(client_id=sp["client_id"], client_secret=sp["client_secret"],
                        refresh_tokens={sp["region"]: sp["refresh_token"]})
        f.catalogue.append(c)
        f.offres = f.frais = f.restrictions = c
    kp = connexions.get("KEEPA")
    if kp:
        k = ClientKeepa(cle=kp["cle"])
        f.catalogue.append(k)
        f.historique = k
    return f
