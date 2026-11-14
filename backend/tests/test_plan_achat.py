"""Plan d'achat, quantité proposée, société, document du bon [RM-AMZ-125 à 128]."""
import io
import unittest
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from sourcing import achats as A
from sourcing import bon_document as BD
from sourcing import plan_achat as PA
from sourcing.achats_serial import ligne_depuis_dict, ligne_vers_dict, prevision_vers_dict
from sourcing.api import creer_app
from sourcing.depot import DepotMemoire
from sourcing.fichier import LigneFournisseur
from sourcing.lots import Prevision
from sourcing.opportunites import Opportunite
from sourcing.parametres import ParametreInvalide, valider

C = "00000000-0000-4000-8000-0000000000aa"
PREV = prevision_vers_dict(Prevision.creer("EUR", 25, 8, 10))
T = datetime(2026, 11, 14, tzinfo=timezone.utc)


def preparer(revente="AUTORISEE"):
    d = DepotMemoire()
    f = A.nouveau_fournisseur(C, "Grossiste A")
    f = A.modifier_fiche(f, revente=revente, courriel="ventes@grossiste.example")
    d.enregistrer_fournisseur(C, f)
    d.enregistrer_catalogue(C, f.id, {"nom_fichier": "prix.xlsx", "lignes": 2, "rejets": 0},
                            [LigneFournisseur(2, "3700000000011", Decimal("5"), "Bougie", colisage=6, minimum=10),
                             LigneFournisseur(3, "3700000000028", Decimal("4"), "Savon")])
    ops = [Opportunite(f"FOURNISSEUR:{f.id}", f.nom, "FR", "3700000000011", "B0AAA00001", "Bougie parfumée",
                       "Bougie", 5.0, 2, 10.0, 25.0, 6.0, 0.6, analyse_le=T, prevision=PREV),
           Opportunite(f"CORRESPONDANCE:{f.id}", f.nom, "FR", "3700000000028", "B0AAA00002", "Savon",
                       "Savon", 4.0, 1, 4.0, 15.0, 3.0, 0.75, analyse_le=T, prevision=PREV),
           Opportunite("FICHIER:liste.xlsx", "liste.xlsx", "FR", "123", "B0AAA00003", "X", analyse_le=T,
                       prevision=PREV),
           Opportunite(f"FOURNISSEUR:{f.id}", f.nom, "FR", "999", "B0AAA00004", "Ancien", analyse_le=T)]
    for o in ops:
        d.ajouter_opportunites(C, o.origine, "FR", [o])
    return d, f, ops


def choix(o, **k):
    return {"origine": o.origine, "marketplace": o.marketplace, "code": o.code, "asin": o.asin, **k}


