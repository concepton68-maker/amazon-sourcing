"""Annuaire de référence des fournisseurs — [RM-AMZ-101, 104].

Commun à tous les comptes, sans aucune donnée de compte. Chaque fait vient de l'étude
docs/recherches/2026-11-14-sources-fournisseurs.md (lue le 14/11/2026) :
- verification « LU » : page officielle lue ;
- verification « EXTRAIT » : texte officiel vu seulement dans l'extrait d'un moteur de recherche (à relire).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

AUTORISEE, INTERDITE, A_VERIFIER = "AUTORISEE", "INTERDITE", "A_VERIFIER"
FICHIER, API, AUCUNE = "FICHIER", "API", "AUCUNE"
DATE_LECTURE = "2026-11-14"


@dataclass(frozen=True)
class Reference:
    code: str
    nom: str
    pays: str
    site: str
    categories: tuple
    revente: str                 # AUTORISEE / INTERDITE / A_VERIFIER
    source: str                  # lien de la page qui fonde « revente »
    verification: str            # LU / EXTRAIT / AUCUNE
    connexion: str               # FICHIER / API / AUCUNE : ce qui est possible aujourd'hui dans l'outil
    api: bool                    # le fournisseur a une API (à brancher, RM-AMZ-104)
    acces: str                   # conditions d'accès connues
    note: str

    def to_dict(self) -> dict:
        return {**asdict(self), "categories": list(self.categories), "date_lecture": DATE_LECTURE}


REFERENCES: tuple[Reference, ...] = (
    Reference("QOGITA", "Qogita", "NL", "https://www.qogita.com", ("BEAUTE", "EPICERIE"), AUTORISEE,
              "https://help.qogita.com/proving-chain-of-supply", "LU", FICHIER, True,
              "Compte acheteur professionnel (numéro de TVA UE) ; export Excel du catalogue",
              "Facture et preuve de chaîne d'approvisionnement prévues pour Amazon ; GTIN, prix, stock, minimum"),
    Reference("BIGBUY", "BigBuy", "ES", "https://www.bigbuy.eu", ("MAISON", "JOUETS", "SPORT", "BEAUTE"), A_VERIFIER,
              "https://www.bigbuy.eu/en/dropshipping-amazon.html", "EXTRAIT", FICHIER, True,
              "Abonnement payant (pack « Ecommerce » ou plus pour l'API et les fichiers)",
              "Offre Amazon dédiée, mais « pas distributeur officiel des marques » (CGV §16) : à relire"),
    Reference("VIDAXL", "vidaXL dropshipping", "NL", "https://dropshipping.vidaxl.com", ("MAISON", "JARDIN"), A_VERIFIER,
              "https://dropshipping.vidaxl.com/terms-conditions/", "EXTRAIT", FICHIER, True,
              "30 €/mois par pays de livraison", "Produits de la marque vidaXL, déjà vendus par vidaXL sur Amazon"),
    Reference("BRANDSDISTRIBUTION", "Brandsdistribution", "IT", "https://www.brandsdistribution.com", ("VETEMENTS",),
              A_VERIFIER, "https://www.brandsdistribution.com/en/cms/dropshipping-guide", "LU", FICHIER, True,
              "99 € HT/mois ou 990 € HT/an", "Aucune règle écrite sur Amazon ; mode de marque : risque de plainte"),
    Reference("ANKORSTORE", "Ankorstore", "FR", "https://www.ankorstore.com", ("MAISON", "EPICERIE", "BEAUTE"), INTERDITE,
              "https://support.ankorstore.com/articles/3353966746-starting-as-a-retailer", "LU", AUCUNE, False,
              "—", "Non éligible si l'on revend seulement sur Amazon ou eBay ; robots interdits (§17.5)"),
    Reference("FAIRE", "Faire", "US", "https://www.faire.com", ("MAISON", "BEAUTE"), INTERDITE,
              "https://www.faire.com/support/articles/18524831904667", "EXTRAIT", AUCUNE, False,
              "—", "« Prohibited sites include Amazon, eBay, Etsy, and Poshmark » (à relire)"),
    Reference("CREOATE", "Creoate", "UK", "https://www.creoate.com", ("MAISON",), INTERDITE,
              "https://www.creoate.com/terms-and-conditions", "EXTRAIT", AUCUNE, False,
              "—", "CGU : commandes sur Amazon interdites ; le centre d'aide diverge (à relire)"),
    Reference("ALIBABA", "Alibaba.com", "CN", "https://www.alibaba.com", (), A_VERIFIER, "", "AUCUNE", FICHIER, False,
              "Devis à la demande", "Pas d'API pour l'acheteur ; collecte automatisée interdite sans accord écrit"),
    Reference("GLOBALSOURCES", "Global Sources", "HK", "https://www.globalsources.com", (), A_VERIFIER, "", "AUCUNE",
              FICHIER, False, "Devis à la demande", "Pas d'API pour l'acheteur ; copie et stockage interdits sans accord"),
)
PAR_CODE = {r.code: r for r in REFERENCES}
