"""Messagerie Microsoft : connexion, envoi du bon, traces [RM-AMZ-129 à 131]."""
import json
import os
import pathlib
import re
import unittest
import urllib.parse
from datetime import datetime, timedelta, timezone
from unittest import mock

import requests
from fastapi.testclient import TestClient

from sourcing import achats as A
from sourcing import messagerie as MS
from sourcing import plan_achat as PA
from sourcing.api import creer_app
from tests.test_plan_achat import C, choix, preparer

CLE = "11" * 32


class Rep:
    def __init__(self, status, corps=None, entetes=None):
        self.status_code, self._j, self.headers = status, corps, entetes or {}
        self.content = b"" if corps is None else json.dumps(corps).encode()

    def json(self):
        return self._j


class FauxMicrosoft:
    """Session requests factice : jeton, /me, sendMail scénarisés."""

    def __init__(self, envois=None, jeton=None):
        self.envois = list(envois or [Rep(202)])
        self.jeton = jeton or Rep(200, {"access_token": "acces", "refresh_token": "neuf", "expires_in": 3599,
                                        "scope": "https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/User.Read"})
        self.appels = []

    def post(self, url, data=None, json=None, headers=None, timeout=None):
        self.appels.append(("POST", url, data, json))
        if url.endswith("/token"):
            if isinstance(self.jeton, Exception):
                raise self.jeton
            return self.jeton
        r = self.envois.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def get(self, url, headers=None, timeout=None):
        self.appels.append(("GET", url, None, None))
        return Rep(200, {"mail": None, "userPrincipalName": "sam@outlook.fr", "displayName": "Sam"})


class TestConnexion(unittest.TestCase):
    def test_url_autorisation(self):
        """[RM-AMZ-129] Code + PKCE S256, point « common », adresse de retour exacte."""
        u = MS.url_autorisation("id-app", "https://vente.example/api/messagerie/microsoft/retour", "st", "verif")
        p = urllib.parse.urlparse(u)
        q = dict(urllib.parse.parse_qsl(p.query))
        self.assertEqual(p.netloc + p.path, "login.microsoftonline.com/common/oauth2/v2.0/authorize")
        self.assertEqual((q["response_type"], q["code_challenge_method"], q["state"]), ("code", "S256", "st"))
        self.assertEqual(q["code_challenge"], MS.defi("verif"))
        self.assertEqual(q["redirect_uri"], "https://vente.example/api/messagerie/microsoft/retour")

    def test_portees_envoi_seul(self):
        """[RM-AMZ-129] Envoi seul : aucune portée de lecture ni d'écriture de la boîte dans le code."""
        self.assertEqual(set(MS.PORTEES.split()), {"openid", "email", "profile", "offline_access",
                                                   "https://graph.microsoft.com/User.Read",
                                                   "https://graph.microsoft.com/Mail.Send"})
        racine = pathlib.Path(MS.__file__).parent
        for f in racine.rglob("*.py"):
            self.assertIsNone(re.search(r"Mail\.Read|Mail\.ReadWrite", f.read_text()), f.name)

    def test_state_usage_unique(self):
        e = MS.Etats()
        t0 = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)
        s, v = e.creer(C, t0)
        with self.assertRaises(MS.ErreurMessagerie):
            e.consommer(s, "00000000-0000-4000-8000-0000000000bb", t0)       # autre compte
        s, v = e.creer(C, t0)
        self.assertEqual(e.consommer(s, C, t0 + timedelta(minutes=9)), v)
        with self.assertRaises(MS.ErreurMessagerie):
            e.consommer(s, C, t0)                                             # déjà utilisé
        s, _ = e.creer(C, t0)
        with self.assertRaises(MS.ErreurMessagerie):
            e.consommer(s, C, t0 + timedelta(minutes=11))                     # expiré

    def test_portee_refusee(self):
        f = FauxMicrosoft(jeton=Rep(200, {"access_token": "a", "refresh_token": "r", "scope": "User.Read"}))
        with self.assertRaises(MS.ErreurMessagerie) as e:
            MS.Microsoft("i", "s", f).echanger("code", "r", "v")
        self.assertEqual(e.exception.args[0], "PORTEE")


