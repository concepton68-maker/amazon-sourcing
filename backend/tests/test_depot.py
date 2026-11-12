"""Contrat commun des dépôts [RM-AMZ-011, RM-AMZ-014] : mêmes tests en mémoire et sur Postgres.

Postgres : définir AMZ_TEST_PG (chaîne de connexion d'un administrateur, ex. "host=/chemin port=55432 user=postgres").
Une base jetable est créée puis supprimée. Sans AMZ_TEST_PG, les tests Postgres sont sautés.
"""
import os
import unittest
import uuid
from datetime import date

from sourcing.depot import AccesRefuse, DepotMemoire
from sourcing.lots import Lot, Prevision, VenteReelle, corriger_prevision, rattacher_fifo
from sourcing.money import Montant

A, B = str(uuid.uuid4()), str(uuid.uuid4())
E = lambda v: Montant.de(v, "EUR")  # noqa: E731


def lot(compte, q=5, jour=date(2026, 8, 1)):
    return Lot(compte, "B0X", "FR", q, jour, Prevision.creer("EUR", 20, 7, 8, sources=["démo"]))


def vente(compte, q=1, ca=20, jour=date(2026, 10, 1)):
    return VenteReelle(compte, "B0X", "FR", jour, q, E(ca), E(7), E(0), E(0), E(0))


class ContratDepot:
    """À mélanger avec unittest.TestCase ; `self.d` est le dépôt, `self.purger(jour)` la purge."""

    def preparer(self):
        self.d.creer_compte(A, "Compte A")
        self.d.creer_compte(B, "Compte B")

    def test_isolation_lecture_ecriture(self):
        """[RM-AMZ-014] Aucun accès croisé entre comptes."""
        la, lb = lot(A), lot(B)
        self.d.ajouter_lot(A, la)
        self.d.ajouter_lot(B, lb)
        with self.assertRaises(AccesRefuse):
            self.d.ajouter_lot(A, lot(B))
        with self.assertRaises(AccesRefuse):
            self.d.lot(A, lb.id)
        self.assertEqual([l.id for l in self.d.lots(A)], [la.id])
        with self.assertRaises(AccesRefuse):
            self.d.ajouter_vente(A, vente(B))

    def test_aller_retour_lot_et_fifo(self):
        """[RM-AMZ-011, RM-AMZ-012] Un lot relu est identique ; les versions se chaînent ; FIFO sur données relues."""
        l = lot(A)
        self.d.ajouter_lot(A, l)
        l2 = corriger_prevision(l, Prevision.creer("EUR", 21, 7, 8), "erreur de prix")
        self.d.ajouter_lot(A, l2)
        relu = self.d.lot(A, l2.id)
        self.assertEqual((relu.version, relu.remplace, relu.motif), (2, l.id, "erreur de prix"))
        self.assertEqual(relu.prevision.profit, l2.prevision.profit)
        self.d.ajouter_vente(A, vente(A, 2, 42), id_externe="amz-1")
        res, _ = rattacher_fifo(self.d.lots(A), self.d.ventes(A))
        self.assertEqual(res[l2.id].quantite_vendue, 2)
        v = VenteReelle(A, "B0X", "FR", date(2026, 10, 9), 0, E(-20), E(0), E(0), E(0), E(0),
                        commande="111-1", differe=True)
        self.d.ajouter_vente(A, v, id_externe="amz-2")
        relue = [x for x in self.d.ventes(A) if x.jour == date(2026, 10, 9)][0]
        self.assertEqual((relue.commande, relue.differe), ("111-1", True))

    def test_vente_rejouable(self):
        """Rejouer la même ligne Amazon met à jour ses montants sans la doubler."""
        self.d.ajouter_vente(A, vente(A, 1, 20), id_externe="amz-7")
        self.d.ajouter_vente(A, vente(A, 1, 19), id_externe="amz-7")
        ventes = self.d.ventes(A)
        self.assertEqual(len(ventes), 1)
        self.assertEqual(ventes[0].chiffre_affaires_ht.valeur, 19)

    def test_purge_apres_revocation(self):
        """[RM-AMZ-014] Données supprimées au plus tard 30 jours après le retrait de l'autorisation."""
        self.d.ajouter_lot(A, lot(A))
        self.d.ajouter_lot(B, lot(B))
        self.assertEqual(self.d.revoquer(A, date(2026, 11, 1)), date(2026, 12, 1))
        self.assertEqual(self.purger(date(2026, 10, 31)), [])
        self.assertEqual(self.purger(date(2026, 11, 2)), [A])
        self.assertEqual(self.d.lots(A), [])
        self.assertEqual(len(self.d.lots(B)), 1)

    def test_appariements_par_compte(self):
        """[RM-AMZ-034, RM-AMZ-014] Mémoire code → ASIN propre à chaque compte, mise à jour, purgée avec le compte."""
        self.d.memoriser_appariement(A, "FR", "2000000000015", ["B0GEN00015"])
        self.assertEqual(self.d.appariement(A, "FR", "2000000000015")[0], ["B0GEN00015"])
        self.assertIsNone(self.d.appariement(B, "FR", "2000000000015"))
        self.assertIsNone(self.d.appariement(A, "DE", "2000000000015"))
        self.d.memoriser_appariement(A, "FR", "2000000000015", ["B0X1", "B0X2"])
        self.assertEqual(self.d.appariement(A, "FR", "2000000000015")[0], ["B0X1", "B0X2"])
        self.d.revoquer(A, date(2026, 11, 1))
        self.purger(date(2026, 11, 2))
        self.assertIsNone(self.d.appariement(A, "FR", "2000000000015"))

    def test_parametres_par_compte_et_versions(self):
        """[RM-AMZ-043, RM-AMZ-014] Paramètres versionnés en ajout seul, propres à chaque compte."""
        self.assertIsNone(self.d.parametres(A))
        self.assertEqual(self.d.enregistrer_parametres(A, {"roi_min": 0.4}), 1)
        self.assertEqual(self.d.enregistrer_parametres(A, {"roi_min": 0.5}), 2)
        self.assertEqual(self.d.parametres(A), {"roi_min": 0.5})
        self.assertIsNone(self.d.parametres(B))
        self.assertEqual([v[1]["roi_min"] for v in self.d.versions_parametres(A)], [0.4, 0.5])


