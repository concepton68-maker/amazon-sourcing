"""Messagerie Microsoft : connexion (code + PKCE) et envoi du bon de commande — [RM-AMZ-129 à 131].

Faits sourcés : docs/recherches/2026-11-14-messagerie-microsoft.md (learn.microsoft.com, lu le 14/11/2026).
Envoi seul : aucune portée de lecture de la boîte n'est jamais demandée.
"""
from __future__ import annotations

import base64
import hashlib
import secrets
import threading
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import requests

AUTORITE = "https://login.microsoftonline.com/common/oauth2/v2.0"
GRAPH = "https://graph.microsoft.com/v1.0"
PORTEES = "openid email profile offline_access https://graph.microsoft.com/User.Read https://graph.microsoft.com/Mail.Send"
DUREE_STATE = timedelta(minutes=10)
PIECE_MAX = 3 * 1024 * 1024          # sous 3 Mo : pièce jointe dans la requête sendMail
DELAI = 20                           # secondes par appel
REPRISES = 2                         # 429 / 503 seulement
ATTENTE_MAX = 5.0

ENVOYE, ECHEC, INCERTAIN = "ENVOYE", "ECHEC", "INCERTAIN"


class ErreurMessagerie(Exception):
    """args = (code,)"""


def _maintenant() -> datetime:
    return datetime.now(timezone.utc)


# ------------------------------------------------------------------------------------------- connexion
@dataclass
class Demarrage:
    compte_id: str
    verificateur: str
    expire: datetime


class Etats:
    """[RM-AMZ-129] `state` aléatoire, à usage unique, 10 minutes, lié au compte (gardé en mémoire)."""

    def __init__(self):
        self._d: dict[str, Demarrage] = {}
        self._verrou = threading.Lock()

    def creer(self, compte_id: str, quand: Optional[datetime] = None) -> tuple[str, str]:
        quand = quand or _maintenant()
        state = secrets.token_urlsafe(32)
        verificateur = secrets.token_urlsafe(64)
        with self._verrou:
            self._d = {k: v for k, v in self._d.items() if v.expire > quand and v.compte_id != compte_id}
            self._d[state] = Demarrage(compte_id, verificateur, quand + DUREE_STATE)
        return state, verificateur

    def consommer(self, state: str, compte_id: str, quand: Optional[datetime] = None) -> str:
        quand = quand or _maintenant()
        with self._verrou:
            d = self._d.pop(state or "", None)
        if d is None or d.compte_id != compte_id or d.expire <= quand:
            raise ErreurMessagerie("STATE_INVALIDE")
        return d.verificateur


def defi(verificateur: str) -> str:
    """PKCE S256."""
    return base64.urlsafe_b64encode(hashlib.sha256(verificateur.encode()).digest()).rstrip(b"=").decode()


def url_autorisation(client_id: str, retour: str, state: str, verificateur: str) -> str:
    q = {"client_id": client_id, "response_type": "code", "redirect_uri": retour, "response_mode": "query",
         "scope": PORTEES, "state": state, "code_challenge": defi(verificateur), "code_challenge_method": "S256",
         "prompt": "select_account"}
    return f"{AUTORITE}/authorize?{urllib.parse.urlencode(q)}"


