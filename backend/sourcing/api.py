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

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .depot import AccesRefuse
from .lots import ResultatLot, decomposer_ecart, rattacher_fifo

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


def creer_app(depot, compte_id: str, servir_interface: bool = True, demo: bool = False) -> FastAPI:
    app = FastAPI(title="Syllig Vente", docs_url="/api/docs", openapi_url="/api/openapi.json")

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
        return creer_app(DepotPostgres(psycopg.connect(url, autocommit=True)), compte)
    from .demo_donnees import construire
    depot, compte = construire()
    return creer_app(depot, compte, demo=True)
