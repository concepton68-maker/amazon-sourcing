"""Conformité Europe [RM-AMZ-060 à 067] : l'outil range ce que le vendeur déclare, cite le texte, signale ce qui manque."""
import unittest
from datetime import date

from fastapi.testclient import TestClient

from sourcing import conformite as CF
from sourcing.api import creer_app
from sourcing.demo_donnees import construire
from sourcing.lots import Lot, Prevision
from sourcing.stock import PhotoStock

C = "00000000-0000-4000-8000-0000000000aa"
FAB = {"nom": "F", "adresse": "1 rue X, Paris", "courriel": "f@x.fr"}
COMPLET = {"fabricant": FAB, "fabricant_hors_ue": False, "avertissements_ok": True, "producteur": "OUI",
           "filieres": ["EMBALLAGES"], "triman_ok": True, "marquage_ce": "NON_CONCERNE"}


def lot(asin, mp):
    return Lot(C, asin, mp, 10, date(2026, 9, 1), Prevision.creer("EUR", 20, 8, 8), designation="Produit " + asin)


def codes(al):
    return [a.code for a in al]


class TestConformite(unittest.TestCase):
    def test_champ_ue(self):
        """[RM-AMZ-060] Hors UE : aucune vérification, statut « non couvert », jamais « conforme »."""
        (l,) = CF.verifier([lot("B0US", "US")], [], {}, [])
        self.assertEqual((l.statut, l.alertes, l.couvert), ("NON_COUVERT", (), False))
        (l,) = CF.verifier([lot("B0UK", "UK")], [PhotoStock("FR", "S", "B0UK", "Stock FR", 3, 0)], {}, [])
        self.assertEqual((l.places, l.statut), (("FR", "UK"), "A_COMPLETER"))
        self.assertEqual(CF.PLACES_UE, ("DE", "FR", "IT", "ES", "NL", "BE", "IE", "SE", "PL"))
        self.assertNotIn("CONFORME", {"NON_COUVERT", "A_COMPLETER", "RIEN_DE_SIGNALE"})

    def test_enregistrements(self):
        """[RM-AMZ-061] Pays UE, filière connue, numéro 1-64 ; AUTRE exige un intitulé ; LUCID ≠ 13 chiffres → avertissement."""
        e = CF.nouvel_enregistrement("FR", "EEE", " FR123 ", intitule="ignoré")
        self.assertEqual((e.numero, e.intitule, e.cle), ("FR123", None, "FR:EEE:"))
        for args, code in ((("UK", "EEE", "1"), "PAYS_HORS_CHAMP"), (("FR", "JOUETS", "1"), "FILIERE_INCONNUE"),
                           (("FR", "EEE", " "), "CHAMP_OBLIGATOIRE"), (("FR", "EEE", "x" * 65), "TROP_LONG"),
                           (("FR", "AUTRE", "1"), "CHAMP_OBLIGATOIRE")):
            with self.subTest(args=args):
                with self.assertRaises(CF.SaisieInvalide) as x:
                    CF.nouvel_enregistrement(*args)
                self.assertEqual(x.exception.args[0], code)
        self.assertEqual(CF.nouvel_enregistrement("FR", "AUTRE", "1", intitule="Jouets").cle, "FR:AUTRE:Jouets")
        self.assertEqual(codes(CF.avertissements_enregistrement(CF.nouvel_enregistrement("DE", "EMBALLAGES", "DE123"))),
                         ["C_LUCID_FORMAT"])
        self.assertEqual(CF.avertissements_enregistrement(CF.nouvel_enregistrement("DE", "EMBALLAGES", "1234567890123")), [])
        self.assertEqual(CF.avertissements_enregistrement(CF.nouvel_enregistrement("DE", "EEE", "DE123")), [])

    def test_fiche_rsgp(self):
        """[RM-AMZ-062] Fiche validée : champ inconnu, courriel mal formé, valeur hors liste refusés."""
        f = CF.valider_fiche("B0X", COMPLET)
        self.assertTrue(f.fabricant.complete())
        self.assertEqual(CF.fiche_depuis_dict("B0X", f.to_dict()), f)
        for brut, champ in (({"inconnu": 1}, "fiche"), ({"fabricant": {"courriel": "pas-un-courriel"}}, "fabricant.courriel"),
                            ({"producteur": "PEUT_ETRE"}, "producteur"), ({"marquage_ce": "OUI?"}, "marquage_ce"),
                            ({"fabricant_hors_ue": "oui"}, "fabricant_hors_ue"), ({"filieres": ["JOUETS"]}, "filieres"),
                            ({"numeros_producteur": {"UK:EEE": "1"}}, "numeros_producteur.UK:EEE")):
            with self.subTest(brut=brut):
                with self.assertRaises(CF.SaisieInvalide) as x:
                    CF.valider_fiche("B0X", brut)
                self.assertEqual(x.exception.args[1], champ)

    def test_alertes_rsgp(self):
        """[RM-AMZ-063] Fabricant incomplet, responsable UE manquant si fabricant hors UE, avertissements à confirmer."""
        enregs = [CF.nouvel_enregistrement("FR", "EMBALLAGES", "IDU1")]
        self.assertEqual(CF.alertes(CF.valider_fiche("B0X", COMPLET), "B0X", ["FR"], enregs), [])
        f = CF.valider_fiche("B0X", {**COMPLET, "fabricant": {"nom": "F"}, "fabricant_hors_ue": True, "avertissements_ok": False})
        al = CF.alertes(f, "B0X", ["FR"], enregs)
        self.assertEqual(codes(al), ["C_FABRICANT_INCOMPLET", "C_RESPONSABLE_MANQUANT", "C_AVERTISSEMENTS_A_CONFIRMER"])
        self.assertEqual([a.params["texte"] for a in al], ["RSGP_19", "RSGP_16", "RSGP_19"])
        f = CF.valider_fiche("B0X", {**COMPLET, "fabricant_hors_ue": True,
                                     "responsable": {"nom": "R", "adresse": "Lyon", "courriel": "r@x.fr"}})
        self.assertEqual(CF.alertes(f, "B0X", ["FR"], enregs), [])
        self.assertIn("C_ORIGINE_FABRICANT_A_PRECISER",
                      codes(CF.alertes(CF.valider_fiche("B0X", {**COMPLET, "fabricant_hors_ue": None}), "B0X", ["FR"], enregs)))

    def test_role_et_filieres(self):
        """[RM-AMZ-064] Rien n'est supposé : rôle à déterminer, filières à déclarer, aucun numéro exigé avant."""
        al = codes(CF.alertes(None, "B0X", ["FR", "DE"], []))
        self.assertIn("C_ROLE_A_DETERMINER", al)
        self.assertIn("C_FILIERES_A_DECLARER", al)
        self.assertNotIn("C_ENREGISTREMENT_MANQUANT", al)
        al = codes(CF.alertes(CF.valider_fiche("B0X", {**COMPLET, "producteur": "A_DETERMINER"}), "B0X", ["FR"], []))
        self.assertEqual(al, ["C_ROLE_A_DETERMINER"])

    def test_numero_attendu(self):
        """[RM-AMZ-065] Numéro par (place UE, filière) : compte si producteur, fiche sinon ; texte cité ; pays non recherché."""
        f = CF.valider_fiche("B0X", {**COMPLET, "filieres": ["EMBALLAGES", "EEE", "PILES"], "marquage_ce": "OUI"})
        al = CF.alertes(f, "B0X", ["FR", "DE", "IT", "UK"], [CF.nouvel_enregistrement("FR", "EMBALLAGES", "1")])
        manq = {(a.params["pays"], a.params["filiere"]): a.params["texte"] for a in al if a.code == "C_ENREGISTREMENT_MANQUANT"}
        self.assertEqual(manq, {("FR", "EEE"): "FR_L541_10_13", ("FR", "PILES"): "FR_L541_10_13",
                                ("DE", "EMBALLAGES"): "DE_VERPACKDG_6", ("DE", "EEE"): "DE_ELEKTROG_6",
                                ("DE", "PILES"): "DE_BATTDG_4", ("IT", "EMBALLAGES"): "UE_EMB_44",
                                ("IT", "PILES"): "UE_PILES_55"})
        nv = [(a.params["pays"], a.params["filiere"]) for a in al if a.code == "C_OBLIGATION_NON_VERIFIEE"]
        self.assertEqual(nv, [("IT", "EEE")])
        # pas producteur : le numéro du producteur, noté sur la fiche
        f2 = CF.valider_fiche("B0X", {**COMPLET, "producteur": "NON", "numeros_producteur": {"FR:EMBALLAGES": "IDU-FOURN"}})
        self.assertEqual(CF.alertes(f2, "B0X", ["FR"], []), [])
        f3 = CF.valider_fiche("B0X", {**COMPLET, "producteur": "NON"})
        (a,) = CF.alertes(f3, "B0X", ["FR"], [CF.nouvel_enregistrement("FR", "EMBALLAGES", "1")])
        self.assertEqual((a.code, a.params["qui"]), ("C_ENREGISTREMENT_MANQUANT", "producteur"))
        # AUTRE : l'intitulé doit correspondre
        f4 = CF.valider_fiche("B0X", {**COMPLET, "filieres": ["AUTRE"], "intitule_autre": "Jouets"})
        self.assertEqual(CF.alertes(f4, "B0X", ["FR"], [CF.nouvel_enregistrement("FR", "AUTRE", "1", intitule="jouets")]), [])
        self.assertEqual(codes(CF.alertes(f4, "B0X", ["FR"], [CF.nouvel_enregistrement("FR", "AUTRE", "1", intitule="Meubles")])),
                         ["C_ENREGISTREMENT_MANQUANT"])

    def test_triman_et_ce(self):
        """[RM-AMZ-066] Triman à confirmer sur FR avec filière ; CE à déterminer."""
        enregs = [CF.nouvel_enregistrement("FR", "EMBALLAGES", "1"), CF.nouvel_enregistrement("DE", "EMBALLAGES", "1234567890123")]
        f = CF.valider_fiche("B0X", {**COMPLET, "triman_ok": False, "marquage_ce": "A_DETERMINER"})
        self.assertEqual(codes(CF.alertes(f, "B0X", ["FR"], enregs)), ["C_TRIMAN_A_CONFIRMER", "C_CE_A_DETERMINER"])
        self.assertEqual(codes(CF.alertes(f, "B0X", ["DE"], enregs)), ["C_CE_A_DETERMINER"])

    def test_bibliotheque(self):
        """[RM-AMZ-067] Chaque texte cité existe dans la bibliothèque avec lien et état ; jamais « conforme »."""
        cites = {CF.texte_numero(p, f) for p in CF.PLACES_UE for f in CF.FILIERES} - {None}
        cites |= {"RSGP_19", "RSGP_16", "FR_L541_9_3", "CE_30", "AMAZON_DE_EPR"}
        for t in cites:
            with self.subTest(texte=t):
                self.assertIn(t, CF.TEXTES)
                self.assertTrue(CF.TEXTES[t].url.startswith("https://"))
        self.assertEqual(CF.DATE_LECTURE, "2026-11-12")
        (l,) = CF.verifier([lot("B0X", "FR")], [], {"B0X": CF.valider_fiche("B0X", COMPLET)},
                           [CF.nouvel_enregistrement("FR", "EMBALLAGES", "1")])
        self.assertEqual(l.statut, "RIEN_DE_SIGNALE")

    def test_api_conformite_demo(self):
        """API : produits de la démo, enregistrement, fiche, suppression."""
        d, c = construire()
        cl = TestClient(creer_app(d, c, servir_interface=False))
        j = cl.get("/api/conformite").json()
        statuts = {p["asin"]: p["statut"] for p in j["produits"]}
        self.assertEqual(statuts["B0DEMO0001"], "RIEN_DE_SIGNALE")
        self.assertEqual(statuts["B0DEMO0003"], "A_COMPLETER")
        self.assertEqual(j["compteurs"]["rien_de_signale"], 1)
        self.assertTrue(all(t["url"].startswith("https://") for t in j["textes"]))
        r = cl.post("/api/conformite/enregistrements", json={"pays": "DE", "filiere": "EEE", "numero": "DE 12345678"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["texte"], "DE_ELEKTROG_6")
        self.assertEqual(cl.post("/api/conformite/enregistrements", json={"pays": "US", "filiere": "EEE", "numero": "1"})
                         .json()["detail"], {"code": "PAYS_HORS_CHAMP", "champ": "pays"})
        p3 = next(p for p in cl.get("/api/conformite").json()["produits"] if p["asin"] == "B0DEMO0003")
        self.assertNotIn(("DE", "EEE"), [(a["params"].get("pays"), a["params"].get("filiere")) for a in p3["alertes"]])
        fiche = {**p3["fiche"], "avertissements_ok": True}
        fiche.pop("asin")
        self.assertEqual(cl.put("/api/conformite/fiches/B0DEMO0003", json=fiche).json()["avertissements_ok"], True)
        self.assertEqual(cl.put("/api/conformite/fiches/B0DEMO0003", json={"x": 1}).status_code, 422)
        self.assertEqual(cl.delete("/api/conformite/enregistrements/DE:EEE:").json(), {"supprime": "DE:EEE:"})
        self.assertEqual(cl.delete("/api/conformite/enregistrements/DE:EEE:").status_code, 404)


if __name__ == "__main__":
    unittest.main()
