"""Connexion des utilisateurs [RM-AMZ-036 à 041]."""
import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from sourcing.analyse import Fournisseurs
from sourcing.api import COOKIE, creer_app
import base64

from sourcing.auth import (CHANGER_MDP, CODE, COMPLET, ENROLER, Authentification, ErreurAuth, StockAuthMemoire,
                           pas_de, totp)
from sourcing.cli import creer_utilisateur
from sourcing.depot import DepotMemoire
from sourcing.providers.demo import FournisseurDemo

MDP = "un-mot-de-passe-solide"
H = {"x-syllig-vente": "1"}
T0 = datetime(2026, 11, 12, 10, tzinfo=timezone.utc)
CLE = bytes.fromhex("22" * 32)


def b32(secret: str) -> bytes:
    return base64.b32decode(secret + "=" * (-len(secret) % 8))


def demo():
    d = FournisseurDemo()
    return Fournisseurs([d], d, d, d, d)


class Base(unittest.TestCase):
    def setUp(self):
        self.depot, self.stock = DepotMemoire(), StockAuthMemoire()
        self.auth = Authentification(self.stock, cle=lambda: CLE)
        self.secrets = {}
        self.ca, _ = creer_utilisateur(self.depot, self.auth, "Compte A", "a@exemple.fr", MDP)
        self.cb, _ = creer_utilisateur(self.depot, self.auth, "Compte B", "B@Exemple.fr", MDP)
        self.app = creer_app(self.depot, servir_interface=False, fournisseurs=demo(), auth=self.auth,
                             traitement_en_fond=False)

    def client(self, courriel=None):
        cl = TestClient(self.app, base_url="https://testserver")
        if courriel:
            r = cl.post("/api/session", json={"courriel": courriel, "mot_de_passe": MDP}, headers=H)
            self.assertEqual(r.status_code, 200, r.text)
            p = pas_de(datetime.now(timezone.utc))
            if r.json()["etape"] == ENROLER:                                  # [RM-AMZ-076] première connexion
                secret = b32(cl.post("/api/session/enrolement", headers=H).json()["secret"])
                self.secrets[courriel.lower()] = secret
                r = cl.post("/api/session/enrolement/confirmer", json={"code": totp(secret, p)}, headers=H)
            else:
                r = cl.post("/api/session/code", json={"code": totp(self.secrets[courriel.lower()], p + 1)}, headers=H)
            self.assertEqual(r.status_code, 200, r.text)
        return cl