class TestPlanAchat(unittest.TestCase):
    def test_plan_achat(self):
        """[RM-AMZ-125] Un brouillon par fournisseur, sans doublon, refus dits ligne par ligne."""
        d, f, ops = preparer()
        r = PA.ajouter(d, C, [choix(o) for o in ops])
        self.assertEqual(r["ajoutees"], 2)
        self.assertEqual({x["motif"] for x in r["refus"]}, {"FOURNISSEUR_REQUIS", "PREVISION_ABSENTE"})
        bons = d.bons(C)
        self.assertEqual(len(bons), 1)
        b = bons[0]
        self.assertEqual((b.fournisseur_id, b.statut), (f.id, A.BROUILLON))
        l1 = next(l for l in b.lignes if l.asin == "B0AAA00001")
        self.assertEqual((l1.code, l1.unites_lot, l1.prix_unitaire), ("3700000000011", 2, Decimal("10.0")))
        # de nouveau : rien n'est ajouté deux fois, le même brouillon est repris
        r2 = PA.ajouter(d, C, [choix(ops[0]), choix(ops[1])])
        self.assertEqual((r2["ajoutees"], r2["deja"], len(d.bons(C))), (0, 2, 1))
        # un bon envoyé n'est plus repris : nouveau brouillon
        d.enregistrer_bon(C, A.envoyer(d.bons(C)[0]))
        r3 = PA.ajouter(d, C, [choix(ops[0])])
        self.assertEqual((r3["ajoutees"], len(d.bons(C))), (1, 2))

    def test_plan_achat_revente_interdite(self):
        d, f, ops = preparer(revente="INTERDITE")
        r = PA.ajouter(d, C, [choix(ops[0])])
        self.assertEqual([x["motif"] for x in r["refus"]], ["REVENTE_INTERDITE"])

    def test_quantite_proposee(self):
        """[RM-AMZ-126] max(minimum, colisage) arrondi au colisage, puis en lots Amazon."""
        self.assertEqual(PA.quantite_proposee(10, 6, 2), 6)       # 12 unités → 6 lots de 2
        self.assertEqual(PA.quantite_proposee(None, None, 1), 1)
        self.assertEqual(PA.quantite_proposee(5, None, 3), 2)     # 5 unités → 2 lots de 3
        self.assertEqual(PA.quantite_proposee(None, 24, 1), 24)
        d, f, ops = preparer()
        PA.ajouter(d, C, [choix(ops[0]), choix(ops[1], quantite=7)])
        q = {l.asin: l.quantite for l in d.bons(C)[0].lignes}
        self.assertEqual(q, {"B0AAA00001": 6, "B0AAA00002": 7})

    def test_modifier_quantite(self):
        d, f, ops = preparer()
        PA.ajouter(d, C, [choix(ops[1])])
        b = d.bons(C)[0]
        b2 = A.modifier_quantite(b, b.lignes[0].id, 40)
        self.assertEqual(b2.lignes[0].quantite, 40)
        for q in (0, 100001, True, "3"):
            with self.subTest(q=q), self.assertRaises(A.ErreurAchat):
                A.modifier_quantite(b, b.lignes[0].id, q)
        with self.assertRaises(A.ErreurAchat):
            A.modifier_quantite(A.envoyer(b), b.lignes[0].id, 3)

    def test_serialisation_ligne(self):
        d, f, ops = preparer()
        PA.ajouter(d, C, [choix(ops[0])])
        l = d.bons(C)[0].lignes[0]
        self.assertEqual(ligne_depuis_dict(ligne_vers_dict(l)), l)


class TestSociete(unittest.TestCase):
    def test_parametres_societe(self):
        """[RM-AMZ-127] Champs connus, textes bornés, courriel lisible, vides ignorés."""
        p = valider({"societe": {"raison_sociale": " GO-SHOPPING ", "adresse": "1 rue A\n68000 Colmar",
                                 "courriel": "", "telephone": None}})
        self.assertEqual(p.societe, {"raison_sociale": "GO-SHOPPING", "adresse": "1 rue A\n68000 Colmar"})
        for brut, code in [({"inconnu": "x"}, "PARAMETRE_INVALIDE"), ({"raison_sociale": "x" * 301}, "TEXTE_TROP_LONG"),
                           ({"courriel": "pas-un-courriel"}, "COURRIEL_INVALIDE"), ({"adresse": 3}, "PARAMETRE_INVALIDE")]:
            with self.subTest(code=code), self.assertRaises(ParametreInvalide) as e:
                valider({"societe": brut})
            self.assertEqual(e.exception.args[0], code)
        self.assertIn("societe", p.to_dict())


