"""Prix plancher — [RM-AMZ-122]. Le plus bas prix de vente qui garde le profit minimum, coût complet compris."""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from .profit import FraisAmazon, ParametresCout, calculer_rentabilite


def prix_plancher(mp, prix_actuel: float, frais: FraisAmazon, couts: ParametresCout, regime: str,
                  profit_min: float, taux_tva_vente: Optional[float] = None) -> Optional[float]:
    """Recherche par dichotomie ; commission proportionnelle au prix, autres frais fixes. None si inatteignable."""
    if not prix_actuel or prix_actuel <= 0:
        return None
    ratio = frais.commission / prix_actuel

    def profit(p: float) -> float:
        f = replace(frais, commission=ratio * p)
        return calculer_rentabilite(mp, p, f, couts, regime, taux_tva_vente=taux_tva_vente).profit_net

    bas, haut = 0.01, prix_actuel * 5
    if profit(haut) < profit_min:
        return None
    for _ in range(60):
        milieu = (bas + haut) / 2
        if profit(milieu) >= profit_min:
            haut = milieu
        else:
            bas = milieu
    p = round(haut + 0.0049, 2)                          # arrondi au centime supérieur
    return p if profit(p) >= profit_min - 0.005 else round(p + 0.01, 2)
