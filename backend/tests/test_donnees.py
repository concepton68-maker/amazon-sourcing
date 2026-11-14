"""Écran « Données » et relevé à la demande [RM-AMZ-140, 141]."""
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from sourcing import donnees as DN
from sourcing import historique as H
from sourcing.api import creer_app
from sourcing.demo_donnees import construire


class TestDonnees(unittest.TestCase):
    def test_donnees_jeux(self):
        """[RM-AMZ-140] Chaque jeu : colonnes typées et lignes plates ; jeu inconnu refusé."""
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False, traitement_en_fond=False))
        for nom in DN.COLONNES:
            r = cl.get(f"/api/donnees/{nom}")
            self.assertEqual(r.status_code, 200, nom)
            j = r.json()
            cles = {x["cle"] for x in j["colonnes"]}
            self.assertTrue(all(set(l) >= cles for l in j["lignes"]), nom)
        self.assertEqual(cl.get("/api/donnees/inconnu").status_code, 404)

    def test_donnees_marche_tendances(self):
        """[RM-AMZ-140] Marché : dernier relevé et tendances sur 30 jours par produit."""
        d, c = construire()
        jour = H.jour_paris(datetime.now(timezone.utc))
        d.enregistrer_releves(c, [H.Releve("FR", "B0DONNEE01", jour - timedelta(days=k), Decimal("20") + k, 2, 1, False,
                                           False, None, 1000 + 10 * k) for k in range(5)])
        lignes = [l for l in DN.marche(d, c, jour) if l["asin"] == "B0DONNEE01"]
        self.assertEqual(len(lignes), 1)
        l = lignes[0]
        self.assertEqual((l["prix_buybox"], l["bsr"], l["vendeurs"], l["releves"], l["jour"]), (20.0, 1000, 3, 5, jour.isoformat()))
        self.assertLess(l["prix_variation"], 0)


class TestReleverMaintenant(unittest.TestCase):
    def test_relever_maintenant(self):
        """[RM-AMZ-141] Seule la tâche « historique de marché » tourne."""
        from tests.test_synchro import Faux
        d, c = construire()
        d.enregistrer_connexion(c, "SPAPI", b"factice")
        cl = TestClient(creer_app(d, c, servir_interface=False, traitement_en_fond=False, fabrique_spapi=lambda v: Faux()))
        self.assertEqual(cl.post("/api/synchro/manuelle", json={"taches": ["HISTORIQUE"]}).status_code, 202)
        e = cl.get("/api/synchro/manuelle").json()["etat"]
        self.assertEqual([x["tache"] for x in e["terminees"]], ["HISTORIQUE"])