@mock.patch.dict(os.environ, {"AMZ_CLE_CHIFFREMENT": CLE, "AMZ_URL_PUBLIQUE": "https://vente.example"})
class TestApi(unittest.TestCase):
    def preparer(self, faux=None):
        self.d, self.f, ops = preparer()
        PA.ajouter(self.d, C, [choix(ops[0])])
        self.bon = self.d.bons(C)[0]
        self.faux = faux or FauxMicrosoft()
        self.cl = TestClient(creer_app(self.d, C, servir_interface=False,
                                       fabrique_microsoft=lambda i, s: MS.Microsoft(i, s, self.faux, attendre=lambda _: None)),
                             follow_redirects=False)
        self.assertEqual(self.cl.put("/api/connexions/MICROSOFT", json={"client_id": "id-app", "client_secret": "secret"}).status_code, 200)

    def connecter(self):
        u = self.cl.post("/api/messagerie/microsoft/demarrer").json()["url"]
        state = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(u).query))["state"]
        return self.cl.get(f"/api/messagerie/microsoft/retour?code=abc&state={state}")

    def test_retour_connexion(self):
        """[RM-AMZ-129] Jeton chiffré, adresse lue (userPrincipalName à défaut de mail), jamais rendu."""
        self.preparer()
        self.assertIsNone(self.cl.get("/api/messagerie").json()["connexion"])
        r = self.connecter()
        self.assertEqual((r.status_code, r.headers["location"]), (303, "/?messagerie=ok#parametres/connexions"))
        e = self.cl.get("/api/messagerie").json()
        self.assertEqual((e["connexion"]["adresse"], e["connexion"]["etat"]), ("sam@outlook.fr", "CONNECTEE"))
        self.assertEqual(e["adresse_retour"], "https://vente.example/api/messagerie/microsoft/retour")
        self.assertNotIn("neuf", json.dumps(e))
        echange = next(a for a in self.faux.appels if a[1].endswith("/token"))[2]
        self.assertEqual((echange["grant_type"], echange["redirect_uri"]),
                         ("authorization_code", "https://vente.example/api/messagerie/microsoft/retour"))
        self.assertIn("code_verifier", echange)
        # state rejoué : refusé
        r2 = self.cl.get("/api/messagerie/microsoft/retour?code=abc&state=faux")
        self.assertIn("cause=expiree", r2.headers["location"])
        self.assertTrue(self.cl.delete("/api/messagerie").json()["retiree"])

    def test_envoi_bon_messagerie(self):
        """[RM-AMZ-130] Aperçu puis envoi : 202 → tentative ENVOYE, bon envoyé, PDF joint, répondre à la Société."""
        self.preparer()
        self.cl.put("/api/parametres", json={"societe": {"raison_sociale": "GO-SHOPPING", "courriel": "achats@go.example"}})
        self.connecter()
        ap = self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie/apercu").json()
        self.assertEqual((ap["a"], ap["expediteur"], ap["repondre_a"]), ("ventes@grossiste.example", "sam@outlook.fr", "achats@go.example"))
        self.assertIn(self.bon.reference, ap["objet"])
        r = self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie", json={"apres": 0}).json()
        self.assertEqual((r["tentative"]["etat"], r["bon"]["statut"]), ("ENVOYE", "ENVOYE"))
        envoi = [a for a in self.faux.appels if a[1].endswith("/me/sendMail")][-1][3]
        self.assertTrue(envoi["saveToSentItems"])
        m = envoi["message"]
        self.assertEqual(m["attachments"][0]["contentType"], "application/pdf")
        self.assertEqual(m["replyTo"][0]["emailAddress"]["address"], "achats@go.example")
        # l'écran qui n'a pas vu la dernière tentative ne renvoie rien
        r2 = self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie", json={"apres": 0}).json()
        self.assertTrue(r2["rejoue"])
        self.assertEqual(len(self.cl.get(f"/api/bons/{self.bon.id}/envois-messagerie").json()), 1)

    def test_envoi_refus(self):
        """[RM-AMZ-130] Non connectée, sans courriel, trop gros : refus, rien n'est envoyé."""
        self.preparer()
        self.assertEqual(self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie/apercu").json()["detail"], "NON_CONNECTEE")
        self.connecter()
        self.d.enregistrer_fournisseur(C, A.modifier_fiche(self.f, courriel=None))
        self.assertEqual(self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie", json={"apres": 0}).json()["detail"], "SANS_COURRIEL")
        self.d.enregistrer_fournisseur(C, self.f)
        with mock.patch("sourcing.bon_document.pdf", return_value=b"x" * MS.PIECE_MAX):
            self.assertEqual(self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie", json={"apres": 0}).json()["detail"], "TROP_GROS")
        self.assertFalse([a for a in self.faux.appels if a[1].endswith("/me/sendMail")])

    def test_incertain_jamais_reessaye(self):
        """[RM-AMZ-131] Délai dépassé : INCERTAIN, un seul appel d'envoi, bon resté brouillon."""
        self.preparer(FauxMicrosoft(envois=[requests.Timeout()]))
        self.connecter()
        r = self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie", json={"apres": 0}).json()
        self.assertEqual((r["tentative"]["etat"], r["bon"]["statut"]), ("INCERTAIN", "BROUILLON"))
        self.assertEqual(len([a for a in self.faux.appels if a[1].endswith("/me/sendMail")]), 1)
        f2 = FauxMicrosoft(envois=[Rep(500)])
        self.assertEqual(MS.Microsoft("i", "s", f2).envoyer("a", {})[0], "INCERTAIN")

    def test_reprise_429(self):
        """[RM-AMZ-131] 429 / 503 : repris deux fois au plus, après Retry-After (5 s au plus)."""
        attentes = []
        f = FauxMicrosoft(envois=[Rep(429, None, {"Retry-After": "30"}), Rep(503), Rep(202)])
        self.assertEqual(MS.Microsoft("i", "s", f, attendre=attentes.append).envoyer("a", {})[0], "ENVOYE")
        self.assertEqual(attentes, [5.0, 1.0])
        f = FauxMicrosoft(envois=[Rep(429), Rep(429), Rep(429)])
        self.assertEqual(MS.Microsoft("i", "s", f, attendre=lambda _: None).envoyer("a", {})[:2], ("ECHEC", "OCCUPE"))
        f = FauxMicrosoft(envois=[requests.ConnectionError()])
        self.assertEqual(MS.Microsoft("i", "s", f).envoyer("a", {})[:2], ("ECHEC", "INJOIGNABLE"))

    def test_a_reconnecter(self):
        """[RM-AMZ-131] Jeton d'actualisation refusé : messagerie « à reconnecter », rien n'est parti."""
        self.preparer()
        self.connecter()
        self.faux.jeton = Rep(400, {"error": "invalid_grant"})
        r = self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie", json={"apres": 0}).json()
        self.assertEqual((r["tentative"]["etat"], r["tentative"]["cause"]), ("ECHEC", "A_RECONNECTER"))
        self.assertEqual(self.cl.get("/api/messagerie").json()["connexion"]["etat"], "A_RECONNECTER")
        self.assertEqual(self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie/apercu").json()["detail"], "NON_CONNECTEE")

    def test_traces_ajout_seul(self):
        """[RM-AMZ-131] Une génération par tentative ; une génération déjà prise est refusée."""
        self.preparer(FauxMicrosoft(envois=[Rep(400), Rep(202)]))
        self.connecter()
        r1 = self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie", json={"apres": 0}).json()
        self.assertEqual(r1["tentative"]["etat"], "ECHEC")
        r2 = self.cl.post(f"/api/bons/{self.bon.id}/envoi-messagerie", json={"apres": 1}).json()
        self.assertEqual((r2["tentative"]["generation"], r2["tentative"]["etat"]), (2, "ENVOYE"))
        t = self.d.envois_bon(C, self.bon.id)[0]
        with self.assertRaises(ValueError):
            self.d.ajouter_envoi_bon(C, t)
        self.assertEqual(len(t.empreinte), 64)


class TestAdresseRetour(unittest.TestCase):
    @mock.patch.dict(os.environ, {"AMZ_CLE_CHIFFREMENT": CLE}, clear=False)
    def test_adresse_retour_https(self):
        """[RM-AMZ-129] Hors poste local, l'adresse de retour est en HTTPS (exigence Microsoft)."""
        os.environ.pop("AMZ_URL_PUBLIQUE", None)
        d, _, _ = preparer()
        cl = TestClient(creer_app(d, C, servir_interface=False))
        self.assertEqual(cl.get("/api/messagerie", headers={"host": "vente.concepton.fr"}).json()["adresse_retour"],
                         "https://vente.concepton.fr/api/messagerie/microsoft/retour")
        self.assertEqual(cl.get("/api/messagerie", headers={"host": "127.0.0.1:8820"}).json()["adresse_retour"],
                         "http://127.0.0.1:8820/api/messagerie/microsoft/retour")
