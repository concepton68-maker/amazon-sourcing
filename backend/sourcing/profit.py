"""Moteur de calcul de rentabilité.

Principe : tous les montants sont dans la devise de la place de marché.
Chaque hypothèse est rendue explicite dans le résultat (`hypotheses`) pour
que l'utilisateur sache exactement ce qui a été calculé et ce qui a été supposé.

Régimes de TVA gérés :
- "assujetti"      : vendeur immatriculé à la TVA dans le pays de vente.
                     TVA collectée reversée, TVA sur achats et sur frais Amazon récupérées.
- "non_assujetti"  : pas de TVA collectée ni récupérée ; la TVA payée
                     (achat, frais Amazon) est un coût.
- "hors_taxe"      : place de marché à prix HT (US, CA) : aucune TVA dans le calcul.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

from .marketplaces import Marketplace

REGIMES_TVA = ("assujetti", "non_assujetti", "hors_taxe")


@dataclass
class FraisAmazon:
    """Frais Amazon par unité, HORS TVA."""
    commission: float                # referral fee
    fba: float = 0.0                 # frais d'expédition FBA
    cloture: float = 0.0             # variable closing fee (médias)
    autres: float = 0.0              # DST, surcharges...
    source: str = "saisie"           # "sp-api", "estimation", "saisie"

    @property
    def total_ht(self) -> float:
        return self.commission + self.fba + self.cloture + self.autres


@dataclass
class ParametresCout:
    prix_achat: float                    # prix d'achat unitaire tel que facturé
    prix_achat_ttc: bool = False         # True si le prix d'achat inclut la TVA
    taux_tva_achat: Optional[float] = None  # défaut : taux de la place de marché
    envoi_entrepot: float = 0.0          # transport jusqu'à l'entrepôt Amazon, par unité (HT)
    preparation: float = 0.0             # prep / étiquetage, par unité (HT)
    stockage_estime: float = 0.0         # stockage FBA estimé par unité (HT)
    taux_retours: float = 0.0            # provision retours, en % du prix de vente (0.03 = 3 %)
    autres_couts: float = 0.0            # tout autre coût unitaire (HT)


@dataclass
class ResultatRentabilite:
    prix_vente: float
    prix_vente_ht: float
    tva_collectee: float
    cout_achat_net: float
    frais_amazon: float
    tva_sur_frais_non_recuperable: float
    autres_couts: float
    profit_net: float
    roi: Optional[float]           # profit / coût d'achat net
    marge: Optional[float]         # profit / prix de vente TTC
    prix_achat_max_pour_roi: Optional[float]  # prix d'achat max (même base que la saisie) pour atteindre le ROI cible
    roi_cible: float
    regime_tva: str
    hypotheses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def calculer_rentabilite(
    mp: Marketplace,
    prix_vente: float,
    frais: FraisAmazon,
    couts: ParametresCout,
    regime_tva: str = "assujetti",
    taux_tva_vente: Optional[float] = None,
    taux_tva_frais: Optional[float] = None,
    roi_cible: float = 0.30,
) -> ResultatRentabilite:
    """Calcule le profit net unitaire d'une vente.

    `prix_vente` est le prix tel qu'affiché sur Amazon (TTC en UE/UK, HT aux US/CA).
    `taux_tva_frais` : TVA facturée par Amazon sur ses frais (par défaut le taux du pays).
    """
    if regime_tva not in REGIMES_TVA:
        raise ValueError(f"Régime TVA inconnu : {regime_tva} (attendus : {REGIMES_TVA})")
    if prix_vente <= 0:
        raise ValueError("Le prix de vente doit être positif.")

    hyp: list[str] = []
    if not mp.prix_ttc or mp.taux_tva_standard == 0:
        if regime_tva != "hors_taxe":
            hyp.append(f"{mp.code} : prix affichés hors taxe ou TVA non modélisée -> calcul sans TVA.")
        regime_tva = "hors_taxe"

    t_vente = mp.taux_tva_standard if taux_tva_vente is None else taux_tva_vente
    t_frais = mp.taux_tva_standard if taux_tva_frais is None else taux_tva_frais
    t_achat = mp.taux_tva_standard if couts.taux_tva_achat is None else couts.taux_tva_achat

    # --- Vente ---
    if regime_tva == "assujetti":
        prix_ht = prix_vente / (1 + t_vente)
        tva_collectee = prix_vente - prix_ht
        hyp.append(f"TVA collectée au taux {t_vente:.1%} (taux standard {mp.code} sauf surcharge ; vérifier les taux réduits).")
    else:
        prix_ht = prix_vente
        tva_collectee = 0.0
        if regime_tva == "non_assujetti":
            hyp.append("Non assujetti : aucune TVA reversée ni récupérée.")

    # --- Coût d'achat ---
    if regime_tva == "assujetti":
        cout_achat = couts.prix_achat / (1 + t_achat) if couts.prix_achat_ttc else couts.prix_achat
        if couts.prix_achat_ttc:
            hyp.append(f"TVA sur achat récupérée au taux {t_achat:.1%}.")
    elif regime_tva == "non_assujetti":
        cout_achat = couts.prix_achat if couts.prix_achat_ttc else couts.prix_achat * (1 + t_achat)
        if not couts.prix_achat_ttc:
            hyp.append(f"Prix d'achat saisi HT : TVA {t_achat:.1%} ajoutée comme coût (non récupérable).")
    else:
        cout_achat = couts.prix_achat

    # --- Frais Amazon ---
    frais_ht = frais.total_ht
    if regime_tva == "non_assujetti":
        tva_frais = frais_ht * t_frais
        hyp.append(f"TVA sur frais Amazon ({t_frais:.1%}) comptée comme coût (non récupérable).")
    else:
        tva_frais = 0.0
    if frais.source != "sp-api":
        hyp.append(f"Frais Amazon issus de : {frais.source} (non confirmés par l'API Amazon).")

    # --- Autres coûts ---
    retours = couts.taux_retours * prix_vente
    autres = couts.envoi_entrepot + couts.preparation + couts.stockage_estime + couts.autres_couts + retours
    if couts.taux_retours:
        hyp.append(f"Provision retours : {couts.taux_retours:.1%} du prix de vente.")

    profit = prix_ht - cout_achat - frais_ht - tva_frais - autres
    roi = profit / cout_achat if cout_achat > 0 else None
    marge = profit / prix_vente

    # Prix d'achat maximum pour atteindre le ROI cible :
    # profit(c) = A - c  avec A = prix_ht - frais - tva_frais - autres ; ROI = (A - c)/c >= r  =>  c <= A/(1+r)
    a = prix_ht - frais_ht - tva_frais - autres
    cout_max_net = a / (1 + roi_cible) if a > 0 else None
    prix_achat_max = None
    if cout_max_net is not None:
        # reconvertir dans la même base que la saisie de l'utilisateur
        if regime_tva == "assujetti":
            prix_achat_max = cout_max_net * (1 + t_achat) if couts.prix_achat_ttc else cout_max_net
        elif regime_tva == "non_assujetti":
            prix_achat_max = cout_max_net if couts.prix_achat_ttc else cout_max_net / (1 + t_achat)
        else:
            prix_achat_max = cout_max_net

    return ResultatRentabilite(
        prix_vente=round(prix_vente, 2),
        prix_vente_ht=round(prix_ht, 2),
        tva_collectee=round(tva_collectee, 2),
        cout_achat_net=round(cout_achat, 2),
        frais_amazon=round(frais_ht, 2),
        tva_sur_frais_non_recuperable=round(tva_frais, 2),
        autres_couts=round(autres, 2),
        profit_net=round(profit, 2),
        roi=None if roi is None else round(roi, 4),
        marge=round(marge, 4),
        prix_achat_max_pour_roi=None if prix_achat_max is None else round(prix_achat_max, 2),
        roi_cible=roi_cible,
        regime_tva=regime_tva,
        hypotheses=hyp,
    )


def estimer_frais(prix_vente: float, taux_commission: float = 0.15, fba: float = 0.0) -> FraisAmazon:
    """Estimation grossière quand l'API Amazon n'est pas disponible.

    La commission Amazon s'applique au prix de vente total payé par le client
    (TVA incluse en Europe). 15 % est le taux le plus courant, mais il varie
    selon la catégorie (de ~5 % à 45 %). À n'utiliser que comme ordre de grandeur.
    """
    return FraisAmazon(
        commission=prix_vente * taux_commission,
        fba=fba,
        source=f"estimation (commission {taux_commission:.0%}, FBA saisi)",
    )
