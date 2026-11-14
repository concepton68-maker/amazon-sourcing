"""Frais FBA Europe hors API — [RM-AMZ-096, 097, 099].

Source unique : grille « FBA Rate Card Europe, effective 2 November 2026 »
(m.media-amazon.com/images/G/02/sell/images/261014-FBA-Rate-Card-EN.pdf), lue le 14/11/2026.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

SOURCE_GRILLE = "FBA Rate Card Europe, 2 novembre 2026"

# [RM-AMZ-097] supplément carburant et logistique sur les frais d'expédition FBA
CARBURANT = ((date(2026, 11, 2), 0.02, frozenset({"UK", "FR", "DE", "IT", "ES", "PL", "SE", "NL", "IE", "BE"})),)

# [RM-AMZ-096] stockage mensuel €/m³ : (janvier–septembre, octobre–décembre)
PLACES_EURO_M3 = frozenset({"DE", "FR", "IT", "ES", "NL", "PL", "BE", "IE"})
VETEMENTS, AUTRES, HORS_GABARIT = "VETEMENTS", "AUTRES", "HORS_GABARIT"
LIBELLES = {VETEMENTS: "vêtements, chaussures, sacs", AUTRES: "autres catégories", HORS_GABARIT: "hors gabarit"}
TARIFS_STOCKAGE = {VETEMENTS: (19.99, 29.23), AUTRES: (27.54, 52.20), HORS_GABARIT: (21.78, 34.49)}
STANDARD_MAX_CM = (45.0, 34.0, 26.0)
STANDARD_MAX_KG = 11.9
STANDARD_MAX_VOLUMETRIQUE_KG = 7.96
DIVISEUR_VOLUMETRIQUE = 5000          # « (length x width x height cm³) divided by 5000 »
# Groupes d'affichage Amazon reconnus comme « vêtements, chaussures, sacs » (choix de l'outil)
GROUPES_VETEMENTS = frozenset({"apparel_display_on_website", "shoes_display_on_website",
                               "luggage_display_on_website"})


def taux_carburant(mp_code: str, jour: date) -> Optional[float]:
    taux = None
    for debut, t, places in CARBURANT:
        if jour >= debut and mp_code in places:
            taux = t
    return taux


def gabarit(dimensions_cm: Optional[tuple], poids_kg: Optional[float]) -> Optional[str]:
    """STANDARD ou HORS_GABARIT ; None si dimensions ou poids inconnus."""
    if not dimensions_cm or len(dimensions_cm) != 3 or poids_kg is None:
        return None
    d = sorted(dimensions_cm, reverse=True)
    volumetrique = d[0] * d[1] * d[2] / DIVISEUR_VOLUMETRIQUE
    tient = all(x <= m for x, m in zip(d, STANDARD_MAX_CM))
    if tient and poids_kg <= STANDARD_MAX_KG and volumetrique <= STANDARD_MAX_VOLUMETRIQUE_KG:
        return "STANDARD"
    return HORS_GABARIT


def stockage(mp_code: str, dimensions_cm: Optional[tuple], poids_kg: Optional[float], groupe: Optional[str],
             debut: date, mois: float) -> Optional[dict]:
    """Coût de stockage par unité sur `mois` mois à partir de `debut` ; None si non calculable."""
    if mp_code not in PLACES_EURO_M3 or mois <= 0:
        return None
    g = gabarit(dimensions_cm, poids_kg)
    if g is None:
        return None
    categorie = HORS_GABARIT if g == HORS_GABARIT else (VETEMENTS if groupe in GROUPES_VETEMENTS else AUTRES)
    volume = dimensions_cm[0] * dimensions_cm[1] * dimensions_cm[2] / 1_000_000
    total, reste, a, m = 0.0, mois, debut.year, debut.month
    while reste > 1e-9:
        part = min(1.0, reste)
        tarif = TARIFS_STOCKAGE[categorie][1 if m >= 10 else 0]
        total += volume * tarif * part
        reste -= part
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return {"montant": round(total, 4), "volume_m3": volume, "categorie": categorie, "mois": mois}
