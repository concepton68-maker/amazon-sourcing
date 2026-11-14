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

    def test_photo_stock_par_compte(self):
        """[RM-AMZ-045, RM-AMZ-014] Photo du jour remplacée ; dernière photo par SKU ; propre au compte."""
        from sourcing.stock import PhotoStock
        self.d.enregistrer_photo_stock(A, date(2026, 11, 11), [PhotoStock("FR", "S1", "B0X", "X", 5, 1)])
        self.d.enregistrer_photo_stock(A, date(2026, 11, 12), [PhotoStock("FR", "S1", "B0X", "X", 4, 0)])
        self.d.enregistrer_photo_stock(A, date(2026, 11, 12), [PhotoStock("FR", "S1", "B0X", "X", 3, 0)])
        jour, photos = self.d.photo_stock(A)
        self.assertEqual((jour, len(photos), photos[0].disponible), (date(2026, 11, 12), 1, 3))
        self.assertEqual(self.d.photo_stock(B), (None, []))

    def test_achats_par_compte(self):
        """[RM-AMZ-049 à 051, RM-AMZ-014] Fournisseur unique sans casse ; bon relu ; réception = bon + lots ; bon reçu définitif."""
        from sourcing import achats as AC
        f = AC.nouveau_fournisseur(A, "Grossiste A")
        self.d.enregistrer_fournisseur(A, f)
        with self.assertRaises(ValueError):
            self.d.enregistrer_fournisseur(A, AC.nouveau_fournisseur(A, "GROSSISTE A"))
        self.d.enregistrer_fournisseur(B, AC.nouveau_fournisseur(B, "Grossiste A"))     # autre compte : permis
        self.assertEqual([x.nom for x in self.d.fournisseurs(A)], ["Grossiste A"])
        self.assertEqual(self.d.prochain_numero(A), 1)
        b = AC.nouveau_bon(A, 1, f)
        b = AC.ajouter_ligne(b, "B0X", "FR", 5, "8", Prevision.creer("EUR", 20, 7, 8), "X")
        self.d.enregistrer_bon(A, b)
        relu = self.d.bon(A, b.id)
        self.assertEqual((relu.reference, relu.lignes[0].quantite, relu.lignes[0].prevision.profit), ("BC-0001", 5, b.lignes[0].prevision.profit))
        with self.assertRaises(AccesRefuse):
            self.d.bon(B, b.id)
        b = AC.envoyer(b)
        self.d.enregistrer_bon(A, b)
        recu, lots = AC.recevoir(b, {b.lignes[0].id: 5}, date(2026, 11, 12), f)
        self.d.receptionner(A, recu, lots)
        self.assertEqual(self.d.bon(A, b.id).statut, "RECU")
        self.assertEqual(self.d.lot(A, lots[0].id).bon_commande, b.id)
        with self.assertRaises(ValueError):
            self.d.enregistrer_bon(A, AC.annuler(b))
        self.assertEqual(self.d.prochain_numero(A), 2)

    def test_remboursements_par_compte(self):
        """[RM-AMZ-059, RM-AMZ-014] Versements et cas relus à l'identique, propres au compte, suivi mis à jour."""
        from decimal import Decimal
        from sourcing import remboursements as RB
        v = RB.RemboursementVerse("R1", date(2026, 10, 1), "C-1", None, "S", "X1", "B0X", "EUR", Decimal("9.8"), 1)
        self.d.enregistrer_verses(A, [v, v])
        self.assertEqual(len(self.d.verses(A)), 1)
        self.assertEqual(self.d.verses(B), [])
        cas = RB.Cas("PERTE_ENTREPOT:DE:X1", RB.PERTE, "DE", "B0X", "S", "X1", None, 2, Decimal("19.6"), "EUR",
                     date(2026, 11, 12), date(2026, 11, 30), faits={"perdus_abimes": 4})
        self.d.enregistrer_cas(A, [cas])
        self.d.enregistrer_cas(A, [RB.changer_suivi(cas, RB.DOSSIER_ENVOYE, "C-9")])
        (relu,) = self.d.cas_remboursement(A)
        self.assertEqual((relu.statut, relu.case_id, relu.unites, relu.faits), ("DOSSIER_ENVOYE", "C-9", 2, {"perdus_abimes": 4}))
        self.assertEqual(self.d.cas_remboursement(B), [])

    def test_conformite_par_compte(self):
        """[RM-AMZ-061, 062, RM-AMZ-014] Enregistrements et fiches relus à l'identique, propres au compte, suppression."""
        from sourcing import conformite as CF
        e = CF.nouvel_enregistrement("FR", "AUTRE", "IDU-9", intitule="Jouets", mandataire="M")
        self.d.enregistrer_enregistrement(A, e)
        self.d.enregistrer_enregistrement(A, CF.nouvel_enregistrement("FR", "AUTRE", "IDU-10", intitule="Jouets"))
        (relu,) = self.d.enregistrements(A)
        self.assertEqual((relu.numero, relu.intitule, relu.mandataire, relu.cle), ("IDU-10", "Jouets", None, e.cle))
        self.assertEqual(self.d.enregistrements(B), [])
        self.d.enregistrer_enregistrement(A, CF.nouvel_enregistrement("DE", "EEE", "DE1"))
        self.assertFalse(self.d.supprimer_enregistrement(B, "DE:EEE:"))
        self.assertTrue(self.d.supprimer_enregistrement(A, "DE:EEE:"))
        self.assertEqual([x.cle for x in self.d.enregistrements(A)], ["FR:AUTRE:Jouets"])
        f = CF.valider_fiche("B0X", {"fabricant": {"nom": "F", "adresse": "Paris", "courriel": "f@x.fr"},
                                     "producteur": "NON", "filieres": ["PILES", "EEE"],
                                     "numeros_producteur": {"FR:EEE": "IDU-F"}})
        self.d.enregistrer_fiche(A, f)
        self.d.enregistrer_fiche(A, CF.fiche_depuis_dict("B0X", f.to_dict()))
        self.assertEqual(self.d.fiches(A), {"B0X": f})
        self.assertEqual(self.d.fiches(B), {})

    def test_connexions_par_compte(self):
        """[RM-AMZ-072, RM-AMZ-014] Chiffré relu à l'identique, propre au compte, remplacé puis retiré."""
        self.d.enregistrer_connexion(A, "KEEPA", b"x" * 40)
        self.d.enregistrer_connexion(A, "KEEPA", b"y" * 40)
        self.assertEqual(self.d.connexions(A)["KEEPA"].chiffre, b"y" * 40)
        self.assertEqual(self.d.connexions(B), {})
        self.assertFalse(self.d.supprimer_connexion(B, "KEEPA"))
        self.assertTrue(self.d.supprimer_connexion(A, "KEEPA"))
        self.assertEqual(self.d.connexions(A), {})

    def test_exploration_par_compte(self):
        """[RM-AMZ-085] Dernier sondage relu, remplacé, propre au compte."""
        self.assertIsNone(self.d.exploration(A))
        self.d.enregistrer_exploration(A, {"le": "2026-11-14", "rayons": [{"code": "CUISINE"}]})
        self.d.enregistrer_exploration(A, {"le": "2026-11-15", "rayons": []})
        self.assertEqual(self.d.exploration(A)["le"], "2026-11-15")
        self.assertIsNone(self.d.exploration(B))

    def test_catalogue_et_fiche_fournisseur(self):
        """[RM-AMZ-100, 102] Fiche complète relue ; catalogue remplacé ; invisible d'un autre compte."""
        from decimal import Decimal
        from sourcing import achats as Ach
        from sourcing.fichier import LigneFournisseur
        f = Ach.modifier_fiche(Ach.nouveau_fournisseur(A, "Grossiste P"), pays="FR", site="https://x.fr",
                               categories=["MAISON"], port_unitaire=0.4, revente="AUTORISEE", connexion="FICHIER",
                               colonnes={"code": "EAN", "prix": "Prix"})
        self.d.enregistrer_fournisseur(A, f)
        g = [x for x in self.d.fournisseurs(A) if x.id == f.id][0]
        self.assertEqual((g.pays, g.categories, g.port_unitaire, g.revente, g.colonnes),
                         ("FR", ("MAISON",), Decimal("0.4"), "AUTORISEE", {"code": "EAN", "prix": "Prix"}))
        l1 = [LigneFournisseur(2, "3700000000017", Decimal("8.5"), "Gourde", 6, None),
              LigneFournisseur(3, "3700000000024", Decimal("15"), None, None, 2)]
        self.d.enregistrer_catalogue(A, f.id, {"nom_fichier": "a.csv", "lignes": 2, "rejets": 1}, l1)
        self.d.enregistrer_catalogue(A, f.id, {"nom_fichier": "b.csv", "lignes": 1, "rejets": 0}, l1[1:])
        meta, lignes = self.d.catalogue(A, f.id)
        self.assertEqual((meta["nom_fichier"], meta["lignes"], [l.code for l in lignes], lignes[0].minimum),
                         ("b.csv", 1, ["3700000000024"], 2))
        self.assertIsNone(self.d.catalogue(B, f.id))
        with self.assertRaises(AccesRefuse):
            self.d.enregistrer_catalogue(B, f.id, {"nom_fichier": "x", "lignes": 0, "rejets": 0}, [])

    def test_opportunites_depot(self):
        """[RM-AMZ-105] Remplacement par origine et place ; propre au compte."""
        from datetime import datetime, timezone
        from sourcing.opportunites import Opportunite
        t = datetime(2026, 11, 14, tzinfo=timezone.utc)
        o = lambda asin, profit, ori="FOURNISSEUR:f": Opportunite(ori, ori, "FR", "370", asin, "T", None, 8.5, 1,  # noqa: E731
                                                                  8.5, 24.9, profit, 0.5, 0.2, 9.8, "ACHETER",
                                                                  "VENDABLE", None, 4200, 5, False, t)
        self.d.enregistrer_opportunites(A, "FOURNISSEUR:f", "F", "FR", [o("B01", 4.28), o("B02", 1.5)])
        self.d.enregistrer_opportunites(A, "FOURNISSEUR:f", "F", "FR", [o("B03", 2.0)])
        self.d.enregistrer_opportunites(A, "FICHIER:x.csv", "x.csv", "FR", [o("B01", 3.0, "FICHIER:x.csv")])
        r = sorted((x.origine, x.asin, x.profit) for x in self.d.opportunites(A))
        self.assertEqual(r, [("FICHIER:x.csv", "B01", 3.0), ("FOURNISSEUR:f", "B03", 2.0)])
        self.assertEqual(self.d.opportunites(B), [])

    # ------------------------------------------------------------ historique [RM-AMZ-086 à 090]
    def test_releve_remplace_meme_jour(self):
        """[RM-AMZ-087] Une ligne par produit, place et jour : le second relevé du jour remplace le premier."""
        from decimal import Decimal
        from sourcing.historique import Releve
        j = date(2026, 11, 14)
        self.d.enregistrer_releves(A, [Releve("FR", "B0AAAAAAAA", j, Decimal("10.0000"), 2, 1, False, False, None, 900, "Cuisine")])
        self.d.enregistrer_releves(A, [Releve("FR", "B0AAAAAAAA", j, Decimal("11.5000"), 3, 0, True, None, None, 800, None)])
        r = self.d.releves(A, "FR")
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0].prix_buybox, r[0].nb_fba, r[0].amazon_vend, r[0].buybox_amazon, r[0].bsr),
                         (Decimal("11.5"), 3, True, None, 800))

    def test_historique_par_compte(self):
        """[RM-AMZ-088] Relevés, suivis, familles et fiches d'un compte invisibles des autres ; effacés avec le compte."""
        from datetime import datetime, timedelta, timezone
        from sourcing.historique import ProduitMarche, Releve
        j = date(2026, 11, 14)
        self.d.enregistrer_releves(A, [Releve("FR", "B0AAAAAAAA", j, bsr=5)])
        self.d.enregistrer_produits_marche(A, [ProduitMarche("FR", "B0AAAAAAAA", "Titre", None, "CUISINE")])
        self.d.enregistrer_produits_marche(A, [ProduitMarche("FR", "B0AAAAAAAA", None, "Marque", None)])
        self.d.ajouter_suivi(A, "FR", "B0AAAAAAAA")
        self.d.ajouter_suivi(A, "FR", "B0AAAAAAAA")                 # sans doublon
        self.d.enregistrer_familles(A, ["CUISINE", "JARDIN", "CUISINE"])
        self.d.memoriser_appariement(A, "FR", "3700000000017", ["B0CCCCCCCC"])
        self.assertEqual(self.d.asins_analyses(A, "FR", datetime.now(timezone.utc) - timedelta(days=1)), ["B0CCCCCCCC"])
        self.assertEqual(self.d.asins_analyses(A, "FR", datetime.now(timezone.utc) + timedelta(days=1)), [])
        p = self.d.produits_marche(A, "FR", famille="CUISINE")
        self.assertEqual([(x.titre, x.marque, x.famille) for x in p], [("Titre", "Marque", "CUISINE")])  # complété, pas écrasé
        self.assertEqual(self.d.suivis(A, "FR"), ["B0AAAAAAAA"])
        self.assertEqual(sorted(self.d.familles_suivies(A)), ["CUISINE", "JARDIN"])
        for lire in (lambda: self.d.releves(B, "FR"), lambda: self.d.suivis(B), lambda: self.d.familles_suivies(B),
                     lambda: self.d.produits_marche(B, "FR")):
            self.assertEqual(lire(), [])
        self.assertTrue(self.d.retirer_suivi(A, "FR", "B0AAAAAAAA"))
        self.assertFalse(self.d.retirer_suivi(A, "FR", "B0AAAAAAAA"))
        self.d.revoquer(A, date(2026, 11, 1))
        self.purger(date(2026, 12, 15))
        self.assertEqual(self.d.releves(A, "FR"), [])
        self.assertEqual(self.d.produits_marche(A, "FR"), [])

    def test_purge_historique_3_ans(self):
        """[RM-AMZ-088] Les relevés de plus de 3 ans sont effacés, les autres gardés."""
        from sourcing.historique import Releve, limite_conservation
        j = date(2026, 11, 14)
        self.assertEqual(limite_conservation(j), date(2023, 11, 14))
        self.assertEqual(limite_conservation(date(2028, 2, 29)), date(2025, 2, 28))
        self.d.enregistrer_releves(A, [Releve("FR", "B0AAAAAAAA", date(2023, 11, 13)),
                                       Releve("FR", "B0AAAAAAAA", date(2023, 11, 14)),
                                       Releve("FR", "B0AAAAAAAA", j)])
        self.d.enregistrer_releves(B, [Releve("FR", "B0AAAAAAAA", date(2020, 1, 1))])
        self.assertEqual(self.d.purger_releves(A, limite_conservation(j)), 1)
        self.assertEqual([r.jour for r in self.d.releves(A, "FR")], [date(2023, 11, 14), j])
        self.assertEqual(len(self.d.releves(B, "FR")), 1)                    # l'autre compte n'est pas touché


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
        from sourcing.auth import pas_de, totp
        from datetime import datetime, timezone
        auth = Authentification(StockAuthPostgres(self.app), cle=lambda: bytes(32))
        auth.creer_utilisateur(A, "a@exemple.fr", "un-mot-de-passe-solide")
        jeton, s = auth.connecter("A@exemple.fr", "un-mot-de-passe-solide")
        self.assertEqual((s.compte_id, s.niveau), (A, "ENROLER"))
        secret, _ = auth.debuter_enrolement(s)                              # [RM-AMZ-076] colonnes et droits en base
        codes = auth.confirmer_enrolement(s, totp(secret, pas_de(datetime.now(timezone.utc))))
        self.assertEqual(auth.session_valide(jeton).niveau, "COMPLET")
        _, s2 = auth.connecter("a@exemple.fr", "un-mot-de-passe-solide")
        auth.verifier_code(s2, codes[3])
        self.assertEqual(len(auth.stock.par_courriel("a@exemple.fr").codes_secours), 9)
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
