"""Utilisateurs, mots de passe et sessions — [RM-AMZ-036, 037, 038, 041].

Les tables d'authentification ne sont pas cloisonnées par compte (on ne connaît le compte
qu'après la connexion) ; elles ne sont lues que par courriel ou par empreinte de jeton.
"""
from __future__ import annotations

import hashlib
import secrets
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


@dataclass(frozen=True)
class Session:
    jeton_hash: str
    utilisateur_id: str
    compte_id: str
    cree_le: datetime
    vu_le: datetime


def _norme(courriel: str) -> str:
    return courriel.strip().lower()


def empreinte_mot_de_passe(mdp: str) -> str:
    if len(mdp) < LONGUEUR_MIN:
        raise ErreurAuth("MOT_DE_PASSE_TROP_COURT")
    return _hacheur.hash(mdp)


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
    def __init__(self, stock):
        self.stock = stock

    def creer_utilisateur(self, compte_id: str, courriel: str, mdp: str) -> Utilisateur:
        """[RM-AMZ-041] Appelé par la ligne de commande seulement."""
        c = _norme(courriel)
        if "@" not in c or len(c) > 254:
            raise ErreurAuth("COURRIEL_INVALIDE")
        if self.stock.par_courriel(c):
            raise ErreurAuth("COURRIEL_DEJA_UTILISE")
        u = Utilisateur(str(uuid.uuid4()), compte_id, c, empreinte_mot_de_passe(mdp))
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
        s = Session(_hash_jeton(jeton), u.id, u.compte_id, maintenant, maintenant)
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

    def _u(self, r) -> Utilisateur:
        return Utilisateur(str(r[0]), str(r[1]), r[2], r[3], r[4], r[5])

    def par_courriel(self, courriel: str) -> Optional[Utilisateur]:
        r = self._x("SELECT id, compte_id, courriel, empreinte, echecs, bloque_jusqua FROM amz.utilisateurs "
                    "WHERE courriel = %s", (_norme(courriel),), un=True)
        return self._u(r) if r else None

    def enregistrer_utilisateur(self, u: Utilisateur) -> None:
        self._x("""INSERT INTO amz.utilisateurs (id, compte_id, courriel, empreinte, echecs, bloque_jusqua)
            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET empreinte = EXCLUDED.empreinte,
            echecs = EXCLUDED.echecs, bloque_jusqua = EXCLUDED.bloque_jusqua""",
            (uuid.UUID(u.id), uuid.UUID(u.compte_id), u.courriel, u.empreinte, u.echecs, u.bloque_jusqua))

    def creer_session(self, s: Session) -> None:
        self._x("INSERT INTO amz.sessions (jeton_hash, utilisateur_id, compte_id, cree_le, vu_le) "
                          "VALUES (%s, %s, %s, %s, %s)", (s.jeton_hash, uuid.UUID(s.utilisateur_id),
                                                          uuid.UUID(s.compte_id), s.cree_le, s.vu_le))

    def session(self, jeton_hash: str) -> Optional[Session]:
        r = self._x("SELECT jeton_hash, utilisateur_id, compte_id, cree_le, vu_le FROM amz.sessions "
                    "WHERE jeton_hash = %s", (jeton_hash,), un=True)
        return Session(r[0], str(r[1]), str(r[2]), r[3], r[4]) if r else None

    def toucher_session(self, jeton_hash: str, quand: datetime) -> None:
        self._x("UPDATE amz.sessions SET vu_le = %s WHERE jeton_hash = %s", (quand, jeton_hash))

    def supprimer_session(self, jeton_hash: str) -> None:
        self._x("DELETE FROM amz.sessions WHERE jeton_hash = %s", (jeton_hash,))