class TestMotsDePasse(Base):
    def test_mot_de_passe_empreinte(self):
        """[RM-AMZ-036] 12 caractères minimum ; seule une empreinte Argon2id est gardée."""
        with self.assertRaises(ErreurAuth) as e:
            self.auth.creer_utilisateur(self.ca, "c@exemple.fr", "court")
        self.assertEqual(e.exception.args[0], "MOT_DE_PASSE_TROP_COURT")
        u = self.stock.par_courriel("a@exemple.fr")
        self.assertTrue(u.empreinte.startswith("$argon2id$"))
        self.assertNotIn(MDP, u.empreinte)
        with self.assertRaises(ErreurAuth):
            self.auth.creer_utilisateur(self.ca, "A@EXEMPLE.FR ", MDP)       # courriel normé : déjà utilisé

    def test_connexion_et_blocage(self):
        """[RM-AMZ-037] Même erreur pour courriel inconnu ou mot de passe faux ; blocage 15 min après 5 échecs."""
        for courriel in ("a@exemple.fr", "inconnu@exemple.fr"):
            with self.assertRaises(ErreurAuth) as e:
                self.auth.connecter(courriel, "mauvais-mot-de-passe", T0)
            self.assertEqual(e.exception.args[0], "IDENTIFIANTS_INVALIDES")
        for _ in range(3):
            with self.assertRaises(ErreurAuth):
                self.auth.connecter("a@exemple.fr", "mauvais-mot-de-passe", T0)
        with self.assertRaises(ErreurAuth) as e:
            self.auth.connecter("a@exemple.fr", "mauvais-mot-de-passe", T0)   # 5e échec
        self.assertEqual(e.exception.args[0], "TROP_D_ESSAIS")
        with self.assertRaises(ErreurAuth) as e:
            self.auth.connecter("a@exemple.fr", MDP, T0 + timedelta(minutes=14))
        self.assertEqual(e.exception.args[0], "TROP_D_ESSAIS")
        jeton, s = self.auth.connecter("a@exemple.fr", MDP, T0 + timedelta(minutes=16))
        self.assertEqual(s.compte_id, self.ca)

    def test_session_cookie_et_expiration(self):
        """[RM-AMZ-038] Cookie HttpOnly, SameSite=Lax, Secure, sans Domain ; 12 h d'inactivité, 30 j au plus."""
        r = TestClient(self.app, base_url="https://testserver").post(
            "/api/session", json={"courriel": "a@exemple.fr", "mot_de_passe": MDP}, headers=H)
        cookie = r.headers["set-cookie"].lower()
        for attendu in ("httponly", "samesite=lax", "secure", "path=/"):
            self.assertIn(attendu, cookie)
        self.assertNotIn("domain", cookie)
        jeton, _ = self.auth.connecter("a@exemple.fr", MDP, T0)
        self.assertNotIn(jeton, str(self.stock.sessions))                  # seule l'empreinte est gardée
        self.assertIsNotNone(self.auth.session_valide(jeton, T0 + timedelta(hours=11)))
        self.assertIsNone(self.auth.session_valide(jeton, T0 + timedelta(hours=11 + 13)))
        jeton, _ = self.auth.connecter("a@exemple.fr", MDP, T0)
        for h in range(1, 30 * 2 + 3):                                      # active toutes les 12 h, mais > 30 j
            ok = self.auth.session_valide(jeton, T0 + timedelta(hours=12 * h - 1))
        self.assertIsNone(ok)
        cl = self.client("a@exemple.fr")
        self.assertEqual(cl.delete("/api/session", headers=H).status_code, 200)
        self.assertEqual(cl.get("/api/lots").status_code, 401)