class Microsoft:
    """Appels HTTP vers Microsoft ; `session` remplaçable dans les tests."""

    def __init__(self, client_id: str, client_secret: str, session: Optional[requests.Session] = None,
                 attendre: Callable[[float], None] = time.sleep):
        self.client_id, self.client_secret = client_id, client_secret
        self.s = session or requests.Session()
        self.attendre = attendre

    def _jeton(self, corps: dict, exiger_actualisation: bool = True) -> dict:
        try:
            r = self.s.post(f"{AUTORITE}/token", data={"client_id": self.client_id, "client_secret": self.client_secret,
                                                        "scope": PORTEES, **corps}, timeout=DELAI)
        except requests.RequestException:
            raise ErreurMessagerie("INDISPONIBLE") from None
        j = r.json() if r.content else {}
        if r.status_code != 200:
            err = j.get("error")
            if err == "invalid_grant":
                raise ErreurMessagerie("A_RECONNECTER")
            if err in ("invalid_client", "unauthorized_client"):
                raise ErreurMessagerie("APPLICATION_REFUSEE")
            raise ErreurMessagerie("ECHANGE")
        if "mail.send" not in (j.get("scope") or "").lower() or (exiger_actualisation and not j.get("refresh_token")):
            raise ErreurMessagerie("PORTEE")
        return j

    def echanger(self, code: str, retour: str, verificateur: str) -> dict:
        return self._jeton({"grant_type": "authorization_code", "code": code, "redirect_uri": retour,
                            "code_verifier": verificateur})

    def actualiser(self, refresh_token: str) -> dict:
        return self._jeton({"grant_type": "refresh_token", "refresh_token": refresh_token}, exiger_actualisation=False)

    def adresse(self, access_token: str) -> tuple[str, Optional[str]]:
        try:
            r = self.s.get(f"{GRAPH}/me?$select=mail,userPrincipalName,displayName",
                           headers={"Authorization": f"Bearer {access_token}"}, timeout=DELAI)
        except requests.RequestException:
            raise ErreurMessagerie("INDISPONIBLE") from None
        if r.status_code != 200:
            raise ErreurMessagerie("ADRESSE")
        j = r.json()
        a = j.get("mail") or j.get("userPrincipalName")
        if not a:
            raise ErreurMessagerie("ADRESSE")
        return a, j.get("displayName")

    def envoyer(self, access_token: str, message: dict) -> tuple[str, Optional[str], Optional[int]]:
        """[RM-AMZ-131] → (état, cause, statut HTTP). 429/503 repris deux fois au plus ; le reste n'est jamais repris."""
        for essai in range(REPRISES + 1):
            try:
                r = self.s.post(f"{GRAPH}/me/sendMail", json={"message": message, "saveToSentItems": True},
                                headers={"Authorization": f"Bearer {access_token}"}, timeout=DELAI)
            except requests.ConnectionError:
                return ECHEC, "INJOIGNABLE", None          # rien n'est parti
            except requests.RequestException:
                return INCERTAIN, "DELAI_DEPASSE", None
            if r.status_code == 202:
                return ENVOYE, None, 202
            if r.status_code in (429, 503) and essai < REPRISES:
                try:
                    attente = float(r.headers.get("Retry-After", "1"))
                except ValueError:
                    attente = 1.0
                self.attendre(min(max(attente, 0.0), ATTENTE_MAX))
                continue
            if r.status_code == 401:
                return ECHEC, "JETON", 401
            if r.status_code in (429, 503):
                return ECHEC, "OCCUPE", r.status_code
            if 400 <= r.status_code < 500:
                return ECHEC, f"REFUS_{r.status_code}", r.status_code
            return INCERTAIN, f"REPONSE_{r.status_code}", r.status_code
        return ECHEC, "OCCUPE", None


# ---------------------------------------------------------------------------------------------- message
def message_bon(bon, fournisseur, societe: dict, pdf: bytes) -> dict:
    """[RM-AMZ-130] Objet, texte, pièce jointe ; « répondre à » = courriel de la Société s'il existe."""
    nom = (societe or {}).get("raison_sociale")
    objet = f"Bon de commande {bon.reference}" + (f" — {nom}" if nom else "")
    texte = (f"Bonjour,\n\nVeuillez trouver ci-joint notre bon de commande {bon.reference}.\n"
             "Merci de nous confirmer sa bonne réception, la disponibilité et la date d'expédition.\n\n"
             "Cordialement,\n" + (nom or ""))
    m = {"subject": objet, "body": {"contentType": "Text", "content": texte},
         "toRecipients": [{"emailAddress": {"address": fournisseur.courriel}}],
         "attachments": [{"@odata.type": "#microsoft.graph.fileAttachment", "name": f"{bon.reference}.pdf",
                          "contentType": "application/pdf", "contentBytes": base64.b64encode(pdf).decode()}]}
    if (societe or {}).get("courriel"):
        m["replyTo"] = [{"emailAddress": {"address": societe["courriel"]}}]
    return m


@dataclass
class Tentative:
    bon_id: str
    generation: int
    a: str
    objet: str
    empreinte: str
    taille: int
    etat: str
    cause: Optional[str] = None
    le: datetime = field(default_factory=_maintenant)
    expediteur: Optional[str] = None


def controler(bon, fournisseur, pdf: bytes, connectee: bool):
    """[RM-AMZ-130] Refus avant tout envoi."""
    if not connectee:
        raise ErreurMessagerie("NON_CONNECTEE")
    if not fournisseur or not fournisseur.courriel:
        raise ErreurMessagerie("SANS_COURRIEL")
    if not bon.lignes:
        raise ErreurMessagerie("BON_VIDE")
    if bon.statut not in ("BROUILLON", "ENVOYE"):
        raise ErreurMessagerie("BON_FERME")
    if len(pdf) >= PIECE_MAX:
        raise ErreurMessagerie("TROP_GROS")


class Verrous:
    """[RM-AMZ-131] Une seule tentative à la fois par bon."""

    def __init__(self):
        self._en_cours: set[str] = set()
        self._v = threading.Lock()

    def prendre(self, bon_id: str) -> bool:
        with self._v:
            if bon_id in self._en_cours:
                return False
            self._en_cours.add(bon_id)
            return True

    def rendre(self, bon_id: str) -> None:
        with self._v:
            self._en_cours.discard(bon_id)
