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
              "Facture et preuve de chaîne d'approvisionnement prévues pour Amazon ; GTIN, prix, stock, minimum ; "
              "API actuelle fermée fin janvier 2027 : demander la « Public API (Buyers) » à api@qogita.com"),
    Reference("BIGBUY", "BigBuy", "ES", "https://www.bigbuy.eu", ("MAISON", "JOUETS", "SPORT", "BEAUTE", "ANIMAUX",
                                                                     "BRICOLAGE", "INFORMATIQUE"), A_VERIFIER,
              "https://www.bigbuy.eu/en/dropshipping-amazon.html", "EXTRAIT", FICHIER, True,
              "Abonnement payant (pack « Ecommerce » ou plus pour l'API et les fichiers)",
              "Offre Amazon dédiée, mais « pas distributeur officiel des marques » (CGV §16) : à relire"),
    Reference("VIDAXL", "vidaXL dropshipping", "NL", "https://dropshipping.vidaxl.com", ("MAISON", "JARDIN"), A_VERIFIER,
              "https://dropshipping.vidaxl.com/terms-conditions/", "EXTRAIT", FICHIER, True,
              "30 €/mois par pays de livraison", "Produits de la marque vidaXL, déjà vendus par vidaXL sur Amazon"),
    Reference("BRANDSDISTRIBUTION", "Brandsdistribution", "IT", "https://www.brandsdistribution.com", ("VETEMENTS",),
              A_VERIFIER, "https://www.brandsdistribution.com/en/cms/dropshipping-guide", "LU", FICHIER, True,
              "99 € HT/mois ou 990 € HT/an", "Aucune règle écrite sur Amazon ; mode de marque : risque de plainte"),
    # Recherche approfondie du 14/11/2026 (docs/recherches/2026-11-14-fournisseurs-api-approfondi.md)
    Reference("BTSWHOLESALER", "BTSwholesaler", "ES", "https://www.btswholesaler.com", ("BEAUTE",), AUTORISEE,
              "https://api.btswholesaler.com/en/site/amazon-info", "LU", FICHIER, True,
              "Inscription professionnelle ; jeton d'API généré dans l'espace client",
              "Intégration Amazon officielle prévue pour l'expédition par le vendeur (pas FBA) ; parfums et cosmétiques"),
    Reference("PUCKATOR", "Puckator", "UK", "https://www.puckator.co.uk", ("MAISON", "CUISINE", "JOUETS", "BAGAGES"),
              AUTORISEE, "https://www.puckator.co.uk/amazon-fulfilment", "LU", FICHIER, False,
              "Compte grossiste, minimum £50 ; flux CSV/XML/JSON dans « My Account »",
              "Envoi vers les centres Amazon pris en charge ; prix en GBP et import UK → UE à chiffrer"),
    Reference("NEDIS", "Nedis", "NL", "https://nedis.com", ("INFORMATIQUE", "MAISON", "LUMINAIRES"), A_VERIFIER,
              "", "AUCUNE", FICHIER, True, "Compte via le bureau Nedis local ; adresse IP fixe déclarée pour l'API",
              "API OAuth2 : prix client et stock en temps réel"),
    Reference("APICOMPUTER", "api Computerhandels", "DE", "https://api.de", ("INFORMATIQUE",), A_VERIFIER, "", "AUCUNE",
              FICHIER, True, "Client professionnel ; liste de prix par lien (3 téléchargements / 15 min)",
              "Liste de prix CSV/XML avec EAN, stock et prix ; envoi au nom du revendeur"),
    Reference("INGRAM", "Ingram Micro", "US", "https://developer.ingrammicro.com", ("INFORMATIQUE",), A_VERIFIER, "",
              "AUCUNE", AUCUNE, True, "Compte revendeur avec historique d'achats, puis application développeur approuvée",
              "API OAuth2 : catalogue, prix et disponibilité, commandes ; difficile pour un compte neuf"),
    Reference("TDSYNNEX", "TD SYNNEX", "EU", "https://developer.api.tdsynnex.com/eu", ("INFORMATIQUE",), A_VERIFIER, "",
              "AUCUNE", AUCUNE, True, "Compte revendeur", "Portail développeur Europe : catalogue, prix, disponibilité"),
    Reference("ALSO", "ALSO", "FR", "https://www.also.com", ("INFORMATIQUE",), A_VERIFIER, "", "AUCUNE", FICHIER, False,
              "Ouverture de compte en ligne ; première commande payée d'avance", "Listes de prix par FTP (TXT/CSV)"),
    Reference("WARMAKO", "Warmako", "NL", "https://www.warmako.com", ("ANIMAUX",), A_VERIFIER, "", "AUCUNE", FICHIER,
              True, "Clients professionnels en Europe, vente en ligne acceptée", "Animalerie premium, plus de 5 000 articles"),
    Reference("BRANDSGATEWAY", "BrandsGateway", "SE", "https://brandsgateway.com", ("VETEMENTS",), A_VERIFIER, "",
              "AUCUNE", FICHIER, True, "Abonnement dropshipping", "Mode de luxe ; risque de plainte des marques"),
    Reference("SPOCKET", "Spocket", "EU", "https://www.spocket.co", ("MAISON", "BEAUTE", "VETEMENTS"), AUTORISEE,
              "https://help.spocket.co/en/articles/3018488-where-can-i-sell-spocket-products", "LU", AUCUNE, False,
              "Abonnement", "Pas d'API pour le revendeur trouvée ; plutôt pour l'expédition par le vendeur"),
    Reference("INTERCARS", "Inter Cars", "PL", "https://intercars.eu", ("AUTO",), A_VERIFIER, "", "AUCUNE", AUCUNE, True,
              "Client B2B Inter Cars", "Pièces auto ; API documentée en ligne"),
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
