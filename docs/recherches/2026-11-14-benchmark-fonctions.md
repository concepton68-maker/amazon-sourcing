# Benchmark des fonctions concurrentes — Syllig Vente

*Recherche documentaire, 14/11/2026. Sources : pages officielles des éditeurs (tarifs, fonctions, aide), documentation API officielle (Keepa, schémas SP-API sur `github.com/amzn/selling-partner-api-models`), pages publiques Amazon (sell.amazon.*, annonces « News_Amazon » des Seller Forums). Toutes consultées le 14/11/2026.*

**Règle de lecture.**
- **VÉRIFIÉ** : lu sur la page citée, avec un court extrait.
- **NON VÉRIFIÉ** : vu seulement dans un résumé de recherche, une source non officielle, ou absent de la page lue. Jamais utilisé pour une conclusion ferme.
- **Analyse** : raisonnement de l'auteur, pas un fait.
- Montants dans la devise de l'éditeur, sans conversion.
- Complète `2026-11-11-donnees-et-outils-verifies.md` (SP-API, Keepa, AUP) sans le répéter.

---

## 1. Tableau des fonctions concurrentes

### 1.1 Prix par mois

| Outil | Prix / mois | Statut |
|---|---|---|
| Helium 10 | Platinum 129 $ (99 $ en annuel) ; Diamond 359 $ (279 $) ; Enterprise dès 1 499 $ | VÉRIFIÉ — [helium10.com/pricing](https://www.helium10.com/pricing/) : « Platinum… $129/month billed monthly » |
| Jungle Scout (Catalyst) | Starter 49 $ ; Growth Accelerator 79 $ ; Brand Owner + CI 149 $ (annuel : 29 / 49 / 129 $) | VÉRIFIÉ — [junglescout.com/pricing/catalyst-plans](https://www.junglescout.com/pricing/catalyst-plans/) : « Starter: $49/mo » |
| SellerAmp SAS | 19,95 $ ; 29,95 $ ; 49,95 $ | VÉRIFIÉ — [selleramp.com/pricing](https://selleramp.com/pricing/) : « Every plan includes the profit calculator with fees, ROI and profit, eligibility and IP alerts » |
| Keepa | Pro 29 €/mois ; API selon tokens/minute | NON VÉRIFIÉ (site en JavaScript, page prix illisible ; la doc API renvoie à keepa.com/api/pricing) |
| SmartScout | Basic 49 $, Essentials 119 $, Business 299 $ (autre jeu de prix affiché : 29 / 99 / 239 $, sans libellé mensuel/annuel) | VÉRIFIÉ (prix), libellé ambigu — [smartscout.com/pricing](https://www.smartscout.com/pricing) |
| Tactical Arbitrage (dans Threecolts Seller 365 Reseller) | Standard 69 $ ; Teams 129 $ ; Pro 199 $ | VÉRIFIÉ — [threecolts.com/seller-365](https://www.threecolts.com/seller-365) (tacticalarbitrage.com/pricing y redirige) : « Includes Reverse Search, Wholesale Search, and Product Finder across 1,400+ retailers » |
| sellerboard | Standard 19 $ (15 $ en annuel) ; Professional 29 $ ; Business 39 $ | Standard VÉRIFIÉ — [sellerboard.com](https://sellerboard.com/) ; Professional/Business NON VÉRIFIÉ (résumé de recherche) |
| ZonGuru | Helix 149 / 299 / 699 $ ; anciens plans recherche 39–79 $ | NON VÉRIFIÉ (pages non lues directement, chiffres contradictoires) |
| Amazon Product Opportunity Explorer / Revenue Calculator | Gratuits avec le compte vendeur (Professional) | VÉRIFIÉ — [sell.amazon.com/tools/product-opportunity-explorer](https://sell.amazon.com/tools/product-opportunity-explorer) (accès via Seller Central > Growth) ; [sell.amazon.com/pricing](https://sell.amazon.com/pricing) : « use our Revenue Calculator to compare estimates for FBA and your own fulfillment method » |

### 1.2 Fonctions par domaine

| Domaine | Helium 10 | Jungle Scout | SellerAmp SAS | Keepa | SmartScout | Tactical Arbitrage | sellerboard | Amazon (POE / Revenue Calc.) |
|---|---|---|---|---|---|---|---|---|
| **Découverte produits** | Black Box : « Filter millions of e-commerce product listings » ; « See entire seller or brand catalogs, ranked by performance » — VÉRIFIÉ ([page](https://www.helium10.com/tools/black-box/)) | Product Database, Opportunity Finder (quotas Starter : « 100 searches/month ») — VÉRIFIÉ ([tarifs](https://www.junglescout.com/pricing/catalyst-plans/)) | Storefront Search : « see SAS analysis for the products in any seller's storefront » — VÉRIFIÉ ([features](https://selleramp.com/features/)). Import d'un fichier fournisseur : **non trouvé** (seul via l'intégration tierce ArbiSource) — NON VÉRIFIÉ | Product Finder : « Search for products in the Keepa database that match your specified criteria » ; filtres `buyBoxSellerId`, `sellerIds`, `outOfStockPercentage90`, `monthlySold`, `brand` ; jusqu'à 10 000 ASIN — VÉRIFIÉ ([doc](https://keepa.com/api-docs/product-finder.html)) | Base marques : « Filter 500K+ brands by criteria » ; « Find brands with few or zero FBA sellers » ; Out-of-Stock Finder — VÉRIFIÉ ([wholesale](https://www.smartscout.com/amazon-wholesale-brands-suppliers-fba), [arbitrage](https://www.smartscout.com/retail-and-online-arbitrage)) | Product Search (1 400+ sites marchands), Reverse Search, Wholesale Search (limite 50k–100k lignes) — VÉRIFIÉ ([Threecolts](https://www.threecolts.com/seller-365)) | — | POE : niches = groupes de termes de recherche, « search terms and volume », « return activity » — VÉRIFIÉ ([page](https://sell.amazon.com/tools/product-opportunity-explorer)) |
| **Estimation de la demande** | Chrome extension : « See estimated sales, revenue, review depth, and seller count » — VÉRIFIÉ ([page](https://www.helium10.com/tools/free/chrome-extension/)). Méthode non publiée | AccuSales : modèle BSR par catégorie et pays, cumul 30 jours — NON VÉRIFIÉ (résumé de recherche sur pages JS) | « Estimated Sales per month » — VÉRIFIÉ ([features](https://selleramp.com/features/)). Méthode NON VÉRIFIÉE | `monthlySold` = badge Amazon « bought past month », « not an estimate » ; `salesRankDrops30/90/180` — VÉRIFIÉ ([product](https://keepa.com/api-docs/product-object.html), [statistics](https://keepa.com/api-docs/statistics-object.html)) | « Monthly sales from any rank » — VÉRIFIÉ | NON VÉRIFIÉ | — | POE : « purchasing behavior » (unités vendues non nommées sur la page) — VÉRIFIÉ |
| **Prix / Buy Box** | Alerts : « you have the Buy Box and that you are the only seller » — VÉRIFIÉ ([alerts](https://www.helium10.com/tools/alerts/)) | NON VÉRIFIÉ | Buy Box analysis (tous plans) ; « Net Buy Box price changes and drops » ; graphiques historiques prix/BSR — VÉRIFIÉ | Historique Buy Box (`BUY_BOX_SHIPPING`), vendeurs ayant tenu la Buy Box (`buyBoxSellerIdHistory`), part Buy Box par vendeur (`buyBoxStats.percentageWon`, « for non-Prime shoppers »), moyennes 30/90/180 — VÉRIFIÉ | Buy Box Map : « Track Buy Box ownership » — VÉRIFIÉ | NON VÉRIFIÉ | Alertes « loss of Buy Box » — VÉRIFIÉ | — |
| **Concurrence** | Nombre de vendeurs (extension) — VÉRIFIÉ | NON VÉRIFIÉ | Offers : « Current stock levels with min/max order indicators » ; alerte « Amazon historically shares the Buy Box » — VÉRIFIÉ | `COUNT_NEW` historisé, `buyBoxEligibleOfferCounts`, `availabilityAmazon`, `buyBoxIsAmazon` — VÉRIFIÉ | Taux de présence Amazon par marque ; « Filter out brands where Amazon is a first-party seller » — VÉRIFIÉ | NON VÉRIFIÉ | Alerte « new sellers » — VÉRIFIÉ | POE : « competition and saturation » — VÉRIFIÉ |
| **Calcul de profit** | « Add your costs and fees to estimate margins at the SKU level » — VÉRIFIÉ ; détail stockage/placement NON VÉRIFIÉ | NON VÉRIFIÉ | Frais, ROI, « Maximum Cost (Max Cost) », « SAS uses your selected VAT Scheme in all calculations », panneau « European Marketplaces » — VÉRIFIÉ ([features](https://selleramp.com/features/)). Placement, stockage, faible stock : NON VÉRIFIÉ | `fbaFees` (pick & pack seul), `referralFeePercentage`, `variableClosingFee` — VÉRIFIÉ | NON VÉRIFIÉ | NON VÉRIFIÉ | Après coup : COGS « constant, batch, period-based, and marketplace-specific », FIFO, remboursements — VÉRIFIÉ ([sellerboard](https://sellerboard.com/)) | Revenue Calculator : comparaison FBA / expédition propre — VÉRIFIÉ |
| **Alertes / suivi** | Hijackers, titre, prix, avis — VÉRIFIÉ | Product Tracker 50 / 150 / 2 000 produits — VÉRIFIÉ | « Eligibility to sell », « Private Label or IP warnings », « Hazmat » — VÉRIFIÉ | Suivi de listes (List Tracking, Pro) — NON VÉRIFIÉ | NON VÉRIFIÉ | Recherches planifiées 30–40 — VÉRIFIÉ | Changements de fiche, nouveaux vendeurs, perte Buy Box, ruptures prévues, remboursements FBA — VÉRIFIÉ | — |
| **Mots-clés / PPC (liste)** | Cerebro, Magnet, Adtomic/Ads (Diamond) | Keyword Scout | — | — | Recherche mots-clés (5 000 ASIN/mois en Basic), Ad Spy (Enterprise) | — | PPC « based on target profitability or ACOS » | POE (volumes de recherche) |

---

## 2. Pertinence pour un revendeur FBA grossiste / arbitrage en Europe

**Analyse.** Le revendeur ne crée pas de fiche : il cherche des ASIN existants où il peut gagner la Buy Box avec marge. Les outils « private label » (niches, mots-clés, avis, fournisseurs d'usine) lui servent peu.

| Fonction | Pertinence revendeur UE | Source de données possible | Statut |
|---|---|---|---|
| Analyse d'un fichier fournisseur (EAN → ASIN → verdict) | **Très forte** | SP-API seule : Catalog `searchCatalogItems` (20 identifiants par appel, `maxItems: 20`), Pricing, Fees, Restrictions | VÉRIFIÉ (schéma `catalogItems_2022-04-01.json`) |
| Prix de Buy Box courant, offres, nombre de vendeurs, Amazon présent | Très forte | SP-API seule : `getCompetitiveSummary` (lots de 20, `lowestPricedOffers` jusqu'à 20 offres, `featuredBuyingOptions` par segment PRIME / NON_PRIME) | VÉRIFIÉ (schéma `productPricing_2022-05-01.json`) |
| Prix de référence « Competitive Price Threshold », « WasPrice » | Forte (risque de perdre l'éligibilité Buy Box si on est au-dessus) | SP-API seule : `referencePrices` | VÉRIFIÉ (même schéma : « `CompetitivePriceThreshold`, `WasPrice`, `CompetitivePrice` ») |
| Prix attendu pour gagner la Buy Box (FOEP) | Forte, **mais seulement sur un SKU déjà listé** | SP-API : `getFeaturedOfferExpectedPriceBatch`, `required: ["marketplaceId","sku"]`, 40 requêtes/lot, 0,033 req/s | VÉRIFIÉ (schéma) |
| Historique prix / BSR / nombre d'offres ; stabilité du prix | Très forte (éviter un prix gonflé momentanément) | **Keepa** obligatoire (rétroactif). SP-API : seulement un historique construit par nos propres relevés à partir d'aujourd'hui | VÉRIFIÉ (Keepa `csv` ; SP-API sans historique : voir étude 11/11) |
| Part de Buy Box par vendeur, rotation | Forte | **Keepa** (`buyBoxStats.percentageWon`, `buyBoxSellerIdHistory`) | VÉRIFIÉ |
| Ventes/mois | Très forte | Keepa `monthlySold` (tranches, badge Amazon) + `salesRankDrops30/90` ; SP-API : BSR courant seulement (`salesRanks`) | VÉRIFIÉ |
| Taux de rupture d'Amazon | Forte (opportunités d'arbitrage) | Keepa `outOfStockPercentage30/90` | VÉRIFIÉ |
| Restriction / éligibilité / hazmat | Très forte | SP-API seule (Listings Restrictions, FBA eligibility) | VÉRIFIÉ (étude 11/11) |
| Recherche par vitrine d'un vendeur (« storefront stalking ») | Moyenne à forte | Keepa (`sellerIds` dans Product Finder, requête seller) ; **SP-API : pas d'opération listant le catalogue d'un autre vendeur** (déduit de la lecture des schémas, NON VÉRIFIÉ par une phrase d'Amazon). Lecture de la page vitrine = **scraping, contraire aux conditions d'Amazon : NON AUTORISÉ** | Keepa VÉRIFIÉ |
| Base de marques « grossiste » (marques peu vendues par Amazon, peu de vendeurs FBA) | Forte | Keepa Product Finder (`brand`, `availabilityAmazon`, `buyBoxIsAmazon`) ; SmartScout (payant, données propres) | VÉRIFIÉ |
| Recherche inverse / sites marchands (Tactical Arbitrage) | Forte pour l'arbitrage en ligne | Lecture des sites de détaillants = scraping de sites tiers ; hors Amazon, conditions propres à chaque site — **non retenu** (Analyse) | — |
| Mots-clés, PPC, avis, fournisseurs d'usine | **Faible** (private label) | — | — |
| Profit après coup (P&L, remboursements) | Forte | SP-API Finances / rapports (déjà fait) | VÉRIFIÉ (étude 11/11) |

---

## 3. Écarts classés et pistes pour faire mieux

**Critère** : « trouver quoi vendre + à quel prix + marge exacte, vite et simplement ». Classement = **Analyse**.

| # | Écart / amélioration | Pourquoi | Source de données | Statut de la base factuelle |
|---|---|---|---|---|
| 1 | **Coût complet par unité** : ajouter au calcul les frais hors `getMyFeesEstimate` — stockage mensuel (par m³, saisonnier), supplément carburant/logistique (2 % UE/UK au 02/11/2026), frais de placement à l'envoi, frais de faible stock, frais de retour | Les concurrents grand public n'affichent pas ces lignes sur leurs pages ; c'est là que la marge « exacte » se perd | SP-API (placement via Inbound v2024-03-20 `fees` ; stockage et frais réels via rapports/Finances) + barèmes Amazon | Surcharge 2 % et stockage par m³ VÉRIFIÉS ; barèmes chiffrés NON VÉRIFIÉS (pages d'aide derrière connexion) |
| 2 | **Prix d'achat maximum avec garde-fou de prix** : max cost calculé sur le plus bas entre Buy Box courante, Competitive Price Threshold et moyenne 90 j (si Keepa) | SellerAmp affiche un « Max Cost » ; on peut le rendre plus prudent avec le seuil Amazon officiel | SP-API (`referencePrices`) + Keepa optionnel (`avg90`) | VÉRIFIÉ |
| 3 | **Ventes/mois honnêtes** : afficher le badge Amazon (`monthlySold`) et les baisses de BSR 30/90 j au lieu d'une estimation « magique », avec part probable = ventes ÷ (vendeurs éligibles Buy Box + 1) | Les concurrents vendent des estimations à méthode opaque ; nous pouvons montrer la donnée observée | **Keepa requis** ; sans Keepa : BSR courant seul → mention « estimation impossible » | VÉRIFIÉ (Keepa) ; formule = Analyse |
| 4 | **Rotation Buy Box et présence Amazon dans le temps** (part de Buy Box par vendeur, % de temps Amazon en Buy Box, taux de rupture Amazon) | Critère n° 1 du revendeur pour ne pas acheter un produit où Amazon garde la Buy Box | **Keepa requis** (`buyBoxStats`, `outOfStockPercentage90`) ; SP-API = instantané seulement | VÉRIFIÉ |
| 5 | **Comparaison multi-marketplaces UE + US en une ligne** (même EAN : meilleur pays de vente, frais et TVA du pays, Pan-EU ou EFN) | SellerAmp a un panneau « European Marketplaces » ; nous pouvons couvrir aussi NL, BE, PL, SE (absents de Keepa) via SP-API | SP-API seule (identifiants de marketplace) | VÉRIFIÉ (SellerAmp, Keepa domaines : étude 11/11) |
| 6 | **TVA exacte par régime** (achat HT récupérable ou non, TVA du pays de vente, TVA sur les frais Amazon) | SellerAmp laisse choisir un « VAT Scheme » ; nous pouvons appliquer le régime réel du vendeur et le pays de destination | Paramètres vendeur + barèmes officiels (règle à sourcer dans `docs/regles/registre.md`) | SellerAmp VÉRIFIÉ ; taux TVA à sourcer |
| 7 | **Vitesse du fichier fournisseur** : lots de 20 en Catalog et Pricing, 40 en FOEP, file d'attente respectant les quotas, reprise | Aucun outil vérifié n'importe un fichier fournisseur en natif sauf Tactical Arbitrage (Wholesale Search) ; SellerAmp passe par un tiers | SP-API seule | Lots VÉRIFIÉS (schémas) ; SellerAmp NON VÉRIFIÉ (absence) |
| 8 | **Recherche par marque / vitrine** pour générer des listes de pistes grossiste | SmartScout et Keepa le font ; c'est la principale « découverte » utile au grossiste | **Keepa requis** (Product Finder, `brand`, `sellerIds`). Sans Keepa : impossible légalement (pas de scraping) | VÉRIFIÉ |
| 9 | **Alertes sur produits achetés / suivis** : perte de Buy Box, Amazon revient, nouveau vendeur, passage sous le prix de seuil | sellerboard et Helium 10 le proposent ; s'appuie sur la synchro nocturne existante | SP-API (notifications `ANY_OFFER_CHANGED` — NON VÉRIFIÉ ici) + relevés propres | Concurrents VÉRIFIÉS ; notification SP-API NON VÉRIFIÉE dans cette étude |
| 10 | **Boucle prévu / réel par lot** (déjà en place) : l'étendre aux frais 2026 réels (placement, faible stock, stockage) prélevés par Amazon | Aucun concurrent vérifié ne compare prévu et réel par lot d'achat (étude 11/11) ; c'est notre avantage principal | SP-API Finances / rapports | VÉRIFIÉ (étude 11/11) |

**Où nous ne pouvons pas égaler (honnêtement)**
- Sans Keepa : **aucun historique** prix/BSR/Buy Box avant notre premier relevé, pas de ventes/mois, pas de part de Buy Box. Les relevés propres ne bâtissent l'historique qu'à partir d'aujourd'hui, et seulement sur les ASIN déjà vus.
- **Pas de base produits globale** (Black Box, Product Database, SmartScout 500K+ marques) : impossible via SP-API seule ; le scraping est contraire aux conditions d'Amazon — non autorisé.
- **Pas de recherche inverse sur sites de détaillants** (Tactical Arbitrage) sans scraper des sites tiers.
- **FOEP** inutilisable pour décider d'un achat : il exige un SKU déjà listé chez le vendeur.

---

## 4. Frais Amazon 2025-2026 à intégrer au calcul de profit

| Frais | Ce qui est établi | Statut |
|---|---|---|
| **Supplément carburant et logistique (UE/UK)** | « the fuel and logistics-related surcharge will increase from 1.5% to 2% » à partir du 2 novembre 2026, sur les frais d'expédition FBA (10 pays européens, dont la France) | VÉRIFIÉ — [sell.amazon.fr/en/tarifs](https://sell.amazon.fr/en/tarifs) ; [sell.amazon.co.uk/pricing](https://sell.amazon.co.uk/pricing) |
| Supplément 1,5 % depuis le 17/04/2026 (UE) ; 3,5 % US/CA depuis le 17/04/2026 | Vu uniquement dans des résumés de recherche | NON VÉRIFIÉ |
| **Stockage mensuel (UE)** | « Charged per cubic metre per month », hausse saisonnière d'octobre à décembre | VÉRIFIÉ — [sell.amazon.fr/en/tarifs](https://sell.amazon.fr/en/tarifs). Montants : NON VÉRIFIÉS |
| **Frais de faible niveau de stock (low-inventory-level fee, US)** | « Amazon will only charge the low-inventory-level fee when the historical days of supply metric are below 28 days » ; calcul sur 30 et 90 jours, facturé seulement si les deux sont sous 28 jours ; produits de taille standard seulement ; exemptions : nouveaux vendeurs Professional (365 j), nouveaux ASIN parents FBA New Selection (180 j), réassort automatique AWD | VÉRIFIÉ — [forum officiel, Bryce_Amazon](https://sellercentral.amazon.com/seller-forums/discussions/t/aa9f98e5-fa91-4949-af8f-6cf918c86a77) (compte Amazon, date exacte non affichée). Barème : NON VÉRIFIÉ |
| Changement au 1er février 2027 (US) | « the fee will apply only when your inventory falls below 28 days of supply » | VÉRIFIÉ — [News_Amazon, « 2027 Updates »](https://sellercentral.amazon.com/seller-forums/discussions/t/bc3deccc-28c6-47c1-ade3-9fbed1f29316) |
| **Équivalent Pan-UE (low-inventory cost coverage fee)** | En vigueur depuis le 01/04/2024 ; exemption des FNSKU Pan-EU « with less than 20 weekly units sold in the last 7 days » (DE, FR, IT, ES) | VÉRIFIÉ pour 2024 — [News_Amazon](https://sellercentral.amazon.com/seller-forums/discussions/t/b48c3178-dc79-48c7-8bc5-231825e75dd5). Règle et montants 2026 : NON VÉRIFIÉS |
| **Frais de placement à l'envoi (inbound placement service fee)** | L'API Inbound v2024-03-20 renvoie pour chaque option de placement `fees` (« The fee for the offered option ») et `discounts`, cible « Placement Services » | VÉRIFIÉ — schéma [`fulfillmentInbound_2024-03-20.json`](https://github.com/amzn/selling-partner-api-models/blob/main/models/fulfillment-inbound-api-model/fulfillmentInbound_2024-03-20.json). Barème (moyennes 2024 0,27 $ / 1,58 $), prélèvement 45 j après réception, application en UE : NON VÉRIFIÉS |
| **Surcharge d'utilisation du stockage (storage utilization surcharge, US)** | Supprimée au 1er février 2027 : « we'll eliminate the storage utilization surcharge » | VÉRIFIÉ — [News_Amazon 2027](https://sellercentral.amazon.com/seller-forums/discussions/t/bc3deccc-28c6-47c1-ade3-9fbed1f29316). Donc encore due jusqu'au 31/01/2027 ; barème NON VÉRIFIÉ |
| **Surcharge stock âgé (US)** | Au 1er février 2027 : « remove the aged inventory surcharge and combine it with monthly storage fees into a single, age-based rate » | VÉRIFIÉ — même source |
| **Frais de traitement des retours** | Le Royaume-Uni mentionne « Additional charges for services such as removals, returns processing, or long-term storage » ; extension US aux produits à fort taux de retour (01/06/2024) | Mention générique VÉRIFIÉE — [sell.amazon.co.uk/pricing](https://sell.amazon.co.uk/pricing) ; règle US 2024 et montants NON VÉRIFIÉS |
| **Frais US 2026** | « FBA fees will increase by an average of $0.08 per unit sold » ; « There will be no new FBA fee types in 2026 » ; effet au 15/01/2026 | VÉRIFIÉ — [News_Amazon, « 2026 Updates »](https://sellercentral.amazon.com/seller-forums/discussions/t/f3fa3211-820b-4e2e-a023-158a9cf55f99) |
| **Frais UE au 5 janvier 2026** | Commission Home Products de 15 % à 8 % jusqu'à 20 €/£ ; tarifs FBA « Low-price » étendus « to products priced at or below £20/€20 » ; autres changements au 01/02/2026 | VÉRIFIÉ — [News_Amazon, EU fee reductions](https://sellercentral.amazon.com/seller-forums/discussions/t/a3b6d192-d78f-4b16-add1-e251e8959783) |
| Commission de vente (UE) | « Amazon charges a referral fee for each item sold », la plupart entre 8 % et 15 % | VÉRIFIÉ — [sell.amazon.fr/en/tarifs](https://sell.amazon.fr/en/tarifs) |
| Ce que couvre `getMyFeesEstimate` | Commission, frais FBA d'expédition, frais de clôture variables ; **pas** le placement, le stockage, le faible stock ni le supplément carburant — à confirmer | NON VÉRIFIÉ (déduit ; l'énumération des types de frais n'a pas été lue) |

**Analyse — conséquences pour le calcul.**
1. Ajouter au coût unitaire prévu : stockage estimé (volume × durée prévue de vente × tarif du mois), placement à l'envoi (repris de l'option choisie dans l'API Inbound, ou une valeur saisie), et une provision faible stock / retours, chaque ligne marquée « estimée » tant que le barème n'est pas sourcé.
2. Vérifier si le supplément carburant est déjà inclus dans la réponse de `getMyFeesEstimate` avant de l'ajouter, pour ne pas le compter deux fois.
3. Toute valeur chiffrée non sourcée va dans `docs/regles/registre.md` avec la mention « non sourcé », sans blocage.

---

## Annexe — Points non vérifiés

- Prix Keepa (Pro 29 €/mois, plans API) : page tarifs en JavaScript, non lisible.
- ZonGuru : prix Helix et anciens plans de recherche contradictoires, pages non lues directement.
- sellerboard Professional / Business : résumé de recherche seulement.
- Jungle Scout : méthode AccuSales et précision (± 10 %) : pages non lues directement.
- SellerAmp : absence d'import de fichier fournisseur natif (seule l'intégration ArbiSource a été trouvée).
- Barèmes chiffrés 2026 : placement à l'envoi, faible stock (US et Pan-UE), stockage, retours, surcharge d'utilisation du stockage. Les pages d'aide de Seller Central exigent une connexion.
- Supplément carburant 1,5 % (UE, 17/04/2026) et 3,5 % (US/CA).
- Notification SP-API `ANY_OFFER_CHANGED` pour les alertes Buy Box (non relue dans cette étude).
- Opération SP-API listant le catalogue d'un autre vendeur : aucune trouvée (déduction).
