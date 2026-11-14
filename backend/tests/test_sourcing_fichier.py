"""Sourcing par fichier fournisseur [RM-AMZ-030 à 035]."""
import io
import pathlib
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from openpyxl import Workbook

from sourcing import fichier as F
from sourcing.analyse import Fournisseurs
from sourcing.api import creer_app
from sourcing.depot import DepotMemoire
from sourcing.marketplaces import get_marketplace
from sourcing.providers.demo import FournisseurDemo
from sourcing.traitement import Traitement, executer

C = "00000000-0000-4000-8000-0000000000cc"
DEMO_CSV = pathlib.Path(__file__).resolve().parents[2] / "docs" / "demo" / "catalogue-fournisseur-demo.csv"
FR = get_marketplace("FR")


def demo():
    d = FournisseurDemo()
    return Fournisseurs([d], d, d, d, d)


def csv(*lignes, sep=";"):
    return ("\n".join(sep.join(l) for l in lignes) + "\n").encode("utf-8")


class TestLecture(unittest.TestCase):
    def test_lecture_csv_et_xlsx(self):
        """[RM-AMZ-030] CSV ; ou , (UTF-8, Windows-1252) et Excel ; lignes vides ignorées."""
        t = F.lire(csv(("EAN", "Prix"), ("3700000000017", "8,50"), ("", "")), "a.csv")
        self.assertEqual((t.entetes, t.lignes), (["EAN", "Prix"], [["3700000000017", "8,50"]]))
        t = F.lire(csv(("EAN", "Désignation"), ("1", "Été"), sep=",").decode().encode("cp1252"), "b.csv")
        self.assertEqual(t.lignes[0][1], "Été")
        wb = Workbook()
        wb.active.append(["EAN", "PU HT"])
        wb.active.append([3700000000017, 8.5])
        b = io.BytesIO()
        wb.save(b)
        t = F.lire(b.getvalue(), "c.xlsx")
        self.assertEqual(t.lignes[0], ["3700000000017", "8.5"])

    def test_limites_fichier(self):
        """[RM-AMZ-030] Format, taille, nombre de lignes et fichier vide contrôlés."""
        for contenu, nom, code in [(b"x", "a.pdf", "FORMAT_NON_GERE"), (csv(("EAN",)), "a.csv", "FICHIER_VIDE"),
                                   (b"0" * (F.MAX_OCTETS + 1), "a.csv", "FICHIER_TROP_GROS"),
                                   (csv(("EAN",), *[(str(i),) for i in range(F.MAX_LIGNES + 1)]), "a.csv", "TROP_DE_LIGNES")]:
            with self.subTest(code=code), self.assertRaises(F.FichierInvalide) as e:
                F.lire(contenu, nom)
            self.assertEqual(e.exception.args[0], code)

    def test_proposition_colonnes(self):
        """[RM-AMZ-031] Synonymes reconnus ; deux candidates exactes → rien n'est deviné."""
        p = F.proposer_colonnes(["Réf. EAN", "Désignation article", "PU HT", "Colisage", "Mini cde"])
        self.assertEqual(p, {"code": 0, "prix": 2, "designation": 1, "colisage": 3, "minimum": 4})
        self.assertEqual(F.proposer_colonnes(["Code", "Désignation", "Prix HT", "Colisage"]),
                         {"code": 0, "prix": 2, "designation": 1, "colisage": 3, "minimum": None})
        p = F.proposer_colonnes(["EAN", "GTIN", "Price"])
        self.assertIsNone(p["code"])
        self.assertEqual(p["prix"], 2)

    def test_lignes_prix_et_cles(self):
        """[RM-AMZ-032] Prix FR/EN, rejets motivés, clé fausse = avertissement, doublons, zéros de tête."""
        self.assertEqual([F.lire_prix(x) for x in ["1 234,56 €", "1.234,56", "1,234.56", "12.5", "8,50", "abc", ""]],
                         [Decimal("1234.56")] * 3 + [Decimal("12.5"), Decimal("8.50"), None, None])
        # jamais un nombre tiré d'un texte (colonne « Désignation » prise pour le prix)
        self.assertEqual([F.lire_prix(x) for x in ["Colle forte gel 50 g", "Eau Evian 1,5 L", "lot de 6", "3,40 € HT", "EUR 2,10"]],
                         [None, None, None, Decimal("3.40"), Decimal("2.10")])
        self.assertTrue(F.cle_gs1_valide("2000000000015"))
        self.assertTrue(F.cle_gs1_valide("036000291452"))           # UPC-A, exemple d'école
        self.assertFalse(F.cle_gs1_valide("2000000000016"))
        self.assertIsNone(F.cle_gs1_valide("B0DEMO0001"))
        t = F.Table(["EAN", "Prix"], [["2000000000015", "8,50"], ["2000000000016", "5"], ["", "3"],
                                      ["2000000000015", "9"], ["123", "-2"], ["36000291452", "4"]])
        p = F.preparer(t, {"code": 0, "prix": 1})
        self.assertEqual([l.code for l in p.lignes], ["2000000000015", "2000000000016", "0036000291452"])
        self.assertEqual([x.code for x in p.lignes[1].avertissements], ["L_CLE_INVALIDE"])
        self.assertEqual([x.code for x in p.lignes[2].avertissements], ["L_ZEROS_AJOUTES"])   # clé valide après
        self.assertEqual([(n, m.code) for n, m in p.rejets], [(4, "L_CODE_ABSENT"), (6, "L_PRIX_INVALIDE")])
        self.assertEqual(p.doublons, [(5, "2000000000015")])
        with self.assertRaises(F.FichierInvalide):
            F.preparer(t, {"code": 0, "prix": None})

    def test_prix_carton_et_lot_amazon(self):
        """[RM-AMZ-033] Prix carton ÷ colisage ; listing en lot de 6 → coût = 6 × prix unitaire."""
        t = F.Table(["EAN", "Prix", "Colisage"], [["2000000001241", "12,54", "6"], ["2000000000015", "10", ""]])
        p = F.preparer(t, {"code": 0, "prix": 1, "colisage": 2}, prix_par_carton=True)
        self.assertEqual(p.lignes[0].prix_unitaire, Decimal("2.09"))
        self.assertEqual([m.code for _, m in p.rejets], ["L_COLISAGE_ABSENT"])
        tr = executer(Traitement("t", C, "FR", 1), p, FR, demo(), DepotMemoire())
        (r,) = tr.resultats
        self.assertEqual((r.unites_lot, r.cout_achat), (6, Decimal("12.54")))
        self.assertIn("L_LOT_AMAZON", [x.code for x in r.lignes])


