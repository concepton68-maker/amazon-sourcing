"""Vérification d'autorisation en masse — [RM-AMZ-120, 121]."""
from __future__ import annotations

import csv
import io
import re
import threading
import time
from datetime import datetime, timezone

from .analyse import resoudre_asins

MAX_CODES = 5000
PAUSE = 0.25                          # 4 requêtes/s, sous le plafond de 5/s
AUTORISE, APPROBATION, INTERDIT, INTROUVABLE, INCONNU = "AUTORISE", "APPROBATION", "INTERDIT", "INTROUVABLE", "INCONNU"


def lire_codes(texte: str) -> list[str]:
    """Codes séparés par retours, virgules, points-virgules ou espaces ; doublons ignorés, ordre gardé."""
    codes = [c.strip().upper() for c in re.split(r"[\s,;]+", texte or "") if c.strip()]
    codes = [c for c in codes if re.fullmatch(r"[A-Z0-9]{8,14}", c)]
    return list(dict.fromkeys(codes))[:MAX_CODES]


def verifier_un(mp, code: str, fx) -> dict:
    try:
        asins = resoudre_asins(mp, code, fx)
    except Exception:
        return {"code": code, "statut": INCONNU}
    if not asins:
        return {"code": code, "statut": INTROUVABLE}
    asin = asins[0]
    try:
        r = fx.restrictions.restrictions(mp, asin)
    except Exception:
        return {"code": code, "asin": asin, "statut": INCONNU}
    if r is None or r.autorise is None:
        statut = INCONNU
    elif r.autorise:
        statut = AUTORISE
    else:
        statut = APPROBATION if r.approbation_requise else INTERDIT
    return {"code": code, "asin": asin, "statut": statut, "motifs": list(r.motifs) if r else [],
            "liens": list(r.liens) if r else []}


class Verifications:
    """[RM-AMZ-121] Une à la fois par compte ; résultats au fil de l'eau ; dernier lot gardé en mémoire."""

    def __init__(self, en_fond: bool = True):
        self.etats: dict[str, dict] = {}
        self.en_fond = en_fond
        self._verrou = threading.Lock()

    def lancer(self, compte_id: str, mp, fx, codes: list[str], attendre=time.sleep) -> bool:
        with self._verrou:
            if self.etats.get(compte_id, {}).get("en_cours"):
                return False
            etat = {"en_cours": True, "marketplace": mp.code, "total": len(codes), "resultats": [],
                    "debut": datetime.now(timezone.utc).isoformat()}
            self.etats[compte_id] = etat

        def travail():
            try:
                for c in codes:
                    etat["resultats"].append(verifier_un(mp, c, fx))
                    attendre(PAUSE)
            finally:
                etat["en_cours"] = False
                etat["fin"] = datetime.now(timezone.utc).isoformat()
        if self.en_fond:
            threading.Thread(target=travail, daemon=True).start()
        else:
            travail()
        return True


def export_csv(etat: dict) -> str:
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow(["code", "asin", "statut", "lien_demande", "motifs"])
    for r in etat.get("resultats", []):
        w.writerow([r["code"], r.get("asin", ""), r["statut"], (r.get("liens") or [{}])[0].get("url", ""),
                    " | ".join(r.get("motifs", []))])
    return out.getvalue()
