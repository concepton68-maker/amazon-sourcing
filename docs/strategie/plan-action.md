# Plan de stratégie — Syllig Vente

Version 1 du 14/11/2026, **à valider par Sam**. Aucun code n'est écrit avant cette validation.
Sources : `docs/recherches/2026-11-11-donnees-et-outils-verifies.md`, `2026-11-14-benchmark-fonctions.md`,
`2026-11-14-sources-fournisseurs.md`. Tout chiffre non sourcé est marqué « à vérifier ».

## 1. Le but

Un **moteur d'opportunités** : il part des catalogues de fournisseurs, puis compare chaque produit à Amazon.
Il calcule le **coût complet** jusqu'à la vente finale et sort une **liste d'achats classée** :

- quel produit acheter ;
- chez quel fournisseur ;
- en quelle quantité ;
- à quel prix le vendre ;
- quel profit en attendre.

Il sert d'abord à Sam (GO-SHOPPING), puis il est vendu à d'autres vendeurs.

**Ce qu'on vend, c'est l'outil, pas les données d'Amazon.** Le règlement d'utilisation de l'API d'Amazon
(articles 4.3 et 4.4) interdit de revendre ou de mettre en commun les données obtenues par l'API.

## 2. Ce qui marche déjà en ligne (vente.concepton.fr)

- Connexion sécurisée avec double authentification.
- Branchement à Amazon par l'API officielle, avec un bouton pour tester la connexion.
- Import d'un fichier fournisseur (EAN, prix, colisage). Pour chaque produit, l'outil sort :
  - la fiche Amazon trouvée ;
  - les frais Amazon ;
  - les offres concurrentes ;
  - l'autorisation de vente ;
  - le verdict.
- Page « Je peux vendre » : sondage de 16 rayons.
- Chaque nuit :
  - relevé des ventes, du stock et des remboursements ;
  - sauvegarde ;
  - page publique de contrôle.

## 3. Le tunnel pour le débutant (6 étapes)

Chaque étape a un écran, une action principale et un état (fait / à faire).

| # | Étape | Ce que l'outil fait | Données |
|---|---|---|---|
| 1 | **Mon compte Amazon** | Branche le compte vendeur, liste les pays ouverts et sonde ce que le vendeur peut vendre (rayons, marques) | API Amazon (fait) |
| 2 | **Trouver des fournisseurs** | Propose des sources compatibles avec la revente Amazon et les branche (API ou fichier) ; liste les marques autorisées pour contacter leurs distributeurs | Qogita, BigBuy, fichiers |
| 3 | **Mettre les catalogues dans l'outil** | Import du fichier ou synchronisation automatique par API ; prix, stock, minimum de commande | Fournisseurs |
| 4 | **Trouver les opportunités** | Rapproche chaque produit du fournisseur avec la fiche Amazon, calcule le coût complet et le prix de vente, applique les filtres et classe | Moteur (§ 4) |
| 5 | **Simuler** (« business virtuel ») | Pour une sélection : quantités, budget, trésorerie, délai de revente, profit total prévu | Moteur + historique |
| 6 | **Acheter et suivre** | Bon de commande, envoi chez Amazon, puis comparaison du prévu et du réel par lot, et alertes | API Amazon (en partie fait) |

## 4. Le moteur d'opportunités

### 4.1 Le coût complet, par unité

