"""Parcours complet sur données FICTIVES : analyse → lot figé → synchro Amazon simulée → prévu vs réel.

python -m sourcing parcours-demo
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from .analyse import Fournisseurs, analyser_asin
from .depot import DepotMemoire
from .lots import Lot, decomposer_ecart, prevision_depuis_analyse, rattacher_fifo
from .marketplaces import get_marketplace
from .profit import ParametresCout
from .providers.demo import FournisseurDemo
from .sync import synchroniser

COMPTE = "compte-demo"
NOMS = {"prix": "Prix de vente", "frais_amazon": "Frais Amazon", "retours": "Retours",
        "stockage": "Stockage", "autres": "Autres"}


def _eur(v):
    return {"currencyCode": "EUR", "currencyAmount": v}


def _tx(tid, jour, commande, montants, qte=1, statut="RELEASED", desc="Order Payment"):
    fr = get_marketplace("FR")
    return {"transactionId": tid, "transactionType": "Shipment", "transactionStatus": statut, "description": desc,
            "postedDate": f"{jour}T10:00:00Z", "marketplaceDetails": {"marketplaceId": fr.marketplace_id},
            "relatedIdentifiers": [{"relatedIdentifierName": "ORDER_ID", "relatedIdentifierValue": commande}],
            "items": [{"breakdowns": [{"breakdownType": k, "breakdownAmount": _eur(v)} for k, v in montants.items()],
                       "contexts": [{"contextType": "ProductContext", "asin": "B0DEMO0001", "quantityShipped": qte}]}]}


class _AmazonSimule:
    """Ventes fictives : 18 ventes, dont une baisse de prix, un remboursement et un frais inconnu."""
    def page_transactions(self, mp, debut, fin, jeton):
        txs = []
        for i in range(18):
            prix_ht = 20.75 if i < 10 else 17.92          # baisse de prix après 10 ventes
            frais = -7.89 if i < 10 else -7.46
            txs.append(_tx(f"V{i}", f"2026-10-{1 + i:02d}", f"C{i}",
                           {"Principal": prix_ht, "Tax": round(prix_ht * 0.2, 2), "FraisFBA": frais / 2,
                            "Commission": frais / 2}, statut="DEFERRED" if i >= 16 else "RELEASED"))
        txs.append(_tx("R1", "2026-11-03", "C4", {"Principal": -20.75, "Commission": 0.60}, qte=0, desc="Refund Order"))
        txs.append(_tx("S1", "2026-11-05", "C5", {"FraisInconnuX": -0.35}, qte=0))
        return {"payload": {"transactions": txs}}


def executer() -> str:
    fr = get_marketplace("FR")
    d = FournisseurDemo()
    couts = ParametresCout(8.50, taux_retours=0.02)
    analyse = analyser_asin(fr, "B0DEMO0001", couts, Fournisseurs([d], d, d, d, d))
    prevision = prevision_depuis_analyse(analyse.rentabilite, couts, "EUR", ["démo"])
    depot = DepotMemoire()
    lot = Lot(COMPTE, "B0DEMO0001", "FR", 30, date(2026, 9, 20), prevision, fournisseur="Grossiste A (fictif)")
    depot.ajouter_lot(COMPTE, lot)
    rapport = synchroniser(COMPTE, fr, _AmazonSimule(), depot, datetime(2026, 11, 12, 3, tzinfo=timezone.utc),
                           classement={"FraisFBA": "frais_amazon", "Commission": "frais_amazon"},
                           attendre=lambda s: None)
    res, orphelines = rattacher_fifo(depot.lots(COMPTE), depot.ventes(COMPTE))
    r = res[lot.id]
    e = decomposer_ecart(r)
    pct = lambda x: "n/d" if x is None else f"{float(x):.0%}"  # noqa: E731
    L = ["DONNÉES FICTIVES", "",
         f"1. Analyse      {analyse.catalogue.titre} · verdict {analyse.verdict} · ROI prévu {pct(prevision.roi)}",
         f"2. Lot figé     {lot.quantite} unités · {lot.fournisseur} · profit prévu {prevision.profit:.2f} €/u",
         f"3. Synchro      {rapport.lignes} lignes Amazon · {rapport.ventes} rattachables · "
         f"types inconnus : {', '.join(rapport.types_inconnus) or 'aucun'}",
         f"4. Résultat     {r.quantite_vendue} vendues · profit réel {r.profit_reel.arrondi().valeur} € "
         f"· prévu {e.profit_prevu:.2f} € · ROI {pct(e.roi_prevu)} → {pct(e.roi_reel)}",
         f"               dont à encaisser : {r.a_encaisser.arrondi().valeur} €", "",
         "   Écart par cause (€, + = mieux que prévu)"]
    for cause, v in e.causes_par_ordre():
        L.append(f"   {NOMS[cause]:<15}{v:>+9.2f}")
    L.append(f"   {'Total':<15}{e.total:>+9.2f}")
    if orphelines:
        L.append(f"\n   Non rattachées : {len(orphelines)} ligne(s)")
    return "\n".join(L)
