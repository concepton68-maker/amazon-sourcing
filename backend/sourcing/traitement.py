"""Traitement d'un fichier fournisseur — [RM-AMZ-033, 034, 035].

Chaque ligne : appariement code → ASIN (mémoire du compte, sinon recherche), analyse complète
(mêmes règles que l'écran Analyse produit), coût recalculé si le listing Amazon est un lot.
"""
from __future__ import annotations

import re

import csv
import io
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from .analyse import ACHETER, A_VERIFIER, PASSER, AnalyseProduit, Fournisseurs, Seuils, analyser_asin, resoudre_asins
from .fichier import LigneFournisseur, Preparation
from .marketplaces import Marketplace
from .messages import Message, m
from .profit import ParametresCout
from .providers.base import ErreurFournisseur

FRAICHEUR_APPARIEMENT = timedelta(days=30)
ORDRE_VERDICT = {ACHETER: 0, A_VERIFIER: 1, PASSER: 2}


@dataclass
class ResultatLigne:
    numero: int
    code: str
    designation: Optional[str]
    prix_unitaire: Decimal
    asin: Optional[str] = None
    titre: Optional[str] = None
    unites_lot: int = 1
    cout_achat: Optional[Decimal] = None        # prix unitaire × unités du listing
    verdict: Optional[str] = None
    prix_vente: Optional[float] = None
    profit: Optional[float] = None
    roi: Optional[float] = None
    ventes_mois: Optional[int] = None
    raisons: list[Message] = field(default_factory=list)
    alertes: list[Message] = field(default_factory=list)
    lignes: list[Message] = field(default_factory=list)   # remarques propres à la ligne du fichier
    statut: str = "ANALYSEE"                     # ANALYSEE, INTROUVABLE, ERREUR_SOURCE
    # liste des produits rentables [RM-AMZ-105, 106]
    marge: Optional[float] = None
    prix_achat_max: Optional[float] = None
    vendabilite: str = "INCONNU"
    motif: Optional[str] = None
    bsr: Optional[int] = None
    nb_vendeurs: Optional[int] = None
    amazon_vend: Optional[bool] = None
    prevision: Optional[dict] = None             # [RM-AMZ-125]


@dataclass
class Traitement:
    id: str
    compte_id: str
    marketplace: str
    total: int
    faits: int = 0
    statut: str = "EN_COURS"                     # EN_COURS, TERMINE, ERREUR
    resultats: list[ResultatLigne] = field(default_factory=list)
    rejets: list[tuple[int, Message]] = field(default_factory=list)
    doublons: list[tuple[int, str]] = field(default_factory=list)
    appariements_memoire: int = 0
    origine: Optional[tuple[str, str]] = None     # (clé, nom) pour la liste des produits rentables [RM-AMZ-105]
    debut: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    arret: bool = False                           # [RM-AMZ-136] demandé : pris en compte entre deux produits

    def tries(self) -> list[ResultatLigne]:
        """[RM-AMZ-035] Verdict puis ROI décroissant ; introuvables et erreurs à la fin."""
        return sorted(self.resultats, key=lambda r: (r.statut != "ANALYSEE", ORDRE_VERDICT.get(r.verdict, 9),
                                                     -(r.roi if r.roi is not None else -9e9)))


def _asins(compte_id: str, mp: Marketplace, code: str, f: Fournisseurs, depot, t: Traitement,
           maintenant: datetime) -> list[str]:
    """[RM-AMZ-034] Mémoire du compte si fraîche, sinon recherche puis mémorisation."""
    connu = depot.appariement(compte_id, mp.code, code)
    if connu and maintenant - connu[1] <= FRAICHEUR_APPARIEMENT:
        t.appariements_memoire += 1
        return connu[0]
    asins = resoudre_asins(mp, code, f)
    depot.memoriser_appariement(compte_id, mp.code, code, asins, maintenant)
    return asins


_PETITS_MOTS = {"de", "du", "des", "la", "le", "les", "l", "d", "et", "en", "pour", "avec", "a", "au", "aux", "un",
                "une", "x", "pc", "pcs", "the", "of", "and", "for", "with"}


def _mots(texte: str) -> set[str]:
    import unicodedata
    t = unicodedata.normalize("NFKD", texte or "").encode("ascii", "ignore").decode().lower()
    mots = set()
    for w in re.findall(r"[a-z]+|\d+", t):
        if w in _PETITS_MOTS:
            continue
        if len(w) > 3 and w.endswith("s") and not w.isdigit():
            w = w[:-1]
        mots.add(w)
    return mots


