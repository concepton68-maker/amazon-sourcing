"""Comparaison entre pays européens — [RM-AMZ-117]. Montants jamais convertis entre devises."""
from __future__ import annotations

from typing import Optional

from .analyse import analyser_asin, resoudre_asins
from .marketplaces import MARKETPLACES
from .messages import m

EUROPE = ("FR", "DE", "IT", "ES", "NL", "BE", "IE", "PL", "SE", "UK")


def places_europe(fx) -> list:
    """Places européennes où le vendeur est inscrit ; sans source capable de le dire : places en euros."""
    src = next((s for s in fx.catalogue if hasattr(s, "participations")), None)
    if src is not None:
        try:
            ids = set(src.participations(MARKETPLACES["FR"]))
            return [MARKETPLACES[c] for c in EUROPE if MARKETPLACES[c].marketplace_id in ids]
        except Exception:
            pass
    return [MARKETPLACES[c] for c in EUROPE if MARKETPLACES[c].devise == "EUR"]


def comparer(code: str, prix_achat: float, fx, parametres, achat_ttc: bool = False,
             taux_tva: Optional[float] = None, places=None) -> list[dict]:
    out = []
    for mp in places if places is not None else places_europe(fx):
        try:
            asins = resoudre_asins(mp, code, fx)
            if not asins:
                out.append({"marketplace": mp.code, "devise": mp.devise, "erreur": "PRODUIT_INTROUVABLE"})
                continue
            a = analyser_asin(mp, asins[0], parametres.couts(prix_achat, achat_ttc, taux_tva), fx,
                              parametres.regime(mp.code), parametres.seuils(), None, taux_tva,
                              **parametres.options_cout())
            r = a.rentabilite
            hyp = [m("HYP_STOCK_PAYS_UK" if mp.code == "UK" else "HYP_STOCK_PAYS")] if mp.code != "FR" else []
            out.append({"marketplace": mp.code, "devise": mp.devise, "asin": a.asin, "titre": a.catalogue.titre,
                        "prix_vente": a.prix_vente_retenu, "profit": r.profit_net if r else None,
                        "roi": r.roi if r else None, "marge": r.marge if r else None,
                        "prix_achat_max": r.prix_achat_max_pour_roi if r else None, "verdict": a.verdict,
                        "autorise": a.restrictions.autorise if a.restrictions else None,
                        "vendeurs": None if not a.offres else (a.offres.nb_offres_fba or 0) + (a.offres.nb_offres_fbm or 0),
                        "amazon_vend": a.offres.amazon_vend if a.offres else None,
                        "hypotheses": [x.to_dict() for x in hyp]})
        except Exception as e:
            out.append({"marketplace": mp.code, "devise": mp.devise, "erreur": type(e).__name__})
    euros = sorted([x for x in out if x["devise"] == "EUR" and x.get("profit") is not None],
                   key=lambda x: -x["profit"])
    reste = [x for x in out if x not in euros]
    return euros + sorted(reste, key=lambda x: (x["devise"], -(x.get("profit") or -1e9)))