class TestSecuriteAmazon(Base):
    def test_politique_mot_de_passe(self):
        """[RM-AMZ-075] 12 caractères dont un spécial ; ancien mot de passe non conforme : changement imposé."""
        with self.assertRaises(ErreurAuth) as e:
            self.auth.creer_utilisateur(self.ca, "c@exemple.fr", "motdepasse1234")
        self.assertEqual(e.exception.args[0], "MOT_DE_PASSE_SANS_CARACTERE_SPECIAL")
        u = self.stock.par_courriel("a@exemple.fr")
        self.stock.enregistrer_utilisateur(u.__class__(**{**u.__dict__, "empreinte":
                                                           __import__("argon2").PasswordHasher().hash("ancienmotdepasse")}))
        jeton, s = self.auth.connecter("a@exemple.fr", "ancienmotdepasse", T0)
        self.assertEqual(s.niveau, CHANGER_MDP)
        for mauvais, code in (("ancienmotdepasse", "MOT_DE_PASSE_SANS_CARACTERE_SPECIAL"), ("court!", "MOT_DE_PASSE_TROP_COURT")):
            with self.assertRaises(ErreurAuth) as e:
                self.auth.changer_mot_de_passe(s, mauvais, T0)
            self.assertEqual(e.exception.args[0], code)
        self.assertEqual(self.auth.changer_mot_de_passe(s, "nouveau-mot-de-passe!", T0), ENROLER)

    def test_expiration_mot_de_passe(self):
        """[RM-AMZ-075] Au-delà de 365 jours, changement imposé ; le même mot de passe est refusé."""
        u = self.stock.par_courriel("a@exemple.fr")
        self.stock.enregistrer_utilisateur(u.__class__(**{**u.__dict__, "mdp_change_le": T0 - timedelta(days=366)}))
        _, s = self.auth.connecter("a@exemple.fr", MDP, T0)
        self.assertEqual(s.niveau, CHANGER_MDP)
        with self.assertRaises(ErreurAuth) as e:
            self.auth.changer_mot_de_passe(s, MDP, T0)
        self.assertEqual(e.exception.args[0], "MOT_DE_PASSE_IDENTIQUE")
        self.auth.changer_mot_de_passe(s, "un-autre-mot-de-passe", T0)
        _, s = self.auth.connecter("a@exemple.fr", "un-autre-mot-de-passe", T0 + timedelta(days=364))
        self.assertEqual(s.niveau, ENROLER)

    def test_totp(self):
        """[RM-AMZ-076] Vecteur de la RFC 6238 (SHA-1, T=59 s) ; tolérance ±1 pas ; un code ne sert qu'une fois."""
        self.assertEqual(totp(b"12345678901234567890", 59 // 30), "287082")   # 94287082 sur 8 chiffres → 6 derniers
        _, s = self.auth.connecter("a@exemple.fr", MDP, T0)
        secret, uri = self.auth.debuter_enrolement(s)
        self.assertTrue(uri.startswith("otpauth://totp/"))
        self.assertNotIn(secret.hex(), str(self.stock.par_courriel("a@exemple.fr").totp_chiffre))   # gardé chiffré
        codes = self.auth.confirmer_enrolement(s, totp(secret, pas_de(T0) - 1), T0)
        self.assertEqual(len(codes), 10)
        _, s = self.auth.connecter("a@exemple.fr", MDP, T0)
        self.assertEqual(s.niveau, CODE)
        with self.assertRaises(ErreurAuth):                                      # code déjà utilisé
            self.auth.verifier_code(s, totp(secret, pas_de(T0) - 1), T0)
        with self.assertRaises(ErreurAuth):                                      # hors tolérance
            self.auth.verifier_code(s, totp(secret, pas_de(T0) + 2), T0)
        self.auth.verifier_code(s, totp(secret, pas_de(T0) + 1), T0)
        self.assertEqual(self.stock.session(s.jeton_hash).niveau, COMPLET)
        _, s = self.auth.connecter("a@exemple.fr", MDP, T0)
        self.auth.verifier_code(s, codes[0].upper(), T0)                         # code de secours
        _, s = self.auth.connecter("a@exemple.fr", MDP, T0)
        with self.assertRaises(ErreurAuth):                                      # consommé
            self.auth.verifier_code(s, codes[0], T0)
        for _ in range(3):
            with self.assertRaises(ErreurAuth):
                self.auth.verifier_code(s, "000000", T0)
        with self.assertRaises(ErreurAuth) as e:                                 # 5e échec : blocage
            self.auth.verifier_code(s, "000000", T0)
        self.assertEqual(e.exception.args[0], "TROP_D_ESSAIS")
        sans_cle = Authentification(self.stock, cle=lambda: None)
        _, s2 = sans_cle.connecter("b@exemple.fr", MDP, T0)
        with self.assertRaises(ErreurAuth) as e:
            sans_cle.debuter_enrolement(s2)
        self.assertEqual(e.exception.args[0], "CHIFFREMENT_NON_CONFIGURE")

    def test_parcours_double_authentification(self):
        """[RM-AMZ-076] Mot de passe seul : aucune donnée ; QR code fourni ; après le code : accès."""
        cl = TestClient(self.app, base_url="https://testserver")
        r = cl.post("/api/session", json={"courriel": "a@exemple.fr", "mot_de_passe": MDP}, headers=H)
        self.assertEqual(r.json()["etape"], ENROLER)
        self.assertEqual(cl.get("/api/lots").json()["detail"], "DOUBLE_AUTHENTIFICATION")
        self.assertEqual(cl.get("/api/session/etape").json()["etape"], ENROLER)
        e = cl.post("/api/session/enrolement", headers=H).json()
        self.assertTrue(e["qr"].startswith("data:image/svg+xml;base64,"))
        self.assertEqual(cl.post("/api/session/code", json={"code": "123456"}, headers=H).json()["detail"], "ETAPE_INVALIDE")
        r = cl.post("/api/session/enrolement/confirmer", json={"code": totp(b32(e["secret"]), pas_de(datetime.now(timezone.utc)))},
                    headers=H).json()
        self.assertEqual(len(r["codes_secours"]), 10)
        self.assertEqual(cl.get("/api/lots").status_code, 200)


class TestAcces(Base):
    def test_routes_protegees(self):
        """[RM-AMZ-039] Sans session : 401 ; avec session : le compte vient de la session."""
        anonyme = self.client()
        for m, url in [("get", "/api/lots"), ("get", "/api/moi"), ("post", "/api/analyse"),
                       ("get", "/api/sourcing/traitements/x"), ("post", "/api/lots")]:
            r = getattr(anonyme, m)(url, headers=H, **({"json": {}} if m == "post" else {}))
            self.assertEqual(r.status_code, 401, url)
        a = self.client("a@exemple.fr")
        self.assertEqual(a.get("/api/moi").json()["compte_id"], self.ca)
        self.assertEqual(a.get("/api/lots?compte_id=" + self.cb).json()["lots"], [])   # paramètre ignoré

    def test_jetons_par_compte(self):
        """[RM-AMZ-039] Analyse, lot et traitement d'un autre compte : introuvables."""
        a, b = self.client("a@exemple.fr"), self.client("b@exemple.fr")
        an = a.post("/api/analyse", json={"code": "B0DEMO0001", "prix_achat": 8.5}, headers=H).json()["analyses"][0]
        r = b.post("/api/lots", json={"jeton_analyse": an["jeton_analyse"], "quantite": 5}, headers=H)
        self.assertEqual((r.status_code, r.json()["detail"]), (404, "ANALYSE_EXPIREE"))
        lot = a.post("/api/lots", json={"jeton_analyse": an["jeton_analyse"], "quantite": 5}, headers=H).json()["id"]
        self.assertEqual(b.get(f"/api/lots/{lot}").status_code, 404)
        self.assertEqual(len(a.get("/api/lots").json()["lots"]), 1)
        f = a.post("/api/sourcing/fichiers", headers=H,
                   files={"fichier": ("f.csv", b"EAN;Prix\n3700000000017;8,5\n", "text/csv")}).json()
        self.assertEqual(b.post(f"/api/sourcing/fichiers/{f['fichier_id']}/traitements", headers=H,
                                json={"colonnes": f["colonnes"]}).status_code, 404)
        tid = a.post(f"/api/sourcing/fichiers/{f['fichier_id']}/traitements", headers=H,
                     json={"colonnes": f["colonnes"]}).json()["traitement_id"]
        self.assertEqual(b.get(f"/api/sourcing/traitements/{tid}").status_code, 404)
        self.assertEqual(a.get(f"/api/sourcing/traitements/{tid}").status_code, 200)

    def test_entete_anti_csrf(self):
        """[RM-AMZ-040] Requête qui modifie sans l'en-tête dédié : refusée, même connecté."""
        a = self.client("a@exemple.fr")
        r = a.post("/api/analyse", json={"code": "B0DEMO0001", "prix_achat": 8.5})
        self.assertEqual((r.status_code, r.json()["detail"]), (403, "ENTETE_MANQUANT"))
        r = TestClient(self.app).post("/api/session", json={"courriel": "a@exemple.fr", "mot_de_passe": MDP})
        self.assertEqual(r.status_code, 403)

    def test_sante_publique(self):
        """Contrôle de santé public et sans information ; documentation de l'API fermée quand la connexion est active."""
        cl = self.client()
        self.assertEqual(cl.get("/api/sante").json(), {"ok": True})
        self.assertEqual(cl.get("/api/docs").status_code, 404)

    def test_creer_utilisateur_cli(self):
        """[RM-AMZ-041] La commande crée le compte vendeur et un utilisateur qui peut se connecter."""
        cid, u = creer_utilisateur(self.depot, self.auth, "Compte C", "c@exemple.fr", MDP)
        self.assertEqual(u.compte_id, cid)
        self.assertEqual(self.client("c@exemple.fr").get("/api/moi").json()["compte_id"], cid)


if __name__ == "__main__":
    unittest.main()
