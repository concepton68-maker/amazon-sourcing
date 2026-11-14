"""Synchronisation de nuit et page de contrôle [RM-AMZ-080, 081]."""
import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

from fastapi.testclient import TestClient

from sourcing import synchro_nuit as SN
from sourcing.api import creer_app
from sourcing.demo_donnees import _tx, construire
from sourcing.depot import DepotMemoire
from sourcing.marketplaces import get_marketplace

C = "00000000-0000-4000-8000-0000000000c1"
NUIT = datetime(2026, 11, 14, 3, 15, tzinfo=timezone.utc)
PG = os.environ.get("AMZ_TEST_PG")


class Faux:
    """Client SP-API simulé : vendeur présent en FR et DE (et US, hors région)."""
    def __init__(self, panne=None):
        self.panne, self.appels = panne, []

    def participations(self, mp):
        return [get_marketplace(x).marketplace_id for x in ("FR", "DE", "US")]

    def page_transactions(self, mp, debut, fin, jeton):
        self.appels.append(("ventes", debut))
        if self.panne == "VENTES":
            raise RuntimeError("403 refusé")
        return {"payload": {"transactions": [_tx("T1", "2026-11-10", "B0X", "C-1", {"Principal": 20.0, "Commission": -3.0})]}}

    def page_inventaire(self, mp, jeton):
        if self.panne == "STOCK":
            raise RuntimeError("403 refusé")
        return {"payload": {"inventorySummaries": [{"sellerSku": "S1", "asin": "B0X", "productName": "X",
                "inventoryDetails": {"fulfillableQuantity": 4}}]}}

    def rapport(self, mp, type_rapport, debut=None, fin=None, options=None):
        return ""

    def envois_fermes(self, mp, debut, fin):
        return []


