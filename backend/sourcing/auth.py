"""Utilisateurs, mots de passe, double authentification et sessions — [RM-AMZ-036 à 038, 041, 075, 076].

Les tables d'authentification ne sont pas cloisonnées par compte (on ne connaît le compte
qu'après la connexion) ; elles ne sont lues que par courriel ou par empreinte de jeton.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

LONGUEUR_MIN = 12
ECHECS_MAX = 5
BLOCAGE = timedelta(minutes=15)
INACTIVITE_MAX = timedelta(hours=12)
DUREE_MAX = timedelta(days=30)
EXPIRATION_MDP = timedelta(days=365)          # [RM-AMZ-075]
TOTP_PAS, TOTP_CHIFFRES, TOTP_TOLERANCE = 30, 6, 1   # [RM-AMZ-076] RFC 6238, paramètres par défaut
NB_CODES_SECOURS = 10
# Étapes d'une session [RM-AMZ-075, 076] : seule COMPLET donne accès aux données.
CHANGER_MDP, ENROLER, CODE, COMPLET = "CHANGER_MDP", "ENROLER", "CODE", "COMPLET"

_hacheur = PasswordHasher()   # Argon2id, réglages par défaut de la bibliothèque (à vérifier, RM-AMZ-036)


class ErreurAuth(Exception):
    """Le code (premier argument) est traduit par l'interface."""


@dataclass(frozen=True)
class Utilisateur:
    id: str
    compte_id: str
    courriel: str
    empreinte: str
    echecs: int = 0
    bloque_jusqua: Optional[datetime] = None
    mdp_change_le: Optional[datetime] = None
    totp_chiffre: Optional[bytes] = None
    totp_actif: bool = False
    totp_dernier_pas: int = 0
    codes_secours: tuple[str, ...] = ()


@dataclass(frozen=True)
class Session:
    jeton_hash: str
    utilisateur_id: str
    compte_id: str
    cree_le: datetime
    vu_le: datetime
    niveau: str = COMPLET


def _norme(courriel: str) -> str:
    return courriel.strip().lower()


def conforme(mdp: str) -> bool:
    """[RM-AMZ-075] 12 caractères au moins dont un caractère spécial (ni lettre ni chiffre)."""
    return len(mdp) >= LONGUEUR_MIN and any(not c.isalnum() for c in mdp)


def empreinte_mot_de_passe(mdp: str) -> str:
    if len(mdp) < LONGUEUR_MIN:
        raise ErreurAuth("MOT_DE_PASSE_TROP_COURT")
    if not conforme(mdp):
        raise ErreurAuth("MOT_DE_PASSE_SANS_CARACTERE_SPECIAL")
    return _hacheur.hash(mdp)