def correspondance(designation: Optional[str], titre: Optional[str]) -> Optional[float]:
    """[RM-AMZ-083] Part des mots significatifs de la désignation retrouvés dans le titre Amazon."""
    d, t = _mots(designation or ""), _mots(titre or "")
    if not d or not t:
        return None
    return len(d & t) / len(d)


def _ligne(l: LigneFournisseur, mp: Marketplace, asin: str, f: Fournisseurs, regime: str, seuils: Seuils,
           achat_ttc: bool, parametres=None) -> ResultatLigne:
    r = ResultatLigne(l.numero, l.code, l.designation, l.prix_unitaire, asin=asin, lignes=list(l.avertissements))
    # 1re passe pour connaître la taille du lot vendu sur Amazon, puis analyse au bon coût [RM-AMZ-033]
    cat = None
    for src in f.catalogue:
        try:
            cat = src.catalogue(mp, asin)
            break
        except ErreurFournisseur:
            continue
    k = cat.nb_unites_lot if cat and cat.nb_unites_lot and cat.nb_unites_lot > 1 else 1
    if k > 1:
        r.lignes.append(m("L_LOT_AMAZON", n=k))
    r.unites_lot, r.cout_achat = k, l.prix_unitaire * k
    couts = parametres.couts(float(r.cout_achat), achat_ttc) if parametres else \
        ParametresCout(float(r.cout_achat), prix_achat_ttc=achat_ttc)       # [RM-AMZ-044] coûts par défaut du compte
    a: AnalyseProduit = analyser_asin(mp, asin, couts, f, regime, seuils,
                                      **(parametres.options_cout() if parametres else {}))
    r.titre, r.verdict, r.prix_vente = a.catalogue.titre, a.verdict, a.prix_vente_retenu
    if a.rentabilite:
        r.profit, r.roi = a.rentabilite.profit_net, a.rentabilite.roi
        from .lots import prevision_depuis_analyse
        from .achats_serial import prevision_vers_dict
        r.prevision = prevision_vers_dict(prevision_depuis_analyse(a.rentabilite, couts, mp.devise, ["analyse:" + (a.origine_prix or "")]))
        r.marge, r.prix_achat_max = a.rentabilite.marge, a.rentabilite.prix_achat_max_pour_roi
    from .opportunites import vendabilite
    r.vendabilite, r.motif = vendabilite(a.restrictions)
    r.bsr = a.catalogue.bsr
    if a.offres and (a.offres.nb_offres_fba is not None or a.offres.nb_offres_fbm is not None):
        r.nb_vendeurs = (a.offres.nb_offres_fba or 0) + (a.offres.nb_offres_fbm or 0)
    r.amazon_vend = a.offres.amazon_vend if a.offres else None
    r.ventes_mois = a.historique.ventes_mois_estimees if a.historique else None
    r.raisons = [x for x in a.raisons if x.code not in ("R_PRIX_ACHAT_MAX", "R_TOUT_OK")]   # le verdict le dit déjà
    r.alertes = [x for x in a.alertes if x.code != "A_LOT_MULTIPLE"]     # déjà dit par L_LOT_AMAZON
    part = correspondance(l.designation, r.titre)                          # [RM-AMZ-083]
    if part is not None and part < 0.5:
        r.lignes.append(m("L_PRODUIT_DIFFERENT", part=round(part, 2)))
        if r.verdict == "ACHETER":
            r.verdict = "A_VERIFIER"
    return r


def opportunite(origine: tuple[str, str], mp_code: str, r: ResultatLigne):
    from .opportunites import Opportunite
    return Opportunite(origine[0], origine[1], mp_code, r.code, r.asin, r.titre, r.designation, float(r.prix_unitaire),
                       r.unites_lot, None if r.cout_achat is None else float(r.cout_achat), r.prix_vente, r.profit,
                       r.roi, r.marge, r.prix_achat_max, r.verdict, r.vendabilite, r.motif, r.bsr, r.nb_vendeurs,
                       r.amazon_vend, datetime.now(timezone.utc), prevision=r.prevision)