class TestTraitement(unittest.TestCase):
    def test_memoire_appariements(self):
        """[RM-AMZ-034] 2e passage : correspondance reprise de la mémoire du compte ; jamais d'un autre compte."""
        d = DepotMemoire()
        p = F.preparer(F.Table(["EAN", "Prix"], [["3700000000017", "8,5"]]), {"code": 0, "prix": 1})
        t1 = executer(Traitement("1", C, "FR", 1), p, FR, demo(), d)
        t2 = executer(Traitement("2", C, "FR", 1), p, FR, demo(), d)
        t3 = executer(Traitement("3", "autre", "FR", 1), p, FR, demo(), d)
        self.assertEqual((t1.appariements_memoire, t2.appariements_memoire, t3.appariements_memoire), (0, 1, 0))
        vieux = datetime.now(timezone.utc) - timedelta(days=31)
        d.memoriser_appariement(C, "FR", "3700000000017", ["B0DEMO0001"], vieux)
        self.assertEqual(executer(Traitement("4", C, "FR", 1), p, FR, demo(), d).appariements_memoire, 0)

    def _api(self):
        app = creer_app(DepotMemoire(), C, servir_interface=False, fournisseurs=demo(), traitement_en_fond=False)
        return TestClient(app)

    def test_traitement_complet(self):
        """[RM-AMZ-035] Fichier de démo : dépôt, colonnes proposées, traitement, tri et comptages."""
        cl = self._api()
        r = cl.post("/api/sourcing/fichiers", files={"fichier": ("demo.csv", DEMO_CSV.read_bytes(), "text/csv")})
        self.assertEqual(r.status_code, 201)
        f = r.json()
        self.assertEqual(f["colonnes"], {"code": 0, "prix": 2, "designation": 1, "colisage": 3, "minimum": 4})
        tid = cl.post(f"/api/sourcing/fichiers/{f['fichier_id']}/traitements",
                      json={"colonnes": f["colonnes"], "marketplace": "FR"}).json()["traitement_id"]
        j = cl.get(f"/api/sourcing/traitements/{tid}").json()
        self.assertEqual((j["statut"], j["faits"], j["total"]), ("TERMINE", j["total"], f["nb_lignes"] - 2))
        c = j["compteurs"]
        self.assertEqual((c["INTROUVABLE"], c["REJETEE"], c["DOUBLON"]), (1, 1, 1))
        self.assertGreaterEqual(c["ACHETER"], 1)
        ordre = {"ACHETER": 0, "A_VERIFIER": 1, "PASSER": 2}
        verdicts = [ordre[x["verdict"]] for x in j["resultats"] if x["statut"] == "ANALYSEE"]
        self.assertEqual(verdicts, sorted(verdicts))
        self.assertEqual(j["resultats"][-1]["statut"], "INTROUVABLE")
        cle = [x for x in j["resultats"] if x["code"] == "2000000000990"][0]
        self.assertIn("L_CLE_INVALIDE", [m["code"] for m in cle["remarques"]])
        pack = [x for x in j["resultats"] if x["unites_lot"] > 1][0]
        self.assertAlmostEqual(pack["cout_achat"], pack["prix_unitaire"] * pack["unites_lot"], places=4)
        self.assertEqual(cl.get("/api/sourcing/traitements/inconnu").status_code, 404)

    def test_export_csv(self):
        """[RM-AMZ-035] Export : une ligne par résultat + rejets, remarques traduites, séparateur « ; »."""
        cl = self._api()
        f = cl.post("/api/sourcing/fichiers", files={"fichier": ("demo.csv", DEMO_CSV.read_bytes(), "text/csv")}).json()
        tid = cl.post(f"/api/sourcing/fichiers/{f['fichier_id']}/traitements",
                      json={"colonnes": f["colonnes"]}).json()["traitement_id"]
        r = cl.get(f"/api/sourcing/traitements/{tid}/export.csv")
        self.assertEqual(r.status_code, 200)
        lignes = r.text.strip().splitlines()
        self.assertTrue(lignes[0].startswith("ligne;code;designation"))
        self.assertTrue(any("REJETEE" in l and "Prix absent" in l for l in lignes))
        self.assertFalse(any("sous le minimum" in l and "%" in l.split("sous le minimum")[1].split("|")[0] for l in lignes))
        self.assertTrue(any("Introuvable sur Amazon" in l for l in lignes))


if __name__ == "__main__":
    unittest.main()
