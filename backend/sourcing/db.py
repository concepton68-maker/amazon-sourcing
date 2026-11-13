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
import json

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
        self._executer(compte_id, *self._insert_lot(lot))

    @staticmethod
    def _insert_lot(lot: Lot):
        p = lot.prevision
        return ("""
            INSERT INTO amz.lots (id, compte_id, asin, marketplace, quantite, date_achat, fournisseur, devise,
                prix_vente_ht, frais_amazon, cout_achat, retours, stockage, autres, sources, version, remplace, motif, cree_le, designation, bon_commande)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (_uuid(lot.id), _uuid(lot.compte_id), lot.asin, lot.marketplace, lot.quantite, lot.date_achat,
             lot.fournisseur, p.devise, p.prix_vente_ht, p.frais_amazon, p.cout_achat, p.retours, p.stockage,
             p.autres, list(p.sources), lot.version, _uuid(lot.remplace) if lot.remplace else None,
             lot.motif, lot.cree_le, lot.designation,
             _uuid(lot.bon_commande) if lot.bon_commande else None))


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
                 "frais_amazon, cout_achat, retours, stockage, autres, sources, version, remplace, motif, cree_le, designation, bon_commande")

    @staticmethod
    def _lot(r) -> Lot:
        (i, c, asin, mp, q, d, fo, dev, pv, fr, co, re, st, au, so, ve, rem, mo, cr, de, bc) = r
        return Lot(str(c), asin, mp, q, d, Prevision(dev, pv, fr, co, re, st, au, tuple(so)), fo, de,
                   id=str(i), version=ve, remplace=str(rem) if rem else None, motif=mo, cree_le=cr,
                   bon_commande=str(bc) if bc else None)

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

    # -------------------------------------------------------------- paramètres [RM-AMZ-042, 043]
    def parametres(self, compte_id: str) -> Optional[dict]:
        rows = self._executer(compte_id, "SELECT valeurs FROM amz.parametres ORDER BY version DESC LIMIT 1")
        return dict(rows[0][0]) if rows else None

    def versions_parametres(self, compte_id: str):
        return [(v, dict(x), q) for v, x, q in self._executer(
            compte_id, "SELECT version, valeurs, cree_le FROM amz.parametres ORDER BY version")]

    def enregistrer_parametres(self, compte_id: str, valeurs: dict) -> int:
        rows = self._executer(compte_id, """SELECT coalesce(max(version), 0) + 1 FROM amz.parametres""")
        v = rows[0][0]
        self._executer(compte_id, "INSERT INTO amz.parametres (compte_id, version, valeurs) VALUES (%s, %s, %s)",
                       (_uuid(compte_id), v, json.dumps(valeurs)))
        return v

    # -------------------------------------------------------------- stock [RM-AMZ-045]
    def enregistrer_photo_stock(self, compte_id: str, jour: date, photos) -> None:
        for p in photos:
            self._executer(compte_id, """INSERT INTO amz.stock_photos (compte_id, marketplace, sku, jour, asin, designation,
                disponible, en_route, reserve, invendable) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (compte_id, marketplace, sku, jour) DO UPDATE SET asin = EXCLUDED.asin,
                designation = EXCLUDED.designation, disponible = EXCLUDED.disponible, en_route = EXCLUDED.en_route,
                reserve = EXCLUDED.reserve, invendable = EXCLUDED.invendable""",
                (_uuid(compte_id), p.marketplace, p.sku, jour, p.asin, p.designation, p.disponible, p.en_route,
                 p.reserve, p.invendable))

    def photo_stock(self, compte_id: str):
        from .stock import PhotoStock
        rows = self._executer(compte_id, """SELECT DISTINCT ON (marketplace, sku) jour, marketplace, sku, asin,
            designation, disponible, en_route, reserve, invendable FROM amz.stock_photos
            ORDER BY marketplace, sku, jour DESC""")
        jour = max((r[0] for r in rows), default=None)
        return jour, [PhotoStock(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]) for r in rows]

    # -------------------------------------------------------------- achats [RM-AMZ-049 à 051]
    def fournisseurs(self, compte_id: str) -> list:
        from .achats import Fournisseur
        return [Fournisseur(str(i), str(c), n, d.strip(), dl, co) for i, c, n, d, dl, co in self._executer(
            compte_id, "SELECT id, compte_id, nom, devise, delai_jours, courriel FROM amz.fournisseurs ORDER BY lower(nom)")]

    def enregistrer_fournisseur(self, compte_id: str, f) -> None:
        if f.compte_id != compte_id:
            raise AccesRefuse("fournisseur d'un autre compte")
        try:
            self._executer(compte_id, """INSERT INTO amz.fournisseurs (id, compte_id, nom, devise, delai_jours, courriel)
                VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO UPDATE SET devise = EXCLUDED.devise,
                delai_jours = EXCLUDED.delai_jours, courriel = EXCLUDED.courriel""",
                (_uuid(f.id), _uuid(compte_id), f.nom, f.devise, f.delai_jours, f.courriel))
        except psycopg.errors.UniqueViolation:
            raise ValueError("FOURNISSEUR_EXISTE") from None

    _COLS_BON = "id, compte_id, numero, fournisseur_id, statut, lignes, cree_le, envoye_le, recu_le, annule_le"

    @staticmethod
    def _bon(r):
        from .achats import BonCommande
        from .achats_serial import ligne_depuis_dict
        return BonCommande(str(r[0]), str(r[1]), r[2], str(r[3]), r[4], tuple(ligne_depuis_dict(x) for x in r[5]),
                           r[6], r[7], r[8], r[9])

    def bons(self, compte_id: str) -> list:
        return [self._bon(r) for r in self._executer(
            compte_id, f"SELECT {self._COLS_BON} FROM amz.bons_commande ORDER BY numero DESC")]

    def bon(self, compte_id: str, bon_id: str):
        rows = self._executer(compte_id, f"SELECT {self._COLS_BON} FROM amz.bons_commande WHERE id = %s", (_uuid(bon_id),))
        if not rows:
            raise AccesRefuse("bon introuvable pour ce compte")
        return self._bon(rows[0])

    def prochain_numero(self, compte_id: str) -> int:
        return self._executer(compte_id, "SELECT coalesce(max(numero), 0) + 1 FROM amz.bons_commande")[0][0]

    @staticmethod
    def _upsert_bon(bon):
        from .achats_serial import ligne_vers_dict
        return ("""INSERT INTO amz.bons_commande (id, compte_id, numero, fournisseur_id, statut, lignes, cree_le,
            envoye_le, recu_le, annule_le) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO UPDATE SET statut = EXCLUDED.statut, lignes = EXCLUDED.lignes,
            envoye_le = EXCLUDED.envoye_le, recu_le = EXCLUDED.recu_le, annule_le = EXCLUDED.annule_le""",
                (_uuid(bon.id), _uuid(bon.compte_id), bon.numero, _uuid(bon.fournisseur_id), bon.statut,
                 json.dumps([ligne_vers_dict(l) for l in bon.lignes]), bon.cree_le, bon.envoye_le, bon.recu_le,
                 bon.annule_le))

    def enregistrer_bon(self, compte_id: str, bon) -> None:
        if bon.compte_id != compte_id:
            raise AccesRefuse("bon d'un autre compte")
        try:
            self._executer(compte_id, *self._upsert_bon(bon))
        except psycopg.errors.CheckViolation:
            raise ValueError("BON_DEFINITIF") from None

    def receptionner(self, compte_id: str, bon, lots) -> None:
        """Une seule transaction : le bon reçu et ses lots, ou rien."""
        if bon.compte_id != compte_id or any(l.compte_id != compte_id for l in lots):
            raise AccesRefuse("donnée d'un autre compte")
        with connexion(self.source) as conn, conn.transaction():
            conn.execute("SELECT set_config('app.compte_id', %s, true)", (str(_uuid(compte_id)),))
            conn.execute(*self._upsert_bon(bon))           # le bon d'abord : les lots y font référence
            for l in lots:
                conn.execute(*self._insert_lot(l))

    # -------------------------------------------------------------- remboursements [RM-AMZ-054 à 059]
    def enregistrer_verses(self, compte_id: str, verses) -> None:
        for v in verses:
            self._executer(compte_id, """INSERT INTO amz.remboursements_verses (compte_id, reimbursement_id, jour, case_id,
                commande, sku, fnsku, asin, devise, montant, quantite) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (compte_id, reimbursement_id) DO UPDATE SET jour = EXCLUDED.jour, case_id = EXCLUDED.case_id,
                commande = EXCLUDED.commande, sku = EXCLUDED.sku, fnsku = EXCLUDED.fnsku, asin = EXCLUDED.asin,
                devise = EXCLUDED.devise, montant = EXCLUDED.montant, quantite = EXCLUDED.quantite""",
                (_uuid(compte_id), v.reimbursement_id, v.jour, v.case_id, v.commande, v.sku, v.fnsku, v.asin, v.devise,
                 v.montant, v.quantite))

    def verses(self, compte_id: str) -> list:
        from .remboursements import RemboursementVerse
        return [RemboursementVerse(*r) for r in self._executer(compte_id, """SELECT reimbursement_id, jour, case_id,
            commande, sku, fnsku, asin, trim(devise), montant, quantite FROM amz.remboursements_verses""")]

    def enregistrer_cas(self, compte_id: str, cas) -> None:
        for x in cas:
            self._executer(compte_id, """INSERT INTO amz.remboursements_cas (compte_id, cle, type, marketplace, asin, sku,
                fnsku, commande, unites, valeur_achat, devise, detecte_le, echeance, statut, case_id, montant_verse, faits)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (compte_id, cle) DO UPDATE SET unites = EXCLUDED.unites, valeur_achat = EXCLUDED.valeur_achat,
                echeance = EXCLUDED.echeance, statut = EXCLUDED.statut, case_id = EXCLUDED.case_id,
                montant_verse = EXCLUDED.montant_verse, faits = EXCLUDED.faits""",
                (_uuid(compte_id), x.cle, x.type, x.marketplace, x.asin, x.sku, x.fnsku, x.commande, x.unites,
                 x.valeur_achat, x.devise, x.detecte_le, x.echeance, x.statut, x.case_id, x.montant_verse,
                 json.dumps(x.faits)))

    def cas_remboursement(self, compte_id: str) -> list:
        from .remboursements import Cas
        return [Cas(*r[:15], faits=dict(r[15])) for r in self._executer(compte_id, """SELECT cle, type, marketplace, asin,
            sku, fnsku, commande, unites, valeur_achat, trim(devise), detecte_le, echeance, statut, case_id, montant_verse,
            faits FROM amz.remboursements_cas""")]

    # -------------------------------------------------------------- conformité [RM-AMZ-061, 062]
    def enregistrements(self, compte_id: str) -> list:
        from .conformite import Enregistrement
        return [Enregistrement(*r) for r in self._executer(compte_id, """SELECT pays, filiere, numero, nullif(intitule, ''),
            mandataire FROM amz.conformite_enregistrements ORDER BY pays, filiere, intitule""")]

    def enregistrer_enregistrement(self, compte_id: str, e) -> None:
        self._executer(compte_id, """INSERT INTO amz.conformite_enregistrements (compte_id, pays, filiere, intitule, numero,
            mandataire) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (compte_id, pays, filiere, intitule)
            DO UPDATE SET numero = EXCLUDED.numero, mandataire = EXCLUDED.mandataire, maj = now()""",
            (_uuid(compte_id), e.pays, e.filiere, e.intitule or "", e.numero, e.mandataire))

    def supprimer_enregistrement(self, compte_id: str, cle: str) -> bool:
        pays, filiere, intitule = (cle.split(":", 2) + ["", ""])[:3]
        avant = len(self.enregistrements(compte_id))
        self._executer(compte_id, """DELETE FROM amz.conformite_enregistrements WHERE pays = %s AND filiere = %s
            AND intitule = %s""", (pays, filiere, intitule))
        return len(self.enregistrements(compte_id)) < avant

    def fiches(self, compte_id: str) -> dict:
        from .conformite import fiche_depuis_dict
        return {a: fiche_depuis_dict(a, dict(d)) for a, d in self._executer(
            compte_id, "SELECT asin, donnees FROM amz.conformite_fiches")}

    def enregistrer_fiche(self, compte_id: str, fiche) -> None:
        self._executer(compte_id, """INSERT INTO amz.conformite_fiches (compte_id, asin, donnees) VALUES (%s,%s,%s)
            ON CONFLICT (compte_id, asin) DO UPDATE SET donnees = EXCLUDED.donnees, maj = now()""",
            (_uuid(compte_id), fiche.asin, json.dumps(fiche.to_dict())))

    # -------------------------------------------------------------- connexions [RM-AMZ-072]
    def connexions(self, compte_id: str) -> dict:
        from .connexions import Connexion
        return {s: Connexion(s, bytes(c), m) for s, c, m in self._executer(
            compte_id, "SELECT source, chiffre, maj FROM amz.connexions")}

    def enregistrer_connexion(self, compte_id: str, source: str, chiffre: bytes) -> None:
        self._executer(compte_id, """INSERT INTO amz.connexions (compte_id, source, chiffre) VALUES (%s, %s, %s)
            ON CONFLICT (compte_id, source) DO UPDATE SET chiffre = EXCLUDED.chiffre, maj = now()""",
            (_uuid(compte_id), source, chiffre))

    def supprimer_connexion(self, compte_id: str, source: str) -> bool:
        avant = source in self.connexions(compte_id)
        self._executer(compte_id, "DELETE FROM amz.connexions WHERE source = %s", (source,))
        return avant

    # -------------------------------------------------------------- synchronisation de nuit [RM-AMZ-080]
    def curseur_synchro(self, compte_id: str, tache: str) -> Optional[datetime]:
        r = self._executer(compte_id, "SELECT curseur FROM amz.synchro_curseurs WHERE tache = %s", (tache,))
        return r[0][0] if r else None

    def enregistrer_curseur_synchro(self, compte_id: str, tache: str, curseur: Optional[datetime]) -> None:
        if curseur:
            self._executer(compte_id, """INSERT INTO amz.synchro_curseurs (compte_id, tache, curseur) VALUES (%s,%s,%s)
                ON CONFLICT (compte_id, tache) DO UPDATE SET curseur = EXCLUDED.curseur""", (_uuid(compte_id), tache, curseur))

    def journaliser_synchro(self, compte_id: str, r) -> None:
        self._executer(compte_id, """INSERT INTO amz.synchro_journal (compte_id, tache, debut, fin, ok, message)
            VALUES (%s,%s,%s,%s,%s,%s)""", (_uuid(compte_id), r.tache, r.debut, r.fin, r.ok, r.message))

    def journal_synchro(self, compte_id: str) -> list:
        from .synchro_nuit import ResultatTache
        return [ResultatTache(*x) for x in self._executer(
            compte_id, "SELECT tache, debut, fin, ok, message FROM amz.synchro_journal ORDER BY debut")]

    def etat_synchros(self) -> dict:
        """[RM-AMZ-081] Vue sans donnée de compte (fonction SECURITY DEFINER)."""
        with connexion(self.source) as conn:
            return {t: (f, ok) for t, f, ok in conn.execute("SELECT tache, fin, ok FROM amz.etat_synchros()").fetchall()}

    # -------------------------------------------------------------- retrait d'autorisation
    def revoquer(self, compte_id: str, jour: date) -> date:
        self._executer(compte_id, "UPDATE amz.comptes SET revoque_le = coalesce(revoque_le, %s)", (jour,))
        return self.echeance_suppression(compte_id)

    def echeance_suppression(self, compte_id: str) -> Optional[date]:
        rows = self._executer(compte_id, "SELECT revoque_le FROM amz.comptes")
        return rows[0][0] + DELAI_SUPPRESSION if rows and rows[0][0] else None


def comptes_connectes(conn_owner: psycopg.Connection) -> list[tuple[str, bytes]]:
    """[RM-AMZ-080] Comptes actifs ayant une connexion SP-API (rôle propriétaire) : (compte_id, chiffré)."""
    return [(str(c), bytes(ch)) for c, ch in conn_owner.execute(
        "SELECT x.compte_id, x.chiffre FROM amz.connexions x JOIN amz.comptes c ON c.id = x.compte_id "
        "WHERE x.source = 'SPAPI' AND c.revoque_le IS NULL ORDER BY x.compte_id").fetchall()]


def purger(conn_owner: psycopg.Connection, aujourd_hui: date) -> list[str]:
    """[RM-AMZ-014] Supprime (en cascade) tous les comptes révoqués au plus tard aujourd'hui."""
    with conn_owner.transaction():
        rows = conn_owner.execute("DELETE FROM amz.comptes WHERE revoque_le IS NOT NULL AND revoque_le <= %s "
                                  "RETURNING id", (aujourd_hui,)).fetchall()
    return sorted(str(r[0]) for r in rows)
