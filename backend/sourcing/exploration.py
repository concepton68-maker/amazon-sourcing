"""Ce que je peux vendre — sondage des rayons [RM-AMZ-084, 085].

Pour chaque rayon : recherche dans le catalogue par mots-clés, tri par classement des ventes, vérification de
l'autorisation de vente de chaque produit. C'est un sondage, jamais une garantie.
"""
from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

# Rayons et mots-clés (choix de l'outil ; amazon.fr dans cette version)
RAYONS: tuple[tuple[str, str], ...] = (
    ("CUISINE", "ustensile cuisine"), ("MAISON", "rangement maison"), ("JARDIN", "jardin"),
    ("BRICOLAGE", "outil bricolage"), ("SPORT", "accessoire sport"), ("ANIMAUX", "accessoire chien chat"),
    ("BUREAU", "fourniture bureau"), ("AUTO", "accessoire voiture"), ("BEBE", "bébé"), ("JOUETS", "jouet enfant"),
    ("BEAUTE", "soin beauté"), ("INFORMATIQUE", "accessoire ordinateur"), ("BAGAGES", "sac voyage"),
    ("LUMINAIRES", "lampe led"), ("EPICERIE", "épicerie"), ("VETEMENTS", "vêtement"),
)
OUVERT, PARTIEL, FERME, INCONNU = "OUVERT", "PARTIEL", "FERME", "INCONNU"
AUTORISE, APPROBATION, INTERDIT = "AUTORISE", "APPROBATION", "INTERDIT"
SEUIL_OUVERT = 0.8
PAUSE_RESTRICTIONS = 0.25        # 4 requêtes/s, sous le plafond de 5/s
PAUSE_RECHERCHE = 0.6            # sous le plafond de 2/s


@dataclass
class ProduitSonde:
    asin: str
    titre: Optional[str]
    bsr: Optional[int]
    categorie: Optional[str]
    statut: str                  # AUTORISE / APPROBATION / INTERDIT / INCONNU


@dataclass
class Rayon:
    code: str
    produits: list[ProduitSonde] = field(default_factory=list)
    erreur: Optional[str] = None

    def compte(self, statut: str) -> int:
        return sum(1 for p in self.produits if p.statut == statut)

    @property
    def statut(self) -> str:
        connus = [p for p in self.produits if p.statut != INCONNU]
        if not connus:
            return INCONNU
        part = self.compte(AUTORISE) / len(connus)
        return OUVERT if part >= SEUIL_OUVERT else PARTIEL if part > 0 else FERME


def statut_restriction(r) -> str:
    if r is None or r.autorise is None:
        return INCONNU
    if r.autorise:
        return AUTORISE
    return APPROBATION if r.approbation_requise else INTERDIT


def sonder(mp, fournisseurs, progression: Callable[[int, int], None] = lambda f, t: None,
           attendre: Callable[[float], None] = time.sleep, rayons=RAYONS, taille: int = 20) -> list[Rayon]:
    """[RM-AMZ-084] Un rayon après l'autre ; une erreur de rayon n'arrête pas les autres."""
    cherche = next((s for s in fournisseurs.catalogue if hasattr(s, "rechercher")), None)
    out = []
    for k, (code, mots) in enumerate(rayons):
        progression(k, len(rayons))
        ray = Rayon(code)
        try:
            items = cherche.rechercher(mp, mots, taille) if cherche else []
            attendre(PAUSE_RECHERCHE)
            items = sorted(items, key=lambda c: (c.bsr is None, c.bsr or 0))[:taille]
            for c in items:
                try:
                    st = statut_restriction(fournisseurs.restrictions.restrictions(mp, c.asin))
                except Exception:
                    st = INCONNU
                ray.produits.append(ProduitSonde(c.asin, c.titre, c.bsr, c.categorie, st))
                attendre(PAUSE_RESTRICTIONS)
        except Exception as e:
            ray.erreur = f"{type(e).__name__}: {str(e)[:200]}"
        out.append(ray)
    progression(len(rayons), len(rayons))
    return out


def en_json(rayons: list[Rayon], place: str, le: datetime) -> dict:
    return {"place": place, "le": le.isoformat(), "rayons": [
        {"code": r.code, "statut": r.statut, "testes": len(r.produits), "autorises": r.compte(AUTORISE),
         "approbation": r.compte(APPROBATION), "interdits": r.compte(INTERDIT), "inconnus": r.compte(INCONNU),
         "erreur": r.erreur, "produits": [asdict(p) for p in r.produits]} for r in rayons]}


class Explorations:
    """[RM-AMZ-085] Une exploration à la fois par compte, en arrière-plan ; le résultat est rangé dans le dépôt."""

    def __init__(self, en_fond: bool = True):
        self.en_cours: dict[str, tuple[int, int]] = {}
        self.en_fond = en_fond
        self._verrou = threading.Lock()

    def lancer(self, compte_id: str, mp, fournisseurs, depot, attendre=time.sleep) -> bool:
        with self._verrou:
            if compte_id in self.en_cours:
                return False
            self.en_cours[compte_id] = (0, len(RAYONS))

        def travail():
            try:
                res = sonder(mp, fournisseurs, lambda f, t: self.en_cours.__setitem__(compte_id, (f, t)), attendre)
                depot.enregistrer_exploration(compte_id, en_json(res, mp.code, datetime.now(timezone.utc)))
            finally:
                self.en_cours.pop(compte_id, None)
        if self.en_fond:
            threading.Thread(target=travail, daemon=True).start()
        else:
            travail()
        return True
