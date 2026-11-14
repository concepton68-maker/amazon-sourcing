"""Base de fournisseurs [RM-AMZ-100 à 104]."""
import io
import unittest
from decimal import Decimal

from fastapi.testclient import TestClient

from sourcing import achats as A
from sourcing import annuaire as AN
from sourcing.api import creer_app
from sourcing.demo_donnees import construire

CSV = "EAN;Libellé;Prix HT;PCB\n3700000000017;Gourde inox;8,50;6\n3700000000024;Jouet;15,00;4\n3700000000017;doublon;9;1\n;sans code;2;1\n"


def client():
    d, c = construire()
    from sourcing.analyse import Fournisseurs
    from sourcing.providers.demo import FournisseurDemo
    demo = FournisseurDemo()
    return d, c, TestClient(creer_app(d, c, servir_interface=False, traitement_en_fond=False,
                                      fournisseurs=Fournisseurs([demo], demo, demo, demo, demo)))


def deposer(cl, fid, texte=CSV, nom="tarif.csv"):
    return cl.post(f"/api/fournisseurs/{fid}/fichier", files={"fichier": (nom, io.BytesIO(texte.encode()), "text/csv")})


class TestBaseFournisseurs(unittest.TestCase):
    def test_fiche_fournisseur(self):
        """[RM-AMZ-100] Champs contrôlés ; port en décimal ; site en lien ; champ inconnu refusé."""
        f = A.nouveau_fournisseur("c", "Grossiste")
        g = A.modifier_fiche(f, pays="FR", site="https://exemple.fr", categories=["MAISON", "MAISON"], port_unitaire=0.35,
                             revente="AUTORISEE", revente_source="https://exemple.fr/cgv", connexion="FICHIER")
        self.assertEqual((g.port_unitaire, g.categories, g.revente), (Decimal("0.35"), ("MAISON",), "AUTORISEE"))
        for champs, code in (({"revente": "PEUT_ETRE"}, "REVENTE_INVALIDE"), ({"site": "exemple.fr"}, "SITE_INVALIDE"),
                             ({"port_unitaire": -1}, "PORT_INVALIDE"), ({"nom": "x"}, "CHAMP_INCONNU")):
            with self.assertRaises(A.ErreurAchat) as e:
                A.modifier_fiche(f, **champs)
            self.assertEqual(e.exception.args[0], code)

    def test_annuaire(self):
        """[RM-AMZ-101, 104] Chaque entrée dit la revente, sa source et sa vérification ; API indiquée « à brancher »."""
        for r in AN.REFERENCES:
            self.assertIn(r.revente, (AN.AUTORISEE, AN.INTERDITE, AN.A_VERIFIER))
            self.assertIn(r.verification, ("LU", "EXTRAIT", "AUCUNE"))
            if r.revente != AN.A_VERIFIER:
                self.assertTrue(r.source.startswith("https://"), r.code)
            self.assertNotEqual(r.connexion, AN.API, r.code)            # aucune API branchée sans documentation lue
        self.assertEqual(AN.PAR_CODE["QOGITA"].revente, AN.AUTORISEE)
        self.assertEqual(AN.PAR_CODE["ANKORSTORE"].revente, AN.INTERDITE)

    def test_ajout_depuis_annuaire(self):
        """[RM-AMZ-101] Un clic : fiche recopiée ; deux fois : refusé ; marqué « ajouté »."""
        d, c, cl = client()
        r = cl.post("/api/annuaire/QOGITA/ajouter")
        self.assertEqual(r.status_code, 201)
        self.assertEqual((r.json()["revente"], r.json()["reference"], r.json()["pays"]), ("AUTORISEE", "QOGITA", "NL"))
        self.assertEqual(cl.post("/api/annuaire/QOGITA/ajouter").status_code, 409)
        self.assertEqual(cl.post("/api/annuaire/INCONNU/ajouter").status_code, 404)
        self.assertTrue([x for x in cl.get("/api/annuaire").json() if x["code"] == "QOGITA"][0]["ajoute"])

    def test_ajout_groupe_annuaire(self):
        """[RM-AMZ-101] Ajout groupé : déjà présents ignorés ; code inconnu refusé."""
        d, c, cl = client()
        cl.post("/api/annuaire/QOGITA/ajouter")
        r = cl.post("/api/annuaire/ajouter", json={"codes": ["QOGITA", "BIGBUY", "PUCKATOR", "BIGBUY"]}).json()
        self.assertEqual((r["ajoutes"], r["ignores"]), (["BIGBUY", "PUCKATOR"], ["QOGITA"]))
        self.assertEqual(cl.post("/api/annuaire/ajouter", json={"codes": ["ZZZ"]}).status_code, 404)
        self.assertEqual(sum(1 for x in cl.get("/api/annuaire").json() if x["ajoute"]), 3)

    def test_catalogue_fournisseur(self):
        """[RM-AMZ-102] Lignes contrôlées, doublons et rejets comptés ; un nouveau fichier remplace le catalogue."""
        d, c, cl = client()
        fid = cl.post("/api/fournisseurs", json={"nom": "Grossiste T"}).json()["id"]
        f = deposer(cl, fid).json()
        r = cl.post(f"/api/fournisseurs/{fid}/catalogue", json={"fichier_id": f["fichier_id"], "colonnes": f["colonnes"]})
        self.assertEqual((r.json()["lignes"], r.json()["doublons"], len(r.json()["rejets"])), (2, 1, 1))
        cat = cl.get(f"/api/fournisseurs/{fid}/catalogue").json()
        self.assertEqual((cat["lignes"], cat["rejets"], cat["apercu"][0]["prix"]), (2, 2, 8.5))
        f2 = deposer(cl, fid, "EAN;Prix HT\n3700000000024;14\n").json()
        cl.post(f"/api/fournisseurs/{fid}/catalogue", json={"fichier_id": f2["fichier_id"], "colonnes": f2["colonnes"]})
        cat = cl.get(f"/api/fournisseurs/{fid}/catalogue").json()
        self.assertEqual((cat["lignes"], cat["apercu"][0]["code"]), (1, "3700000000024"))
        fiche = [x for x in cl.get("/api/fournisseurs").json() if x["id"] == fid][0]
        self.assertEqual((fiche["connexion"], fiche["catalogue"]["lignes"]), ("FICHIER", 1))

    def test_colonnes_memorisees(self):
        """[RM-AMZ-102] Les en-têtes choisis sont reproposés au fichier suivant, même dans un autre ordre."""
        d, c, cl = client()
        fid = cl.post("/api/fournisseurs", json={"nom": "Grossiste M"}).json()["id"]
        texte = "Réf;Valeur;Nom\n3700000000017;8,5;Gourde\n"
        f = deposer(cl, fid, texte).json()
        self.assertIsNone(f["colonnes"]["prix"])                        # en-tête non reconnu
        cl.post(f"/api/fournisseurs/{fid}/catalogue", json={"fichier_id": f["fichier_id"],
                 "colonnes": {"code": 0, "prix": 1, "designation": 2}})
        f2 = deposer(cl, fid, "Nom;Réf;Valeur\nGourde;3700000000017;8,5\n").json()
        self.assertEqual((f2["colonnes"]["code"], f2["colonnes"]["prix"], f2["colonnes"]["designation"]), (1, 2, 0))

    def test_analyse_catalogue_fournisseur(self):
        """[RM-AMZ-103] Analyse du catalogue enregistré avec le port du fournisseur."""
        d, c, cl = client()
        fid = cl.post("/api/fournisseurs", json={"nom": "Grossiste A2"}).json()["id"]
        cl.put(f"/api/fournisseurs/{fid}", json={"port_unitaire": 0.5})
        self.assertEqual(cl.post(f"/api/fournisseurs/{fid}/analyse", json={}).status_code, 404)   # pas de catalogue
        f = deposer(cl, fid).json()
        cl.post(f"/api/fournisseurs/{fid}/catalogue", json={"fichier_id": f["fichier_id"], "colonnes": f["colonnes"]})
        tid = cl.post(f"/api/fournisseurs/{fid}/analyse", json={}).json()["traitement_id"]
        s = cl.get(f"/api/sourcing/traitements/{tid}").json()
        self.assertEqual(s["statut"], "TERMINE")
        sans = cl.post("/api/analyse", json={"code": "3700000000017", "prix_achat": 8.5}).json()["analyses"][0]
        ligne = [x for x in s["resultats"] if x["code"] == "3700000000017"][0]
        self.assertAlmostEqual(sans["rentabilite"]["profit"] - ligne["profit"], 0.5, places=2)   # port du fournisseur

    def test_revente_interdite_bloque_analyse(self):
        """[RM-AMZ-100] Revente sur Amazon interdite : fiche gardée, catalogue non analysé."""
        d, c, cl = client()
        fid = cl.post("/api/annuaire/ANKORSTORE/ajouter").json()["id"]
        f = deposer(cl, fid).json()
        cl.post(f"/api/fournisseurs/{fid}/catalogue", json={"fichier_id": f["fichier_id"], "colonnes": f["colonnes"]})
        r = cl.post(f"/api/fournisseurs/{fid}/analyse", json={})
        self.assertEqual((r.status_code, r.json()["detail"]), (409, "REVENTE_INTERDITE"))


if __name__ == "__main__":
    unittest.main()
