"""Analyse complète d'un produit : données + rentabilité + verdict expliqué.

Chaque fournisseur est optionnel : l'analyse se dégrade proprement et dit
explicitement ce qui n'a pas pu être vérifié (plutôt que d'inventer).
Raisons, alertes et données non vérifiées sont des messages codés [RM-AMZ-027].
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .marketplaces import Marketplace
from .messages import Message, m
from .profit import FraisAmazon, ParametresCout, ResultatRentabilite, calculer_rentabilite, estimer_frais
from .providers.base import ErreurFournisseur, Historique, InfosCatalogue, InfosOffres, InfosRestrictions

ACHETER, A_VERIFIER, PASSER = "ACHETER", "A_VERIFIER", "PASSER"

# Raisons qui font échouer un seuil d'achat (le verdict se décide sur ces codes).
RAISONS_SEUIL = {"R_ROI_SOUS_SEUIL", "R_PROFIT_SOUS_SEUIL", "R_VENTES_FAIBLES", "R_PART_FAIBLE"}
RAISONS_BLOQUANTES = {"R_VENTE_NON_AUTORISEE", "R_APPROBATION_REQUISE", "R_PROFIT_NEGATIF"}


@dataclass
class Seuils:
    roi_min: float = 0.30
    profit_min: float = 3.0
    ventes_mois_min: int = 10          # ventes mensuelles estimées minimales du listing
    part_ventes_min: float = 3.0       # ventes/mois estimées pour VOUS (part de Buy Box)
    ecart_prix_max: float = 0.20       # prix actuel > moyenne 90 j de plus de 20 % -> pic suspect


@dataclass
class Fournisseurs:
    catalogue: list[Any] = field(default_factory=list)   # par ordre de priorité
    offres: Optional[Any] = None
    frais: Optional[Any] = None
    restrictions: Optional[Any] = None
    historique: Optional[Any] = None


@dataclass
class AnalyseProduit:
    marketplace: str
    asin: str
    catalogue: InfosCatalogue
    offres: Optional[InfosOffres]
    restrictions: Optional[InfosRestrictions]
    historique: Optional[Historique]
    frais: Optional[FraisAmazon]
    prix_vente_retenu: Optional[float]
    origine_prix: str                  # code : SAISI, BUYBOX, FBA_MIN, MOYENNE_90J, AUCUN
    rentabilite: Optional[ResultatRentabilite]
    rentabilite_prudente: Optional[ResultatRentabilite]   # au prix moyen 90 j si plus bas
    ventes_estimees_pour_vous: Optional[float]
    verdict: str
    raisons: list[Message]
    alertes: list[Message]
    non_verifie: list[Message]

    def to_dict(self) -> dict:
        return asdict(self)


def _essayer(fn, non_verifie: list[Message], source: str):
    try:
        return fn()
    except ErreurFournisseur as e:
        non_verifie.append(m("NV_SOURCE_ERREUR", source=source, detail=str(e)))
        return None


def resoudre_asins(mp: Marketplace, code: str, f: Fournisseurs) -> list[str]:
    erreurs = []
    for src in f.catalogue:
        try:
            asins = src.rechercher_asins(mp, code)
            if asins:
                return asins
        except ErreurFournisseur as e:
            erreurs.append(str(e))
    if erreurs:
        raise ErreurFournisseur("; ".join(erreurs))
    return []


def analyser_asin(
    mp: Marketplace,
    asin: str,
    couts: ParametresCout,
    f: Fournisseurs,
    regime_tva: str = "assujetti",
    seuils: Seuils = Seuils(),
    prix_vente_force: Optional[float] = None,
    taux_tva_vente: Optional[float] = None,
) -> AnalyseProduit:
    nv: list[Message] = []
    alertes: list[Message] = []
    raisons: list[Message] = []

    # 1. Catalogue (fusion des sources : la première gagne, les suivantes complètent)
    cat = InfosCatalogue(asin=asin)
    for src in f.catalogue:
        c = _essayer(lambda: src.catalogue(mp, asin), nv, "CATALOGUE")
        if c:
            for k, v in asdict(c).items():
                if getattr(cat, k) in (None, "") and v not in (None, ""):
                    setattr(cat, k, v)

    # 2. Offres, restrictions, historique
    off = _essayer(lambda: f.offres.offres(mp, asin), nv, "OFFRES") if f.offres else None
    if not f.offres:
        nv.append(m("NV_PAS_SOURCE_OFFRES"))
    restr = _essayer(lambda: f.restrictions.restrictions(mp, asin), nv, "RESTRICTIONS") if f.restrictions else None
    if not f.restrictions:
        nv.append(m("NV_PAS_SOURCE_RESTRICTIONS"))
    hist = _essayer(lambda: f.historique.historique(mp, asin), nv, "HISTORIQUE") if f.historique else None
    if not f.historique:
        nv.append(m("NV_PAS_SOURCE_HISTORIQUE"))

    # 3. Prix de vente retenu [RM-AMZ-001]
    prix, origine = None, "AUCUN"
    if prix_vente_force:
        prix, origine = prix_vente_force, "SAISI"
    elif off and off.prix_buybox:
        prix, origine = off.prix_buybox, "BUYBOX"
    elif off and off.prix_plus_bas_fba:
        prix, origine = off.prix_plus_bas_fba, "FBA_MIN"
    elif hist and hist.prix_buybox_moy90:
        prix, origine = hist.prix_buybox_moy90, "MOYENNE_90J"

    frais = rent = rent_prudente = None
    if prix:
        if f.frais:
            frais = _essayer(lambda: f.frais.frais(mp, asin, prix), nv, "FRAIS")
        if frais is None:
            frais = estimer_frais(prix)
            nv.append(m("NV_FRAIS_ESTIMES"))
        rent = calculer_rentabilite(mp, prix, frais, couts, regime_tva, taux_tva_vente=taux_tva_vente,
                                    roi_cible=seuils.roi_min)
        moy = hist.prix_buybox_moy90 if hist else None
        if moy and moy < prix * 0.98:            # [RM-AMZ-007]
            frais_p = None
            if f.frais and frais.source == "sp-api":
                frais_p = _essayer(lambda: f.frais.frais(mp, asin, moy), [], "FRAIS")
            if frais_p is None:  # mise à l'échelle de la commission
                ratio = moy / prix
                frais_p = FraisAmazon(frais.commission * ratio, frais.fba, frais.cloture, frais.autres, frais.source)
            rent_prudente = calculer_rentabilite(mp, moy, frais_p, couts, regime_tva,
                                                 taux_tva_vente=taux_tva_vente, roi_cible=seuils.roi_min)
    else:
        nv.append(m("NV_PAS_DE_PRIX"))

    # 4. Part de ventes estimée pour vous (ESTIMATION : partage égal entre vendeurs FBA) [RM-AMZ-010]
    ventes_vous = None
    if hist and hist.ventes_mois_estimees is not None:
        nb = (off.nb_offres_fba if off and off.nb_offres_fba is not None else hist.nb_offres_neuf_moy90) or 0
        ventes_vous = round(hist.ventes_mois_estimees / (nb + 1), 1)

    # 5. Raisons et alertes [RM-AMZ-008, RM-AMZ-009]
    if restr and restr.autorise is False:
        raisons.append(m("R_APPROBATION_REQUISE" if restr.approbation_requise else "R_VENTE_NON_AUTORISEE"))
    if rent:
        if rent.profit_net <= 0:
            raisons.append(m("R_PROFIT_NEGATIF", profit=rent.profit_net, devise=mp.devise))
        else:
            if rent.roi is not None and rent.roi < seuils.roi_min:
                raisons.append(m("R_ROI_SOUS_SEUIL", roi=rent.roi, seuil=seuils.roi_min))
            if rent.profit_net < seuils.profit_min:
                raisons.append(m("R_PROFIT_SOUS_SEUIL", profit=rent.profit_net, minimum=seuils.profit_min,
                                 devise=mp.devise))
    if rent_prudente and rent_prudente.profit_net <= 0 < (rent.profit_net if rent else 0):
        alertes.append(m("A_PRUDENT_NEGATIF", prix=rent_prudente.prix_vente, profit=rent_prudente.profit_net))
    if hist and hist.ventes_mois_estimees is not None and hist.ventes_mois_estimees < seuils.ventes_mois_min:
        raisons.append(m("R_VENTES_FAIBLES", ventes=hist.ventes_mois_estimees))
    if ventes_vous is not None and ventes_vous < seuils.part_ventes_min:
        raisons.append(m("R_PART_FAIBLE", part=ventes_vous))
    if off and off.buybox_amazon:
        alertes.append(m("A_AMAZON_BUYBOX"))
    elif off and off.amazon_vend:
        alertes.append(m("A_AMAZON_VEND"))
    if hist and hist.amazon_en_stock_pct90 is not None and hist.amazon_en_stock_pct90 > 0.5:
        alertes.append(m("A_AMAZON_EN_STOCK", pct=hist.amazon_en_stock_pct90))
    if prix and hist and hist.prix_buybox_moy90 and prix > hist.prix_buybox_moy90 * (1 + seuils.ecart_prix_max):
        alertes.append(m("A_PIC_PRIX", prix=prix, moyenne=hist.prix_buybox_moy90, seuil=seuils.ecart_prix_max))
    if cat.nb_unites_lot and cat.nb_unites_lot > 1:
        alertes.append(m("A_LOT_MULTIPLE", n=cat.nb_unites_lot))
    if hist and hist.prix_buybox_min90 and hist.prix_buybox_max90 and hist.prix_buybox_min90 > 0:
        amplitude = hist.prix_buybox_max90 / hist.prix_buybox_min90 - 1
        if amplitude > 0.4:
            alertes.append(m("A_PRIX_INSTABLE", amplitude=amplitude))

    # 6. Verdict, décidé sur les codes [RM-AMZ-008, RM-AMZ-027]
    codes = {r.code for r in raisons}
    if codes & RAISONS_BLOQUANTES:
        verdict = PASSER
    elif not rent:
        verdict = A_VERIFIER
    elif codes & RAISONS_SEUIL:
        verdict = PASSER if (rent.roi or 0) < seuils.roi_min / 2 else A_VERIFIER
    elif nv or alertes or restr is None:
        verdict = A_VERIFIER
    else:
        verdict = ACHETER
    if verdict == ACHETER:
        raisons.insert(0, m("R_TOUT_OK", roi=rent.roi, profit=rent.profit_net, devise=mp.devise))
    if rent and rent.prix_achat_max_pour_roi is not None:
        raisons.append(m("R_PRIX_ACHAT_MAX", roi=seuils.roi_min, montant=rent.prix_achat_max_pour_roi,
                         devise=mp.devise))

    return AnalyseProduit(
        marketplace=mp.code, asin=asin, catalogue=cat, offres=off, restrictions=restr, historique=hist,
        frais=frais, prix_vente_retenu=prix, origine_prix=origine, rentabilite=rent,
        rentabilite_prudente=rent_prudente, ventes_estimees_pour_vous=ventes_vous,
        verdict=verdict, raisons=raisons, alertes=alertes, non_verifie=nv,
    )
