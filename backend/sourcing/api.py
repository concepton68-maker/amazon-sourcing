"""API web de Syllig Vente.

Modes (D-AMZ-019) : `AMZ_MODE=dev` = démonstration sans connexion (données fictives) ;
`AMZ_MODE=prod` = Postgres + connexion obligatoire. Le compte vendeur vient toujours de la
session, jamais de la requête [RM-AMZ-039]. Montants en chaînes ou nombres avec leur devise ;
textes = codes traduits par l'interface.
"""
from __future__ import annotations

import os
import pathlib
import uuid
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import achats as A
from . import conformite as CF
from . import connexions as CX
from . import exploration as EX
from . import historique as H
from . import tableau as TB
from . import frais_fba as FF
from . import annuaire as AN
from . import opportunites as OP
from . import correspondance as CO
from . import remboursements as RB
from . import fichier as fich
from .analyse import AnalyseProduit, Fournisseurs, Seuils, analyser_asin, resoudre_asins
from .auth import Authentification, ErreurAuth
from .depot import AccesRefuse
from .lots import Lot, ResultatLot, decomposer_ecart, prevision_depuis_analyse, rattacher_fifo
from .marketplaces import MARKETPLACES, get_marketplace
from .messages import texte_fr
from .parametres import ParametreInvalide, Parametres, valider
from .profit import REGIMES_TVA, ParametresCout
from .providers.base import ErreurFournisseur
from .stock import calculer as calculer_stock, commandes_par_fournisseur
from .traitement import Traitements, export_csv

DIST = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "dist"


def _s(x: Optional[Decimal], q: str = "0.01") -> Optional[str]:
    return None if x is None else str(x.quantize(Decimal(q)))


def _statut(r: ResultatLot) -> str:
    """[RM-AMZ-024]"""
    return "ECOULE" if r.quantite_vendue >= r.lot.quantite else "EN_VENTE"


def _resume(r: ResultatLot) -> dict:
    e, p = decomposer_ecart(r), r.lot.prevision
    return {
        "id": r.lot.id, "designation": r.lot.designation, "asin": r.lot.asin, "marketplace": r.lot.marketplace,
        "fournisseur": r.lot.fournisseur, "date_achat": r.lot.date_achat.isoformat(), "devise": p.devise,
        "quantite": r.lot.quantite, "vendues": r.quantite_vendue, "statut": _statut(r),
        "roi_prevu": _s(p.roi, "0.0001"), "roi_reel": _s(r.roi_reel, "0.0001"),
        "profit_prevu": _s(e.profit_prevu), "profit_reel": _s(r.profit_reel.valeur), "ecart": _s(e.total),
        "a_encaisser": _s(r.a_encaisser.valeur),
    }


def _detail(r: ResultatLot) -> dict:
    """[RM-AMZ-025] Comparaison par unité vendue ; profit prévu du lot entier à part."""
    e, p, q = decomposer_ecart(r), r.lot.prevision, r.quantite_vendue
    par_u = (lambda m: m.valeur / q) if q else (lambda m: None)
    lignes = [
        ("PRIX_VENTE_HT", p.prix_vente_ht, par_u(r.chiffre_affaires)),
        ("FRAIS_AMAZON", p.frais_amazon, par_u(r.frais_amazon)),
        ("RETOURS", p.retours, par_u(r.retours)),
        ("STOCKAGE", p.stockage, par_u(r.stockage)),
        ("AUTRES", p.autres, par_u(r.autres)),
        ("COUT_ACHAT", p.cout_achat, p.cout_achat if q else None),
        ("PROFIT", p.profit, par_u(r.profit_reel)),
    ]
    sens = {"PRIX_VENTE_HT": 1, "PROFIT": 1}
    return {
        **_resume(r),
        "profit_prevu_lot_entier": _s(p.profit * r.lot.quantite),
        "comparatif": [{"poste": k, "prevu": _s(a), "reel": _s(b),
                        "ecart": None if b is None else _s((b - a) * sens.get(k, -1))} for k, a, b in lignes],
        "causes": [{"cause": c.upper(), "montant": _s(v)} for c, v in e.causes_par_ordre()],
        "sources": list(p.sources), "version": r.lot.version,
    }


