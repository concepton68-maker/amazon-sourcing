"""Analyse complète d'un produit : données + rentabilité + verdict expliqué.

Chaque fournisseur est optionnel : l'analyse se dégrade proprement et dit
explicitement ce qui n'a pas pu être vérifié (plutôt que d'inventer).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .marketplaces import Marketplace
from .profit import FraisAmazon, ParametresCout, ResultatRentabilite, calculer_rentabilite, estimer_frais
from .providers.base import ErreurFournisseur, Historique, InfosCatalogue, InfosOffres, InfosRestrictions

ACHETER, A_VERIFIER, PASSER = "ACHETER", "À VÉRIFIER", "PASSER"


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
    origine_prix: str
    rentabilite: Optional[ResultatRentabilite]
    rentabilite_prudente: Optional[ResultatRentabilite]   # au prix moyen 90 j si plus bas
    ventes_estimees_pour_vous: Optional[float]
    verdict: str
    raisons: list[str]
    alertes: list[str]
    non_verifie: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _essayer(fn, non_verifie: list[str], libelle: str):
    try:
        return fn()
    except ErreurFournisseur as e:
        non_verifie.append(f"{libelle} : {e}")
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
    nv: list[str] = []
    alertes: list[str] = []
    raisons: list[str] = []

    # 1. Catalogue (fusion des sources : la première gagne, les suivantes complètent)
    cat = InfosCatalogue(asin=asin)
    for src in f.catalogue:
        c = _essayer(lambda: src.catalogue(mp, asin), nv, f"Catalogue ({type(src).__name__})")
        if c:
            for k, v in asdict(c).items():
                if getattr(cat, k) in (None, "") and v not in (None, ""):
                    setattr(cat, k, v)

    # 2. Offres, restrictions, historique
    off = _essayer(lambda: f.offres.offres(mp, asin), nv, "Offres") if f.offres else None
    if not f.offres:
        nv.append("Offres / Buy Box : pas de source SP-API configurée.")
    restr = _essayer(lambda: f.restrictions.restrictions(mp, asin), nv, "Restrictions") if f.restrictions else None
    if not f.restrictions:
        nv.append("Autorisation de vente : non vérifiée (SP-API requise).")
    hist = _essayer(lambda: f.historique.historique(mp, asin), nv, "Historique") if f.historique else None
    if not f.historique:
        nv.append("Historique prix/BSR et ventes estimées : pas de source Keepa configurée.")

    # 3. Prix de vente retenu
    prix, origine = None, "aucun"
    if prix_vente_force:
        prix, origine = prix_vente_force, "saisi"
    elif off and off.prix_buybox:
        prix, origine = off.prix_buybox, "Buy Box actuelle (SP-API)"
    elif off and off.prix_plus_bas_fba:
        prix, origine = off.prix_plus_bas_fba, "offre FBA la plus basse (SP-API)"
    elif hist and hist.prix_buybox_moy90:
        prix, origine = hist.prix_buybox_moy90, "moyenne 90 j (Keepa)"

    frais = rent = rent_prudente = None
    if prix:
        if f.frais:
            frais = _essayer(lambda: f.frais.frais(mp, asin, prix), nv, "Frais")
        if frais is None:
            frais = estimer_frais(prix)
            nv.append("Frais FBA inconnus (0 dans le calcul) et commission estimée à 15 % : profit SURESTIMÉ.")
        rent = calculer_rentabilite(mp, prix, frais, couts, regime_tva, taux_tva_vente=taux_tva_vente,
                                    roi_cible=seuils.roi_min)
        moy = hist.prix_buybox_moy90 if hist else None
        if moy and moy < prix * 0.98:
            frais_p = None
            if f.frais and frais.source == "sp-api":
                frais_p = _essayer(lambda: f.frais.frais(mp, asin, moy), [], "Frais")
            if frais_p is None:  # mise à l'échelle de la commission
                ratio = moy / prix
                frais_p = FraisAmazon(frais.commission * ratio, frais.fba, frais.cloture, frais.autres, frais.source)
            rent_prudente = calculer_rentabilite(mp, moy, frais_p, couts, regime_tva,
                                                 taux_tva_vente=taux_tva_vente, roi_cible=seuils.roi_min)
    else:
        nv.append("Aucun prix de vente disponible : rentabilité non calculable.")

    # 4. Part de ventes estimée pour vous (ESTIMATION grossière : partage égal entre vendeurs FBA)
    ventes_vous = None
    if hist and hist.ventes_mois_estimees is not None:
        nb = (off.nb_offres_fba if off and off.nb_offres_fba is not None else hist.nb_offres_neuf_moy90) or 0
        ventes_vous = round(hist.ventes_mois_estimees / (nb + 1), 1)

    # 5. Verdict
    bloquant = False
    if restr and restr.autorise is False:
        bloquant = True
        raisons.append("Vous n'êtes pas autorisé à vendre ce produit"
                       + (" (approbation requise)." if restr.approbation_requise else "."))
    if rent:
        if rent.profit_net <= 0:
            bloquant = True
            raisons.append(f"Profit négatif ({rent.profit_net:.2f} {mp.devise}).")
        else:
            if rent.roi is not None and rent.roi < seuils.roi_min:
                raisons.append(f"ROI {rent.roi:.0%} < objectif {seuils.roi_min:.0%}.")
            if rent.profit_net < seuils.profit_min:
                raisons.append(f"Profit {rent.profit_net:.2f} < minimum {seuils.profit_min:.2f} {mp.devise}.")
        if rent.prix_achat_max_pour_roi is not None:
            raisons.append(f"Prix d'achat maximum pour {seuils.roi_min:.0%} de ROI : "
                           f"{rent.prix_achat_max_pour_roi:.2f} {mp.devise}.")
    if rent_prudente and rent_prudente.profit_net <= 0 < (rent.profit_net if rent else 0):
        alertes.append(f"Au prix moyen 90 j ({rent_prudente.prix_vente:.2f}), le profit devient négatif "
                       f"({rent_prudente.profit_net:.2f}) : le prix actuel est peut-être temporaire.")
    if hist and hist.ventes_mois_estimees is not None and hist.ventes_mois_estimees < seuils.ventes_mois_min:
        raisons.append(f"Ventes estimées faibles ({hist.ventes_mois_estimees}/mois).")
    if ventes_vous is not None and ventes_vous < seuils.part_ventes_min:
        raisons.append(f"Part de ventes estimée pour vous faible (~{ventes_vous}/mois, partage égal supposé).")
    if off and off.buybox_amazon:
        alertes.append("Amazon détient la Buy Box : vente difficile pour un vendeur tiers.")
    elif off and off.amazon_vend:
        alertes.append("Amazon vend aussi ce produit.")
    if hist and hist.amazon_en_stock_pct90 is not None and hist.amazon_en_stock_pct90 > 0.5:
        alertes.append(f"Amazon en stock {hist.amazon_en_stock_pct90:.0%} du temps sur 90 j.")
    if prix and hist and hist.prix_buybox_moy90 and prix > hist.prix_buybox_moy90 * (1 + seuils.ecart_prix_max):
        alertes.append(f"Prix actuel {prix:.2f} > moyenne 90 j {hist.prix_buybox_moy90:.2f} de plus de "
                       f"{seuils.ecart_prix_max:.0%} : risque de pic temporaire.")
    if cat.nb_unites_lot and cat.nb_unites_lot > 1:
        alertes.append(f"Listing en lot de {cat.nb_unites_lot} : votre prix d'achat doit couvrir le lot entier.")
    if hist and hist.prix_buybox_min90 and hist.prix_buybox_max90 and hist.prix_buybox_min90 > 0:
        amplitude = hist.prix_buybox_max90 / hist.prix_buybox_min90 - 1
        if amplitude > 0.4:
            alertes.append(f"Prix instable : écart de {amplitude:.0%} entre min et max sur 90 j.")

    if bloquant or not rent:
        verdict = PASSER if bloquant else A_VERIFIER
    elif raisons and any(r.startswith(("ROI", "Profit", "Ventes", "Part")) for r in raisons):
        verdict = PASSER if (rent.roi or 0) < seuils.roi_min / 2 else A_VERIFIER
    elif nv or alertes or (restr is None):
        verdict = A_VERIFIER
    else:
        verdict = ACHETER
    if verdict == ACHETER:
        raisons.insert(0, f"ROI {rent.roi:.0%} et profit {rent.profit_net:.2f} {mp.devise} au-dessus des seuils, "
                          "vente autorisée, aucune alerte.")

    return AnalyseProduit(
        marketplace=mp.code, asin=asin, catalogue=cat, offres=off, restrictions=restr, historique=hist,
        frais=frais, prix_vente_retenu=prix, origine_prix=origine, rentabilite=rent,
        rentabilite_prudente=rent_prudente, ventes_estimees_pour_vous=ventes_vous,
        verdict=verdict, raisons=raisons, alertes=alertes, non_verifie=nv,
    )