class TestDocument(unittest.TestCase):
    def setUp(self):
        self.d, self.f, ops = preparer()
        PA.ajouter(self.d, C, [choix(ops[0]), choix(ops[1])])
        self.b = self.d.bons(C)[0]
        self.societe = {"raison_sociale": "GO-SHOPPING", "adresse": "1 rue A\n68000 Colmar", "tva_intra": "FR00123"}

    def test_lignes_document(self):
        """[RM-AMZ-128] Quantité et prix en unités du fournisseur ; total du lot inchangé."""
        ls = {l["ref"]: l for l in BD.lignes_document(self.b)}
        bougie = ls["3700000000011"]
        self.assertEqual((bougie["quantite"], bougie["prix"], bougie["total"]), (12, Decimal("5"), Decimal("60.0")))
        self.assertEqual(BD.montant(Decimal("1234.5")), "1 234,50")
        self.assertEqual(BD.prix(Decimal("0.12345")), "0,1235")
        self.assertEqual(BD.prix(Decimal("5")), "5,00")

    def test_document_bon_pdf(self):
        pdf = BD.pdf(self.b, self.f, self.societe, quand=T)
        self.assertTrue(pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF"))
        for attendu in (b"BON DE COMMANDE", self.b.reference.encode(), b"GO-SHOPPING", b"3700000000011",
                        "Désignation".encode("cp1252"), b"60,00", b"14/11/2026"):
            self.assertIn(attendu, pdf)
        self.assertNotIn(b"B0AAA00001", pdf)                  # l'ASIN reste interne
        # xref cohérente : chaque position pointe sur « n 0 obj »
        xref = int(pdf.rsplit(b"startxref\n", 1)[1].split(b"\n")[0])
        entrees = pdf[xref:].split(b"\n")[3:]
        for i, e in enumerate(e for e in entrees if e.endswith(b" n ")):
            pos = int(e[:10])
            self.assertTrue(pdf[pos:].startswith(b"%d 0 obj" % (i + 1)))
        # société incomplète : le document le dit
        self.assertIn("Société à compléter".encode("cp1252"), BD.pdf(self.b, self.f, {}, quand=T))

    def test_document_bon_pdf_plusieurs_pages(self):
        b = self.b
        for i in range(60):
            b = A.ajouter_ligne(b, f"B0Z{i:07d}", "FR", 1, 2, Prevision.creer("EUR", 20, 7, 8), f"Produit {i}", "EUR",
                                code=f"C{i}")
        self.assertIn(b"Page 2 / ", BD.pdf(b, self.f, self.societe, quand=T))

    def test_document_bon_excel(self):
        from openpyxl import load_workbook
        ws = load_workbook(io.BytesIO(BD.excel(self.b, self.f, self.societe, quand=T))).active
        valeurs = [c for row in ws.iter_rows(values_only=True) for c in row if c is not None]
        for attendu in ("BON DE COMMANDE", self.b.reference, "3700000000011", 12, 60.0, "EUR"):
            self.assertIn(attendu, valeurs)
        self.assertNotIn("B0AAA00001", valeurs)


class TestApi(unittest.TestCase):
    def test_api_plan_et_document(self):
        d, f, ops = preparer()
        cl = TestClient(creer_app(d, C, servir_interface=False))
        r = cl.post("/api/plan-achat", json={"lignes": [choix(ops[0]), choix(ops[2])]})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["ajoutees"], 1)
        bid = r.json()["bons"][0]
        b = cl.get(f"/api/bons/{bid}").json()
        self.assertEqual((b["lignes"][0]["code"], b["lignes"][0]["unites_lot"]), ("3700000000011", 2))
        r = cl.patch(f"/api/bons/{bid}/lignes/{b['lignes'][0]['id']}", json={"quantite": 3})
        self.assertEqual(r.json()["lignes"][0]["quantite"], 3)
        self.assertEqual(cl.patch(f"/api/bons/{bid}/lignes/{b['lignes'][0]['id']}", json={"quantite": 0}).status_code, 422)
        r = cl.get(f"/api/bons/{bid}/document.pdf")
        self.assertEqual((r.status_code, r.headers["content-type"]), (200, "application/pdf"))
        self.assertIn("BC-", r.headers["content-disposition"])
        self.assertEqual(cl.get(f"/api/bons/{bid}/document.xlsx").status_code, 200)
        self.assertEqual(cl.get(f"/api/bons/{bid}/document.doc").status_code, 404)