class TestDepotMemoire(ContratDepot, unittest.TestCase):
    def setUp(self):
        self.d = DepotMemoire()
        self.purger = self.d.purger
        self.preparer()


PG = os.environ.get("AMZ_TEST_PG")


@unittest.skipUnless(PG, "AMZ_TEST_PG non défini : tests Postgres sautés")
class TestDepotPostgres(ContratDepot, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from sourcing import db
        cls.psycopg, cls.db = psycopg, db
        cls.nom = "amz_test_" + uuid.uuid4().hex[:8]
        with psycopg.connect(PG, autocommit=True) as adm:
            adm.execute(open(os.path.join(os.path.dirname(__file__), "..", "..", "deploy", "bootstrap_roles.sql")).read())
            adm.execute(f"CREATE DATABASE {cls.nom} OWNER amz_owner")
        cls.owner = psycopg.connect(PG + f" dbname={cls.nom}", autocommit=True)
        cls.owner.execute("SET ROLE amz_owner")
        cls.migrees = db.migrer(cls.owner)

    @classmethod
    def tearDownClass(cls):
        cls.owner.close()
        with cls.psycopg.connect(PG, autocommit=True) as adm:
            adm.execute(f"DROP DATABASE {cls.nom} WITH (FORCE)")

    def setUp(self):
        self.owner.execute("TRUNCATE amz.comptes CASCADE")
        self.app = self.psycopg.connect(PG + f" dbname={self.nom}", autocommit=True)
        self.app.execute("SET ROLE amz_app")
        self.d = self.db.DepotPostgres(self.app)
        self.purger = lambda jour: self.db.purger(self.owner, jour)
        self.preparer()

    def tearDown(self):
        self.app.close()

    def test_migrations_rejouables(self):
        """Rejouer les migrations n'applique rien de plus."""
        self.assertIn("0001_socle.sql", self.migrees)
        self.assertEqual(self.db.migrer(self.owner), [])

    def test_base_refuse_acces_croise_meme_sans_le_code(self):
        """[RM-AMZ-014] La base elle-même refuse une ligne d'un autre compte (contournement du code)."""
        self.d.ajouter_lot(B, lot(B))
        with self.app.transaction():
            self.app.execute("SELECT set_config('app.compte_id', %s, true)", (A,))
            self.assertEqual(self.app.execute("SELECT count(*) FROM amz.lots").fetchone()[0], 0)
        with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
            with self.app.transaction():
                self.app.execute("SELECT set_config('app.compte_id', %s, true)", (A,))
                self.app.execute("INSERT INTO amz.lots (id, compte_id, asin, marketplace, quantite, date_achat, devise,"
                                 " prix_vente_ht, frais_amazon, cout_achat) VALUES (%s,%s,'B0X','FR',1,'2026-01-01',"
                                 "'EUR',1,1,1)", (uuid.uuid4(), B))

    def test_base_refuse_modification_de_lot(self):
        """[RM-AMZ-011] Ni l'application (droit absent) ni le propriétaire (déclencheur) ne modifient un lot."""
        l = lot(A)
        self.d.ajouter_lot(A, l)
        with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
            with self.app.transaction():
                self.app.execute("SELECT set_config('app.compte_id', %s, true)", (A,))
                self.app.execute("UPDATE amz.lots SET quantite = 99")
        with self.assertRaises(self.psycopg.errors.CheckViolation):
            self.owner.execute("UPDATE amz.lots SET quantite = 99 WHERE id = %s", (uuid.UUID(l.id),))

    def test_authentification_postgres(self):
        """[RM-AMZ-036 à 038] Utilisateur et session en base, avec le rôle de l'application ; jeton jamais stocké."""
        from sourcing.auth import Authentification, StockAuthPostgres
        auth = Authentification(StockAuthPostgres(self.app))
        auth.creer_utilisateur(A, "a@exemple.fr", "un-mot-de-passe-solide")
        jeton, s = auth.connecter("A@exemple.fr", "un-mot-de-passe-solide")
        self.assertEqual(s.compte_id, A)
        self.assertEqual(auth.session_valide(jeton).compte_id, A)
        stockes = [r[0] for r in self.owner.execute("SELECT jeton_hash FROM amz.sessions").fetchall()]
        self.assertNotIn(jeton, stockes)
        auth.deconnecter(jeton)
        self.assertIsNone(auth.session_valide(jeton))

    def test_application_ne_supprime_rien(self):
        """La suppression est réservée à la purge (rôle propriétaire)."""
        self.d.ajouter_lot(A, lot(A))
        with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
            with self.app.transaction():
                self.app.execute("SELECT set_config('app.compte_id', %s, true)", (A,))
                self.app.execute("DELETE FROM amz.lots")


if __name__ == "__main__":
    unittest.main()