| Ligne | État |
|---|---|
| Prix d'achat HT ÷ colisage, minimum de commande | fait |
| Port fournisseur (forfait ou par unité, saisi par fournisseur) | à faire |
| Commission Amazon et frais d'expédition FBA (`getMyFeesEstimate`) | fait |
| Supplément carburant et logistique de **2 %** sur les frais d'expédition FBA en Europe, depuis le 02/11/2026 | vérifié (sell.amazon.fr/en/tarifs), **à intégrer** si l'estimation d'Amazon ne l'inclut pas déjà (à vérifier) |
| Frais de placement à l'envoi (Inbound 2024-03-20) | à faire, montants à vérifier |
| Stockage mensuel (au m³, hausse d'octobre à décembre) × durée de revente prévue | principe vérifié, montants à vérifier |
| Frais de faible stock et de retour | à vérifier |
| Envoi vers l'entrepôt Amazon (transporteur) | à saisir par le vendeur |
| TVA selon le régime du vendeur et le pays de vente | règle à sourcer |

Il en sort, pour chaque produit :

- le **profit par unité** ;
- le **retour sur investissement (ROI)** ;
- le **prix d'achat maximum** pour atteindre l'objectif ;
- le **prix de vente prudent** : le plus bas entre la Buy Box, le prix de seuil d'Amazon et la moyenne de notre historique.

### 4.2 Les filtres

- autorisé à vendre ;
- marge minimale ;
- ROI minimal ;
- Amazon absent de la Buy Box ;
- nombre de vendeurs maximal ;
- classement des ventes maximal ;
- famille de produits officielle d'Amazon ;
- pays de vente ;
- budget.

### 4.3 Le classement

La liste est triée par **profit mensuel probable**. Pour l'estimer :

- **ventes du produit** : déduites de notre historique (baisses du classement) ;
- **part probable du vendeur** : ventes ÷ (vendeurs présents + 1) ;
- **profit mensuel** : part probable × profit par unité.

Sans assez d'historique, la ligne est marquée « estimation fragile ».

### 4.4 Notre propre historique (sans Keepa, D-AMZ-026)

**Ce qui est suivi chaque nuit**, pour chaque compte :

- les produits analysés ;
- les produits des catalogues fournisseurs rapprochés ;
- la liste de suivi.

**Ce qui est relevé** :

- le prix de la Buy Box et qui la détient ;
- le nombre de vendeurs ;
- la présence d'Amazon ;
- le classement des ventes.

**Capacité par nuit de 6 h**, calculée à partir des débits par défaut documentés par Amazon :

| Opération | Débit documenté | Capacité sur 6 h |
|---|---|---|
| `getItemOffers` | 0,5 requête/s | environ 10 800 produits |
| `getCompetitiveSummary` | 0,033 requête/s, 20 produits par requête | environ 14 000 produits |

**Point faible** : l'historique commence le jour du premier relevé. Il faut environ 30 jours pour une tendance utile.

**Règle** : l'historique de chaque compte sert à ce compte seul (articles 4.4 et 4.6).

### 4.5 Ce qu'on ne fait pas

- **Aucune aspiration de pages**, ni chez Amazon (contraire à ses conditions d'utilisation et risque pour le compte
  vendeur et l'accès à l'API), ni chez les fournisseurs (Ankorstore, Made-in-China et Global Sources l'interdisent).
- **Aucune revente de données** obtenues par l'API d'Amazon.
- Pas de fournisseurs qui interdisent la revente sur Amazon : Faire, Ankorstore, Creoate.

## 5. Les fournisseurs

**Ordre de branchement :**

1. **Fichier fournisseur** (CSV ou Excel) : le cœur, valable pour tout grossiste. Déjà en place, à améliorer :
   port fournisseur et mémorisation des colonnes par fournisseur.
2. **Qogita**, par API : hygiène et beauté, en Europe ; revente sur Amazon prévue par leurs règles (facture,
   preuve d'origine). Leur API est encore en développement.
3. **BigBuy**, par API ou fichier de prix : généraliste, mais il faut un abonnement payant et ce n'est pas
   un distributeur officiel des marques.
4. **Plus tard** : vidaXL, Brandsdistribution (mode de marque, risque de plainte sur l'authenticité).

**Aide à la recherche de fournisseurs :**

- à partir des marques que le vendeur peut vendre (sondage), l'outil liste les marques à contacter ;
- l'IA rédige les courriels de demande de tarif.

**Factures acceptées par Amazon pour l'approbation dans les catégories restreintes : à vérifier.** Les pages
officielles demandent d'être connecté à Seller Central.

## 6. Où l'IA aide (avec minimisation, D-AMZ-008)

| Usage | Rôle | Garde-fou |
|---|---|---|
| Rapprocher la désignation du fournisseur et la fiche Amazon (même produit ? même lot ?) | Proposer, avec un niveau de confiance | Jamais de verdict « Acheter » sur la seule IA |
| Lire un fichier fournisseur mal formé (colonnes, unités) | Proposer la correspondance des colonnes | Le vendeur valide |
| Rédiger les courriels aux marques et aux grossistes | Brouillon | Envoyé par le vendeur |
| Expliquer un verdict en une phrase | Résumé | Sur des chiffres déjà calculés |
| Plus tard : interroger l'outil en langage courant | Questions sur les données du compte | Données du compte seulement |

**Les chiffres (frais, profit, TVA) ne viennent jamais de l'IA** : ils sont toujours calculés à partir de sources.

## 7. Les lots, dans l'ordre

| # | Lot | Pourquoi maintenant |
|---|---|---|
| 1 | **Nouveau design** (maquette validée) sur tout le site | Vitrine de l'outil, base de tous les écrans |
| 2 | **Coût complet** (§ 4.1) et prix de vente prudent | Sans lui, la marge est fausse |
| 3 | **Historique maison** chaque nuit (§ 4.4) | Il doit démarrer tôt : 30 jours avant d'être utile |
| 4 | **Liste d'opportunités** : filtres et classement (§ 4.2, 4.3), recherche par famille officielle | Le cœur de l'outil |
| 5 | **Fournisseurs** : mémorisation des colonnes, port, puis branchement Qogita | Alimenter le moteur |
| 6 | **Simulation** « business virtuel » (étape 5) | Décider avec le budget |
| 7 | **Tunnel du débutant** (§ 3) et alertes (perte de la Buy Box, retour d'Amazon) | Accompagner, puis suivre |
| 8 | **Extension de navigateur** : notre analyse affichée sur la page Amazon consultée | Confort de type Keepa ou SellerAmp, sans aspiration |
| 9 | **Serveur en Europe**, avant le premier client | Données des clients européens |
| 10 | Plus tard : BigBuy, multi-clients payants, marque blanche, accès par MCP, branchement Keepa pour les clients | Croissance |

## 8. Décisions demandées à Sam

1. Valider ce plan et l'ordre des lots.
2. Valider la maquette du design (accueil et analyse).
3. Ouvrir un compte acheteur chez Qogita, gratuit (à vérifier), pour tester leur API. Sam crée le compte
   lui-même ; aucun identifiant dans le chat.
4. Choisir les objectifs par défaut : marge minimale, ROI minimal, durée de revente prévue.
