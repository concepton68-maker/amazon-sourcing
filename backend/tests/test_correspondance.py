"""Produit différent ? [RM-AMZ-083] — cas réels de l'essai du 14/11/2026."""
import unittest
from decimal import Decimal

from sourcing.analyse import Fournisseurs, Seuils
from sourcing.fichier import LigneFournisseur
from sourcing.marketplaces import get_marketplace
from sourcing.providers.demo import FournisseurDemo
from sourcing.traitement import _ligne, correspondance


class TestCorrespondance(unittest.TestCase):
    def test_correspondance_titre(self):
        """Fiches sans rapport signalées ; bonnes correspondances acceptées ; jamais « Acheter » si différent."""
        bons = [("Nutella 400 g", "Nutella Pâte à Tartiner aux Noisettes/au Cacao 400 g"),
                ("Coca-Cola 33 cl", "COCA COLA Canette de boisson gazeuse pétillante de 33 cl"),
                ("Colle forte gel 50 g KRAFTPROTZ", "Colle forte gel 50 g – ne coule pas – KRAFTPROTZ"),
                ("Boxers QINCAO lot de 6", "QINCAO Boxer Homme Coton Peigné Lot de 6")]
        mauvais = [("Surligneur Stabilo Boss jaune", "Elettromek italia Indicateur de niveau d'eau à LED pour réservoir"),
                   ("Surligneur Stabilo Boss jaune", "Feutre Stabilo Point 88 - Bleu azur"),
                   ("Eau Evian 1,5 L", "Evian - Mineral Water - 500 ml")]
        for d, t in bons:
            with self.subTest(d=d):
                self.assertGreaterEqual(correspondance(d, t), 0.5)
        for d, t in mauvais:
            with self.subTest(d=d, t=t):
                self.assertLess(correspondance(d, t), 0.5)
        self.assertIsNone(correspondance(None, "Titre"))
        self.assertIsNone(correspondance("Gourde", None))
        d = FournisseurDemo()
        f = Fournisseurs([d], d, d, d, d)
        fr = get_marketplace("FR")
        ok = _ligne(LigneFournisseur(2, "B0DEMO0001", Decimal("8.5"), None, None, None, []), fr, "B0DEMO0001", f,
                    "assujetti", Seuils(), False)
        self.assertEqual(ok.verdict, "ACHETER")
        diff = _ligne(LigneFournisseur(2, "B0DEMO0001", Decimal("8.5"), "Tondeuse à gazon électrique", None, None, []),
                      fr, "B0DEMO0001", f, "assujetti", Seuils(), False)
        self.assertIn("L_PRODUIT_DIFFERENT", [x.code for x in diff.lignes])
        self.assertEqual(diff.verdict, "A_VERIFIER")


if __name__ == "__main__":
    unittest.main()