def executer(t: Traitement, prep: Preparation, mp: Marketplace, f: Fournisseurs, depot,
             regime: str = "assujetti", seuils: Optional[Seuils] = None, achat_ttc: bool = False,
             parametres=None) -> Traitement:
    seuils = seuils or Seuils()
    t.rejets, t.doublons = prep.rejets, prep.doublons
    maintenant = datetime.now(timezone.utc)
    direct = bool(t.origine) and hasattr(depot, "ajouter_opportunites")        # [RM-AMZ-116]
    if direct:
        depot.vider_opportunites(t.compte_id, t.origine[0], mp.code)

    def ranger(r):
        if direct and r.statut == "ANALYSEE" and r.asin:
            depot.ajouter_opportunites(t.compte_id, t.origine[0], mp.code, [opportunite(t.origine, mp.code, r)])
    try:
        for l in prep.lignes:
            if t.arret:
                t.statut = "ARRETE"
                break
            try:
                asins = _asins(t.compte_id, mp, l.code, f, depot, t, maintenant)
            except ErreurFournisseur:
                t.resultats.append(ResultatLigne(l.numero, l.code, l.designation, l.prix_unitaire,
                                                 lignes=[m("L_SOURCE_ERREUR")], statut="ERREUR_SOURCE"))
                t.faits += 1
                continue
            if not asins:
                t.resultats.append(ResultatLigne(l.numero, l.code, l.designation, l.prix_unitaire,
                                                 lignes=list(l.avertissements) + [m("L_INTROUVABLE")],
                                                 statut="INTROUVABLE"))
            for asin in asins:                    # un code peut donner plusieurs listings (lots, variantes)
                t.resultats.append(_ligne(l, mp, asin, f, regime, seuils, achat_ttc, parametres))
                ranger(t.resultats[-1])
            t.faits += 1
        if t.statut == "EN_COURS":
            t.statut = "TERMINE"
        if t.origine and not direct and hasattr(depot, "enregistrer_opportunites"):   # [RM-AMZ-105]
            depot.enregistrer_opportunites(t.compte_id, t.origine[0], t.origine[1], mp.code,
                                           [opportunite(t.origine, mp.code, r) for r in t.resultats
                                            if r.statut == "ANALYSEE" and r.asin])
    except Exception:                             # une panne n'efface pas ce qui est déjà calculé
        t.statut = "ERREUR"
        raise
    return t


class Traitements:
    """Registre des traitements en cours, par compte. En mémoire : un redémarrage les efface (D-AMZ-018)."""

    def __init__(self):
        self._t: dict[str, Traitement] = {}
        self._verrou = threading.Lock()

    def lancer(self, compte_id: str, prep: Preparation, mp: Marketplace, f: Fournisseurs, depot, regime: str,
               achat_ttc: bool, seuils: Optional[Seuils] = None, en_fond: bool = True, parametres=None,
               origine: Optional[tuple[str, str]] = None) -> Traitement:
        t = Traitement(str(uuid.uuid4()), compte_id, mp.code, total=len(prep.lignes), origine=origine)
        with self._verrou:
            self._t[t.id] = t
        travail = lambda: executer(t, prep, mp, f, depot, regime, seuils, achat_ttc, parametres)  # noqa: E731
        if en_fond:
            threading.Thread(target=self._sans_bruit, args=(travail,), daemon=True).start()
        else:
            travail()
        return t

    @staticmethod
    def _sans_bruit(travail):
        try:
            travail()
        except Exception:
            pass  # le statut ERREUR est déjà posé sur le traitement

    def arreter(self, compte_id: str) -> int:
        """[RM-AMZ-136]"""
        en = self.en_cours(compte_id)
        for t in en:
            t.arret = True
        return len(en)

    def en_cours(self, compte_id: str) -> list[Traitement]:
        return [t for t in self._t.values() if t.compte_id == compte_id and t.statut == "EN_COURS"]

    def obtenir(self, compte_id: str, tid: str) -> Optional[Traitement]:
        t = self._t.get(tid)
        return t if t and t.compte_id == compte_id else None


def export_csv(t: Traitement, texte) -> str:
    """[RM-AMZ-035] Export des résultats ; `texte(msg)` traduit un message."""
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow(["ligne", "code", "designation", "asin", "titre", "unites_lot", "cout_achat", "verdict",
                "prix_vente", "profit", "roi", "ventes_mois", "remarques"])
    for r in t.tries():
        rem = " | ".join(texte(x) for x in r.lignes + r.raisons + r.alertes)
        w.writerow([r.numero, r.code, r.designation or "", r.asin or "", r.titre or "", r.unites_lot,
                    "" if r.cout_achat is None else f"{r.cout_achat:.2f}", r.verdict or r.statut,
                    "" if r.prix_vente is None else f"{r.prix_vente:.2f}", "" if r.profit is None else f"{r.profit:.2f}",
                    "" if r.roi is None else f"{r.roi:.4f}", "" if r.ventes_mois is None else r.ventes_mois, rem])
    for n, msg in t.rejets:
        w.writerow([n, "", "", "", "", "", "", "REJETEE", "", "", "", "", texte(msg)])
    return out.getvalue()
