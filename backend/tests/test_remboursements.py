"""Remboursements FBA [RM-AMZ-054 à 059]."""
import inspect
import unittest
from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from sourcing import remboursements as RB
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.lots import Lot, Prevision, VenteReelle
from sourcing.money import Montant
from sourcing.providers import spapi

J = date(2026, 11, 12)
E = lambda v: Montant.de(v, "EUR")  # noqa: E731
LOT = Lot("c", "B0X", "DE", 10, date(2026, 8, 1), Prevision.creer("EUR", 20, 7, 9.8), fournisseur="G")

LEDGER_TSV = ("Date\tFNSKU\tASIN\tMSKU\tTitle\tDisposition\tFound\tLost\tDamaged\tLocation\n"
              "10/01/2026\tX1\tB0X\tSKU-X\tProduit\tSELLABLE\t1\t-3\t-1\tDE\n")
REMB_TSV = ("approval-date\treimbursement-id\tcase-id\tamazon-order-id\treason\tsku\tfnsku\tasin\tproduct-name\tcondition\t"
            "currency-unit\tamount-per-unit\tamount-total\tquantity-reimbursed-cash\tquantity-reimbursed-inventory\t"
            "quantity-reimbursed-total\toriginal-reimbursement-id\toriginal-reimbursement-type\n"
            "2026-10-20\tR1\t\t\tLost_Warehouse\tSKU-X\tX1\tB0X\tProduit\tNew\tEUR\t9.80\t9.80\t1\t0\t1\t\t\n")
RETOURS_TSV = ("return-date\torder-id\tsku\tasin\tfnsku\tproduct-name\tquantity\tfulfillment-center-id\tdetailed-disposition\t"
               "reason\tstatus\tlicense-plate-number\tcustomer-comments\n"
               "2026-09-25T10:00:00+00:00\t111-B\tSKU-X\tB0X\tX1\tProduit\t1\tFRA1\tSELLABLE\tNO_LONGER_NEEDED\tUnit returned to inventory\tLPN1\t\n")


def rembourse(commande, jour):
    return VenteReelle("c", "B0X", "DE", jour, 0, E(0), E(-0.6), E(20), E(0), E(0), commande=commande)


