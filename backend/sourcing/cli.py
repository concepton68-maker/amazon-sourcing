"""Ligne de commande.

Exemples :
  python -m sourcing analyse 3700000000017 --mp FR --achat 8.50 --demo
  python -m sourcing analyse B0XXXXXXXX --mp DE --achat 12 --achat-ttc --tva non_assujetti
  python -m sourcing comparer 3700000000017 --mp FR,DE,IT,ES,UK --achat 8.50 --demo
  python -m sourcing places
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .analyse import Fournisseurs, Seuils, analyser_asin, resoudre_asins
from .marketplaces import MARKETPLACES, get_marketplace
from .messages import texte_fr
from .profit import REGIMES_TVA, ParametresCout
from .providers.base import ErreurFournisseur


def charger_env(chemin: Path = Path(".env")) -> None:
    """Charge un fichier .env simple (CLE=valeur) sans dépendance externe."""
    if not chemin.exists():
        return
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            k, v = ligne.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def construire_fournisseurs(demo: bool) -> tuple[Fournisseurs, list[str]]:
    if demo:
        from .providers.demo import FournisseurDemo
        d = FournisseurDemo()
        return Fournisseurs([d], d, d, d, d), ["Mode DÉMO : données fictives."]
    notes, f = [], Fournisseurs()
    try:
        from .providers.spapi import ClientSPAPI
        sp = ClientSPAPI()
        f.catalogue.append(sp)
        f.offres = f.frais = f.restrictions = sp
    except ErreurFournisseur as e:
        notes.append(f"SP-API indisponible : {e}")
    try:
        from .providers.keepa import ClientKeepa
        kp = ClientKeepa()
        f.catalogue.append(kp)
        f.historique = kp
    except ErreurFournisseur as e:
        notes.append(f"Keepa indisponible : {e}")
    return f, notes


def creer_utilisateur(depot, auth, nom_compte: str, courriel: str, mot_de_passe: str):
    """[RM-AMZ-041] Crée un compte vendeur et son premier utilisateur. Renvoie (compte_id, utilisateur)."""
    import uuid
    compte_id = str(uuid.uuid4())
    depot.creer_compte(compte_id, nom_compte)
    return compte_id, auth.creer_utilisateur(compte_id, courriel, mot_de_passe)


def _m(v, devise="", pct=False):
    if v is None:
        return "n/d"
    return f"{v:.0%}" if pct else f"{v:,.2f} {devise}".replace(",", " ").strip()


def afficher(a, devise: str) -> str:
    c, r, h, o = a.catalogue, a.rentabilite, a.historique, a.offres
    L = [
        "=" * 72,
        f"[{a.verdict}]  {a.marketplace}  {a.asin}  {c.titre or ''}",
        f"Marque : {c.marque or 'n/d'} · Catégorie : {c.categorie or 'n/d'} · BSR : {c.bsr or 'n/d'}",
        "-" * 72,
        f"Prix de vente retenu : {_m(a.prix_vente_retenu, devise)} ({a.origine_prix})",
    ]
    if o:
        L.append(f"Offres neuves : {o.nb_offres_fba} FBA / {o.nb_offres_fbm} FBM · "
                 f"Amazon vend : {'oui' if o.amazon_vend else 'non' if o.amazon_vend is False else 'n/d'}")
    if h:
        L.append(f"90 j : prix moyen {_m(h.prix_buybox_moy90, devise)} (min {_m(h.prix_buybox_min90)} / "
                 f"max {_m(h.prix_buybox_max90)}) · BSR moyen {h.bsr_moy90 or 'n/d'} · "
                 f"chutes BSR 30 j : {h.chutes_bsr_30j if h.chutes_bsr_30j is not None else 'n/d'}")
        L.append(f"Ventes estimées : {h.ventes_mois_estimees if h.ventes_mois_estimees is not None else 'n/d'}/mois "
                 f"(listing) · ~{a.ventes_estimees_pour_vous if a.ventes_estimees_pour_vous is not None else 'n/d'}"
                 "/mois pour vous [ESTIMATION]")
    if a.frais:
        f = a.frais
        L.append(f"Frais Amazon HT : commission {_m(f.commission)} + FBA {_m(f.fba)} + clôture {_m(f.cloture)} "
                 f"+ autres {_m(f.autres)} = {_m(f.total_ht, devise)} [{f.source}]")
    if r:
        L += [
            "-" * 72,
            f"Vente HT {_m(r.prix_vente_ht)} − achat net {_m(r.cout_achat_net)} − frais {_m(r.frais_amazon)}"
            f" − TVA frais {_m(r.tva_sur_frais_non_recuperable)} − autres {_m(r.autres_couts)}",
            f"PROFIT NET : {_m(r.profit_net, devise)} · ROI : {_m(r.roi, pct=True)} · "
            f"Marge : {_m(r.marge, pct=True)} · Régime TVA : {r.regime_tva}",
        ]
        if a.rentabilite_prudente:
            p = a.rentabilite_prudente
            L.append(f"Scénario prudent (prix moyen 90 j {_m(p.prix_vente)}) : profit {_m(p.profit_net, devise)}"
                     f" · ROI {_m(p.roi, pct=True)}")
    if a.restrictions:
        s = a.restrictions
        L.append(f"Autorisé à vendre : {'oui' if s.autorise else 'NON' if s.autorise is False else 'n/d'}"
                 + (f" — {'; '.join(s.motifs)}" if s.motifs else ""))
    for titre, liste in (("Pourquoi", a.raisons), ("Alertes", a.alertes), ("Non vérifié", a.non_verifie),
                         ("Hypothèses de calcul", r.hypotheses if r else [])):
        if liste:
            L.append(f"{titre} :")
            L += [f"  • {texte_fr(x)}" for x in liste]
    return "\n".join(L)


def main(argv=None) -> int:
    charger_env()
    p = argparse.ArgumentParser(prog="sourcing", description="Analyse de sourcing Amazon (toutes places de marché).")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("places", help="Lister les places de marché gérées")
    cu = sub.add_parser("creer-utilisateur", help="Créer un compte vendeur et son utilisateur (AMZ_DATABASE_URL requis)")
    cu.add_argument("--courriel", required=True)
    cu.add_argument("--compte", required=True, help="Nom du compte vendeur")
    srv = sub.add_parser("serveur", help="Interface web (AMZ_MODE=dev ou prod)")
    srv.add_argument("--port", type=int, default=8820)
    srv.add_argument("--hote", default="127.0.0.1", help="Adresse d'écoute (0.0.0.0 dans un conteneur)")
    sub.add_parser("migrer", help="Appliquer les migrations (AMZ_DATABASE_URL_OWNER requis)")
    sub.add_parser("synchroniser-nuit", help="Synchronisation de nuit de tous les comptes connectés (AMZ_DATABASE_URL_OWNER, AMZ_CLE_CHIFFREMENT)")
    sub.add_parser("purger", help="Supprimer les comptes révoqués arrivés à échéance (AMZ_DATABASE_URL_OWNER requis)")
    sub.add_parser("parcours-demo", help="Parcours complet sur données fictives (analyse → lot → ventes → écart)")

    for nom, aide in (("analyse", "Analyser un produit sur une place de marché"),
                      ("comparer", "Comparer un produit sur plusieurs places de marché")):
        s = sub.add_parser(nom, help=aide)
        s.add_argument("code", help="ASIN, EAN, UPC ou ISBN")
        s.add_argument("--mp", default="FR", help="Code(s) place de marché, ex. FR ou FR,DE,IT (défaut FR)")
        s.add_argument("--achat", type=float, required=True, help="Prix d'achat unitaire (devise de la place)")
        s.add_argument("--achat-ttc", action="store_true", help="Le prix d'achat inclut la TVA")
        s.add_argument("--tva", choices=REGIMES_TVA, default="assujetti")
        s.add_argument("--taux-tva", type=float, help="Taux de TVA du produit si réduit (ex. 0.055)")
        s.add_argument("--prix-vente", type=float, help="Forcer le prix de vente")
        s.add_argument("--envoi", type=float, default=0.0, help="Envoi vers Amazon par unité")
        s.add_argument("--prep", type=float, default=0.0, help="Préparation par unité")
        s.add_argument("--retours", type=float, default=0.0, help="Provision retours (0.03 = 3 %%)")
        s.add_argument("--roi-min", type=float, default=0.30)
        s.add_argument("--profit-min", type=float, default=3.0)
        s.add_argument("--demo", action="store_true", help="Données fictives, sans clé API")
        s.add_argument("--json", action="store_true", help="Sortie JSON")

    a = p.parse_args(argv)

    if a.cmd == "migrer":
        import psycopg

        from .db import migrer
        url = os.environ.get("AMZ_DATABASE_URL_OWNER")
        if not url:
            print("AMZ_DATABASE_URL_OWNER requis.", file=sys.stderr)
            return 2
        with psycopg.connect(url, autocommit=True) as conn:
            faites = migrer(conn)
        print("Migrations appliquées : " + (", ".join(faites) or "aucune (base à jour)"))
        return 0

    if a.cmd == "synchroniser-nuit":  # [RM-AMZ-080]
        from datetime import datetime, timezone

        import psycopg

        from . import connexions as CX
        from .db import DepotPostgres, comptes_connectes
        from .synchro_nuit import executer
        url, cle = os.environ.get("AMZ_DATABASE_URL_OWNER"), CX.cle_serveur()
        if not url or not cle:
            print("AMZ_DATABASE_URL_OWNER et AMZ_CLE_CHIFFREMENT requis.", file=sys.stderr)
            return 2
        with psycopg.connect(url, autocommit=True) as conn:
            comptes = []
            for cid, chiffre in comptes_connectes(conn):
                try:
                    comptes.append((cid, CX.dechiffrer(cle, cid, "SPAPI", chiffre)))
                except Exception:
                    print(f"compte {cid[:8]} : identifiants illisibles", file=sys.stderr)
            res = executer(comptes, DepotPostgres(conn), datetime.now(timezone.utc))
        echecs = sum(1 for r in res.values() for t in r if not t.ok)
        for cid, r in res.items():
            print(f"compte {cid[:8]} : " + " ; ".join(f"{t.tache} {'OK' if t.ok else 'ÉCHEC'} {t.message}" for t in r))
        print(f"{len(res)} compte(s), {echecs} tâche(s) en échec")
        return 1 if echecs else 0

    if a.cmd == "purger":  # [RM-AMZ-068]
        from datetime import date

        import psycopg

        from .db import purger
        url = os.environ.get("AMZ_DATABASE_URL_OWNER")
        if not url:
            print("AMZ_DATABASE_URL_OWNER requis.", file=sys.stderr)
            return 2
        with psycopg.connect(url, autocommit=True) as conn:
            faits = purger(conn, date.today())
        print(f"Comptes supprimés : {len(faits)}")
        return 0

    if a.cmd == "creer-utilisateur":
        import getpass

        import psycopg

        from .auth import Authentification, ErreurAuth, StockAuthPostgres
        from .db import DepotPostgres
        url = os.environ.get("AMZ_DATABASE_URL")
        if not url:
            print("AMZ_DATABASE_URL requis.", file=sys.stderr)
            return 2
        mdp = getpass.getpass("Mot de passe (12 caractères au moins) : ")
        if mdp != getpass.getpass("Confirmer : "):
            print("Les deux saisies diffèrent.", file=sys.stderr)
            return 2
        with psycopg.connect(url, autocommit=True) as conn:
            try:
                cid, u = creer_utilisateur(DepotPostgres(conn), Authentification(StockAuthPostgres(conn)),
                                           a.compte, a.courriel, mdp)
            except ErreurAuth as e:
                print(f"Refusé : {e.args[0]}", file=sys.stderr)
                return 2
        print(f"Compte {cid} créé, utilisateur {u.courriel}.")
        return 0

    if a.cmd == "serveur":
        import uvicorn
        from .api import app_depuis_environnement
        uvicorn.run(app_depuis_environnement(), host=a.hote, port=a.port, proxy_headers=True)
        return 0

    if a.cmd == "parcours-demo":
        from .demo_parcours import executer
        print(executer())
        return 0

    if a.cmd == "places":
        for m in MARKETPLACES.values():
            print(f"{m.code:3} {m.domaine:16} {m.devise}  TVA std {m.taux_tva_standard:>5.0%}  "
                  f"région {m.region}  Keepa {'oui' if m.keepa_domain else 'non'}")
        return 0

    fournisseurs, notes = construire_fournisseurs(a.demo)
    for n in notes:
        print(f"ℹ {n}", file=sys.stderr)
    couts = ParametresCout(prix_achat=a.achat, prix_achat_ttc=a.achat_ttc, taux_tva_achat=a.taux_tva,
                           envoi_entrepot=a.envoi, preparation=a.prep, taux_retours=a.retours)
    seuils = Seuils(roi_min=a.roi_min, profit_min=a.profit_min)

    resultats = []
    for code_mp in a.mp.split(","):
        mp = get_marketplace(code_mp)
        try:
            asins = resoudre_asins(mp, a.code, fournisseurs)
        except ErreurFournisseur as e:
            print(f"✗ {mp.code} : {e}", file=sys.stderr)
            continue
        if not asins:
            print(f"✗ {mp.code} : aucun ASIN trouvé pour {a.code}.", file=sys.stderr)
            continue
        if len(asins) > 1:
            print(f"ℹ {mp.code} : {len(asins)} ASIN pour {a.code} (lots ou variantes) — tous analysés.", file=sys.stderr)
        for asin in asins:
            res = analyser_asin(mp, asin, couts, fournisseurs, a.tva, seuils, a.prix_vente, a.taux_tva)
            resultats.append(res)
            if not a.json and a.cmd == "analyse":
                print(afficher(res, mp.devise))

    if a.json:
        print(json.dumps([r.to_dict() for r in resultats], ensure_ascii=False, indent=2))
    elif a.cmd == "comparer" and resultats:
        print(f"{'Place':6}{'ASIN':12}{'Verdict':12}{'Prix':>10}{'Profit':>10}{'ROI':>7}  Devise")
        for r in sorted(resultats, key=lambda x: (x.rentabilite.roi or -9) if x.rentabilite else -9, reverse=True):
            rt = r.rentabilite
            print(f"{r.marketplace:6}{r.asin:12}{r.verdict:12}{_m(r.prix_vente_retenu):>10}"
                  f"{_m(rt.profit_net) if rt else 'n/d':>10}{_m(rt.roi, pct=True) if rt else 'n/d':>7}  "
                  f"{get_marketplace(r.marketplace).devise}")
        print("Attention : prix d'achat supposé dans la devise de chaque place ; conversion non faite.")
    return 0 if resultats else 1
