"""Fournisseurs et bons de commande [RM-AMZ-049 à 053]."""
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from sourcing import achats as A
from sourcing.analyse import Fournisseurs
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.depot import DepotMemoire
from sourcing.lots import Lot, Prevision, VenteReelle
from sourcing.money import Montant
from sourcing.providers.demo import FournisseurDemo

C = "00000000-0000-4000-8000-0000000000ee"
P = Prevision.creer("EUR", 20, 7, 8)
E = lambda v: Montant.de(v, "EUR")  # noqa: E731


def fournisseur(nom="Grossiste A", **k):
    return A.nouveau_fournisseur(C, nom, **k)


class TestDomaine(unittest.TestCase):
    def test_fournisseur_regles(self):
        """[RM-AMZ-049] Nom obligatoire et unique sans casse ; délai, devise, courriel contrôlés."""
        f = fournisseur("  Grossiste   A ")
        self.assertEqual((f.nom, f.devise, f.delai_jours, f.courriel), ("Grossiste A", "EUR", 7, None))
        for args, code in [(("",), "NOM_FOURNISSEUR_INVALIDE"), (("grossiste a",), "FOURNISSEUR_EXISTE"),
                           (("X",), "DELAI_INVALIDE"), (("Y",), "DEVISE_INVALIDE"), (("Z",), "COURRIEL_INVALIDE")]:
            kw = {"existants": [f]}
            if code == "DELAI_INVALIDE":
                kw["delai_jours"] = 400
            if code == "DEVISE_INVALIDE":
                kw["devise"] = "EU"
            if code == "COURRIEL_INVALIDE":
                kw["courriel"] = "pas-un-courriel"
            with self.subTest(code=code), self.assertRaises(A.ErreurAchat) as e:
                A.nouveau_fournisseur(C, *args, **kw)
            self.assertEqual(e.exception.args[0], code)

    def test_bon_cycle_de_vie(self):
        """[RM-AMZ-050] BROUILLON → ENVOYÉ → REÇU ; annulation possible avant réception ; le reste refusé."""
        f = fournisseur()
        b = A.nouveau_bon(C, 1, f)
        self.assertEqual(b.reference, "BC-0001")
        with self.assertRaises(A.ErreurAchat) as e:
            A.envoyer(b)
        self.assertEqual(e.exception.args[0], "BON_VIDE")
        b = A.envoyer(A.ajouter_ligne(b, "B0X", "FR", 10, "8", P))
        for fn in (lambda x: A.envoyer(x), lambda x: A.ajouter_ligne(x, "B0Y", "FR", 1, "1", P)):
            with self.assertRaises(A.ErreurAchat):
                fn(b)
        recu, _ = A.recevoir(b, {b.lignes[0].id: 10}, date(2026, 11, 12), f)
        for fn in (A.annuler, A.envoyer):
            with self.assertRaises(A.ErreurAchat) as e:
                fn(recu)
            self.assertEqual(e.exception.args[0], "TRANSITION_INTERDITE")
        self.assertEqual(A.annuler(A.nouveau_bon(C, 2, f)).statut, A.ANNULE)
        with self.assertRaises(A.ErreurAchat):
            A.nouveau_bon("autre", 1, f)

    def test_bon_lignes(self):
        """[RM-AMZ-050] Quantité et prix > 0 ; prévision figée au prix de la ligne ; même devise que le fournisseur."""
        b = A.nouveau_bon(C, 1, fournisseur())
        b = A.ajouter_ligne(b, "B0X", "FR", 10, "9.50", P, "Produit X", "EUR")
        (l,) = b.lignes
        self.assertEqual((l.prevision.cout_achat, l.prevision.prix_vente_ht, b.montant), (Decimal("9.50"), Decimal(20), Decimal("95.00")))
        for q, prix, code in [(0, "1", "QUANTITE_INVALIDE"), (1, "0", "PRIX_INVALIDE")]:
            with self.assertRaises(A.ErreurAchat) as e:
                A.ajouter_ligne(b, "B0X", "FR", q, prix, P)
            self.assertEqual(e.exception.args[0], code)
        with self.assertRaises(A.ErreurAchat) as e:
            A.ajouter_ligne(b, "B0X", "US", 1, "1", Prevision.creer("USD", 20, 7, 8), devise_fournisseur="EUR")
        self.assertEqual(e.exception.args[0], "DEVISE_DIFFERENTE")
        self.assertEqual(A.retirer_ligne(b, l.id).lignes, ())

    def test_reception_cree_les_lots(self):
        """[RM-AMZ-051] Ligne reçue > 0 → lot (quantité reçue, date, fournisseur, prévision, lien) ; 0 → pas de lot."""
        f = fournisseur()
        b = A.ajouter_ligne(A.ajouter_ligne(A.nouveau_bon(C, 1, f), "B0X", "FR", 10, "8", P, "X"), "B0Y", "FR", 5, "3", P)
        b = A.envoyer(b)
        l1, l2 = b.lignes
        with self.assertRaises(A.ErreurAchat) as e:
            A.recevoir(b, {l1.id: 11}, date(2026, 11, 12), f)
        self.assertEqual(e.exception.args[0], "QUANTITE_RECUE_INVALIDE")
        recu, lots = A.recevoir(b, {l1.id: 9}, date(2026, 11, 12), f)
        (lot,) = lots
        self.assertEqual((lot.quantite, lot.date_achat, lot.fournisseur, lot.bon_commande, lot.prevision.cout_achat),
                         (9, date(2026, 11, 12), "Grossiste A", b.id, Decimal(8)))
        self.assertEqual([(x.quantite_recue, x.lot_id) for x in recu.lignes], [(9, lot.id), (0, None)])
        with self.assertRaises(A.ErreurAchat):
            A.recevoir(recu, {}, date(2026, 11, 13), f)

    def test_bilan_fournisseur(self):
        """[RM-AMZ-052] ROI prévu et réel pondérés, montant 12 mois, délai réel ; sans données : None."""
        fa, fb = fournisseur("A"), fournisseur("B")
        l1 = Lot(C, "B0X", "FR", 10, date(2026, 9, 1), Prevision.creer("EUR", 20, 7, 8), fournisseur="A")
        l2 = Lot(C, "B0Y", "FR", 10, date(2024, 1, 1), Prevision.creer("EUR", 20, 7, 4), fournisseur="A")
        v = [VenteReelle(C, "B0X", "FR", date(2026, 10, 1), 10, E(200), E(70), E(0), E(0), E(0))]
        b = A.envoyer(A.ajouter_ligne(A.nouveau_bon(C, 1, fa), "B0X", "FR", 1, "8", P), datetime(2026, 11, 1, tzinfo=timezone.utc))
        b, _ = A.recevoir(b, {}, date(2026, 11, 6), fa)
        bil = {x.fournisseur.nom: x for x in A.bilans([fa, fb], [l1, l2], v, [b], date(2026, 11, 12))}
        a = bil["A"]
        self.assertEqual((a.lots, a.achete_12_mois, a.delai_reel_jours), (2, Decimal(80), 5.0))
        self.assertAlmostEqual(float(a.roi_prevu), (5 / 8 * 80 + 9 / 4 * 40) / 120, places=6)
        self.assertAlmostEqual(float(a.roi_reel), 5 / 8, places=6)                # seul le lot vendu compte
        self.assertEqual((bil["B"].lots, bil["B"].roi_prevu, bil["B"].roi_reel, bil["B"].delai_reel_jours), (0, None, None, None))


