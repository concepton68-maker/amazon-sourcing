"""Paramètres du compte — [RM-AMZ-042, 043, 044]."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from .analyse import Seuils
from .marketplaces import MARKETPLACES
from .profit import ParametresCout

# Bornes [RM-AMZ-042] : (minimum, maximum) inclus.
BORNES = {
    "roi_min": (0.0, 10.0), "profit_min": (0.0, 1000.0), "ventes_mois_min": (0, 100000),
    "part_ventes_min": (0.0, 100000.0), "ecart_prix_max": (0.0, 5.0),
    "envoi": (0.0, 1000.0), "preparation": (0.0, 1000.0), "stockage": (0.0, 1000.0), "retours": (0.0, 1.0),
    # coût complet [RM-AMZ-096 à 098]
    "port_fournisseur": (0.0, 1000.0), "placement": (0.0, 1000.0), "duree_stock_mois": (0.0, 24.0),
    "carburant_taux": (0.0, 0.2), "carburant_actif": (0, 1),
    # stock [RM-AMZ-047, 048] : jours
    "delai_fournisseur": (0, 365), "delai_reception": (0, 365), "marge_securite": (0, 365),
    "seuil_rupture": (0, 365), "seuil_surstock": (1, 3650),
}
REGIMES_REGLABLES = ("assujetti", "non_assujetti")


class ParametreInvalide(ValueError):
    """args = (code, champ)."""


def _hors_taxe(mp_code: str) -> bool:
    mp = MARKETPLACES[mp_code]
    return not mp.prix_ttc or mp.taux_tva_standard == 0


@dataclass
class Parametres:
    roi_min: float = 0.30
    profit_min: float = 3.0
    ventes_mois_min: int = 10
    part_ventes_min: float = 3.0
    ecart_prix_max: float = 0.20
    envoi: float = 0.0
    preparation: float = 0.0
    stockage: float = 0.0
    retours: float = 0.0
    port_fournisseur: float = 0.0
    placement: float = 0.0
    duree_stock_mois: float = 2.0       # durée de stockage prévue avant la vente (choix de l'outil, modifiable)
    carburant_taux: float = 0.02         # [RM-AMZ-097] pré-rempli : valeur officielle au 2/11/2026
    carburant_actif: int = 1             # décoché : le taux reste enregistré
    delai_fournisseur: int = 7
    delai_reception: int = 10
    marge_securite: int = 14
    seuil_rupture: int = 15
    seuil_surstock: int = 180
    tva: dict[str, str] = field(default_factory=dict)     # place -> régime ; absent = assujetti

    def regime(self, mp_code: str) -> str:
        if _hors_taxe(mp_code):
            return "hors_taxe"
        return self.tva.get(mp_code, "assujetti")

    def seuils(self) -> Seuils:
        return Seuils(self.roi_min, self.profit_min, self.ventes_mois_min, self.part_ventes_min, self.ecart_prix_max)

    def couts(self, prix_achat: float, achat_ttc: bool = False, taux_tva: Optional[float] = None) -> ParametresCout:
        """[RM-AMZ-044] Coûts par défaut du compte appliqués à un prix d'achat."""
        return ParametresCout(prix_achat=prix_achat, prix_achat_ttc=achat_ttc, taux_tva_achat=taux_tva,
                              envoi_entrepot=self.envoi, preparation=self.preparation,
                              stockage_estime=self.stockage, taux_retours=self.retours,
                              port_fournisseur=self.port_fournisseur, placement=self.placement)

    def options_cout(self) -> dict:
        """[RM-AMZ-096, 097] Options de coût complet passées à l'analyse."""
        return {"duree_stock_mois": self.duree_stock_mois,
                "carburant_taux": self.carburant_taux if self.carburant_actif else None}

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tva"] = {mp: self.regime(mp) for mp in MARKETPLACES}
        return d


def valider(brut: dict) -> Parametres:
    """[RM-AMZ-042] Refuse champ inconnu, type faux ou valeur hors bornes ; complète par les défauts."""
    p = Parametres()
    for cle, valeur in brut.items():
        if cle == "tva":
            if not isinstance(valeur, dict):
                raise ParametreInvalide("PARAMETRE_INVALIDE", "tva")
            for mp, regime in valeur.items():
                if mp not in MARKETPLACES:
                    raise ParametreInvalide("PLACE_INCONNUE", f"tva.{mp}")
                if _hors_taxe(mp):
                    continue                                  # toujours hors taxe, réglage ignoré
                if regime not in REGIMES_REGLABLES:
                    raise ParametreInvalide("REGIME_TVA_INCONNU", f"tva.{mp}")
                p.tva[mp] = regime
            continue
        if cle == "carburant_inclus":                     # ancien réglage (1 jour en ligne) : « inclus » = inactif
            p.carburant_actif = 0 if valeur else 1
            continue
        if cle not in BORNES:
            raise ParametreInvalide("PARAMETRE_INCONNU", cle)
        mini, maxi = BORNES[cle]
        if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
            raise ParametreInvalide("PARAMETRE_INVALIDE", cle)
        if not (mini <= valeur <= maxi):
            raise ParametreInvalide("PARAMETRE_HORS_BORNES", cle)
        setattr(p, cle, int(valeur) if isinstance(mini, int) else float(valeur))
    return p
