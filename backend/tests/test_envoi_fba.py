"""Envoi FBA par l'API, partie 1 [RM-AMZ-137 à 139]."""
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from sourcing import envoi_fba as FBA
from sourcing.api import creer_app
from sourcing.depot import DepotMemoire
from sourcing.marketplaces import get_marketplace

C = "00000000-0000-4000-8000-0000000000dd"
SOCIETE = {"raison_sociale": "GO-SHOPPING", "expedition_rue": "1 rue A", "expedition_cp": "68000",
           "expedition_ville": "Colmar", "expedition_pays": "FR", "telephone": "0600000000"}


class FauxInbound:
    """`_appel` simulé : opérations, options d'emballage, groupes."""

    def __init__(self, statuts=None):
        self.appels = []
        self.statuts = list(statuts or [])
        self.n = 0

    def _appel(self, mp, methode, chemin, params=None, json=None):
        self.appels.append((methode, chemin, json))
        if chemin.endswith("/inboundPlans") and methode == "POST":
            return {"inboundPlanId": "wf-1", "operationId": "op-plan"}
        if "/operations/" in chemin:
            self.n += 1
            s = self.statuts.pop(0) if self.statuts else "SUCCESS"
            return {"operationStatus": s, "operationProblems": [] if s != "FAILED" else
                    [{"code": "FBA_INB_0182", "message": "Adresse refusée", "severity": "ERROR"}]}
        if chemin.endswith("/packingOptions") and methode == "GET":
            return {"packingOptions": [{"packingOptionId": "po-1", "status": "OFFERED", "packingGroups": ["pg-1"],
                                        "fees": [], "discounts": [], "supportedConfigurations": [
                                            {"boxRequirements": {"weight": {"minimum": 0.1, "maximum": 23, "unit": "KG"}}}]}]}
        if "/packingGroups/" in chemin:
            return {"items": [{"msku": "SKU-A"}, {"msku": "SKU-B"}]}
        return {"operationId": "op-x"}


def app(faux):
    d = DepotMemoire()
    cl = TestClient(creer_app(d, C, servir_interface=False, traitement_en_fond=False, fabrique_spapi=lambda v: faux))
    d.enregistrer_connexion(C, "SPAPI", b"factice")
    cl.put("/api/parametres", json={"societe": SOCIETE})
    return d, cl


class TestBrouillon(unittest.TestCase):
    def test_brouillon_envoi(self):
        """[RM-AMZ-137] Nom, lignes uniques et quantités 1 à 500 000, propriétaires connus."""
        e = FBA.nouveau_brouillon(C, " Envoi  1 ", "FR", [{"msku": "SKU-A", "quantite": 12}])
        self.assertEqual((e.nom, e.statut, e.proprietaire_etiquette), ("Envoi 1", "BROUILLON", "SELLER"))
        for lignes, code in [([], "ENVOI_VIDE"), ([{"msku": "A", "quantite": 0}], "QUANTITE_INVALIDE"),
                             ([{"msku": "A", "quantite": 1}, {"msku": "A", "quantite": 2}], "SKU_INVALIDE"),
                             ([{"msku": "A", "quantite": 500001}], "QUANTITE_INVALIDE")]:
            with self.subTest(code=code), self.assertRaises(FBA.ErreurEnvoi) as x:
                FBA.nouveau_brouillon(C, "E", "FR", lignes)
            self.assertEqual(x.exception.args[0], code)
        with self.assertRaises(FBA.ErreurEnvoi):
            FBA.nouveau_brouillon(C, "E", "FR", [{"msku": "A", "quantite": 1}], etiquette="MOI")
        corps = FBA.corps_plan(e, get_marketplace("FR").marketplace_id, FBA.adresse_expedition(SOCIETE))
        self.assertEqual(len(corps["destinationMarketplaces"]), 1)
        self.assertEqual(corps["items"][0], {"msku": "SKU-A", "quantity": 12, "labelOwner": "SELLER", "prepOwner": "NONE"})

    def test_adresse_expedition(self):
        """[RM-AMZ-137] Champs obligatoires d'Amazon, longueurs, pays en 2 lettres."""
        a = FBA.adresse_expedition(SOCIETE)
        self.assertEqual((a["name"], a["countryCode"], a["postalCode"]), ("GO-SHOPPING", "FR", "68000"))
        with self.assertRaises(FBA.ErreurEnvoi) as x:
            FBA.adresse_expedition({**SOCIETE, "expedition_ville": None, "telephone": ""})
        self.assertEqual(x.exception.args, ("ADRESSE_INCOMPLETE", "city,phoneNumber"))
        with self.assertRaises(FBA.ErreurEnvoi):
            FBA.adresse_expedition({**SOCIETE, "expedition_ville": "x" * 31})