# ------------------------------------------------------------------ TOTP [RM-AMZ-076]
def totp(secret: bytes, pas: int) -> str:
    """RFC 6238 / RFC 4226 : HMAC-SHA1 du compteur, troncature dynamique, 6 chiffres."""
    h = hmac.new(secret, struct.pack(">Q", pas), hashlib.sha1).digest()
    o = h[-1] & 0x0F
    n = (struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % 10 ** TOTP_CHIFFRES
    return str(n).zfill(TOTP_CHIFFRES)


def pas_de(quand: datetime) -> int:
    return int(quand.timestamp()) // TOTP_PAS


def uri_totp(secret: bytes, courriel: str) -> str:
    from urllib.parse import quote
    b32 = base64.b32encode(secret).decode().rstrip("=")
    return f"otpauth://totp/{quote('Syllig Vente:' + courriel)}?secret={b32}&issuer={quote('Syllig Vente')}&digits=6&period=30"


def qr_svg(texte: str) -> str:
    import io

    import qrcode
    import qrcode.image.svg
    tampon = io.BytesIO()
    qrcode.make(texte, image_factory=qrcode.image.svg.SvgPathImage, box_size=8).save(tampon)
    return tampon.getvalue().decode()


def _h(code: str) -> str:
    return hashlib.sha256(code.strip().lower().replace("-", "").encode()).hexdigest()


def _hash_jeton(jeton: str) -> str:
    return hashlib.sha256(jeton.encode()).hexdigest()


# ------------------------------------------------------------------ stockage en mémoire (tests, démo)
class StockAuthMemoire:
    def __init__(self):
        self.utilisateurs: dict[str, Utilisateur] = {}   # courriel normé -> utilisateur
        self.sessions: dict[str, Session] = {}

    def par_courriel(self, courriel: str) -> Optional[Utilisateur]:
        return self.utilisateurs.get(_norme(courriel))

    def enregistrer_utilisateur(self, u: Utilisateur) -> None:
        self.utilisateurs[u.courriel] = u

    def par_id(self, uid: str) -> Optional[Utilisateur]:
        return next((u for u in self.utilisateurs.values() if u.id == uid), None)

    def changer_niveau(self, jeton_hash: str, niveau: str) -> None:
        s = self.sessions.get(jeton_hash)
        if s:
            self.sessions[jeton_hash] = replace(s, niveau=niveau)

    def creer_session(self, s: Session) -> None:
        self.sessions[s.jeton_hash] = s

    def session(self, jeton_hash: str) -> Optional[Session]:
        return self.sessions.get(jeton_hash)

    def toucher_session(self, jeton_hash: str, quand: datetime) -> None:
        s = self.sessions.get(jeton_hash)
        if s:
            self.sessions[jeton_hash] = replace(s, vu_le=quand)

    def supprimer_session(self, jeton_hash: str) -> None:
        self.sessions.pop(jeton_hash, None)


# ------------------------------------------------------------------ service
class Authentification:
    def __init__(self, stock, cle=None):
        """`cle` : fonction qui renvoie la clé de chiffrement du serveur (secret TOTP chiffré, RM-AMZ-072)."""
        self.stock = stock
        if cle is None:
            from .connexions import cle_serveur as cle
        self.cle = cle

    def creer_utilisateur(self, compte_id: str, courriel: str, mdp: str) -> Utilisateur:
        """[RM-AMZ-041] Appelé par la ligne de commande seulement."""
        c = _norme(courriel)
        if "@" not in c or len(c) > 254:
            raise ErreurAuth("COURRIEL_INVALIDE")
        if self.stock.par_courriel(c):
            raise ErreurAuth("COURRIEL_DEJA_UTILISE")
        u = Utilisateur(str(uuid.uuid4()), compte_id, c, empreinte_mot_de_passe(mdp),
                        mdp_change_le=datetime.now(timezone.utc))
        self.stock.enregistrer_utilisateur(u)
        return u

    def connecter(self, courriel: str, mdp: str, maintenant: Optional[datetime] = None) -> tuple[str, Session]:
        """[RM-AMZ-037] Renvoie (jeton en clair pour le cookie, session). Même erreur que le courriel existe ou non."""
        maintenant = maintenant or datetime.now(timezone.utc)
        u = self.stock.par_courriel(courriel)
        if u is None:
            _hacheur.hash(mdp)            # même coût de calcul : ne révèle pas l'existence du courriel
            raise ErreurAuth("IDENTIFIANTS_INVALIDES")
        if u.bloque_jusqua and u.bloque_jusqua > maintenant:
            raise ErreurAuth("TROP_D_ESSAIS")
        try:
            _hacheur.verify(u.empreinte, mdp)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            echecs = u.echecs + 1
            bloque = maintenant + BLOCAGE if echecs >= ECHECS_MAX else None
            self.stock.enregistrer_utilisateur(replace(u, echecs=0 if bloque else echecs, bloque_jusqua=bloque))
            raise ErreurAuth("TROP_D_ESSAIS" if bloque else "IDENTIFIANTS_INVALIDES") from None
        if _hacheur.check_needs_rehash(u.empreinte):
            u = replace(u, empreinte=_hacheur.hash(mdp))
        self.stock.enregistrer_utilisateur(replace(u, echecs=0, bloque_jusqua=None))
        jeton = secrets.token_urlsafe(32)                      # 256 bits [RM-AMZ-038]
        expire = u.mdp_change_le is None or maintenant - u.mdp_change_le > EXPIRATION_MDP
        niveau = CHANGER_MDP if (expire or not conforme(mdp)) else (CODE if u.totp_actif else ENROLER)
        s = Session(_hash_jeton(jeton), u.id, u.compte_id, maintenant, maintenant, niveau)
        self.stock.creer_session(s)
        return jeton, s

    def session_valide(self, jeton: Optional[str], maintenant: Optional[datetime] = None) -> Optional[Session]:
        """[RM-AMZ-038] Inactivité 12 h, durée totale 30 j ; une session expirée est supprimée."""
        if not jeton:
            return None
        maintenant = maintenant or datetime.now(timezone.utc)
        h = _hash_jeton(jeton)
        s = self.stock.session(h)
        if s is None:
            return None
        if maintenant - s.vu_le > INACTIVITE_MAX or maintenant - s.cree_le > DUREE_MAX:
            self.stock.supprimer_session(h)
            return None
        self.stock.toucher_session(h, maintenant)
        return s

    # ---------------------------------------------------------- étapes après le mot de passe [RM-AMZ-075, 076]
    def _etape(self, s: Session, attendu: str) -> Utilisateur:
        if s.niveau != attendu:
            raise ErreurAuth("ETAPE_INVALIDE")
        u = self.stock.par_id(s.utilisateur_id)
        if u is None:
            raise ErreurAuth("NON_CONNECTE")
        return u

    def changer_mot_de_passe(self, s: Session, nouveau: str, maintenant: Optional[datetime] = None) -> str:
        maintenant = maintenant or datetime.now(timezone.utc)
        u = self._etape(s, CHANGER_MDP)
        empreinte = empreinte_mot_de_passe(nouveau)
        try:
            _hacheur.verify(u.empreinte, nouveau)
            raise ErreurAuth("MOT_DE_PASSE_IDENTIQUE")
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            pass
        u = replace(u, empreinte=empreinte, mdp_change_le=maintenant)
        self.stock.enregistrer_utilisateur(u)
        niveau = CODE if u.totp_actif else ENROLER
        self.stock.changer_niveau(s.jeton_hash, niveau)
        return niveau

    def _cle(self) -> bytes:
        k = self.cle()
        if not k:
            raise ErreurAuth("CHIFFREMENT_NON_CONFIGURE")
        return k

    def debuter_enrolement(self, s: Session) -> tuple[bytes, str]:
        """Nouveau secret (160 bits), gardé chiffré, inactif jusqu'à la confirmation. Renvoie (secret, URI)."""
        from .connexions import chiffrer
        u = self._etape(s, ENROLER)
        secret = secrets.token_bytes(20)
        self.stock.enregistrer_utilisateur(replace(u, totp_chiffre=chiffrer(self._cle(), u.id, "TOTP", {"s": secret.hex()}),
                                                   totp_actif=False))
        return secret, uri_totp(secret, u.courriel)

    def _secret(self, u: Utilisateur) -> bytes:
        from .connexions import dechiffrer
        if not u.totp_chiffre:
            raise ErreurAuth("ENROLEMENT_NON_COMMENCE")
        return bytes.fromhex(dechiffrer(self._cle(), u.id, "TOTP", u.totp_chiffre)["s"])

    def _pas_valide(self, u: Utilisateur, code: str, maintenant: datetime) -> Optional[int]:
        code = (code or "").strip().replace(" ", "")
        if not (code.isdigit() and len(code) == TOTP_CHIFFRES):
            return None
        secret, p = self._secret(u), pas_de(maintenant)
        for d in range(-TOTP_TOLERANCE, TOTP_TOLERANCE + 1):
            if p + d > u.totp_dernier_pas and hmac.compare_digest(totp(secret, p + d), code):
                return p + d
        return None

    def _echec(self, u: Utilisateur, maintenant: datetime):
        echecs = u.echecs + 1
        bloque = maintenant + BLOCAGE if echecs >= ECHECS_MAX else None
        self.stock.enregistrer_utilisateur(replace(u, echecs=0 if bloque else echecs, bloque_jusqua=bloque))
        raise ErreurAuth("TROP_D_ESSAIS" if bloque else "CODE_INVALIDE")

    def confirmer_enrolement(self, s: Session, code: str, maintenant: Optional[datetime] = None) -> list[str]:
        """Active la double authentification et renvoie les 10 codes de secours (affichés une seule fois)."""
        maintenant = maintenant or datetime.now(timezone.utc)
        u = self._etape(s, ENROLER)
        p = self._pas_valide(u, code, maintenant)
        if p is None:
            self._echec(u, maintenant)
        codes = [f"{secrets.token_hex(3)}-{secrets.token_hex(3)}" for _ in range(NB_CODES_SECOURS)]
        self.stock.enregistrer_utilisateur(replace(u, totp_actif=True, totp_dernier_pas=p, echecs=0, bloque_jusqua=None,
                                                   codes_secours=tuple(_h(c) for c in codes)))
        self.stock.changer_niveau(s.jeton_hash, COMPLET)
        return codes

    def verifier_code(self, s: Session, code: str, maintenant: Optional[datetime] = None) -> None:
        """Code TOTP (une seule fois chacun) ou code de secours (consommé)."""
        maintenant = maintenant or datetime.now(timezone.utc)
        u = self._etape(s, CODE)
        if u.bloque_jusqua and u.bloque_jusqua > maintenant:
            raise ErreurAuth("TROP_D_ESSAIS")
        p = self._pas_valide(u, code, maintenant)
        if p is not None:
            u = replace(u, totp_dernier_pas=p)
        elif _h(code or "") in u.codes_secours:
            u = replace(u, codes_secours=tuple(c for c in u.codes_secours if c != _h(code)))
        else:
            self._echec(u, maintenant)
        self.stock.enregistrer_utilisateur(replace(u, echecs=0, bloque_jusqua=None))
        self.stock.changer_niveau(s.jeton_hash, COMPLET)

    def deconnecter(self, jeton: Optional[str]) -> None:
        if jeton:
            self.stock.supprimer_session(_hash_jeton(jeton))


# ------------------------------------------------------------------ stockage Postgres
class StockAuthPostgres:
    def __init__(self, source):
        self.source = source            # connexion psycopg ou db.Reserve

    def _x(self, sql, params=(), un=False):
        from .db import connexion
        with connexion(self.source) as conn:
            cur = conn.execute(sql, params)
            return cur.fetchone() if un else None

    _COLS = ("id, compte_id, courriel, empreinte, echecs, bloque_jusqua, mdp_change_le, totp_chiffre, totp_actif, "
             "totp_dernier_pas, codes_secours")

    def _u(self, r) -> Utilisateur:
        return Utilisateur(str(r[0]), str(r[1]), r[2], r[3], r[4], r[5], r[6], bytes(r[7]) if r[7] else None, r[8],
                           r[9], tuple(r[10] or ()))

    def par_courriel(self, courriel: str) -> Optional[Utilisateur]:
        r = self._x(f"SELECT {self._COLS} FROM amz.utilisateurs WHERE courriel = %s", (_norme(courriel),), un=True)
        return self._u(r) if r else None

    def par_id(self, uid: str) -> Optional[Utilisateur]:
        r = self._x(f"SELECT {self._COLS} FROM amz.utilisateurs WHERE id = %s", (uuid.UUID(uid),), un=True)
        return self._u(r) if r else None

    def enregistrer_utilisateur(self, u: Utilisateur) -> None:
        self._x("""INSERT INTO amz.utilisateurs (id, compte_id, courriel, empreinte, echecs, bloque_jusqua, mdp_change_le,
            totp_chiffre, totp_actif, totp_dernier_pas, codes_secours)
            VALUES (%s, %s, %s, %s, %s, %s, coalesce(%s, now()), %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET
            empreinte = EXCLUDED.empreinte, echecs = EXCLUDED.echecs, bloque_jusqua = EXCLUDED.bloque_jusqua,
            mdp_change_le = EXCLUDED.mdp_change_le, totp_chiffre = EXCLUDED.totp_chiffre, totp_actif = EXCLUDED.totp_actif,
            totp_dernier_pas = EXCLUDED.totp_dernier_pas, codes_secours = EXCLUDED.codes_secours""",
            (uuid.UUID(u.id), uuid.UUID(u.compte_id), u.courriel, u.empreinte, u.echecs, u.bloque_jusqua, u.mdp_change_le,
             u.totp_chiffre, u.totp_actif, u.totp_dernier_pas, list(u.codes_secours)))

    def changer_niveau(self, jeton_hash: str, niveau: str) -> None:
        self._x("UPDATE amz.sessions SET niveau = %s WHERE jeton_hash = %s", (niveau, jeton_hash))

    def creer_session(self, s: Session) -> None:
        self._x("INSERT INTO amz.sessions (jeton_hash, utilisateur_id, compte_id, cree_le, vu_le, niveau) "
                "VALUES (%s, %s, %s, %s, %s, %s)", (s.jeton_hash, uuid.UUID(s.utilisateur_id),
                                                    uuid.UUID(s.compte_id), s.cree_le, s.vu_le, s.niveau))

    def session(self, jeton_hash: str) -> Optional[Session]:
        r = self._x("SELECT jeton_hash, utilisateur_id, compte_id, cree_le, vu_le, niveau FROM amz.sessions "
                    "WHERE jeton_hash = %s", (jeton_hash,), un=True)
        return Session(r[0], str(r[1]), str(r[2]), r[3], r[4], r[5]) if r else None

    def toucher_session(self, jeton_hash: str, quand: datetime) -> None:
        self._x("UPDATE amz.sessions SET vu_le = %s WHERE jeton_hash = %s", (quand, jeton_hash))

    def supprimer_session(self, jeton_hash: str) -> None:
        self._x("DELETE FROM amz.sessions WHERE jeton_hash = %s", (jeton_hash,))