class DemandeAnalyse(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    marketplace: str = "FR"
    prix_achat: float = Field(gt=0)
    achat_ttc: bool = False
    regime_tva: Optional[str] = None          # absent : régime du compte pour cette place [RM-AMZ-044]
    taux_tva: Optional[float] = Field(default=None, ge=0, lt=1)
    prix_vente: Optional[float] = Field(default=None, gt=0)
    port_fournisseur: Optional[float] = Field(default=None, ge=0, le=1000)   # [RM-AMZ-098] remplace le défaut


class DemandeSynchroManuelle(BaseModel):
    taches: list[str] = Field(max_length=20)


class DemandeAjoutAnnuaire(BaseModel):
    codes: list[str] = Field(min_length=1, max_length=200)


class DemandeCatalogue(BaseModel):
    fichier_id: str
    colonnes: dict[str, Optional[int]]
    prix_par_carton: bool = False


class DemandeAnalyseCatalogue(BaseModel):
    marketplace: str = "FR"
    achat_ttc: bool = False


class DemandeTraitement(BaseModel):
    colonnes: dict[str, Optional[int]]
    marketplace: str = "FR"
    regime_tva: Optional[str] = None
    achat_ttc: bool = False
    prix_par_carton: bool = False


def _num(x):
    return None if x is None else float(x)


def _resultat_json(r) -> dict:
    msgs = lambda l: [x.to_dict() for x in l]  # noqa: E731
    return {"ligne": r.numero, "code": r.code, "designation": r.designation, "asin": r.asin, "titre": r.titre,
            "prix_unitaire": _num(r.prix_unitaire), "unites_lot": r.unites_lot, "cout_achat": _num(r.cout_achat),
            "verdict": r.verdict, "statut": r.statut, "prix_vente": r.prix_vente, "profit": r.profit, "roi": r.roi,
            "ventes_mois": r.ventes_mois, "remarques": msgs(r.lignes), "raisons": msgs(r.raisons),
            "alertes": msgs(r.alertes)}


class DemandeFournisseur(BaseModel):
    nom: str = Field(max_length=200)
    devise: str = "EUR"
    delai_jours: int = 7
    courriel: Optional[str] = Field(default=None, max_length=254)


class DemandeBon(BaseModel):
    fournisseur_id: str


class DemandeLigne(BaseModel):
    jeton_analyse: Optional[str] = None
    asin: Optional[str] = Field(default=None, max_length=20)
    marketplace: Optional[str] = None
    quantite: int
    prix_unitaire: Optional[float] = None


class DemandeReception(BaseModel):
    quantites: dict[str, int]
    date_reception: Optional[date] = None


class DemandeBonStock(BaseModel):
    fournisseur: str


ERREURS_SAISIE = {"NOM_FOURNISSEUR_INVALIDE", "DELAI_INVALIDE", "DEVISE_INVALIDE", "COURRIEL_INVALIDE",
                  "QUANTITE_INVALIDE", "PRIX_INVALIDE", "QUANTITE_RECUE_INVALIDE", "DEVISE_DIFFERENTE",
                  "CHAMP_INCONNU", "CHAMP_INVALIDE", "REVENTE_INVALIDE", "CONNEXION_INVALIDE", "PORT_INVALIDE",
                  "TEXTE_TROP_LONG", "SITE_INVALIDE"}


def _erreur_achat(e: Exception) -> HTTPException:
    code = e.args[0] if e.args else "ERREUR"
    return HTTPException(422 if code in ERREURS_SAISIE else 409, code)


def _bon_json(b: "A.BonCommande", fournisseurs: dict) -> dict:
    f = fournisseurs.get(b.fournisseur_id)
    cout = sum((l.prevision.cout_achat * l.quantite for l in b.lignes), Decimal(0))
    profit = sum((l.prevision.profit * l.quantite for l in b.lignes), Decimal(0))
    return {
        "id": b.id, "reference": b.reference, "statut": b.statut,
        "fournisseur": None if f is None else {"id": f.id, "nom": f.nom, "devise": f.devise},
        "devise": f.devise if f else None, "montant": _num(b.montant),
        "roi_prevu": None if cout == 0 else float(round(profit / cout, 4)),
        "cree_le": b.cree_le.isoformat(), "envoye_le": b.envoye_le.isoformat() if b.envoye_le else None,
        "recu_le": b.recu_le.isoformat() if b.recu_le else None,
        "lignes": [{"id": l.id, "asin": l.asin, "marketplace": l.marketplace, "designation": l.designation,
                    "quantite": l.quantite, "prix_unitaire": _num(l.prix_unitaire),
                    "montant": _num(l.prix_unitaire * l.quantite),
                    "roi_prevu": None if l.prevision.roi is None else float(round(l.prevision.roi, 4)),
                    "quantite_recue": l.quantite_recue, "lot_id": l.lot_id} for l in b.lignes],
    }


class DemandeSuivi(BaseModel):
    statut: str
    case_id: Optional[str] = Field(default=None, max_length=40)


def _cas_json(x: "RB.Cas") -> dict:
    return {"cle": x.cle, "type": x.type, "marketplace": x.marketplace, "asin": x.asin, "sku": x.sku, "fnsku": x.fnsku,
            "commande": x.commande, "unites": x.unites, "valeur_achat": _num(x.valeur_achat), "devise": x.devise,
            "detecte_le": x.detecte_le.isoformat(), "echeance": x.echeance.isoformat() if x.echeance else None,
            "statut": x.statut, "case_id": x.case_id, "montant_verse": _num(x.montant_verse), "faits": x.faits}


class DemandeEnregistrement(BaseModel):
    pays: str
    filiere: str
    numero: Optional[str] = None
    intitule: Optional[str] = None
    mandataire: Optional[str] = None


def _enreg_json(e: "CF.Enregistrement") -> dict:
    return {"cle": e.cle, "pays": e.pays, "filiere": e.filiere, "numero": e.numero, "intitule": e.intitule,
            "mandataire": e.mandataire, "texte": CF.texte_numero(e.pays, e.filiere),
            "avertissements": [x.to_dict() for x in CF.avertissements_enregistrement(e)]}


class DemandeFamilles(BaseModel):
    familles: list[str] = Field(max_length=len(EX.RAYONS))


class DemandeSuiviProduit(BaseModel):
    asin: str = Field(pattern=r"^[A-Za-z0-9]{10}$")
    marketplace: str = "FR"


class DemandeLot(BaseModel):
    jeton_analyse: str
    quantite: int = Field(gt=0)
    fournisseur: Optional[str] = Field(default=None, max_length=120)
    date_achat: Optional[date] = None


def _r(x):
    return None if x is None else round(x, 4)


def _analyse_json(a: AnalyseProduit, jeton: str) -> dict:
    """[RM-AMZ-028] Données et messages codés ; aucun texte."""
    mp = get_marketplace(a.marketplace)
    r, p, o, h, c = a.rentabilite, a.rentabilite_prudente, a.offres, a.historique, a.catalogue
    msgs = lambda l: [x.to_dict() for x in l]  # noqa: E731
    return {
        "jeton_analyse": jeton, "asin": a.asin, "marketplace": a.marketplace, "devise": mp.devise,
        "titre": c.titre, "marque": c.marque, "categorie": c.categorie, "bsr": c.bsr, "unites_lot": c.nb_unites_lot,
        "verdict": a.verdict, "origine_prix": a.origine_prix, "prix_vente": a.prix_vente_retenu,
        "rentabilite": None if not r else {
            "prix_vente_ht": r.prix_vente_ht, "tva_collectee": r.tva_collectee, "cout_achat_net": r.cout_achat_net,
            "frais_amazon": r.frais_amazon, "tva_frais": r.tva_sur_frais_non_recuperable, "autres": r.autres_couts,
            "profit": r.profit_net, "roi": r.roi, "marge": r.marge, "prix_achat_max": r.prix_achat_max_pour_roi,
            "roi_cible": r.roi_cible, "regime_tva": r.regime_tva, "hypotheses": msgs(r.hypotheses), "detail": r.detail},
        "frais_source": a.frais.source if a.frais else None,
        "prudent": None if not p else {"prix_vente": p.prix_vente, "profit": p.profit_net, "roi": p.roi},
        "offres": None if not o else {"nb_fba": o.nb_offres_fba, "nb_fbm": o.nb_offres_fbm,
                                      "amazon_vend": o.amazon_vend, "buybox_amazon": o.buybox_amazon},
        "historique": None if not h else {
            "prix_moy90": h.prix_buybox_moy90, "prix_min90": h.prix_buybox_min90, "prix_max90": h.prix_buybox_max90,
            "ventes_mois": h.ventes_mois_estimees, "chutes_bsr_30j": h.chutes_bsr_30j, "bsr_moy90": h.bsr_moy90,
            "amazon_en_stock": _r(h.amazon_en_stock_pct90)},
        "ventes_pour_vous": a.ventes_estimees_pour_vous,
        "autorise": None if a.restrictions is None else a.restrictions.autorise,
        "raisons": msgs(a.raisons), "alertes": msgs(a.alertes), "non_verifie": msgs(a.non_verifie),
    }


COOKIE = "sv_session"
ENTETE_ANTI_CSRF = "x-syllig-vente"


class DemandeMotDePasse(BaseModel):
    nouveau: str = Field(max_length=200)


class DemandeCode(BaseModel):
    code: str = Field(max_length=20)


class DemandeConnexion(BaseModel):
    courriel: str = Field(min_length=3, max_length=254)
    mot_de_passe: str = Field(min_length=1, max_length=1024)


def creer_app(depot, compte_demo: Optional[str] = None, servir_interface: bool = True, demo: bool = False,
              fournisseurs: Optional[Fournisseurs] = None, seuils: Optional[Seuils] = None,
              traitement_en_fond: bool = True, auth: Optional[Authentification] = None,
              cookie_secure: bool = True, fabrique_spapi=None) -> FastAPI:
    """`auth` absent : un seul compte fixe (`compte_demo`), mode démonstration. `auth` présent : sessions."""
    if auth is None and not compte_demo:
        raise ValueError("compte_demo requis sans authentification")
    app = FastAPI(title="Syllig Vente", docs_url="/api/docs" if auth is None else None,
                  openapi_url="/api/openapi.json" if auth is None else None)
    fournisseurs = fournisseurs or Fournisseurs()
    _cache_sources: dict[str, tuple[tuple, Fournisseurs]] = {}

    def sources(c: str) -> Fournisseurs:
        """[RM-AMZ-073] Sources du compte si elles existent, sinon celles du serveur."""
        cx = depot.connexions(c)
        cle = CX.cle_serveur()
        if not cx or not cle:
            return fournisseurs
        empreinte = tuple(sorted((s, x.maj.isoformat()) for s, x in cx.items()))
        deja = _cache_sources.get(c)
        if deja and deja[0] == empreinte:
            return deja[1]
        try:
            f = CX.fournisseurs_du_compte({s: CX.dechiffrer(cle, c, s, x.chiffre) for s, x in cx.items()})
        except Exception:  # identifiants illisibles (clé changée) : on ne devine rien
            return fournisseurs
        _cache_sources[c] = (empreinte, f)
        return f
    seuils = seuils or Seuils()
    analyses: "OrderedDict[str, tuple[str, AnalyseProduit, ParametresCout]]" = OrderedDict()
    utilisees: set[str] = set()                   # [RM-AMZ-029] une analyse, un lot
    fichiers: "OrderedDict[str, tuple[str, str, fich.Table]]" = OrderedDict()
    traitements = Traitements()
    explorations = EX.Explorations(en_fond=traitement_en_fond)
    correspondances = CO.Correspondances(en_fond=traitement_en_fond)
    from . import synchro_nuit as SN
    manuelles = SN.SynchrosManuelles(en_fond=traitement_en_fond)

    @app.middleware("http")
    async def anti_csrf(request: Request, appel_suivant):
        """[RM-AMZ-040] Hors démo, toute requête qui modifie doit porter l'en-tête dédié."""
        if auth is not None and request.url.path.startswith("/api/") \
                and request.method in ("POST", "PUT", "PATCH", "DELETE") \
                and request.headers.get(ENTETE_ANTI_CSRF) != "1":
            return JSONResponse({"detail": "ENTETE_MANQUANT"}, status_code=403)
        return await appel_suivant(request)

    def compte(request: Request) -> str:
        """[RM-AMZ-039] Le compte vient de la session ; jamais d'un paramètre de la requête."""
        if auth is None:
            return compte_demo
        s = auth.session_valide(request.cookies.get(COOKIE))
        if s is None:
            raise HTTPException(401, "NON_CONNECTE")
        if s.niveau != "COMPLET":  # [RM-AMZ-075, 076] mot de passe à changer ou double authentification à faire
            raise HTTPException(401, "DOUBLE_AUTHENTIFICATION")
        return s.compte_id

    def session_partielle(request: Request):
        if auth is None:
            raise HTTPException(404, "MODE_DEMO")
        s = auth.session_valide(request.cookies.get(COOKIE))
        if s is None:
            raise HTTPException(401, "NON_CONNECTE")
        return s

    def _erreur_auth(e: "ErreurAuth"):
        code = e.args[0]
        statut = {"TROP_D_ESSAIS": 429, "CHIFFREMENT_NON_CONFIGURE": 503, "NON_CONNECTE": 401}.get(code, 400)
        raise HTTPException(statut, code) from None

    @app.get("/version.json")
    def page_controle():
        """[RM-AMZ-081] Public : dates et OK/ÉCHEC seulement, aucune donnée de compte."""
        dossier = pathlib.Path(os.environ.get("AMZ_ETAT_DIR", "/etat"))

        def lire(nom):
            try:
                quand, _, statut = (dossier / f"{nom}.txt").read_text(encoding="utf-8").strip().partition(" ")
                return {"le": quand or None, "statut": statut or None}
            except OSError:
                return None
        try:
            version = (dossier / "version.txt").read_text(encoding="utf-8").strip()[:40] or None
        except OSError:
            version = None
        try:
            synchros = {t: {"le": f.isoformat(), "statut": "OK" if ok else "ECHEC"} for t, (f, ok) in depot.etat_synchros().items()}
        except Exception:
            synchros = None
        return {"version": version, "mise_a_jour": lire("maj"), "sauvegarde": lire("sauvegarde"), "purge": lire("purge"),
                "antivirus": lire("antivirus"), "synchronisation": synchros}

    @app.get("/api/sante")
    def sante():
        """Contrôle de santé (Docker, surveillance) : public, ne révèle rien."""
        return {"ok": True}

    # ------------------------------------------------------------- session [RM-AMZ-037, 038]
    @app.post("/api/session")
    def connexion(d: DemandeConnexion):
        if auth is None:
            raise HTTPException(404, "MODE_DEMO")
        try:
            jeton, _ = auth.connecter(d.courriel, d.mot_de_passe)
        except ErreurAuth as e:
            raise HTTPException(401 if e.args[0] == "IDENTIFIANTS_INVALIDES" else 429, e.args[0]) from None
        r = JSONResponse({"ok": True, "etape": _.niveau})
        r.set_cookie(COOKIE, jeton, httponly=True, samesite="lax", secure=cookie_secure, path="/",
                     max_age=int(30 * 24 * 3600))
        return r

    # ------------------------------------------------------------- étapes après le mot de passe [RM-AMZ-075, 076]
    @app.get("/api/session/etape")
    def etape(s=Depends(session_partielle)):
        return {"etape": s.niveau}

    @app.post("/api/session/mot-de-passe")
    def nouveau_mot_de_passe(d: DemandeMotDePasse, s=Depends(session_partielle)):
        try:
            return {"etape": auth.changer_mot_de_passe(s, d.nouveau)}
        except ErreurAuth as e:
            _erreur_auth(e)

    @app.post("/api/session/enrolement")
    def enrolement(s=Depends(session_partielle)):
        import base64
        from .auth import qr_svg
        try:
            secret, uri = auth.debuter_enrolement(s)
        except ErreurAuth as e:
            _erreur_auth(e)
        return {"secret": base64.b32encode(secret).decode().rstrip("="), "uri": uri,
                "qr": "data:image/svg+xml;base64," + base64.b64encode(qr_svg(uri).encode()).decode()}

    @app.post("/api/session/enrolement/confirmer")
    def confirmer_enrolement(d: DemandeCode, s=Depends(session_partielle)):
        try:
            return {"etape": "COMPLET", "codes_secours": auth.confirmer_enrolement(s, d.code)}
        except ErreurAuth as e:
            _erreur_auth(e)

    @app.post("/api/session/code")
    def code_double_authentification(d: DemandeCode, s=Depends(session_partielle)):
        try:
            auth.verifier_code(s, d.code)
        except ErreurAuth as e:
            _erreur_auth(e)
        return {"etape": "COMPLET"}

    @app.delete("/api/session")
    def deconnexion(request: Request):
        if auth is not None:
            auth.deconnecter(request.cookies.get(COOKIE))
        r = JSONResponse({"ok": True})
        r.delete_cookie(COOKIE, path="/")
        return r

    @app.get("/api/moi")
    def moi(c: str = Depends(compte)):
        return {"compte_id": c, "demo": demo, "connexion": auth is not None}

    # ------------------------------------------------------------- paramètres [RM-AMZ-042 à 044]
    def params(c: str) -> Parametres:
        return valider(depot.parametres(c) or {})

    @app.get("/api/parametres")
    def lire_parametres(c: str = Depends(compte)):
        return {**params(c).to_dict(), "versions": len(depot.versions_parametres(c)),
                "reference_carburant": {"taux": FF.CARBURANT[-1][1], "depuis": FF.CARBURANT[-1][0].isoformat()}}

    @app.put("/api/parametres")
    def ecrire_parametres(brut: dict, c: str = Depends(compte)):
        try:
            p = valider(brut)
        except ParametreInvalide as e:
            raise HTTPException(422, {"code": e.args[0], "champ": e.args[1]}) from None
        valeurs = p.to_dict()
        valeurs["tva"] = {k: v for k, v in valeurs["tva"].items() if v != "hors_taxe"}
        version = depot.enregistrer_parametres(c, valeurs)
        return {**p.to_dict(), "versions": version,
                "reference_carburant": {"taux": FF.CARBURANT[-1][1], "depuis": FF.CARBURANT[-1][0].isoformat()}}

    # ------------------------------------------------------------- fournisseurs et bons [RM-AMZ-049 à 053]
    def _fournisseurs(c: str) -> dict:
        return {f.id: f for f in depot.fournisseurs(c)}

    def _bon(c: str, bon_id: str):
        try:
            return depot.bon(c, bon_id)
        except AccesRefuse:
            raise HTTPException(404, "BON_INTROUVABLE") from None

    def _sauver(c: str, b):
        try:
            depot.enregistrer_bon(c, b)
        except ValueError as e:
            raise _erreur_achat(e) from None
        return _bon_json(b, _fournisseurs(c))

    def _dernier_lot(c: str, asin: str, mp: str):
        lots = [l for l in depot.lots(c) if l.asin == asin and l.marketplace == mp]
        return lots[-1] if lots else None

    @app.get("/api/fournisseurs")
    def lister_fournisseurs(c: str = Depends(compte)):
        bs = A.bilans(depot.fournisseurs(c), depot.lots(c), depot.ventes(c), depot.bons(c), date.today())
        return [{**_fiche_json(c, b.fournisseur), "lots": b.lots,
                 "achete_12_mois": _num(b.achete_12_mois), "roi_prevu": _num(b.roi_prevu), "roi_reel": _num(b.roi_reel),
                 "delai_reel_jours": b.delai_reel_jours} for b in bs]

    def _fiche_json(c: str, f) -> dict:
        cat = depot.catalogue(c, f.id)
        return {"id": f.id, "nom": f.nom, "devise": f.devise, "delai_jours": f.delai_jours, "courriel": f.courriel,
                "pays": f.pays, "site": f.site, "categories": list(f.categories), "port_unitaire": _num(f.port_unitaire),
                "revente": f.revente, "revente_source": f.revente_source, "connexion": f.connexion, "notes": f.notes,
                "reference": f.reference, "colonnes": f.colonnes, "analysable": A.analysable(f),
                "catalogue": None if not cat else {"nom_fichier": cat[0]["nom_fichier"], "lignes": cat[0]["lignes"],
                                                   "rejets": cat[0]["rejets"], "maj": cat[0]["maj"].isoformat()}}

    def _fournisseur(c: str, fid: str):
        f = next((x for x in depot.fournisseurs(c) if x.id == fid), None)
        if f is None:
            raise HTTPException(404, "FOURNISSEUR_INTROUVABLE")
        return f

    # [RM-AMZ-101] annuaire de référence
    @app.get("/api/annuaire")
    def annuaire(c: str = Depends(compte)):
        mes = {f.reference for f in depot.fournisseurs(c) if f.reference}
        return [{**r.to_dict(), "ajoute": r.code in mes} for r in AN.REFERENCES]

    @app.post("/api/annuaire/{code}/ajouter", status_code=201)
    def ajouter_depuis_annuaire(code: str, c: str = Depends(compte)):
        ref = AN.PAR_CODE.get(code)
        if ref is None:
            raise HTTPException(404, "REFERENCE_INCONNUE")
        try:
            f = A.depuis_reference(c, ref, depot.fournisseurs(c))
            depot.enregistrer_fournisseur(c, f)
        except (A.ErreurAchat, ValueError) as e:
            raise _erreur_achat(e) from None
        return _fiche_json(c, f)

    @app.post("/api/annuaire/ajouter", status_code=201)
    def ajouter_plusieurs(d: DemandeAjoutAnnuaire, c: str = Depends(compte)):
        """[RM-AMZ-101] Ajout groupé : les déjà présents sont ignorés, jamais en double."""
        ajoutes, ignores = [], []
        for code in dict.fromkeys(d.codes):
            ref = AN.PAR_CODE.get(code)
            if ref is None:
                raise HTTPException(404, "REFERENCE_INCONNUE")
            try:
                f = A.depuis_reference(c, ref, depot.fournisseurs(c))
                depot.enregistrer_fournisseur(c, f)
                ajoutes.append(code)
            except (A.ErreurAchat, ValueError):
                ignores.append(code)
        return {"ajoutes": ajoutes, "ignores": ignores}

    # [RM-AMZ-100] fiche
    @app.put("/api/fournisseurs/{fid}")
    def modifier_fournisseur(fid: str, brut: dict, c: str = Depends(compte)):
        try:
            f = A.modifier_fiche(_fournisseur(c, fid), **brut)
            depot.enregistrer_fournisseur(c, f)
        except (A.ErreurAchat, ValueError, TypeError) as e:
            raise _erreur_achat(e if not isinstance(e, TypeError) else A.ErreurAchat("CHAMP_INVALIDE")) from None
        return _fiche_json(c, f)

    # [RM-AMZ-102] catalogue par fichier
    @app.post("/api/fournisseurs/{fid}/fichier", status_code=201)
    async def deposer_tarif(fid: str, fichier: UploadFile = File(...), c: str = Depends(compte)):
        f = _fournisseur(c, fid)
        contenu = await fichier.read(fich.MAX_OCTETS + 1)
        try:
            table = fich.lire(contenu, fichier.filename or "")
        except fich.FichierInvalide as e:
            raise HTTPException(422, e.args[0]) from None
        fid_t = str(uuid.uuid4())
        fichiers[fid_t] = (c, fichier.filename or "", table)
        while len(fichiers) > 50:
            fichiers.popitem(last=False)
        proposees = fich.proposer_colonnes(table.entetes)
        if f.colonnes and all(k in fich.ROLES for k in f.colonnes):       # mémorisées : par nom d'en-tête
            for role, entete in f.colonnes.items():
                if entete in table.entetes:
                    proposees[role] = table.entetes.index(entete)
        return {"fichier_id": fid_t, "nom": fichier.filename, "entetes": table.entetes, "apercu": table.lignes[:5],
                "nb_lignes": len(table.lignes), "colonnes": proposees}

    @app.post("/api/fournisseurs/{fid}/catalogue", status_code=201)
    def enregistrer_tarif(fid: str, d: DemandeCatalogue, c: str = Depends(compte)):
        f = _fournisseur(c, fid)
        t = fichiers.get(d.fichier_id)
        if t is None or t[0] != c:
            raise HTTPException(404, "FICHIER_EXPIRE")
        colonnes = {r: d.colonnes.get(r) for r in fich.ROLES}
        try:
            prep = fich.preparer(t[2], colonnes, d.prix_par_carton)
        except fich.FichierInvalide as e:
            raise HTTPException(422, e.args[0]) from None
        depot.enregistrer_catalogue(c, f.id, {"nom_fichier": t[1], "lignes": len(prep.lignes),
                                              "rejets": len(prep.rejets) + len(prep.doublons)}, prep.lignes)
        memo = {r: t[2].entetes[i] for r, i in colonnes.items() if i is not None}
        depot.enregistrer_fournisseur(c, A.modifier_fiche(f, colonnes=memo, connexion="FICHIER" if f.connexion == "AUCUNE"
                                                          else f.connexion))
        fx = sources(c)                                                   # [RM-AMZ-114] correspondance aussitôt
        lancee = False
        if fx.catalogue and A.analysable(f):
            p = params(c)
            mp = get_marketplace("FR")
            lancee = correspondances.lancer(c, mp, fx, depot, p, p.regime(mp.code))
        return {"lignes": len(prep.lignes), "rejets": [{"ligne": n, "message": x.to_dict()} for n, x in prep.rejets],
                "doublons": len(prep.doublons), "correspondance_lancee": lancee}

    @app.get("/api/fournisseurs/{fid}/catalogue")
    def lire_tarif(fid: str, c: str = Depends(compte)):
        _fournisseur(c, fid)
        cat = depot.catalogue(c, fid)
        if cat is None:
            raise HTTPException(404, "CATALOGUE_ABSENT")
        meta, lignes = cat
        return {"nom_fichier": meta["nom_fichier"], "lignes": meta["lignes"], "rejets": meta["rejets"],
                "maj": meta["maj"].isoformat(),
                "apercu": [{"code": l.code, "designation": l.designation, "prix": _num(l.prix_unitaire),
                            "colisage": l.colisage, "minimum": l.minimum} for l in lignes[:50]]}

    # [RM-AMZ-103] analyse du catalogue enregistré
    @app.post("/api/fournisseurs/{fid}/analyse", status_code=201)
    def analyser_tarif(fid: str, d: DemandeAnalyseCatalogue, c: str = Depends(compte)):
        f = _fournisseur(c, fid)
        if not A.analysable(f):
            raise HTTPException(409, "REVENTE_INTERDITE")
        cat = depot.catalogue(c, fid)
        if cat is None:
            raise HTTPException(404, "CATALOGUE_ABSENT")
        fx = sources(c)
        if not fx.catalogue:
            raise HTTPException(503, "SOURCE_NON_CONFIGUREE")
        mp = _place(d.marketplace)
        p = params(c)
        if f.port_unitaire is not None:
            from dataclasses import replace as _remplacer
            p = _remplacer(p, port_fournisseur=float(f.port_unitaire))
        prep = fich.Preparation(cat[1], [], [])
        t = traitements.lancer(c, prep, mp, fx, depot, p.regime(mp.code), d.achat_ttc, p.seuils(),
                               en_fond=traitement_en_fond, parametres=p, origine=(f"FOURNISSEUR:{f.id}", f.nom))
        return {"traitement_id": t.id}

    @app.post("/api/fournisseurs", status_code=201)
    def creer_fournisseur(d: DemandeFournisseur, c: str = Depends(compte)):
        try:
            f = A.nouveau_fournisseur(c, d.nom, d.devise, d.delai_jours, d.courriel, depot.fournisseurs(c))
            depot.enregistrer_fournisseur(c, f)
        except (A.ErreurAchat, ValueError) as e:
            raise _erreur_achat(e) from None
        return {"id": f.id}

    @app.get("/api/bons")
    def lister_bons(c: str = Depends(compte)):
        fs = _fournisseurs(c)
        return [_bon_json(b, fs) for b in depot.bons(c)]

    @app.post("/api/bons", status_code=201)
    def creer_bon(d: DemandeBon, c: str = Depends(compte)):
        f = _fournisseurs(c).get(d.fournisseur_id)
        if f is None:
            raise HTTPException(404, "FOURNISSEUR_INCONNU")
        return _sauver(c, A.nouveau_bon(c, depot.prochain_numero(c), f))

    @app.get("/api/bons/{bon_id}")
    def lire_bon(bon_id: str, c: str = Depends(compte)):
        return _bon_json(_bon(c, bon_id), _fournisseurs(c))

    @app.post("/api/bons/{bon_id}/lignes")
    def ajouter_ligne_bon(bon_id: str, d: DemandeLigne, c: str = Depends(compte)):
        b = _bon(c, bon_id)
        f = _fournisseurs(c).get(b.fournisseur_id)
        if d.jeton_analyse:
            trouve = analyses.get(d.jeton_analyse)
            if trouve is None or trouve[0] != c:
                raise HTTPException(404, "ANALYSE_EXPIREE")
            _, a, couts = trouve
            if a.rentabilite is None:
                raise HTTPException(409, "ANALYSE_SANS_RENTABILITE")
            mp = get_marketplace(a.marketplace)
            base = prevision_depuis_analyse(a.rentabilite, couts, mp.devise, ["prix:" + a.origine_prix])
            asin, mpc, designation = a.asin, a.marketplace, a.catalogue.titre
        elif d.asin and d.marketplace:
            lot = _dernier_lot(c, d.asin, d.marketplace)
            if lot is None:
                raise HTTPException(409, "PREVISION_ABSENTE")
            base, asin, mpc, designation = lot.prevision, lot.asin, lot.marketplace, lot.designation
        else:
            raise HTTPException(422, "PRODUIT_MANQUANT")
        prix = d.prix_unitaire if d.prix_unitaire is not None else base.cout_achat
        try:
            b = A.ajouter_ligne(b, asin, mpc, d.quantite, prix, base, designation, f.devise if f else None)
        except A.ErreurAchat as e:
            raise _erreur_achat(e) from None
        return _sauver(c, b)

    @app.delete("/api/bons/{bon_id}/lignes/{ligne_id}")
    def retirer_ligne_bon(bon_id: str, ligne_id: str, c: str = Depends(compte)):
        try:
            return _sauver(c, A.retirer_ligne(_bon(c, bon_id), ligne_id))
        except A.ErreurAchat as e:
            raise _erreur_achat(e) from None

    @app.post("/api/bons/{bon_id}/envoyer")
    def envoyer_bon(bon_id: str, c: str = Depends(compte)):
        try:
            return _sauver(c, A.envoyer(_bon(c, bon_id)))
        except A.ErreurAchat as e:
            raise _erreur_achat(e) from None

    @app.post("/api/bons/{bon_id}/annuler")
    def annuler_bon(bon_id: str, c: str = Depends(compte)):
        try:
            return _sauver(c, A.annuler(_bon(c, bon_id)))
        except A.ErreurAchat as e:
            raise _erreur_achat(e) from None

    @app.post("/api/bons/{bon_id}/recevoir")
    def recevoir_bon(bon_id: str, d: DemandeReception, c: str = Depends(compte)):
        b = _bon(c, bon_id)
        f = _fournisseurs(c).get(b.fournisseur_id)
        try:
            b2, lots = A.recevoir(b, d.quantites, d.date_reception or date.today(), f)
            depot.receptionner(c, b2, lots)
        except (A.ErreurAchat, ValueError) as e:
            raise _erreur_achat(e) from None
        return {**_bon_json(b2, _fournisseurs(c)), "lots_crees": [l.id for l in lots]}

    @app.post("/api/bons/depuis-stock", status_code=201)
    def bon_depuis_stock(d: DemandeBonStock, c: str = Depends(compte)):
        """[RM-AMZ-053] Commande suggérée → bon brouillon."""
        f = next((x for x in depot.fournisseurs(c) if x.nom.lower() == d.fournisseur.strip().lower()), None)
        if f is None:
            raise HTTPException(404, "FOURNISSEUR_INCONNU")
        p = params(c)
        jour, photos = depot.photo_stock(c)
        lignes = calculer_stock(photos, depot.ventes(c), depot.lots(c), jour or date.today(), p.delai_fournisseur,
                                p.delai_reception, p.marge_securite, p.seuil_rupture, p.seuil_surstock)
        b = A.nouveau_bon(c, depot.prochain_numero(c), f)
        for l in lignes:
            if l.a_commander <= 0 or (l.fournisseur or "").lower() != f.nom.lower():
                continue
            lot = _dernier_lot(c, l.photo.asin, l.photo.marketplace)
            if lot is None:
                continue
            try:
                b = A.ajouter_ligne(b, lot.asin, lot.marketplace, l.a_commander, lot.prevision.cout_achat,
                                    lot.prevision, lot.designation, f.devise)
            except A.ErreurAchat:
                continue                     # devise différente : la ligne n'est pas proposée
        if not b.lignes:
            raise HTTPException(409, "RIEN_A_COMMANDER")
        return _sauver(c, b)

    # ------------------------------------------------------------- remboursements [RM-AMZ-054 à 059]
    @app.get("/api/remboursements")
    def remboursements(c: str = Depends(compte)):
        cas = depot.cas_remboursement(c)
        ordre = {RB.DETECTE: 0, RB.DOSSIER_ENVOYE: 1, RB.REMBOURSE: 2, RB.REFUSE: 3, RB.CLOS: 4}
        cas.sort(key=lambda x: (ordre[x.statut], x.echeance or date.max, x.cle))
        un_an = date.today().replace(year=date.today().year - 1)
        verse: dict[str, Decimal] = {}
        n = 0
        for v in depot.verses(c):
            if v.jour and v.jour >= un_an and v.montant is not None:
                verse[v.devise or "?"] = verse.get(v.devise or "?", Decimal(0)) + v.montant
                n += 1
        return {"cas": [_cas_json(x) for x in cas],
                "compteurs": {"a_verifier": sum(1 for x in cas if x.statut == RB.DETECTE),
                              "en_cours": sum(1 for x in cas if x.statut == RB.DOSSIER_ENVOYE),
                              "verses_12_mois": [{"devise": d, "montant": _num(m)} for d, m in verse.items()],
                              "nb_verses_12_mois": n},
                "source_delais": RB.SOURCE_DELAIS}

    @app.post("/api/remboursements/{cle:path}/suivi")
    def suivre_cas(cle: str, d: DemandeSuivi, c: str = Depends(compte)):
        x = next((y for y in depot.cas_remboursement(c) if y.cle == cle), None)
        if x is None:
            raise HTTPException(404, "CAS_INTROUVABLE")
        try:
            x = RB.changer_suivi(x, d.statut, (d.case_id or "").strip() or None)
        except ValueError as e:
            raise HTTPException(422, e.args[0]) from None
        depot.enregistrer_cas(c, [x])
        return _cas_json(x)

    # ------------------------------------------------------------- connexions [RM-AMZ-072 à 074]
    @app.get("/api/connexions")
    def lire_connexions(c: str = Depends(compte)):
        cx = depot.connexions(c)
        return {"chiffrement": CX.cle_serveur() is not None,
                "sources": [{"source": s, "champs": list(ch), "enregistree_le": cx[s].maj.isoformat() if s in cx else None}
                            for s, ch in CX.SOURCES.items()], "regions": list(CX.REGIONS)}

    @app.put("/api/connexions/{source}")
    def ecrire_connexion(source: str, brut: dict, c: str = Depends(compte)):
        try:
            ancien, cle, cx = None, CX.cle_serveur(), depot.connexions(c)
            if source in cx and cle:
                try:
                    ancien = CX.dechiffrer(cle, c, source, cx[source].chiffre)
                except Exception:  # illisible (clé changée) : tout doit être ressaisi
                    ancien = None
            valeurs = CX.valider(source, brut, ancien)
            chiffre = CX.chiffrer(cle, c, source, valeurs)
        except CX.ConnexionInvalide as e:
            raise HTTPException(503 if e.args[0] == "CHIFFREMENT_NON_CONFIGURE" else 422,
                                {"code": e.args[0], "champ": e.args[1]}) from None
        depot.enregistrer_connexion(c, source, chiffre)
        return {"source": source, "enregistree": True}

    @app.post("/api/connexions/SPAPI/test")
    def tester_connexion(d: dict, c: str = Depends(compte)):
        """[RM-AMZ-079] Une ligne par accès : OK ou refusé, message d'Amazon, identifiant de requête."""
        cx, cle = depot.connexions(c), CX.cle_serveur()
        if "SPAPI" not in cx:
            raise HTTPException(404, "CONNEXION_INTROUVABLE")
        if not cle:
            raise HTTPException(503, "CHIFFREMENT_NON_CONFIGURE")
        try:
            mp = get_marketplace(str(d.get("marketplace") or "FR"))
        except ValueError:
            raise HTTPException(422, "PLACE_INCONNUE") from None
        from .providers.spapi import ClientSPAPI
        v = CX.dechiffrer(cle, c, "SPAPI", cx["SPAPI"].chiffre)
        client = ClientSPAPI(client_id=v["client_id"], client_secret=v["client_secret"], seller_id=v.get("seller_id"),
                             refresh_tokens={v["region"]: v["refresh_token"]})
        if mp.region != v["region"]:
            raise HTTPException(422, "REGION_DIFFERENTE")
        return {"marketplace": mp.code, "etapes": client.tester(mp)}

    @app.get("/api/synchro/journal")
    def journal_synchro(c: str = Depends(compte)):
        """[RM-AMZ-080] 20 dernières tâches de nuit du compte."""
        j = sorted(depot.journal_synchro(c), key=lambda r: r.debut, reverse=True)[:20]
        return [{"tache": r.tache, "le": r.fin.isoformat(), "ok": r.ok, "message": r.message} for r in j]

    @app.delete("/api/connexions/{source}")
    def retirer_connexion(source: str, c: str = Depends(compte)):
        if not depot.supprimer_connexion(c, source):
            raise HTTPException(404, "CONNEXION_INTROUVABLE")
        return {"source": source, "retiree": True}

    # ------------------------------------------------------------- travaux de nuit lancés à la main [RM-AMZ-115]
    @app.get("/api/synchro/manuelle")
    def etat_synchro_manuelle(c: str = Depends(compte)):
        e = manuelles.etats.get(c)
        return {"taches": list(SN.TACHES), "etat": e}

    @app.post("/api/synchro/manuelle", status_code=202)
    def lancer_synchro_manuelle(d: DemandeSynchroManuelle, c: str = Depends(compte)):
        inconnues = [x for x in d.taches if x not in SN.TACHES]
        if inconnues or not d.taches:
            raise HTTPException(422, "TACHE_INCONNUE")
        cx = depot.connexions(c).get("SPAPI")
        cle = CX.cle_serveur()
        if cx is None or (cle is None and fabrique_spapi is None):
            raise HTTPException(503, "SOURCE_NON_CONFIGUREE")
        v = CX.dechiffrer(cle, c, "SPAPI", cx.chiffre) if cle else {"region": "EU"}
        client = (fabrique_spapi or SN.client_spapi)(v)
        if not manuelles.lancer(c, client, v.get("region", "EU"), depot, set(d.taches)):
            raise HTTPException(409, "SYNCHRO_EN_COURS")
        return {"lancee": True}

    # ------------------------------------------------------------- ce que je peux vendre [RM-AMZ-084, 085]
    @app.get("/api/exploration")
    def lire_exploration(c: str = Depends(compte)):
        prog = explorations.en_cours.get(c)
        return {"en_cours": prog is not None, "progression": list(prog) if prog else None,
                "resultat": depot.exploration(c), "rayons": [r for r, _ in EX.RAYONS]}

    @app.post("/api/exploration/vu")
    def exploration_vue(c: str = Depends(compte)):
        """[RM-AMZ-113] Les nouveautés ont été vues : pastilles retirées."""
        r = depot.exploration(c)
        if r and r.get("nouveautes") and not r["nouveautes"].get("vu"):
            depot.enregistrer_exploration(c, {**r, "nouveautes": {**r["nouveautes"], "vu": True}})
        return {"vu": True}

    @app.post("/api/exploration", status_code=202)
    def lancer_exploration(c: str = Depends(compte)):
        fx = sources(c)
        if not fx.catalogue or fx.restrictions is None or not any(hasattr(x, "rechercher") for x in fx.catalogue):
            raise HTTPException(503, "SOURCE_NON_CONFIGUREE")
        if not explorations.lancer(c, get_marketplace("FR"), fx, depot):
            raise HTTPException(409, "EXPLORATION_EN_COURS")
        return {"lancee": True}

    # ------------------------------------------------------------- d'Amazon vers les fournisseurs [RM-AMZ-109 à 112]
    @app.get("/api/produits/{marketplace}/{asin}/ou-acheter")
    def ou_acheter(marketplace: str, asin: str, c: str = Depends(compte)):
        mp = _place(marketplace)
        fx = sources(c)
        if not fx.catalogue:
            raise HTTPException(503, "SOURCE_NON_CONFIGUREE")
        p = params(c)
        return CO.ou_acheter(mp, asin.upper(), fx, depot, c, p, p.regime(mp.code))

    @app.get("/api/correspondance")
    def lire_correspondance(c: str = Depends(compte)):
        prog = correspondances.en_cours.get(c)
        return {"en_cours": prog is not None, "progression": list(prog[:2]) if prog else None,
                "phase": prog[2] if prog else None, "bilan": correspondances.bilans.get(c)}

    @app.post("/api/correspondance", status_code=202)
    def lancer_correspondance(c: str = Depends(compte)):
        fx = sources(c)
        if not fx.catalogue:
            raise HTTPException(503, "SOURCE_NON_CONFIGUREE")
        mp, p = get_marketplace("FR"), params(c)
        if not correspondances.lancer(c, mp, fx, depot, p, p.regime(mp.code)):
            raise HTTPException(409, "CORRESPONDANCE_EN_COURS")
        return {"lancee": True}

    # ------------------------------------------------------------- produits rentables [RM-AMZ-105 à 108]
    @app.get("/api/opportunites")
    def opportunites(tri: str = "profit", ordre: str = "desc", vendabilite: Optional[str] = None,
                     roi_min: Optional[float] = None, profit_min: Optional[float] = None,
                     marge_min: Optional[float] = None, origine: Optional[str] = None, verdict: Optional[str] = None,
                     amazon_absent: bool = False, c: str = Depends(compte)):
        ops = depot.opportunites(c)
        jour = H.jour_paris(datetime.now(timezone.utc))
        par_place: dict[str, list] = {}
        for o in ops:
            par_place.setdefault(o.marketplace, []).append(o.asin)
        rel: dict[tuple, list] = {}
        for mp_code, asins in par_place.items():                          # [RM-AMZ-108] rotation
            for r in depot.releves(c, mp_code, list(dict.fromkeys(asins)), jour - timedelta(days=30)):
                rel.setdefault((mp_code, r.asin), []).append(r)
        for o in ops:
            t = H.tendances(rel.get((o.marketplace, o.asin), []), jour, 30)
            o.historique_court = t["court"]
            o.rotation = None if t["court"] else t["jours_baisse_bsr"]
        niveaux = None if not vendabilite else set(vendabilite.split(","))
        if niveaux and not niveaux <= set(OP.NIVEAUX):
            raise HTTPException(422, "VENDABILITE_INCONNUE")
        try:
            liste = OP.filtrer_trier(ops, OP.Criteres(tri, ordre != "asc", niveaux, roi_min, profit_min, marge_min,
                                                      origine, verdict, amazon_absent))
        except ValueError:
            raise HTTPException(422, "TRI_INCONNU") from None
        origines = sorted({(o.origine, o.origine_nom) for o in ops}, key=lambda x: x[1].lower())
        return {
            "total": len(ops), "nombre": len(liste),
            "compteurs": {n: sum(1 for o in ops if o.vendabilite == n) for n in OP.NIVEAUX},
            "origines": [{"cle": k, "nom": n} for k, n in origines],
            "produits": [{k: getattr(o, k) for k in ("origine", "origine_nom", "marketplace", "code", "asin", "titre",
                          "designation", "prix_achat", "unites_lot", "cout_achat", "prix_vente", "profit", "roi", "marge",
                          "prix_achat_max", "verdict", "vendabilite", "motif", "bsr", "nb_vendeurs", "amazon_vend",
                          "rotation", "historique_court")} | {"analyse_le": o.analyse_le.isoformat() if o.analyse_le else None}
                         for o in liste[:2000]],
        }

    def _deblocages(ex):
        """[RM-AMZ-113] Nouveautés du dernier sondage, tant qu'elles n'ont pas été vues."""
        n = (ex or {}).get("nouveautes")
        if not n or n.get("vu") or not (n.get("rayons") or n.get("produits")):
            return None
        return {"rayons": n["rayons"], "produits": len(n["produits"]), "le": ex.get("le")}

    # ------------------------------------------------------------- tableau de bord [RM-AMZ-091 à 094]
    @app.get("/api/tableau")
    def tableau(c: str = Depends(compte)):
        p = params(c)
        maintenant = datetime.now(timezone.utc)
        jour = H.jour_paris(maintenant)
        lots, ventes = depot.lots(c), depot.ventes(c)
        jour_photo, photos = depot.photo_stock(c)
        stock = calculer_stock(photos, ventes, lots, jour_photo or jour, p.delai_fournisseur, p.delai_reception,
                               p.marge_securite, p.seuil_rupture, p.seuil_surstock)
        ch = TB.chiffres(lots, ventes, stock, jour)
        conf = CF.verifier(lots, photos, depot.fiches(c), depot.enregistrements(c))
        af = TB.a_faire(stock, depot.cas_remboursement(c), conf, depot.journal_synchro(c))
        asins = list(dict.fromkeys(depot.suivis(c, "FR") + depot.asins_analyses(
            c, "FR", maintenant - timedelta(days=H.JOURS_ANALYSES))))[:H.MAX_FAMILLE]
        mv = TB.mouvements(depot.releves(c, "FR", asins, jour - timedelta(days=7)), jour) if asins else []
        titres = {x.asin: x.titre for x in depot.produits_marche(c, "FR", asins=[m["asin"] for m in mv])} if mv else {}
        return {
            "devise": ch["devise"],
            "par_devise": {dv: {k: (_num(v) if isinstance(v, Decimal) else v) for k, v in x.items()}
                           for dv, x in ch["par_devise"].items()},
            "serie": [{"jour": s["jour"], "profit": _num(s["profit"])} for s in ch["serie"]],
            "ventes_non_rattachees": ch["ventes_non_rattachees"], "unites_sans_cout": ch["unites_sans_cout"],
            "a_faire": {**af, "carburant": p.carburant_taux if p.carburant_actif else None,
                        "deblocages": _deblocages(depot.exploration(c)),
                        "valeur_remboursements": {k: _num(v) for k, v in af["valeur_remboursements"].items()}},
            "mouvements": [{**m, "prix": _num(m["prix"]), "titre": titres.get(m["asin"])} for m in mv],
        }

    # ------------------------------------------------------------- historique et suivi de marché [RM-AMZ-086 à 090]
    def _place(code: str):
        try:
            return get_marketplace(code)
        except ValueError:
            raise HTTPException(422, "PLACE_INCONNUE") from None

    def _ligne_marche(p, rel: list, jour) -> dict:
        t = H.tendances(rel, jour, 30)
        d = rel[-1] if rel else None
        return {"asin": p.asin, "titre": p.titre, "marque": p.marque, "famille": p.famille,
                "dernier": d.jour.isoformat() if d else None,
                "prix": _num(d.prix_buybox) if d else None, "bsr": d.bsr if d else None,
                "vendeurs": ((d.nb_fba or 0) + (d.nb_fbm or 0)) if d and (d.nb_fba is not None or d.nb_fbm is not None) else None,
                "amazon_vend": d.amazon_vend if d else None,
                "tendance": {k: _num(v) if isinstance(v, Decimal) else v for k, v in t.items()}}

    @app.get("/api/marche")
    def marche(groupe: str = "SUIVI", marketplace: str = "FR", c: str = Depends(compte)):
        mp = _place(marketplace)
        jour = H.jour_paris(datetime.now(timezone.utc))
        if groupe == "SUIVI":
            asins = depot.suivis(c, mp.code)
        elif groupe == "ANALYSE":
            asins = depot.asins_analyses(c, mp.code, datetime.now(timezone.utc) - timedelta(days=H.JOURS_ANALYSES))
        elif groupe in H.FAMILLES:
            asins = [p.asin for p in depot.produits_marche(c, mp.code, famille=groupe)]
        else:
            raise HTTPException(422, "GROUPE_INCONNU")
        asins = asins[:H.MAX_FAMILLE]
        fiches = {p.asin: p for p in depot.produits_marche(c, mp.code, asins=asins)} if asins else {}
        rel: dict[str, list] = {}
        for r in depot.releves(c, mp.code, asins, jour - timedelta(days=30)) if asins else []:
            rel.setdefault(r.asin, []).append(r)
        lignes = [_ligne_marche(fiches.get(a) or H.ProduitMarche(mp.code, a), rel.get(a, []), jour) for a in asins]
        lignes.sort(key=lambda x: (x["bsr"] is None, x["bsr"] or 0))
        return {"groupe": groupe, "marketplace": mp.code, "familles": [
                    {"code": f, "suivie": f in depot.familles_suivies(c)} for f in H.FAMILLES],
                "suivis": len(depot.suivis(c, mp.code)), "produits": lignes}

    @app.put("/api/marche/familles")
    def familles(d: DemandeFamilles, c: str = Depends(compte)):
        inconnues = [f for f in d.familles if f not in H.FAMILLES]
        if inconnues:
            raise HTTPException(422, "FAMILLE_INCONNUE")
        depot.enregistrer_familles(c, d.familles)
        return {"familles": depot.familles_suivies(c)}

    @app.post("/api/marche/suivi", status_code=201)
    def suivre(d: DemandeSuiviProduit, c: str = Depends(compte)):
        mp = _place(d.marketplace)
        depot.ajouter_suivi(c, mp.code, d.asin.upper())
        return {"asin": d.asin.upper(), "marketplace": mp.code, "suivi": True}

    @app.delete("/api/marche/suivi/{marketplace}/{asin}")
    def ne_plus_suivre(marketplace: str, asin: str, c: str = Depends(compte)):
        if not depot.retirer_suivi(c, _place(marketplace).code, asin.upper()):
            raise HTTPException(404, "SUIVI_INTROUVABLE")
        return {"asin": asin.upper(), "suivi": False}

    @app.get("/api/marche/produit/{marketplace}/{asin}")
    def historique_produit(marketplace: str, asin: str, c: str = Depends(compte)):
        mp, asin = _place(marketplace), asin.upper()
        jour = H.jour_paris(datetime.now(timezone.utc))
        rel = depot.releves(c, mp.code, [asin], jour - timedelta(days=90))
        fiche = next(iter(depot.produits_marche(c, mp.code, asins=[asin])), None)
        return {"asin": asin, "marketplace": mp.code, "titre": fiche.titre if fiche else None,
                "suivi": asin in depot.suivis(c, mp.code),
                "releves": [{"jour": r.jour.isoformat(), "prix": _num(r.prix_buybox), "bsr": r.bsr,
                             "vendeurs": None if r.nb_fba is None and r.nb_fbm is None else (r.nb_fba or 0) + (r.nb_fbm or 0),
                             "amazon_vend": r.amazon_vend, "buybox_amazon": r.buybox_amazon} for r in rel],
                "tendances": {str(n): {k: _num(v) if isinstance(v, Decimal) else v
                                       for k, v in H.tendances(rel, jour, n).items()} for n in (7, 30)}}

    # ------------------------------------------------------------- conformité [RM-AMZ-060 à 067]
    @app.get("/api/conformite")
    def conformite(c: str = Depends(compte)):
        enregs = depot.enregistrements(c)
        fiches = depot.fiches(c)
        _, photos = depot.photo_stock(c)
        lignes = CF.verifier(depot.lots(c), photos, fiches, enregs)
        return {
            "produits": [{"asin": l.asin, "designation": l.designation, "places": list(l.places), "statut": l.statut,
                          "alertes": [x.to_dict() for x in l.alertes],
                          "fiche": (fiches.get(l.asin) or CF.Fiche(l.asin)).to_dict()} for l in lignes],
            "enregistrements": [_enreg_json(e) for e in enregs],
            "compteurs": {"a_completer": sum(1 for l in lignes if l.statut == "A_COMPLETER"),
                          "rien_de_signale": sum(1 for l in lignes if l.statut == "RIEN_DE_SIGNALE"),
                          "non_couverts": sum(1 for l in lignes if l.statut == "NON_COUVERT")},
            "textes": [{"code": t.code, "reference": t.reference, "url": t.url, "verifie": t.verifie, "note": t.note}
                       for t in CF.TEXTES.values()],
            "date_lecture": CF.DATE_LECTURE, "places_ue": list(CF.PLACES_UE), "filieres": list(CF.FILIERES),
        }

    @app.post("/api/conformite/enregistrements")
    def enregistrer_conformite(d: DemandeEnregistrement, c: str = Depends(compte)):
        try:
            e = CF.nouvel_enregistrement(d.pays, d.filiere, d.numero, d.intitule, d.mandataire)
        except CF.SaisieInvalide as x:
            raise HTTPException(422, {"code": x.args[0], "champ": x.args[1]}) from None
        depot.enregistrer_enregistrement(c, e)
        return _enreg_json(e)

    @app.delete("/api/conformite/enregistrements/{cle:path}")
    def supprimer_conformite(cle: str, c: str = Depends(compte)):
        if not depot.supprimer_enregistrement(c, cle):
            raise HTTPException(404, "ENREGISTREMENT_INTROUVABLE")
        return {"supprime": cle}

    @app.put("/api/conformite/fiches/{asin}")
    def fiche_conformite(asin: str, brut: dict, c: str = Depends(compte)):
        if not (1 <= len(asin) <= 20) or not asin.isalnum():
            raise HTTPException(422, {"code": "SAISIE_INVALIDE", "champ": "asin"})
        try:
            f = CF.valider_fiche(asin, brut)
        except CF.SaisieInvalide as x:
            raise HTTPException(422, {"code": x.args[0], "champ": x.args[1]}) from None
        depot.enregistrer_fiche(c, f)
        return f.to_dict()

    # ------------------------------------------------------------- stock [RM-AMZ-045 à 048]
    @app.get("/api/stock")
    def stock(c: str = Depends(compte)):
        p = params(c)
        jour, photos = depot.photo_stock(c)
        reference = jour or date.today()
        lignes = calculer_stock(photos, depot.ventes(c), depot.lots(c), reference, p.delai_fournisseur,
                                p.delai_reception, p.marge_securite, p.seuil_rupture, p.seuil_surstock)
        return {
            "jour": None if jour is None else jour.isoformat(),
            "lignes": [{"marketplace": l.photo.marketplace, "sku": l.photo.sku, "asin": l.photo.asin,
                        "designation": l.photo.designation, "disponible": l.photo.disponible,
                        "en_route": l.photo.en_route, "reserve": l.photo.reserve, "invendable": l.photo.invendable,
                        "vendus_30j": l.vendus_30j, "vitesse": float(round(l.vitesse, 2)), "couverture": l.couverture,
                        "rupture_le": None if l.rupture_le is None else l.rupture_le.isoformat(),
                        "a_commander": l.a_commander, "fournisseur": l.fournisseur,
                        "cout_unitaire": _num(l.cout_unitaire), "devise": l.devise,
                        "alertes": [x.to_dict() for x in l.alertes]} for l in lignes],
            "commandes": [{"fournisseur": g.fournisseur, "lignes": g.lignes, "unites": g.unites,
                           "montant": _num(g.montant), "devise": g.devise} for g in commandes_par_fournisseur(lignes)],
            "compteurs": {"unites": sum(l.photo.disponible + l.photo.en_route for l in lignes),
                          "ruptures": sum(1 for l in lignes if any(a.code == "S_RUPTURE" for a in l.alertes)),
                          "surstocks": sum(1 for l in lignes if any(a.code in ("S_SURSTOCK", "S_SANS_VENTE") for a in l.alertes))},
        }

    # ------------------------------------------------------------- lots
    def resultats(c: str):
        return rattacher_fifo(depot.lots(c), depot.ventes(c))

    @app.get("/api/lots")
    def lister_lots(c: str = Depends(compte)):
        res, orphelines = resultats(c)
        lots = sorted((_resume(r) for r in res.values()), key=lambda x: x["date_achat"], reverse=True)
        return {"lots": lots, "ventes_non_rattachees": len(orphelines), "demo": demo}

    @app.get("/api/lots/{lot_id}")
    def detail_lot(lot_id: str, c: str = Depends(compte)):
        try:
            depot.lot(c, lot_id)
        except AccesRefuse:
            raise HTTPException(404, "LOT_INTROUVABLE") from None
        res, _ = resultats(c)
        if lot_id not in res:                   # version remplacée : on montre la version en vigueur
            raise HTTPException(404, "LOT_REMPLACE")
        return _detail(res[lot_id])

    # ------------------------------------------------------------- analyse [RM-AMZ-028]
    @app.get("/api/places")
    def places():
        return [{"code": m.code, "domaine": m.domaine, "devise": m.devise} for m in MARKETPLACES.values()]

    @app.post("/api/analyse")
    def analyser(d: DemandeAnalyse, c: str = Depends(compte)):
        try:
            mp = get_marketplace(d.marketplace)
        except ValueError:
            raise HTTPException(422, "PLACE_INCONNUE") from None
        p = params(c)
        regime = d.regime_tva or p.regime(mp.code)
        if regime not in REGIMES_TVA:
            raise HTTPException(422, "REGIME_TVA_INCONNU")
        fx = sources(c)
        if not fx.catalogue:  # [RM-AMZ-071]
            raise HTTPException(503, "SOURCE_NON_CONFIGUREE")
        try:
            asins = resoudre_asins(mp, d.code, fx)
        except ErreurFournisseur:
            raise HTTPException(502, "SOURCE_INDISPONIBLE") from None
        if not asins:
            raise HTTPException(404, "PRODUIT_INTROUVABLE")
        depot.memoriser_appariement(c, mp.code, d.code.strip().upper(), asins)   # relevé de nuit [RM-AMZ-086]
        couts = p.couts(d.prix_achat, d.achat_ttc, d.taux_tva)
        if d.port_fournisseur is not None:
            from dataclasses import replace as _remplacer
            couts = _remplacer(couts, port_fournisseur=d.port_fournisseur)
        sortie = []
        for asin in asins:
            a = analyser_asin(mp, asin, couts, fx, regime, p.seuils(), d.prix_vente, d.taux_tva, **p.options_cout())
            jeton = str(uuid.uuid4())
            analyses[jeton] = (c, a, couts)
            while len(analyses) > 500:
                analyses.popitem(last=False)
            sortie.append(_analyse_json(a, jeton))
        return {"analyses": sortie}

    @app.post("/api/lots", status_code=201)
    def creer_lot(d: DemandeLot, c: str = Depends(compte)):
        """[RM-AMZ-029] La prévision vient de l'analyse gardée côté serveur, jamais du navigateur."""
        if d.jeton_analyse in utilisees:
            raise HTTPException(409, "ANALYSE_DEJA_UTILISEE")
        trouve = analyses.get(d.jeton_analyse)
        if trouve is None or trouve[0] != c:     # [RM-AMZ-039] analyse d'un autre compte = introuvable
            raise HTTPException(404, "ANALYSE_EXPIREE")
        _, a, couts = trouve
        if a.rentabilite is None:
            raise HTTPException(409, "ANALYSE_SANS_RENTABILITE")
        mp = get_marketplace(a.marketplace)
        sources = ["prix:" + a.origine_prix, "frais:" + (a.frais.source if a.frais else "aucun")]
        lot = Lot(c, a.asin, a.marketplace, d.quantite, d.date_achat or date.today(),
                  prevision_depuis_analyse(a.rentabilite, couts, mp.devise, sources),
                  fournisseur=(d.fournisseur or "").strip() or None, designation=a.catalogue.titre)
        depot.ajouter_lot(c, lot)
        del analyses[d.jeton_analyse]
        utilisees.add(d.jeton_analyse)
        return {"id": lot.id}

    # ------------------------------------------------------------- sourcing par fichier [RM-AMZ-030 à 035]
    @app.post("/api/sourcing/fichiers", status_code=201)
    async def deposer_fichier(fichier: UploadFile = File(...), c: str = Depends(compte)):
        contenu = await fichier.read(fich.MAX_OCTETS + 1)
        try:
            table = fich.lire(contenu, fichier.filename or "")
        except fich.FichierInvalide as e:
            raise HTTPException(422, e.args[0]) from None
        fid = str(uuid.uuid4())
        fichiers[fid] = (c, fichier.filename or "", table)
        while len(fichiers) > 50:
            fichiers.popitem(last=False)
        return {"fichier_id": fid, "nom": fichier.filename, "entetes": table.entetes, "apercu": table.lignes[:5],
                "nb_lignes": len(table.lignes), "colonnes": fich.proposer_colonnes(table.entetes)}

    @app.post("/api/sourcing/fichiers/{fid}/traitements", status_code=201)
    def lancer_traitement(fid: str, d: DemandeTraitement, c: str = Depends(compte)):
        fx = sources(c)
        if not fx.catalogue:  # [RM-AMZ-071]
            raise HTTPException(503, "SOURCE_NON_CONFIGUREE")
        f = fichiers.get(fid)
        if f is None or f[0] != c:
            raise HTTPException(404, "FICHIER_EXPIRE")
        try:
            mp = get_marketplace(d.marketplace)
        except ValueError:
            raise HTTPException(422, "PLACE_INCONNUE") from None
        p = params(c)
        regime = d.regime_tva or p.regime(mp.code)
        if regime not in REGIMES_TVA:
            raise HTTPException(422, "REGIME_TVA_INCONNU")
        colonnes = {r: d.colonnes.get(r) for r in fich.ROLES}
        try:
            prep = fich.preparer(f[2], colonnes, d.prix_par_carton)
        except fich.FichierInvalide as e:
            raise HTTPException(422, e.args[0]) from None
        t = traitements.lancer(c, prep, mp, fx, depot, regime, d.achat_ttc, p.seuils(),
                               en_fond=traitement_en_fond, parametres=p, origine=(f"FICHIER:{f[1]}", f[1]))
        return {"traitement_id": t.id}

    @app.get("/api/sourcing/traitements/{tid}")
    def suivre_traitement(tid: str, c: str = Depends(compte)):
        t = traitements.obtenir(c, tid)
        if t is None:
            raise HTTPException(404, "TRAITEMENT_INTROUVABLE")
        res = t.tries()
        n = lambda v: sum(1 for r in res if r.verdict == v and r.statut == "ANALYSEE")  # noqa: E731
        return {
            "statut": t.statut, "total": t.total, "faits": t.faits, "marketplace": t.marketplace,
            "devise": get_marketplace(t.marketplace).devise,
            "compteurs": {"ACHETER": n("ACHETER"), "A_VERIFIER": n("A_VERIFIER"), "PASSER": n("PASSER"),
                          "INTROUVABLE": sum(1 for r in res if r.statut == "INTROUVABLE"),
                          "ERREUR_SOURCE": sum(1 for r in res if r.statut == "ERREUR_SOURCE"),
                          "REJETEE": len(t.rejets), "DOUBLON": len(t.doublons), "MEMOIRE": t.appariements_memoire},
            "resultats": [_resultat_json(r) for r in res],
            "rejets": [{"ligne": k, "message": msg.to_dict()} for k, msg in t.rejets],
            "doublons": [{"ligne": k, "code": code} for k, code in t.doublons],
        }

    @app.get("/api/sourcing/traitements/{tid}/export.csv")
    def exporter(tid: str, c: str = Depends(compte)):
        t = traitements.obtenir(c, tid)
        if t is None:
            raise HTTPException(404, "TRAITEMENT_INTROUVABLE")
        return Response(export_csv(t, texte_fr), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="sourcing-{tid[:8]}.csv"'})

    # ------------------------------------------------------------- interface
    if servir_interface and DIST.exists():
        app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

        @app.get("/{chemin:path}", include_in_schema=False)
        def interface(chemin: str):
            if chemin.startswith("api/"):
                raise HTTPException(404, "INTROUVABLE")
            return FileResponse(DIST / "index.html")
    return app


def app_depuis_environnement() -> FastAPI:
    """D-AMZ-019 : `dev` = démonstration sans connexion ; `prod` = Postgres + connexion obligatoire."""
    mode = os.environ.get("AMZ_MODE")
    if mode == "dev":
        from .demo_donnees import construire, historique_demo, opportunites_demo
        from .historique import jour_paris
        from .providers.demo import FournisseurDemo
        depot, c = construire()
        historique_demo(depot, c, jour_paris(datetime.now(timezone.utc)))
        d = FournisseurDemo()
        opportunites_demo(depot, c, Fournisseurs([d], d, d, d, d))
        sondage = EX.en_json(EX.sonder(get_marketplace("FR"), Fournisseurs([d], d, d, d, d), attendre=lambda s: None),
                             "FR", datetime.now(timezone.utc))
        veille = {**sondage, "le": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),   # démo : rayon débloqué
                  "rayons": [{**r, "statut": "FERME", "autorises": 0, "approbation": r["testes"]} if r["code"] == "SPORT"
                             else r for r in sondage["rayons"]]}
        depot.enregistrer_exploration(c, veille)
        EX.enregistrer(depot, c, sondage)
        return creer_app(depot, c, demo=True, fournisseurs=Fournisseurs([d], d, d, d, d))
    if mode == "prod":
        url = os.environ.get("AMZ_DATABASE_URL")
        if not url:
            raise SystemExit("AMZ_DATABASE_URL requis en mode prod.")
        from .auth import StockAuthPostgres
        from .cli import construire_fournisseurs
        from .db import DepotPostgres, Reserve
        reserve = Reserve(url)
        f, _ = construire_fournisseurs(demo=False)
        return creer_app(DepotPostgres(reserve), auth=Authentification(StockAuthPostgres(reserve)), fournisseurs=f,
                         cookie_secure=True)
    raise SystemExit("AMZ_MODE doit valoir dev ou prod (D-AMZ-019).")