class TestApi(unittest.TestCase):
    def setUp(self):
        d = FournisseurDemo()
        self.depot = DepotMemoire()
        self.cl = TestClient(creer_app(self.depot, C, servir_interface=False, fournisseurs=Fournisseurs([d], d, d, d, d)))

    def test_parcours_api(self):
        """[RM-AMZ-050, 051] Fournisseur → bon → ligne depuis une analyse → envoi → réception → lot visible."""
        fid = self.cl.post("/api/fournisseurs", json={"nom": "Grossiste A", "delai_jours": 6}).json()["id"]
        self.assertEqual(self.cl.post("/api/fournisseurs", json={"nom": "grossiste a"}).json()["detail"], "FOURNISSEUR_EXISTE")
        b = self.cl.post("/api/bons", json={"fournisseur_id": fid}).json()
        an = self.cl.post("/api/analyse", json={"code": "B0DEMO0001", "prix_achat": 8.5}).json()["analyses"][0]
        b = self.cl.post(f"/api/bons/{b['id']}/lignes", json={"jeton_analyse": an["jeton_analyse"], "quantite": 24}).json()
        self.assertEqual((b["reference"], b["montant"], b["lignes"][0]["prix_unitaire"]), ("BC-0001", 204.0, 8.5))
        self.assertEqual(self.cl.post(f"/api/bons/{b['id']}/recevoir", json={"quantites": {}}).status_code, 409)
        b = self.cl.post(f"/api/bons/{b['id']}/envoyer").json()
        r = self.cl.post(f"/api/bons/{b['id']}/recevoir", json={"quantites": {b["lignes"][0]["id"]: 24},
                                                                 "date_reception": "2026-11-12"}).json()
        self.assertEqual((r["statut"], len(r["lots_crees"])), ("RECU", 1))
        lot = self.cl.get(f"/api/lots/{r['lots_crees'][0]}").json()
        self.assertEqual((lot["quantite"], lot["fournisseur"], lot["roi_prevu"]), (24, "Grossiste A", an["rentabilite"]["roi"] and lot["roi_prevu"]))
        self.assertEqual(self.cl.post(f"/api/bons/{b['id']}/annuler").json()["detail"], "TRANSITION_INTERDITE")
        f = self.cl.get("/api/fournisseurs").json()[0]
        self.assertEqual((f["lots"], f["achete_12_mois"]), (1, 204.0))

    def test_bon_depuis_stock(self):
        """[RM-AMZ-053] La commande suggérée du stock devient un bon brouillon au coût du dernier lot."""
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False))
        r = cl.post("/api/bons/depuis-stock", json={"fournisseur": "grossiste a"})
        self.assertEqual(r.status_code, 201)
        b = r.json()
        self.assertEqual((b["statut"], len(b["lignes"]), b["lignes"][0]["asin"], b["lignes"][0]["quantite"],
                          b["lignes"][0]["prix_unitaire"]), ("BROUILLON", 1, "B0DEMO0001", 7, 8.5))
        self.assertEqual(cl.post("/api/bons/depuis-stock", json={"fournisseur": "Inconnu"}).status_code, 404)
        self.assertEqual(cl.post("/api/bons/depuis-stock", json={"fournisseur": "MarqueDemo"}).json()["detail"], "RIEN_A_COMMANDER")


if __name__ == "__main__":
    unittest.main()
