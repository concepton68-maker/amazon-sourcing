"""API web de Syllig Vente — écran « Achats & lots » [RM-AMZ-024, 025, 026].

Lancement : `AMZ_MODE=dev python -m sourcing serveur` (D-AMZ-017 : aucun autre mode tant que la
connexion des utilisateurs n'existe pas). Les montants sont des chaînes décimales avec leur devise ;
les textes sont des codes traduits par l'interface.
"""
from __future__ import annotations

import os
import pathlib
from decimal import Decimal
from typing import Optional

import uuid
from collections import OrderedDict
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .analyse import AnalyseProduit, Fournisseurs, Seuils, analyser_asin, resoudre_asins
from .depot import AccesRefuse
from .lots import Lot, ResultatLot, decomposer_ecart, prevision_depuis_analyse, rattacher_fifo
from .marketplaces import MARKETPLACES, get_marketplace
from .profit import REGIMES_TVA, ParametresCout
from .providers.base import ErreurFournisseur

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
    regime_tva: str = "assujetti"
    taux_tva: Optional[float] = Field(default=None, ge=0, lt=1)
    prix_vente: Optional[float] = Field(default=None, gt=0)


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
            "roi_cible": r.roi_cible, "regime_tva": r.regime_tva, "hypotheses": msgs(r.hypotheses)},
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


def creer_app(depot, compte_id: str, servir_interface: bool = True, demo: bool = False,
              fournisseurs: Optional[Fournisseurs] = None, seuils: Optional[Seuils] = None) -> FastAPI:
    app = FastAPI(title="Syllig Vente", docs_url="/api/docs", openapi_url="/api/openapi.json")
    fournisseurs = fournisseurs or Fournisseurs()
    seuils = seuils or Seuils()
    analyses: "OrderedDict[str, tuple[AnalyseProduit, ParametresCout]]" = OrderedDict()  # gardées côté serveur
    utilisees: set[str] = set()  # [RM-AMZ-029] une analyse, un lot

    @app.get("/api/places")
    def places():
        return [{"code": m.code, "domaine": m.domaine, "devise": m.devise} for m in MARKETPLACES.values()]

    @app.post("/api/analyse")
    def analyser(d: DemandeAnalyse):
        try:
            mp = get_marketplace(d.marketplace)
        except ValueError:
            raise HTTPException(422, "PLACE_INCONNUE") from None
        if d.regime_tva not in REGIMES_TVA:
            raise HTTPException(422, "REGIME_TVA_INCONNU")
        try:
            asins = resoudre_asins(mp, d.code, fournisseurs)
        except ErreurFournisseur:
            raise HTTPException(502, "SOURCE_INDISPONIBLE") from None
        if not asins:
            raise HTTPException(404, "PRODUIT_INTROUVABLE")
        couts = ParametresCout(prix_achat=d.prix_achat, prix_achat_ttc=d.achat_ttc, taux_tva_achat=d.taux_tva)
        sortie = []
        for asin in asins:
            a = analyser_asin(mp, asin, couts, fournisseurs, d.regime_tva, seuils, d.prix_vente, d.taux_tva)
            jeton = str(uuid.uuid4())
            analyses[jeton] = (a, couts)
            while len(analyses) > 500:
                analyses.popitem(last=False)
            sortie.append(_analyse_json(a, jeton))
        return {"analyses": sortie}

    @app.post("/api/lots", status_code=201)
    def creer_lot(d: DemandeLot):
        """[RM-AMZ-029] La prévision vient de l'analyse gardée côté serveur, jamais du navigateur."""
        if d.jeton_analyse in utilisees:
            raise HTTPException(409, "ANALYSE_DEJA_UTILISEE")
        trouve = analyses.get(d.jeton_analyse)
        if trouve is None:
            raise HTTPException(404, "ANALYSE_EXPIREE")
        a, couts = trouve
        if a.rentabilite is None:
            raise HTTPException(409, "ANALYSE_SANS_RENTABILITE")
        mp = get_marketplace(a.marketplace)
        sources = ["prix:" + a.origine_prix, "frais:" + (a.frais.source if a.frais else "aucun")]
        lot = Lot(compte_id, a.asin, a.marketplace, d.quantite, d.date_achat or date.today(),
                  prevision_depuis_analyse(a.rentabilite, couts, mp.devise, sources),
                  fournisseur=(d.fournisseur or "").strip() or None, designation=a.catalogue.titre)
        depot.ajouter_lot(compte_id, lot)
        del analyses[d.jeton_analyse]
        utilisees.add(d.jeton_analyse)
        return {"id": lot.id}

    def resultats():
        res, orphelines = rattacher_fifo(depot.lots(compte_id), depot.ventes(compte_id))
        return res, orphelines

    @app.get("/api/lots")
    def lister_lots():
        res, orphelines = resultats()
        lots = sorted((_resume(r) for r in res.values()), key=lambda x: x["date_achat"], reverse=True)
        return {"lots": lots, "ventes_non_rattachees": len(orphelines), "demo": demo}

    @app.get("/api/lots/{lot_id}")
    def detail_lot(lot_id: str):
        try:
            depot.lot(compte_id, lot_id)
        except AccesRefuse:
            raise HTTPException(404, "LOT_INTROUVABLE") from None
        res, _ = resultats()
        if lot_id not in res:                   # version remplacée : on montre la version en vigueur
            raise HTTPException(404, "LOT_REMPLACE")
        return _detail(res[lot_id])

    if servir_interface and DIST.exists():
        app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

        @app.get("/{chemin:path}", include_in_schema=False)
        def interface(chemin: str):
            return FileResponse(DIST / "index.html")
    return app


def app_depuis_environnement() -> FastAPI:
    """D-AMZ-017 : refuse de démarrer hors mode dev tant que la connexion des utilisateurs n'existe pas."""
    if os.environ.get("AMZ_MODE") != "dev":
        raise SystemExit("AMZ_MODE=dev requis : l'authentification n'existe pas encore (D-AMZ-017).")
    url = os.environ.get("AMZ_DATABASE_URL")
    if url:
        import psycopg

        from .db import DepotPostgres
        compte = os.environ.get("AMZ_COMPTE_ID")
        if not compte:
            raise SystemExit("AMZ_COMPTE_ID requis avec AMZ_DATABASE_URL.")
        from .cli import construire_fournisseurs
        f, _ = construire_fournisseurs(demo=False)
        return creer_app(DepotPostgres(psycopg.connect(url, autocommit=True)), compte, fournisseurs=f)
    from .demo_donnees import construire
    from .providers.demo import FournisseurDemo
    depot, compte = construire()
    d = FournisseurDemo()
    return creer_app(depot, compte, demo=True, fournisseurs=Fournisseurs([d], d, d, d, d))