class TestSynchro(unittest.TestCase):
    def test_synchro_nuit_compte(self):
        """Places = participations ∩ région ; trois tâches journalisées ; curseur posé ; pas d'attente réelle."""
        d = DepotMemoire()
        d.creer_compte(C, "A")
        self.assertEqual([m.code for m in SN.places_du_vendeur(Faux(), "EU")], ["DE", "FR"])
        res = SN.executer([(C, {"region": "EU"})], d, NUIT, fabrique=lambda v: Faux(), attendre=lambda s: None)[C]
        self.assertEqual([(r.tache, r.ok) for r in res], [("VENTES", True), ("STOCK", True), ("REMBOURSEMENTS", True)])
        self.assertEqual(len(d.ventes(C)), 1)
        self.assertIsNotNone(d.curseur_synchro(C, "VENTES"))
        self.assertEqual(len(d.journal_synchro(C)), 3)
        self.assertEqual(set(d.etat_synchros()), {"VENTES", "STOCK", "REMBOURSEMENTS"})

    def test_synchro_echec_isole(self):
        """Une tâche en échec n'arrête pas les autres ; le curseur des ventes n'avance pas en cas d'échec."""
        d = DepotMemoire()
        d.creer_compte(C, "A")
        res = SN.executer_compte(C, Faux(panne="VENTES"), "EU", d, NUIT, attendre=lambda s: None)
        self.assertEqual([(r.tache, r.ok) for r in res], [("VENTES", False), ("STOCK", True), ("REMBOURSEMENTS", True)])
        self.assertIn("403", res[0].message)
        self.assertIsNone(d.curseur_synchro(C, "VENTES"))
        res = SN.executer_compte(C, Faux(panne="STOCK"), "EU", d, NUIT, attendre=lambda s: None)
        self.assertEqual([r.ok for r in res], [True, False, True])

    def test_page_controle(self):
        """Public, sans connexion ; dates et statuts seulement, aucune donnée de compte."""
        d, c = construire()
        with tempfile.TemporaryDirectory() as dossier:
            open(os.path.join(dossier, "version.txt"), "w").write("abc123\n")
            open(os.path.join(dossier, "sauvegarde.txt"), "w").write("2026-11-14T02:15:03Z OK\n")
            SN.executer([(c, {"region": "EU"})], d, NUIT, fabrique=lambda v: Faux(), attendre=lambda s: None)
            with mock.patch.dict(os.environ, {"AMZ_ETAT_DIR": dossier}):
                j = TestClient(creer_app(d, c, servir_interface=False)).get("/version.json").json()
        self.assertEqual(j["version"], "abc123")
        self.assertEqual(j["sauvegarde"], {"le": "2026-11-14T02:15:03Z", "statut": "OK"})
        self.assertIsNone(j["purge"])
        self.assertEqual(j["synchronisation"]["VENTES"]["statut"], "OK")
        self.assertNotIn(c, str(j))
        self.assertNotIn("ventes", str(j).lower().replace("ventes\"", "").replace("'ventes'", ""))

    def test_journal_dans_parametres(self):
        """[RM-AMZ-080] Le compte voit ses dernières tâches, les plus récentes d'abord."""
        d, c = construire()
        SN.executer_compte(c, Faux(panne="STOCK"), "EU", d, NUIT, attendre=lambda s: None)
        for r in SN.executer_compte(c, Faux(panne="STOCK"), "EU", d, NUIT, attendre=lambda s: None):
            d.journaliser_synchro(c, r)
        j = TestClient(creer_app(d, c, servir_interface=False)).get("/api/synchro/journal").json()
        self.assertEqual([(x["tache"], x["ok"]) for x in j][:3], [("REMBOURSEMENTS", True), ("STOCK", False), ("VENTES", True)])
        self.assertIn("403", j[1]["message"])

    def test_rapport_annule_vide(self):
        """Rapport CANCELLED (aucune donnée selon le modèle d'Amazon) : vide, pas une erreur ; FATAL : erreur."""
        from sourcing.providers.base import ErreurFournisseur
        from sourcing.providers.spapi import ClientSPAPI
        for statut, attendu in (("CANCELLED", ""), ("FATAL", None)):
            c = ClientSPAPI(client_id="i", client_secret="s", refresh_tokens={"EU": "r"})
            reponses = iter([{"reportId": "R1"}, {"processingStatus": statut}])
            c._appel = lambda *a, **k: next(reponses)
            if attendu is None:
                with self.assertRaises(ErreurFournisseur):
                    c.rapport(get_marketplace("FR"), "GET_FBA_REIMBURSEMENTS_DATA", attendre=lambda s: None)
            else:
                self.assertEqual(c.rapport(get_marketplace("FR"), "GET_FBA_REIMBURSEMENTS_DATA", attendre=lambda s: None), "")

    @unittest.skipUnless(PG, "AMZ_TEST_PG absent")
    def test_synchro_journal_postgres(self):
        """Curseur et journal en base (rôle de l'application) ; comptes connectés (propriétaire) ; état sans compte."""
        import psycopg

        from sourcing.db import DepotPostgres, comptes_connectes, migrer
        nom = "amz_test_synchro"
        with psycopg.connect(PG + " dbname=postgres", autocommit=True) as adm:
            adm.execute(f"DROP DATABASE IF EXISTS {nom} WITH (FORCE)")
            adm.execute(f"CREATE DATABASE {nom}")
            adm.execute(open(os.path.join(os.path.dirname(__file__), "..", "..", "deploy", "bootstrap_roles.sql")).read())
            adm.execute("ALTER ROLE amz_app PASSWORD 'test-app'")
        try:
            with psycopg.connect(PG + f" dbname={nom}", autocommit=True) as owner:
                migrer(owner)
                owner.execute("INSERT INTO amz.comptes (id, nom) VALUES (%s, 'A')", (C,))
                owner.execute("INSERT INTO amz.connexions (compte_id, source, chiffre) VALUES (%s, 'SPAPI', %s)", (C, b"x"))
                self.assertEqual(comptes_connectes(owner), [(C, b"x")])
                SN.executer([(C, {"region": "EU"})], DepotPostgres(owner), NUIT, fabrique=lambda v: Faux(),
                            attendre=lambda s: None)
            hote = dict(x.split("=") for x in PG.split())
            with psycopg.connect(f"host={hote['host']} port={hote['port']} user=amz_app password=test-app dbname={nom}",
                                 autocommit=True) as app:
                dp = DepotPostgres(app)
                self.assertIsNotNone(dp.curseur_synchro(C, "VENTES"))
                self.assertEqual([r.tache for r in dp.journal_synchro(C)], ["VENTES", "STOCK", "REMBOURSEMENTS"])
                self.assertEqual(dp.journal_synchro("00000000-0000-4000-8000-0000000000c2"), [])
                self.assertEqual({t: ok for t, (f, ok) in dp.etat_synchros().items()},
                                 {"VENTES": True, "STOCK": True, "REMBOURSEMENTS": True})
        finally:
            with psycopg.connect(PG + " dbname=postgres", autocommit=True) as adm:
                adm.execute(f"DROP DATABASE IF EXISTS {nom} WITH (FORCE)")


if __name__ == "__main__":
    unittest.main()
