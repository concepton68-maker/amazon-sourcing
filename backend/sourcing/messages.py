"""Messages codés [RM-AMZ-027, D-AMZ-010] : un code et ses paramètres, jamais une phrase.

L'interface web traduit avec `frontend/src/i18n/<langue>.json` ; la ligne de commande avec
`FR` ci-dessous (outil de développement). Ajouter un code = l'ajouter aux deux traductions
(un test le vérifie).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Message:
    code: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"code": self.code, "params": self.params}


def m(code: str, **params) -> Message:
    return Message(code, params)


# Textes français pour la ligne de commande. Pourcentages en fraction (0.3 = 30 %).
FR: dict[str, str] = {
    # hypothèses de calcul
    "HYP_HORS_TAXE": "{mp} : prix hors taxe, calcul sans TVA",
    "HYP_TVA_COLLECTEE": "TVA collectée {taux:.1%} (taux standard {mp} sauf taux réduit)",
    "HYP_NON_ASSUJETTI": "Non assujetti : aucune TVA reversée ni récupérée",
    "HYP_TVA_ACHAT_RECUPEREE": "TVA sur achat récupérée {taux:.1%}",
    "HYP_TVA_ACHAT_COUT": "TVA sur achat {taux:.1%} comptée comme coût",
    "HYP_TVA_FRAIS_COUT": "TVA sur frais Amazon {taux:.1%} comptée comme coût",
    "HYP_FRAIS_NON_CONFIRMES": "Frais Amazon non confirmés par l'API ({source})",
    "HYP_PROVISION_RETOURS": "Provision retours {taux:.1%} du prix de vente",
    # données non vérifiées
    "NV_SOURCE_ERREUR": "{source} : {detail}",
    "NV_PAS_SOURCE_OFFRES": "Offres et Buy Box non vérifiées",
    "NV_PAS_SOURCE_RESTRICTIONS": "Autorisation de vente non vérifiée",
    "NV_PAS_SOURCE_HISTORIQUE": "Historique et ventes non vérifiés",
    "NV_FRAIS_ESTIMES": "Frais estimés (commission 15 %, FBA 0) : profit surestimé",
    "NV_PAS_DE_PRIX": "Aucun prix de vente disponible",
    # raisons du verdict
    "R_VENTE_NON_AUTORISEE": "Vente non autorisée sur votre compte",
    "R_APPROBATION_REQUISE": "Vente non autorisée : approbation requise",
    "R_PROFIT_NEGATIF": "Profit négatif ({profit:.2f} {devise})",
    "R_ROI_SOUS_SEUIL": "ROI {roi:.0%} sous l'objectif {seuil:.0%}",
    "R_PROFIT_SOUS_SEUIL": "Profit {profit:.2f} sous le minimum {seuil:.2f} {devise}",
    "R_PRIX_ACHAT_MAX": "Prix d'achat maximum pour {roi:.0%} de ROI : {montant:.2f} {devise}",
    "R_VENTES_FAIBLES": "Ventes faibles ({ventes}/mois)",
    "R_PART_FAIBLE": "Part de ventes estimée faible (~{part}/mois)",
    "R_TOUT_OK": "ROI {roi:.0%} et profit {profit:.2f} {devise} au-dessus des seuils, vente autorisée, aucune alerte",
    # alertes
    "A_AMAZON_BUYBOX": "Amazon détient la Buy Box",
    "A_AMAZON_VEND": "Amazon vend aussi ce produit",
    "A_AMAZON_EN_STOCK": "Amazon en stock {pct:.0%} du temps sur 90 j",
    "A_PRUDENT_NEGATIF": "Au prix moyen 90 j ({prix:.2f}), profit négatif ({profit:.2f})",
    "A_PIC_PRIX": "Prix actuel {prix:.2f} > moyenne 90 j {moyenne:.2f} de plus de {seuil:.0%}",
    "A_LOT_MULTIPLE": "Listing en lot de {n} : le prix d'achat doit couvrir le lot",
    "A_PRIX_INSTABLE": "Prix instable : écart {amplitude:.0%} entre min et max sur 90 j",
}


def texte_fr(msg: Message) -> str:
    modele = FR.get(msg.code)
    if modele is None:
        return msg.code
    try:
        return modele.format(**msg.params)
    except (KeyError, ValueError, TypeError):
        return f"{msg.code} {msg.params}"