class TestApi(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(FBA, "PAUSE_ECRITURE", 0)
        p.start()
        self.addCleanup(p.stop)
        self.faux = FauxInbound()
        self.d, self.cl = app(self.faux)
        r = self.cl.post("/api/envois-fba", json={"nom": "Envoi 1", "lignes": [{"msku": "SKU-A", "quantite": 10},
                                                                                {"msku": "SKU-B", "quantite": 4}]})
        self.assertEqual(r.status_code, 201, r.text)
        self.eid = r.json()["id"]

    def attendre_nul(self):
        return mock.patch("sourcing.envoi_fba.time.sleep", lambda s: None)

    def test_creation_plan(self):
        """[RM-AMZ-138] Création puis options d'emballage ; rien de payant appelé."""
        with self.attendre_nul():
            e = self.cl.post(f"/api/envois-fba/{self.eid}/creer-plan").json()
        e = self.cl.get(f"/api/envois-fba/{self.eid}").json()
        self.assertEqual((e["statut"], e["plan_id"]), ("PLAN_CREE", "wf-1"))
        self.assertEqual(e["donnees"]["options"][0]["id"], "po-1")
        chemins = [c[1] for c in self.faux.appels]
        self.assertFalse(any("placementOptions" in x or "transportationOptions" in x for x in chemins))
        self.assertEqual(self.cl.post(f"/api/envois-fba/{self.eid}/creer-plan").status_code, 409)

    def test_operation_echec(self):
        """[RM-AMZ-138] Opération FAILED : statut ERREUR, problème d'Amazon gardé."""
        self.faux.statuts = ["IN_PROGRESS", "FAILED"]
        with self.attendre_nul():
            self.cl.post(f"/api/envois-fba/{self.eid}/creer-plan")
        e = self.cl.get(f"/api/envois-fba/{self.eid}").json()
        self.assertEqual(e["statut"], "ERREUR")
        self.assertEqual(e["donnees"]["probleme_plan"][0]["gravite"], "ERROR")

    def test_options_emballage(self):
        """[RM-AMZ-138] Confirmation sur l'option choisie ; groupes et poids limites retenus."""
        with self.attendre_nul():
            self.cl.post(f"/api/envois-fba/{self.eid}/creer-plan")
            self.assertEqual(self.cl.post(f"/api/envois-fba/{self.eid}/confirmer-emballage", json={"option": "x"}).status_code, 422)
            self.cl.post(f"/api/envois-fba/{self.eid}/confirmer-emballage", json={"option": "po-1"})
        e = self.cl.get(f"/api/envois-fba/{self.eid}").json()
        self.assertEqual(e["statut"], "EMBALLAGE_CONFIRME")
        self.assertEqual(e["donnees"]["groupes"], [{"id": "pg-1", "mskus": ["SKU-A", "SKU-B"], "poids_min": 0.1, "poids_max": 23.0}])
        self.assertTrue(any(c[1].endswith("/packingOptions/po-1/confirmation") for c in self.faux.appels))

    def preparer_cartons(self):
        with self.attendre_nul():
            self.cl.post(f"/api/envois-fba/{self.eid}/creer-plan")
            self.cl.post(f"/api/envois-fba/{self.eid}/confirmer-emballage", json={"option": "po-1"})

    def test_cartons_controles(self):
        """[RM-AMZ-139] Quantités incomplètes, poids hors limites, SKU hors groupe : refus."""
        self.preparer_cartons()
        base = {"groupe": "pg-1", "longueur": 40, "largeur": 30, "hauteur": 30, "poids": 8, "nombre": 2}
        for cartons, code in [([{**base, "contenu": {"SKU-A": 5}}], "QUANTITES_CARTONS"),
                              ([{**base, "poids": 30, "contenu": {"SKU-A": 5, "SKU-B": 2}}], "POIDS_HORS_LIMITES"),
                              ([{**base, "contenu": {"SKU-Z": 5}}], "SKU_HORS_GROUPE"),
                              ([{**base, "longueur": 0, "contenu": {"SKU-A": 5, "SKU-B": 2}}], "CARTON_INVALIDE")]:
            with self.subTest(code=code):
                r = self.cl.post(f"/api/envois-fba/{self.eid}/cartons", json={"cartons": cartons})
                self.assertEqual((r.status_code, r.json()["detail"]["code"]), (422, code))

    def test_cartons_envoyes(self):
        """[RM-AMZ-139] Corps setPackingInformation : contenu fourni, cm, kg, cartons identiques."""
        self.preparer_cartons()
        cartons = [{"groupe": "pg-1", "longueur": 40, "largeur": 30, "hauteur": 30, "poids": 8, "nombre": 2,
                    "contenu": {"SKU-A": 5, "SKU-B": 2}}]
        with self.attendre_nul():
            self.cl.post(f"/api/envois-fba/{self.eid}/cartons", json={"cartons": cartons})
        self.assertEqual(self.cl.get(f"/api/envois-fba/{self.eid}").json()["statut"], "CARTONS_ENVOYES")
        corps = next(c[2] for c in self.faux.appels if c[1].endswith("/packingInformation"))
        box = corps["packageGroupings"][0]["boxes"][0]
        self.assertEqual(corps["packageGroupings"][0]["packingGroupId"], "pg-1")
        self.assertEqual((box["contentInformationSource"], box["dimensions"]["unitOfMeasurement"], box["weight"]["unit"],
                          box["quantity"]), ("BOX_CONTENT_PROVIDED", "CM", "KG", 2))

    def test_annuler_plan(self):
        """[RM-AMZ-139] Brouillon annulé sans appel ; plan annulé par cancelInboundPlan."""
        r = self.cl.post("/api/envois-fba", json={"nom": "B", "lignes": [{"msku": "SKU-A", "quantite": 1}]}).json()
        self.assertEqual(self.cl.post(f"/api/envois-fba/{r['id']}/annuler").json()["statut"], "ANNULE")
        with self.attendre_nul():
            self.cl.post(f"/api/envois-fba/{self.eid}/creer-plan")
            self.cl.post(f"/api/envois-fba/{self.eid}/annuler")
        self.assertEqual(self.cl.get(f"/api/envois-fba/{self.eid}").json()["statut"], "ANNULE")
        self.assertTrue(any(c[0] == "PUT" and c[1].endswith("/cancellation") for c in self.faux.appels))

    def test_adresse_manquante_refusee(self):
        self.cl.put("/api/parametres", json={"societe": {"raison_sociale": "GO-SHOPPING"}})
        r = self.cl.post(f"/api/envois-fba/{self.eid}/creer-plan")
        self.assertEqual((r.status_code, r.json()["detail"]["code"]), (422, "ADRESSE_INCOMPLETE"))
        self.assertFalse(self.faux.appels)
