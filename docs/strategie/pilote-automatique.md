# Syllig Pilot — feuille de route « pilote automatique » (proposition du 14/11/2026, à valider par Sam)

Demande de Sam (14/11) : un outil qui pilote toute la vente sur Amazon, de la recherche de produits au suivi des
performances, presque automatique, avec des objectifs donnés par le vendeur et des validations humaines en bout de ligne.
Sources : `docs/recherches/2026-11-14-passerelle-amazon-sp-api.md` (API d'Amazon et ce qu'elles permettent),
`2026-11-14-audit-coherence-concurrence.md`, `2026-11-14-envoi-fba-api-inbound.md`, `2026-11-14-messagerie-microsoft.md`.

## 1. Le cadre

- **Objectifs** donnés par le vendeur : budget d'achat par mois, ROI et marge minimum, rotation maximale (jours de
  stock), rayons et fournisseurs autorisés, plafond par commande.
- **Garde-fous** : prix plancher et plafond, aucune action hors des rayons ou des fournisseurs choisis, plafond de
  dépense, bouton **« Pause du pilote »** qui arrête toute action automatique.
- **Niveaux d'autonomie**, réglables étape par étape : 0 informe · 1 propose, le vendeur valide · 2 agit seul dans
  les limites et prévient · 3 agit seul, bilan quotidien.
- **Toute action automatique est tracée** (quoi, quand, pourquoi, résultat) et résumée dans un **bilan quotidien**.
- **Ce qui engage de l'argent reste au niveau 1** : commande fournisseur, paiement, frais de placement et de transport
  d'un envoi FBA. L'AUP d'Amazon (2.10) exige des contrôles avant une décision automatique qui engage le compte.

## 2. La chaîne et son niveau cible

| Étape | Aujourd'hui | API d'Amazon | Cible |
|---|---|---|---|
| Trouver des produits | Relevés de nuit, sondage des rayons, correspondance fournisseurs, produits rentables | Catalog Items, Pricing, Fees, Restrictions | 3 |
| Choisir quoi acheter | Plan d'achat validé par le vendeur | — (calcul maison) | 1, proposé chaque matin selon les objectifs |
| Commander au fournisseur | Bon PDF/Excel, envoi par la messagerie | — (courriel ; API fournisseurs plus tard) | 1 |
| Payer le fournisseur | Hors outil | — | 1, après étude réglementaire |
| Réceptionner | Réception du bon → lots | — | 1 |
| Envoyer chez Amazon (FBA) | Absent | Fulfillment Inbound 2024-03-20, FBA Inbound Eligibility | 3 pour préparer, 1 pour les deux confirmations payantes |
| Fixer et ajuster les prix | Prix plancher, repricer gratuit d'Amazon | Listings Items (Automate Pricing), Pricing | 2 |
| Suivre stock, Buy Box, concurrence | Relevés de nuit, alerte sous plancher | Notifications (ANY_OFFER_CHANGED, FBA_INVENTORY_AVAILABILITY_CHANGES…), FBA Inventory | 3 (temps réel) |
| Réapprovisionner | Calcul de réassort, bon depuis le stock | FBA Inventory, Sales | 1, proposé |
| Après-vente | Remboursements détectés, conformité, profit réel | Reports, Finances, Solicitations, Messaging | 2 à 3 (demande d'avis automatique, réponses types) |
| Performance | Tableau de bord, prévu / réel | Sales, Data Kiosk, Finances | 3 (bilan quotidien et hebdomadaire) |
| S'étendre en Europe | Comparaison entre pays | Listings Items, Action Plans (EXPAND_CROSS_STORE) | 1 |

**Sans API chez Amazon** (l'outil prépare et ouvre la bonne page de Seller Central en un clic) : demande d'approbation
de catégorie ou de marque, ouverture d'un cas au support, réclamation FBA, création de promotion ou de coupon, ordre de
retrait FBA, Brand Registry. **Publicité** : API Amazon Ads séparée (demande d'accès à part), à décider plus tard.
**Réservé aux marques** : Brand Analytics et Search Query Performance (inaccessibles à un revendeur sans marque).

## 3. Ordre proposé (ordinateur d'abord ; téléphone ensuite, D-AMZ-033)

1. **Fiabilité du socle** : la mise à jour du site attend la fin d'un travail en cours ; avancement des remboursements
   rapport par rapport ; contrôle de la première nuit complète.
2. **Boucle d'achat complète** : envoi FBA par l'API (préparé automatiquement, deux validations payantes), lien
   bon reçu → envoi FBA.
3. **Objectifs et pilote** : rubrique « Objectifs » dans les Paramètres, journal des actions automatiques,
   « Pause du pilote », plan d'achat proposé chaque matin, bilan quotidien.
4. **Temps réel** : notifications d'Amazon (changement d'offre, stock, commande, rapport prêt) au lieu d'attendre la
   nuit. Demande une file de messages chez Amazon Web Services (SQS) : petit coût, décision de Sam.
5. **Après-vente automatique** : demande d'avis automatique après livraison, réponses types, rapprochement des
   versements.
6. **Europe** : mise en vente dans d'autres pays depuis la comparaison existante.
7. **Mode téléphone nomade** (D-AMZ-033) : suivi, actions urgentes, scan de code-barres. Le scan est faisable dans le
   navigateur (BarcodeDetector sur Chrome Android ; sur iPhone il faudra une solution de secours ou la saisie du code).

## 4. Ce que Sam décide

- Valider le cadre (objectifs, garde-fous, niveaux, validation de l'argent au niveau 1).
- Valider l'ordre des étapes.
- Plus tard : file SQS chez Amazon Web Services (étape 4), accès à l'API Amazon Ads (publicité).
