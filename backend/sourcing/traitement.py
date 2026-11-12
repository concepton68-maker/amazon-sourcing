"""Traitement d'un fichier fournisseur — [RM-AMZ-033, 034, 035].

Chaque ligne : appariement code → ASIN (mémoire du compte, sinon recherche), analyse complète
(mêmes règles que l'écran Analyse produit), coût recalculé si le listing Amazon est un lot.
"""
from __future__ import annotations

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
    debut: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

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


def _ligne(l: LigneFournisseur, mp: Marketplace, asin: str, f: Fournisseurs, regime: str, seuils: Seuils,
           achat_ttc: bool) -> ResultatLigne:
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
    a: AnalyseProduit = analyser_asin(mp, asin, ParametresCout(float(r.cout_achat), prix_achat_ttc=achat_ttc),
                                      f, regime, seuils)
    r.titre, r.verdict, r.prix_vente = a.catalogue.titre, a.verdict, a.prix_vente_retenu
    if a.rentabilite:
        r.profit, r.roi = a.rentabilite.profit_net, a.rentabilite.roi
    r.ventes_mois = a.historique.ventes_mois_estimees if a.historique else None
    r.raisons = [x for x in a.raisons if x.code not in ("R_PRIX_ACHAT_MAX", "R_TOUT_OK")]   # le verdict le dit déjà
    r.alertes = [x for x in a.alertes if x.code != "A_LOT_MULTIPLE"]     # déjà dit par L_LOT_AMAZON
    return r


def executer(t: Traitement, prep: Preparation, mp: Marketplace, f: Fournisseurs, depot,
             regime: str = "assujetti", seuils: Optional[Seuils] = None, achat_ttc: bool = False) -> Traitement:
    seuils = seuils or Seuils()
    t.rejets, t.doublons = prep.rejets, prep.doublons
    maintenant = datetime.now(timezone.utc)
    try:
        for l in prep.lignes:
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
                t.resultats.append(_ligne(l, mp, asin, f, regime, seuils, achat_ttc))
            t.faits += 1
        t.statut = "TERMINE"
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
               achat_ttc: bool, seuils: Optional[Seuils] = None, en_fond: bool = True) -> Traitement:
        t = Traitement(str(uuid.uuid4()), compte_id, mp.code, total=len(prep.lignes))
        with self._verrou:
            self._t[t.id] = t
        travail = lambda: executer(t, prep, mp, f, depot, regime, seuils, achat_ttc)  # noqa: E731
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
