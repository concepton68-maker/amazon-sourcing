"""Base Postgres : migrations et dépôt cloisonné par compte.

- `migrer(conn)` applique, dans l'ordre, les fichiers `migrations/NNNN_*.sql` non encore appliqués
  (connexion du rôle propriétaire `amz_owner`).
- `DepotPostgres(conn)` offre la même interface que `DepotMemoire` (connexion du rôle `amz_app`).
  Chaque opération ouvre une transaction et y fixe `app.compte_id` : la sécurité au niveau des
  lignes de Postgres refuse alors toute ligne d'un autre compte [RM-AMZ-014].
- `purger(conn_owner, jour)` supprime les comptes révoqués (rôle propriétaire, contourne le cloisonnement).
"""
from __future__ import annotations

import hashlib
import pathlib
import uuid
from datetime import date, datetime, timezone
from typing import Optional

import contextlib

import psycopg

from .depot import DELAI_SUPPRESSION, AccesRefuse
from .lots import Lot, Prevision, VenteReelle
from .money import Montant

MIGRATIONS = pathlib.Path(__file__).resolve().parents[1] / "migrations"


# ------------------------------------------------------------------ migrations
def migrer(conn: psycopg.Connection) -> list[str]:
    """Applique les migrations manquantes ; refuse une migration déjà appliquée puis modifiée."""
    with conn.transaction():
        conn.execute("""CREATE TABLE IF NOT EXISTS public.amz_migrations (
                            nom text PRIMARY KEY, empreinte text NOT NULL,
                            applique_le timestamptz NOT NULL DEFAULT now())""")
    faites = dict(conn.execute("SELECT nom, empreinte FROM public.amz_migrations").fetchall())
    appliquees = []
    for f in sorted(MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        sql = f.read_text(encoding="utf-8")
        emp = hashlib.sha256(sql.encode()).hexdigest()
        if f.name in faites:
            if faites[f.name] != emp:
                raise RuntimeError(f"migration {f.name} modifiée après application : créer une nouvelle migration")
            continue
        with conn.transaction():
            conn.execute(sql)
            conn.execute("INSERT INTO public.amz_migrations (nom, empreinte) VALUES (%s, %s)", (f.name, emp))
        appliquees.append(f.name)
    return appliquees


# ------------------------------------------------------------------ connexions
class Reserve:
    """Réserve de connexions (plusieurs requêtes en parallèle) ; chaque connexion en autocommit."""

    def __init__(self, url: str, taille_max: int = 10):
        from psycopg_pool import ConnectionPool
        self.pool = ConnectionPool(url, min_size=1, max_size=taille_max, kwargs={"autocommit": True}, open=True)

    def connexion(self):
        return self.pool.connection()


def connexion(source):
    """Une connexion psycopg (tests, scripts) ou une `Reserve` (application)."""
    if isinstance(source, Reserve):
        return source.connexion()
    return contextlib.nullcontext(source)


# ------------------------------------------------------------------ dépôt cloisonné
def _uuid(x: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(x))
    except ValueError:
        raise AccesRefuse("identifiant de compte invalide") from None


class DepotPostgres:
    def __init__(self, source) -> None:
        self.source = source            # connexion psycopg ou Reserve

    def _executer(self, compte_id: str, sql: str, params=()):
        with connexion(self.source) as conn, conn.transaction():
            conn.execute("SELECT set_config('app.compte_id', %s, true)", (str(_uuid(compte_id)),))
            try:
                cur = conn.execute(sql, params)
                return cur.fetchall() if sql.lstrip().upper().startswith("SELECT") else None
            except psycopg.errors.InsufficientPrivilege as e:  # politique de cloisonnement violée
                raise AccesRefuse("donnée d'un autre compte") from e

    # -------------------------------------------------------------- comptes
    def creer_compte(self, compte_id: str, nom: str) -> None:
        self._executer(compte_id, "INSERT INTO amz.comptes (id, nom) VALUES (%s, %s)", (str(_uuid(compte_id)), nom))

    # -------------------------------------------------------------- écriture
    def ajouter_lot(self, compte_id: str, lot: Lot) -> None:
        if lot.compte_id != compte_id:
            raise AccesRefuse("lot d'un autre compte")
        p = lot.prevision
        self._executer(compte_id, """
            INSERT INTO amz.lots (id, compte_id, asin, marketplace, quantite, date_achat, fournisseur, devise,
                prix_vente_ht, frais_amazon, cout_achat, retours, stockage, autres, sources, version, remplace, motif, cree_le, designation)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (_uuid(lot.id), _uuid(lot.compte_id), lot.asin, lot.marketplace, lot.quantite, lot.date_achat,
             lot.fournisseur, p.devise, p.prix_vente_ht, p.frais_amazon, p.cout_achat, p.retours, p.stockage,
             p.autres, list(p.sources), lot.version, _uuid(lot.remplace) if lot.remplace else None,
             lot.motif, lot.cree_le, lot.designation))

    def ajouter_vente(self, compte_id: str, vente: VenteReelle, id_externe: Optional[str] = None) -> None:
        """Rejouable : une même ligne Amazon (`id_externe`) met à jour ses montants au lieu de doubler."""
        if vente.compte_id != compte_id:
            raise AccesRefuse("vente d'un autre compte")
        ide = id_externe or uuid.uuid4().hex
        self._executer(compte_id, """
            INSERT INTO amz.ventes (id, compte_id, id_externe, asin, marketplace, jour, quantite, devise,
                chiffre_affaires_ht, frais_amazon, retours, stockage, autres, commande, differe)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (compte_id, id_externe) DO UPDATE SET
                chiffre_affaires_ht = EXCLUDED.chiffre_affaires_ht, frais_amazon = EXCLUDED.frais_amazon,
                retours = EXCLUDED.retours, stockage = EXCLUDED.stockage, autres = EXCLUDED.autres,
                differe = EXCLUDED.differe""",
            (uuid.uuid4(), _uuid(compte_id), ide, vente.asin, vente.marketplace, vente.jour, vente.quantite,
             vente.chiffre_affaires_ht.devise, vente.chiffre_affaires_ht.valeur, vente.frais_amazon.valeur,
             vente.retours.valeur, vente.stockage.valeur, vente.autres.valeur, vente.commande, vente.differe))

    # -------------------------------------------------------------- lecture
    _COLS_LOT = ("id, compte_id, asin, marketplace, quantite, date_achat, fournisseur, devise, prix_vente_ht, "
                 "frais_amazon, cout_achat, retours, stockage, autres, sources, version, remplace, motif, cree_le, designation")

    @staticmethod
    def _lot(r) -> Lot:
        (i, c, asin, mp, q, d, fo, dev, pv, fr, co, re, st, au, so, ve, rem, mo, cr, de) = r
        return Lot(str(c), asin, mp, q, d, Prevision(dev, pv, fr, co, re, st, au, tuple(so)), fo, de,
                   id=str(i), version=ve, remplace=str(rem) if rem else None, motif=mo, cree_le=cr)

    def lot(self, compte_id: str, lot_id: str) -> Lot:
        rows = self._executer(compte_id, f"SELECT {self._COLS_LOT} FROM amz.lots WHERE id = %s", (_uuid(lot_id),))
        if not rows:
            raise AccesRefuse("lot introuvable pour ce compte")
        return self._lot(rows[0])

    def lots(self, compte_id: str) -> list[Lot]:
        return [self._lot(r) for r in self._executer(
            compte_id, f"SELECT {self._COLS_LOT} FROM amz.lots ORDER BY date_achat, cree_le")]

    def ventes(self, compte_id: str) -> list[VenteReelle]:
        rows = self._executer(compte_id, """SELECT compte_id, asin, marketplace, jour, quantite, devise,
            chiffre_affaires_ht, frais_amazon, retours, stockage, autres, commande, differe
            FROM amz.ventes ORDER BY jour""")
        return [VenteReelle(str(c), a, m, j, q, Montant(ca, d), Montant(f, d), Montant(r, d), Montant(s, d),
                            Montant(o, d), cmd, dif) for (c, a, m, j, q, d, ca, f, r, s, o, cmd, dif) in rows]

    # -------------------------------------------------------------- appariements [RM-AMZ-034]
    def appariement(self, compte_id: str, marketplace: str, code: str):
        rows = self._executer(compte_id, "SELECT asins, vu_le FROM amz.appariements WHERE marketplace = %s AND code = %s",
                              (marketplace, code))
        return (list(rows[0][0]), rows[0][1]) if rows else None

    def memoriser_appariement(self, compte_id: str, marketplace: str, code: str, asins: list[str],
                              quand: Optional[datetime] = None) -> None:
        self._executer(compte_id, """INSERT INTO amz.appariements (compte_id, marketplace, code, asins, vu_le)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (compte_id, marketplace, code)
            DO UPDATE SET asins = EXCLUDED.asins, vu_le = EXCLUDED.vu_le""",
            (_uuid(compte_id), marketplace, code, list(asins), quand or datetime.now(timezone.utc)))

    # -------------------------------------------------------------- retrait d'autorisation
    def revoquer(self, compte_id: str, jour: date) -> date:
        self._executer(compte_id, "UPDATE amz.comptes SET revoque_le = coalesce(revoque_le, %s)", (jour,))
        return self.echeance_suppression(compte_id)

    def echeance_suppression(self, compte_id: str) -> Optional[date]:
        rows = self._executer(compte_id, "SELECT revoque_le FROM amz.comptes")
        return rows[0][0] + DELAI_SUPPRESSION if rows and rows[0][0] else None


def purger(conn_owner: psycopg.Connection, aujourd_hui: date) -> list[str]:
    """[RM-AMZ-014] Supprime (en cascade) tous les comptes révoqués au plus tard aujourd'hui."""
    with conn_owner.transaction():
        rows = conn_owner.execute("DELETE FROM amz.comptes WHERE revoque_le IS NOT NULL AND revoque_le <= %s "
                                  "RETURNING id", (aujourd_hui,)).fetchall()
    return sorted(str(r[0]) for r in rows)