class TestRemboursements(unittest.TestCase):
    def test_aucune_reclamation_automatique(self):
        """[RM-AMZ-054] Aucun appel d'écriture vers l'API Support d'Amazon : l'outil ne dépose rien."""
        source = inspect.getsource(spapi) + inspect.getsource(RB)
        for interdit in ("/support/", "createCase", "case/create"):
            self.assertNotIn(interdit, source)

    def test_detection_pertes_entrepot(self):
        """[RM-AMZ-055] |Lost| + |Damaged| − |Found| − déjà remboursé sans commande ; colonnes officielles lues."""
        ledger, verses = RB.parser_ledger_synthese(LEDGER_TSV), RB.parser_remboursements(REMB_TSV)
        self.assertEqual((ledger[0].perdus, ledger[0].abimes, ledger[0].retrouves, ledger[0].jour), (3, 1, 1, date(2026, 10, 1)))
        (c,) = RB.detecter(ledger, verses, [], [], [], [LOT], J)
        self.assertEqual((c.type, c.unites, c.faits["deja_rembourse"], c.valeur_achat), (RB.PERTE, 2, 1, Decimal("19.6")))
        verses += [RB.RemboursementVerse("R2", J, None, None, "SKU-X", "X1", "B0X", "EUR", Decimal("19.6"), 2)]
        self.assertEqual(RB.detecter(ledger, verses, [], [], [], [LOT], J), [])

    def test_detection_retour_non_restitue(self):
        """[RM-AMZ-056] Remboursé au client il y a ≥ 45 j, sans retour ni remboursement de la commande → cas."""
        retours = RB.parser_retours(RETOURS_TSV)
        ventes = [rembourse("111-A", J - timedelta(days=50)), rembourse("111-B", J - timedelta(days=50)),
                  rembourse("111-C", J - timedelta(days=30))]
        verses = [RB.RemboursementVerse("R9", J, None, "111-D", None, None, "B0X", "EUR", Decimal(20), 1)]
        ventes.append(rembourse("111-D", J - timedelta(days=60)))
        cas = RB.detecter([], verses, retours, ventes, [], [], J)
        self.assertEqual([c.commande for c in cas], ["111-A"])          # B retourné, C trop récent, D déjà remboursé

    def test_detection_envoi_incomplet(self):
        """[RM-AMZ-057] Envoi CLOSED : expédié − reçu − déjà remboursé ; aucune échéance (délai non vérifié)."""
        envois = [RB.LigneEnvoi("FBA1", "CLOSED", "DE", "SKU-X", "X1", 40, 37), RB.LigneEnvoi("FBA2", "RECEIVING", "DE", "S", "X2", 10, 2)]
        verses = RB.parser_remboursements(REMB_TSV)
        (c,) = RB.detecter([], verses, [], [], envois, [LOT], J, asins_par_sku={"SKU-X": "B0X"})
        self.assertEqual((c.type, c.unites, c.echeance, c.valeur_achat), (RB.ENVOI, 2, None, Decimal("19.6")))

    def test_echeances_et_montants(self):
        """[RM-AMZ-058] Pertes : 60 j après la perte ; retours : 105 j après le remboursement ; jamais de montant « dû »."""
        (p,) = RB.detecter(RB.parser_ledger_synthese(LEDGER_TSV), [], [], [], [], [LOT], J)
        self.assertEqual(p.echeance, date(2026, 10, 1) + timedelta(days=60))
        (r,) = RB.detecter([], [], [], [rembourse("111-A", date(2026, 9, 1))], [], [], J)
        self.assertEqual(r.echeance, date(2026, 9, 1) + timedelta(days=105))
        self.assertIsNone(r.montant_verse)
        self.assertIn("2025", RB.SOURCE_DELAIS)
        champs = set(vars(p))
        self.assertFalse({"montant_du", "montant_estime"} & champs)

    def test_suivi_des_cas(self):
        """[RM-AMZ-059] Suivi gardé à la redétection ; dossier exige un n° de cas ; disparition + versement → REMBOURSÉ."""
        ledger = RB.parser_ledger_synthese(LEDGER_TSV)
        (c,) = RB.detecter(ledger, [], [], [], [], [LOT], J)
        with self.assertRaises(ValueError):
            RB.changer_suivi(c, RB.DOSSIER_ENVOYE)
        c = RB.changer_suivi(c, RB.DOSSIER_ENVOYE, "C-77")
        (c2,) = RB.appliquer_suivi(RB.detecter(ledger, [], [], [], [], [LOT], J + timedelta(days=1)), [c], [])
        self.assertEqual((c2.statut, c2.case_id, c2.detecte_le), (RB.DOSSIER_ENVOYE, "C-77", J))
        paye = [RB.RemboursementVerse("R5", J, "C-77", None, None, "X1", "B0X", "EUR", Decimal("29.4"), 3)]
        (c3,) = RB.appliquer_suivi(RB.detecter(ledger, paye, [], [], [], [LOT], J), [c2], paye)
        self.assertEqual((c3.statut, c3.montant_verse), (RB.REMBOURSE, Decimal("29.4")))

    def test_api_remboursements_demo(self):
        """API : 3 cas à vérifier dans la démo ; passage en « dossier envoyé » avec numéro de cas."""
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False))
        j = cl.get("/api/remboursements").json()
        self.assertEqual(sorted(x["type"] for x in j["cas"]), sorted([RB.PERTE, RB.RETOUR, RB.ENVOI]))
        self.assertEqual(j["compteurs"]["a_verifier"], 3)
        cle = j["cas"][0]["cle"]
        self.assertEqual(cl.post(f"/api/remboursements/{cle}/suivi", json={"statut": "DOSSIER_ENVOYE"}).json()["detail"],
                         "NUMERO_DE_CAS_REQUIS")
        r = cl.post(f"/api/remboursements/{cle}/suivi", json={"statut": "DOSSIER_ENVOYE", "case_id": "C-1"}).json()
        self.assertEqual((r["statut"], r["case_id"]), ("DOSSIER_ENVOYE", "C-1"))
        self.assertEqual(cl.get("/api/remboursements").json()["compteurs"]["en_cours"], 1)


if __name__ == "__main__":
    unittest.main()
