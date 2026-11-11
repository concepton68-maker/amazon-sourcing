# Viser le lot d'achat, pas la donnée

*Rapport de recherche documentaire. Date de contexte : 11 novembre 2026. Toutes les sources citées ont été consultées le 11/11/2026, sauf mention contraire. Lorsqu'une page affiche sa propre date de publication ou de mise à jour, elle est indiquée.*

**Règle de lecture.** Le corps du rapport ne contient que des faits vérifiés sur source primaire : documentation officielle, page tarifs ou CGU de l'éditeur, décision de justice, ou page Trustpilot lue directement. Chaque fait porte son URL. Les passages intitulés **« Analyse »** contiennent des raisonnements, des calculs ou des recommandations de l'auteur. Ce ne sont pas des faits. Les calculs ne réutilisent que des chiffres vérifiés. Tout ce qui n'a pu être vu que dans des sources secondaires, ou n'a pas pu être lu, figure uniquement dans l'annexe « Points non vérifiés ». Ces éléments n'ont pas pesé sur les conclusions. Les montants restent dans la devise affichée par l'éditeur : aucun taux de change n'a été appliqué.

---

## 1. Synthèse

**Le marché vend déjà le combiné « sourcing + gestion de compte ».** Quatre offres le réunissent dans un seul abonnement, aux prix vérifiés suivants :

- **Threecolts Seller 365 Reseller Standard** : 69 $/mois, ou 65 $/mois en annuel ([Threecolts](https://www.threecolts.com/seller-365)).
- **Jungle Scout Growth Accelerator** : 79 $/mois, ou 49 $/mois en annuel ([Jungle Scout](https://www.junglescout.com/pricing/catalyst-plans)).
- **Seller Assistant Business** (sellerassistant.app) : 79,99 $/mois, ou 69,99 $/mois en annuel ([Seller Assistant](https://sellerassistant.app/pricing)).
- **Helium 10 Platinum** : 129 $/mois, ou 99 $/mois en annuel ([Helium 10](https://www.helium10.com/pricing/)).

Combiner les deux briques ne suffit donc pas à différencier un nouvel outil. Les trous vérifiés sont plus étroits.

1. **Aucune offre complète sous environ 30 $/mois.** Seller Assistant Pro (24,99 à 29,99 $) ne propose la rentabilité qu'en « Preview » ([Seller Assistant](https://sellerassistant.app/pricing)).
2. **Le pilotage PPC et le sourcing ne sont réunis qu'à partir de 279 à 359 $/mois**, dans Helium 10 Diamond, avec en plus 2 % des dépenses publicitaires ([Helium 10](https://www.helium10.com/pricing/)).
3. **Aucun outil étudié ne documente la comparaison entre le ROI prévu à l'achat et le profit réalisé, lot d'achat par lot d'achat.** Seller Assistant s'en approche le plus : ses données d'analyse passent dans le bon de commande et son P&L est réalisé, mais il est ventilé par produit, marque et fournisseur, pas par bon de commande ([Seller Assistant](https://sellerassistant.app/)).

**Côté données, l'essentiel du sourcing en temps réel est gratuit, à condition de passer par son propre compte.** La SP-API d'Amazon est sans frais : Amazon a annulé les frais annoncés, avec la réserve « at this time » ([Amazon, publié le 11/06/2026, modifié le 01/07/2026](https://developer.amazonservices.com/cancellation-of-sp-api-fees)). Elle fournit au vendeur qui l'autorise les éléments suivants ([Amazon SP-API](https://developer-docs.amazon/sp-api/reference/getitemoffers.md)) :

- les offres et la Buy Box ;
- les frais estimés ;
- les restrictions de vente ;
- l'éligibilité FBA et le statut hazmat ;
- la conversion EAN → ASIN ;
- le BSR courant.

**Trois choses restent hors de portée de la SP-API.** L'historique des prix et du BSR, l'historique du badge « bought in past month » et les estimations de ventes passent par Keepa, payant ([Keepa](https://keepa.com/api-docs/product-object.html)). Keepa ne couvre ni les Pays-Bas, ni la Belgique, ni la Pologne, ni la Suède ([Keepa](https://keepa.com/api-docs/product.html)). Les tarifs et les conditions de réutilisation de Keepa n'ont pas pu être lus en primaire.

**Les règles d'usage d'Amazon (AUP) encadrent toute l'architecture** ([AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)) :

- l'article 4.4 interdit d'agréger les données de plusieurs vendeurs ;
- l'article 4.6 interdit de divulguer les données d'un utilisateur à un autre ;
- l'article 4.3 interdit d'« use, offer or promote » des services externes qui vendent des données issues des sites Amazon. C'est le point de tension avec Keepa.

**Les plafonds d'autorisation conditionnent le passage à la phase commerciale** ([Amazon, mis à jour le 09/09/2026](https://developer-docs.amazon/sp-api/docs/application-authorization-limits.md)) :

| Type d'application | Plafond d'autorisations |
|---|---|
| Privée | 10 |
| Publique non listée | 25 vendeurs |
| Listée sur l'Appstore | Illimité |

**Côté gestion pure, les prix d'entrée bas cachent des mécanismes contractuels** :

- mise à niveau automatique de palier, chez sellerboard et Shopkeeper ;
- abonnements non remboursables ;
- commissions de 12 à 25 % sur les remboursements récupérés ;
- reconduction annuelle chez AMALYTIX, alors que sa page tarifs annonce l'inverse.

**Recommandation (Analyse).** Construire d'abord l'outil personnel autour d'une **boucle « décision d'achat → lot → profit réalisé, prévu contre réel »**, alimentée uniquement par la SP-API de son propre compte. Garder Keepa comme module optionnel tant que ses conditions écrites et la position d'Amazon sur l'article 4.3 ne sont pas obtenues. En phase commerciale, viser le **revendeur francophone (arbitrage en ligne et grossiste) sur les places de marché UE**, avec une tarification transparente qui se distingue justement des pratiques citées plus haut. Positionner l'offre dans la bande vide sous 30 $ pour l'entrée, et sous les combinés à 65–80 $ pour l'offre complète. Ces prix sont des hypothèses à tester, pas des données.

---

## 2. La SP-API couvre le temps réel, Keepa l'historique, et l'AUP trace la frontière

### Tableau maître des données de sourcing

Débits : valeurs par défaut documentées, en requêtes par seconde, par paire vendeur/application. Amazon précise que certains vendeurs « may see higher rate and burst values » ([getItemOffers](https://developer-docs.amazon/sp-api/reference/getitemoffers.md)).

**Données SP-API (toutes gratuites, 0 $)**

| Donnée | Source / endpoint | Limites documentées | Droits / contraintes | Nature |
|---|---|---|---|---|
| Offres les plus basses, prix Buy Box, nombre d'offres par canal FBA/FBM, `IsBuyBoxWinner`, `IsFulfilledByAmazon`, `SalesRankings` | Product Pricing v0 `getItemOffers` ([doc](https://developer-docs.amazon/sp-api/reference/getitemoffers.md)) | 0,5 req/s, burst 1 | Vendeur ayant autorisé l'app ; AUP 4.4/4.6 | Observé |
| Idem, en lot | `getItemOffersBatch` ([doc](https://developer-docs.amazon/sp-api/reference/getitemoffersbatch.md)) | 0,1 req/s, burst 1 ; 1 à 20 requêtes par lot | Idem | Observé |
| Offres mises en avant, prix de référence, offres les plus basses, articles similaires | Product Pricing 2022-05-01 `getCompetitiveSummary` ([doc](https://developer-docs.amazon/sp-api/reference/getcompetitivesummary.md)) | 0,033 req/s, burst 1 ; 20 ASIN par lot | Idem | Observé |
| Prix attendu pour remporter l'offre mise en avant (FOEP) | `getFeaturedOfferExpectedPriceBatch` ([doc](https://developer-docs.amazon/sp-api/reference/getfeaturedofferexpectedpricebatch.md)) | 0,033 req/s ; jusqu'à 40 requêtes par lot | SKU du vendeur | Calculé par Amazon |
| Frais estimés (commission, FBA…) par ASIN | Product Fees v0 `getMyFeesEstimateForASIN` ([doc](https://developer-docs.amazon/sp-api/reference/getmyfeesestimateforasin.md)) | 1 req/s, burst 2 | Amazon avertit : « Actual costs may vary » | Estimé par Amazon |
| Frais estimés, en lot | `getMyFeesEstimates` ([doc](https://developer-docs.amazon/sp-api/reference/getmyfeesestimates.md)) | 0,5 req/s ; 20 articles par lot | Idem | Estimé par Amazon |
| Restrictions de vente (`APPROVAL_REQUIRED`, `NOT_ELIGIBLE`, `ASIN_NOT_FOUND`) et lien de demande d'approbation | Listings Restrictions `getListingsRestrictions` ([doc](https://developer-docs.amazon/sp-api/reference/getlistingsrestrictions.md)) | 5 req/s, burst 10 ; chaque marketplace compte comme une requête | « Sellers only », rôle Product Listing ; résultat propre au compte | Observé, spécifique au compte |
| Éligibilité FBA, hazmat ou dangerous goods (codes FBA_INB_0014/0015/0016/0097), expiration, restrictions régionales | FBA Inbound Eligibility `getItemEligibilityPreview` ([doc](https://developer-docs.amazon/sp-api/reference/getitemeligibilitypreview.md)) | 1 req/s, burst 1 | Vendeur autorisé | Observé (classement Amazon) |
| Conversion EAN/UPC/GTIN/ISBN/JAN → ASIN, dimensions, images, BSR courant, relations | Catalog Items 2022-04-01 `searchCatalogItems` ([doc](https://developer-docs.amazon/sp-api/reference/searchcatalogitems.md)) | 2 req/s, burst 2 ; 20 identifiants par requête ; identifiants et mots-clés non combinables | Vendeur autorisé | Observé |
| Rang de fréquence des termes de recherche | Rapport `GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT` ([doc](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md)) | Rapport | Brand Registry + rôle Brand Analytics + représentant de marque | Calculé par Amazon (un rang, pas un volume) |
| Search Query Performance | `GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT` ([doc](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md)) | Rapport | Brand Registry + rôle Brand Analytics | Observé |

**Autres sources**

| Donnée | Source | Gratuit / payant | Coût exact | Limites | Droits / contraintes | Nature |
|---|---|---|---|---|---|---|
| Niches, volume de recherche | Product Opportunity Explorer, interface Seller Central ([Amazon](https://sell.amazon.com/tools/product-opportunity-explorer)) | Compte Pro | La page renvoie au plan Pro à 39,99 $/mois (US) | Aucune API officielle trouvée | Compte Professional | Calculé par Amazon |
| Barèmes d'abonnement | Pages publiques US, FR et UK | Gratuit | US : 39,99 $/mois ou 0,99 $/article ([US](https://sell.amazon.com/pricing)) ; FR : 39 € HT/mois ou 0,99 €/unité ([FR](https://sell.amazon.fr/tarifs)) ; UK : 25 £ HT/mois ou 0,75 £/unité ([UK](https://sell.amazon.co.uk/pricing)) | Pas d'API | Public | Barème officiel |
| Historique prix/BSR/offres, stats 30/90/180 jours, Buy Box historique | Keepa API `/product` ([doc](https://keepa.com/api-docs/product.html)) | Payant | Prix des plans **non vérifié** (annexe). Coût en tokens vérifié : 1 token par produit ; `offers` 6 tokens par page de 10 offres ; `buybox` +2 ([Keepa](https://keepa.com/api-docs/plans-tokens.html)) | Réserve plafonnée à rate × 60 tokens ; tokens expirés après 60 min ; facturation mensuelle d'avance ; downgrade une fois tous les 28 jours ; « Keepa does not offer discounts » | CGU de réutilisation **non vérifiées** ; tension avec l'AUP 4.3 | Observé (collecté par Keepa) + stats calculées |
| Badge « bought in past month » historisé | Keepa `monthlySold` / `monthlySoldHistory` ([doc](https://keepa.com/api-docs/product-object.html)) | Payant | Inclus dans la requête produit | Tranches (« 10+ », « 100+ ») ; « Most ASINs do not have this value set » | Abonné Keepa | Observé : « It is not an estimate » |
| Frais FBA et commission recalculés par Keepa | Keepa `fbaFees`, `referralFeePercentage` ([doc](https://keepa.com/api-docs/product-object.html)) | Payant | Inclus | Calculés sur le prix courant, sinon le dernier prix connu, sinon une valeur par défaut de 100,00 | Abonné Keepa | Calculé |
| Marketplaces couvertes par Keepa | Domain IDs ([doc](https://keepa.com/api-docs/product.html)) | — | — | com, co.uk, de, fr, co.jp, ca, it, es, in, com.mx, com.br. **Pas de NL, BE, PL ni SE** | — | — |

**Analyse : débits utiles par vendeur.** Ces chiffres sont calculés à partir des débits par défaut ci-dessus, hors burst.

| Opération | Calcul | Débit |
|---|---|---|
| `searchCatalogItems` | 2 × 20 | 40 EAN convertis par seconde |
| `getItemOffersBatch` | 0,1 × 20 | 2 ASIN/s, soit environ 7 200 ASIN/h |
| `getMyFeesEstimates` | 0,5 × 20 | 10 ASIN/s |
| `getListingsRestrictions` | 5 req/s, une marketplace | 5 ASIN/s |
| `getItemEligibilityPreview` | 1 req/s | 3 600 ASIN/h |

Le goulot est l'éligibilité FBA. Pour un fichier fournisseur de 5 000 lignes sur une seule marketplace, cela donne environ :

- 2 min pour la conversion EAN → ASIN ;
- 42 min pour les offres ;
- 8 min pour les frais ;
- 17 min pour les restrictions ;
- 83 min pour l'éligibilité.

C'est acceptable pour un usage personnel en tâche de fond, pas pour un scan instantané.

### Peut-on faire avec du gratuit ?

**Oui, pour l'analyse d'un deal à l'instant T sur son propre compte. Non, pour l'historique et la demande estimée.**

Avec son compte Professional, que le vendeur paie de toute façon pour vendre ([FR](https://sell.amazon.fr/tarifs)), et une application SP-API privée, sans frais Amazon ([Amazon](https://developer.amazonservices.com/cancellation-of-sp-api-fees)), on obtient :

- l'état courant des offres et de la Buy Box ;
- les frais estimés ;
- les restrictions propres au compte ;
- l'éligibilité FBA et hazmat ;
- le catalogue, avec conversion EAN → ASIN et BSR courant ;
- Brand Analytics, si le vendeur est en Brand Registry.

Ces sources sont détaillées dans le tableau ci-dessus. Le Revenue Calculator d'Amazon redirige vers la connexion Seller Central ([constaté le 11/11/2026](https://sellercentral.amazon.com/revenuecalculator)).

**Ce qu'il faut payer (Keepa)** :

- l'historique des prix, du BSR et des offres ;
- les statistiques sur 30, 90 et 180 jours ;
- l'historique du badge « bought in past month ».

Keepa est le seul fournisseur vérifié dans ce dossier. Aucune opération SP-API exposant le badge n'a été trouvée dans les schémas Catalog et Pricing lus ([Keepa](https://keepa.com/api-docs/product-object.html)). Cette absence est déduite de la lecture des schémas, Amazon ne l'affirme pas.

**Ce qui est impossible, gratuit ou payant, par les voies vérifiées** :

- un volume de recherche absolu par mot-clé : Brand Analytics donne un rang, pas un volume ([Amazon](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md)) ;
- un historique rétroactif pour NL, BE, PL et SE : Keepa ne couvre pas ces domaines ([Keepa](https://keepa.com/api-docs/product.html)) ;
- une liste officielle de marques à risque de plaintes en propriété intellectuelle, ou un indicateur « meltable » par ASIN : aucune API Amazon trouvée ([getItemEligibilityPreview](https://developer-docs.amazon/sp-api/reference/getitemeligibilitypreview.md)).

**Analyse.** Le seul historique gratuit et conforme consiste à enregistrer ses propres relevés SP-API dans le temps. Il ne couvre que les ASIN interrogés, ne remonte pas avant le premier relevé, et reste réservé au vendeur qui l'a généré.

### Contraintes juridiques

**L'AUP, dont la version anglaise fait foi** ([AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)), contient cinq règles décisives.

- **4.3** : « Do not use, offer or promote external (non-Amazon) data services that vend information or data retrieved from Amazon's websites. »
- **4.4** : « Do not aggregate data across Authorized Users' businesses or customers obtained through the Amazon Services API to provide or sell to any parties, including competing Authorized Users. »
- **4.6** : interdiction de divulguer l'« Information » à d'autres utilisateurs de l'application, sauf pour servir le vendeur qui l'a autorisée. La définition de l'« Information » couvre les données « public or non-public » exposées par l'API ou par les sites publics d'Amazon.
- **2.4** : obligation d'être explicite sur les calculs, les modèles d'IA, leur précision et la fraîcheur des données.
- **3.10** : interdiction de contourner les quotas en multipliant comptes ou applications.

**La Data Protection Policy** ([DPP](https://sellercentral.amazon.com/mws/static/policy?documentType=DPP&locale=en_US)) impose :

- une conservation limitée au strict nécessaire ;
- une suppression sous 30 jours après la révocation de l'autorisation ;
- une conservation des données personnelles limitée à 30 jours après la livraison de la commande ;
- des journaux conservés au moins 12 mois.

**Les plafonds d'autorisation** sont les suivants : 10 pour une application privée ; 25 vendeurs pour une application publique non listée ; illimité pour une application listée sur l'Appstore. « Private applications are available only to your organization » ([Amazon, 09/09/2026](https://developer-docs.amazon/sp-api/docs/application-authorization-limits.md)).

**La Creators API (successeur de PA-API) est exclue pour un outil vendeurs.** La licence Associates interdit, sans accord écrit, d'utiliser la Creators API, la PA-API ou les Data Feeds « in connection with any software or other application intended for use by persons or entities that offer products on an Amazon Site ». Elle exclut aussi le suivi et les alertes de prix, et la revente du contenu ([Amazon Associates](https://affiliate-program.amazon.com/help/operating/policies)). L'accès lui-même suppose 10 ventes qualifiées sur 30 jours ([Creators API](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction)).

**Keepa ne couvre pas NL, BE, PL ni SE.** Sa liste de domaines s'arrête à com, co.uk, de, fr, co.jp, ca, it, es, in, com.mx et com.br ([Keepa](https://keepa.com/api-docs/product.html) ; [dépôt officiel](https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/AmazonLocale.java)). La SP-API, elle, dispose d'identifiants pour ces quatre marketplaces ([Amazon](https://developer-docs.amazon/sp-api/docs/store-identifiers.md)).

**Analyse : effets en phase 1 (usage personnel).**

- Une application privée suffit, avec 10 autorisations possibles.
- Les articles 4.4 et 4.6 ne posent pas de problème, puisqu'il n'y a qu'un seul utilisateur.
- L'article 4.3 vise aussi le verbe « use ». Brancher Keepa dans une application SP-API, même personnelle, se heurte donc littéralement à son texte. Le risque est une suspension de l'accès SP-API. La fréquence réelle d'application par Amazon est inconnue.
- Mesure prudente : garder Keepa dans un module séparé et désactivable.

**Analyse : effets en phase 2 (commercial).**

- L'application doit être publique. Au-delà de 25 vendeurs, le listing sur l'Appstore est nécessaire. Les exigences de ce listing n'ont pas été analysées.
- Aucun cache partagé n'est possible : chaque réponse SP-API obtenue avec le jeton d'un vendeur ne sert que ce vendeur. Cela ferme la voie « base Keepa maison alimentée par les clients ».
- Le capital de débit grandit avec le nombre de clients, puisque les quotas s'appliquent par paire vendeur/application ([Amazon](https://developer-docs.amazon/sp-api/docs/usage-plans-and-rate-limits.md)).
- Proposer Keepa à des clients, c'est « offer or promote » au sens de l'article 4.3. Le risque est maximal précisément en phase commerciale.

---

## 3. Les flux d'affiliation offrent une source propre, encore inexploitée par les outils documentés

### Options vérifiées, coûts et limites

| Source | Ce qu'elle fournit | Accès / coût vérifié | Contrainte vérifiée |
|---|---|---|---|
| **Awin** – Product Feed List Download ([Awin](https://help.awin.com/developers/docs/product-feed-list-download)) | Flux produits des annonceurs rejoints, et de ceux qui autorisent la promotion avant adhésion ; colonne « Membership Status » | Publisher ID + « data feed key » propre ; la clé Publisher API ne fonctionne pas pour cet usage | Chaque flux « Includes only the columns the advertiser has filled in » : la présence de l'EAN et du stock dépend de l'annonceur |
| **Rakuten Advertising** ([guide PDF officiel](https://pubhelp.rakutenadvertising.com/hc/en-us/article_attachments/22365119792013)) | Retail Price (requis), Sale Price, Availability, UPC/EAN/JAN (optionnel), Currency ; livraison SFTP en XML ou pipe-delimited, complète ou en delta | Double approbation : technique, puis « by each of your participating advertiser partners » | EAN optionnel |
| **eBay Browse API** ([eBay](https://developer.ebay.com/develop/api/buy/api_call_limits)) | Recherche par mot-clé, catégorie, GTIN, produit ou image | 5 000 appels/jour ; Feed API item_snapshot 75 000/jour ; jeton d'application | Contrat de licence eBay non lu (annexe) |
| **Bol.com Marketing Catalog API** ([bol](https://api.bol.com/marketing/docs/catalog-api/index.html) ; [spec](https://api.bol.com/marketing/docs/api-reference/catalog-api-v1.html)) | Offres, prix, délais de livraison (NL/BE) | Réservée aux affiliés bol inscrits | CGU affiliés non lues |
| **Google Shopping via DataForSEO** ([DataForSEO](https://dataforseo.com/pricing/merchant/google-shopping-api)) | Produits et vendeurs d'une requête Google Shopping | 0,001 $ par page de 40 produits (file standard, jusqu'à 45 min) ; 0,002 $ en priorité ; vendeurs : 0,001 $ par page de 10 | Redistribution non analysée |
| **Google Shopping via SerpApi** ([SerpApi](https://serpapi.com/pricing)) | Résultats de recherche | Gratuit : 250 recherches/mois ; 25 $ : 1 000 ; 75 $ : 5 000 ; 150 $ : 15 000 | Mentionne une « U.S. Legal Shield » |
| **EAN-Search.org** ([EAN-Search](https://www.ean-search.org/ean-database-api.html)) | Base EAN | 19 € : 5 000 requêtes/mois ; 39 € : 50 000 ; 99 € : 150 000 ; 149 € : 300 000 ; TTC ; −10 % en annuel | Redistribution non lue |
| **UPCitemdb** ([UPCitemdb](https://www.upcitemdb.com/wp/docs/main/development/api-rate-limits/)) | Base UPC/EAN | Gratuit : 100 requêtes/jour, dont 40 recherches ; plan DEV : 20 000 lookups + 2 000 recherches/jour (prix non extrait) | — |
| **Barcode Lookup** ([Barcode Lookup](https://www.barcodelookup.com/api)) | Base codes-barres | 99 $ : 5 000 appels ; 249 $ : 25 000 ; 499 $ : 100 000 ; 949 $ : 500 000 ; au mois | — |
| **Open Food Facts** ([CGU](https://world.openfoodfacts.org/terms-of-use) ; [API](https://openfoodfacts.github.io/openfoodfacts-server/api/)) | Produits alimentaires, EAN | Gratuit ; licence ODbL, usage commercial permis | Share-alike sur les dérivés ; 15 req/min en lecture ; le dump est demandé au-delà de quelques centaines de produits |
| **ImportGenius**, douanes US ([ImportGenius](https://www.importgenius.com/pricing)) | Importations US au niveau du connaissement (Bill of Lading) : importateurs d'une marque | 229 $/mois, ou 183 $/mois en annuel (2 198 $/an) ; Pro 449 $ ou 359 $ ; Global Enterprise dès 1 999 $ | US uniquement |
| **Proxies résidentiels** (pour le scraping) | — | Bright Data : 4 $/GB en paiement à l'usage, promo −50 % sur 8 $ ([Bright Data](https://brightdata.com/pricing/proxy-network/residential-proxies)) ; Oxylabs : 6 → 2,50 $/GB ([Oxylabs](https://oxylabs.io/products/residential-proxy-pool)) ; Decodo : 4 → 2 $/GB HT ([Decodo](https://decodo.com/proxies/residential-proxies)) | Voir le risque juridique ci-dessous |

**Sources fermées ou inutilisables, vérifiées** :

- **Best Buy** interdit à des tiers d'utiliser son service « for the purposes of analyzing, receiving or reviewing information regarding Best Buy pricing ». Il limite aussi le cache à 72 h ([Best Buy](https://developer.bestbuy.com/legal)).
- **Allegro** réserve la recherche d'offres aux « verified applications only » ([Allegro](https://developer.allegro.pl/docs/offers-listing)).

**Contradiction interne relevée.** Oxylabs affiche des plans dès 15 $ alors que sa propre FAQ indique « start at $30 per month » ([Oxylabs](https://oxylabs.io/products/residential-proxy-pool)).

### Ce que documentent les concurrents

Tactical Arbitrage annonce « 1,400+ online retail sites ». La même page affiche aussi « 1392 sourcing sites available », un léger écart dans ses propres chiffres. La recherche rapide s'appuie sur des « cached retailer data », exécutées « entirely on our servers ». Le site ne mentionne aucun flux d'affiliation ([Tactical Arbitrage](https://tacticalarbitrage.com/)). Aucun autre outil d'arbitrage n'a été vérifié en primaire sur ce point.

### Risques juridiques du scraping de détaillants

**Droit de l'UE : CJUE, C-762/19 CV-Online Latvia, 3 juin 2021** ([EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62019CJ0762)). La Cour juge qu'un moteur spécialisé qui copie et indexe tout ou partie substantielle d'une base librement accessible, puis la rend interrogeable, réalise une « extraction » et une « réutilisation ». Le producteur peut les interdire lorsqu'elles portent atteinte à son investissement. La Cour reconnaît aussi que les agrégateurs « contribute to the smooth functioning of competition » (points 41-42).

**Droit de l'UE : CJUE, C-30/14 Ryanair, 15 janvier 2015** ([EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62014CJ0030)). Lorsqu'une base n'est protégée ni par le droit d'auteur ni par le droit sui generis, son auteur peut fixer des limitations contractuelles à son usage.

**Droit américain : Meta v. Bright Data, N.D. Cal., 23 janvier 2024** ([ordonnance](https://storage.courtlistener.com/recap/gov.uscourts.cand.406956/gov.uscourts.cand.406956.181.0.pdf)). Le tribunal rejette la demande de Meta et accorde le jugement sommaire à Bright Data. Il relève l'absence de preuve d'un scraping effectué en étant connecté à un compte.

**Analyse.**

1. **Combinaison A (France, la plus propre).** Flux Awin et Rakuten des détaillants français qui acceptent l'éditeur, puis EAN, puis ASIN via la SP-API de l'utilisateur, puis calcul de la marge. Les données sont fournies volontairement par les détaillants, ce qui évite le terrain CV-Online. Rien n'indique publiquement que Tactical Arbitrage procède ainsi. C'est la piste d'innovation la plus nette. Elle reste suspendue aux conditions éditeur des réseaux, non lues, et à l'approbation de chaque annonceur.
2. **Combinaison B (découverte).** DataForSEO par GTIN : 100 000 GTIN par mois sur une page chacun coûtent environ 100 $ (100 000 × 0,001 $). On y ajoute eBay Browse pour les prix de revente, dans la limite de 5 000 appels par jour.
3. **Combinaison C (grossistes US).** ImportGenius, de 183 à 229 $ par mois, pour repérer les importateurs d'une marque. Aucun équivalent européen n'a été vérifié.
4. **Historique propre pour NL, BE, PL et SE.** Relevés SP-API par vendeur, à son seul usage, pour couvrir les marketplaces absentes de Keepa.
5. **À écarter.** La Creators API, le scraping d'Amazon, la Best Buy API pour l'analyse de prix, et le scraping massif de détaillants français. Ce dernier relève du terrain CV-Online : l'atteinte à l'investissement s'apprécie au cas par cas.

---

## 4. Les outils de gestion facturent surtout le dépassement et les remboursements

### Tableau par outil (prix et conditions lus sur les pages officielles)

| Outil | Plans et prix | Limites clés | Inclus | Add-ons / commissions | Pièges contractuels vérifiés |
|---|---|---|---|---|---|
| **sellerboard** ([tarifs](https://sellerboard.com/en/) ; [CGU](https://sellerboard.com/terms)) | Standard 19 $ (15 $ en annuel, 179 $/an) ; Professional 29 $ (23 $, 279 $/an) ; Business 39 $ (31 $, 369 $/an) ; Enterprise 79 $ (63 $, 759 $/an) | 3 000 / 6 000 / 15 000 / 50 000 commandes par mois ; 150 / 6 000 / 15 000 / 30 000 e-mails par mois ; 30 000 produits par compte | Dashboard de profit, alertes, optimisation PPC, repricer, stock, « Refunds for lost inventory », LTV ; droits d'accès fins seulement en Enterprise | Commission éventuelle sur les remboursements non publiée (annexe) | « may be automatically upgraded to a higher plan » ; prix modifiables « without notice » ; reconduction automatique ; « subscription fees are non-refundable » ; prix UE hors TVA ; essai d'un mois sans carte |
| **Shopkeeper** ([tarifs](https://shopkeeper.com/pricing) ; [remboursements](https://shopkeeper.com/pricing/reimbursement) ; [CGU](https://shopkeeper.com/terms)) | Starter 20 $ ; Intermediate 45 $ ; Master 90 $ ; Superseller 250 $ ; Enterprise sur devis | ≤ 250 / 1 000 / 5 000 / 10 000 commandes ; mensuel uniquement | Mêmes fonctions dans tous les plans (dont PPC, TVA, gestion des utilisateurs) | Service de remboursement : 5 $/mois (Starter), 10 $/mois (Intermediate), **15 %** (Master), **12 %** (Super Seller) | Remboursements, PPC, alertes, coaching et support premium « not included in the monthly subscription » ; ajustement au prorata **prélevé automatiquement** et non remboursable en cas de dépassement ; reconduction au « then-current pricing » ; paiements non remboursables. L'éditeur se présente comme britannique, mais l'adresse publiée est en Floride |
| **SELLERLOGIC Business Analytics** ([BA](https://www.sellerlogic.com/en/business-analytics-tool-amazon/)) | Engagement de 3 mois : gratuit jusqu'à 100 commandes ; 10 € (101–500) ; 15 € (501–1 000) ; 25 € (–2 500) ; 50 € (–5 000) ; 75 € (–10 000) ; 129 € (–25 000) ; 149 € (–50 000) ; 199 € ; 249 € | Remise de 5 / 10 / 15 % sur 6 / 12 / 24 mois ; **aucune option mensuelle** | Analyse des profits | — | Engagement minimum de 3 mois ; hors TVA |
| **SELLERLOGIC Repricer** ([Repricer](https://www.sellerlogic.com/en/amazon-dynamic-repricing-tool/)) | Starter : 39 € (100 produits) à 1 359 € (20 000) ; Advanced : 49 € (100) ; 106 € (500) ; 136 € (1 000) ; 499 € (5 000) ; 936 € (10 000) ; 1 699 € (20 000) | Freemium : 20 produits par jour | Toutes les marketplaces | Annuel = 2 mois offerts | Reconduction automatique ; carte bancaire uniquement |
| **SELLERLOGIC Lost & Found** ([L&F](https://www.sellerlogic.com/en/amazon-lost-and-found/)) | Sans fixe | Audit sur 18 mois | — | **25 %** des remboursements reçus | Résiliable chaque jour, sans préavis |
| **AMALYTIX** ([tarifs](https://www.amalytix.com/en/amazon-seller-tool/) ; [CGU](https://www.amalytix.com/en/about-us/terms-of-services/)) | Essential 69 € (690 €/an) ; Professional 149 € (1 490 €/an) ; Scale 249 € (2 490 €/an) ; Custom | 500 / 1 500 / 5 000 « produits », sachant qu'un ASIN enfant sur 3 marketplaces compte pour 3 ; 3 sièges (Pro), 5 (Scale) | Dashboards, monitoring, alertes, mots-clés, « Advertising » ; agent IA à partir de Pro | — | **Contradiction** : la page tarifs dit « without long-term lock-in », mais l'article 9.2 des CGU prolonge le contrat d'un an faute de préavis d'un mois ; hors TVA |
| **Sellerise** ([données de tarifs](https://sellerise.com/pricing/data) ; [FAQ](https://sellerise.com/pricing/)) | Starter 19,99 $ ; Growing 39,99 $ ; Advanced 99,99 $ ; Pro-Seller 299,99 $ ; Top-Seller 599,99 $ (mensuel) | 1 / 2 / 5 / 10 / 20 comptes ; 1 000 / 5 000 / 50 000 / 150 000 / 300 000 commandes | App mobile, PPC Dashboard, Review Requester, stock, P&L ; remboursements à partir de Growing | Commandes en plus : 2 $ par tranche de 1 000 (lecture interprétative des champs JSON) ; compte : 20 $ ; collaborateur : 10 $ ; Keyword Tracker : 1 $ / 100 mots-clés ; Review Dashboard : 2 $ / 10 produits | **Contradiction** : la FAQ annonce les remboursements sur « every subscription plan », mais les données de plans excluent le module du plan Starter. La FAQ indique « no percentage/extra fees ». Essai de 7 jours sans carte. Prix visibles uniquement via l'endpoint JSON, la page HTML ne les affiche pas |
| **SellerApp** ([tarifs](https://www.sellerapp.com/pricing.html)) | Freemium 0 $ ; Pro « starts with $99 » ; Smart « $149 », puis **250 $/mois après 3 mois** ; Custom | Prix fixé par questionnaire | Automatisation publicitaire et account manager dans Smart | Agences : 300 $ + 0,5 à 2,5 % des dépenses publicitaires | Prix d'appel limité à 3 mois ; grille réelle non publiée |
| **Perpetua** ([tarifs](https://perpetua.io/pricing)) | Essentials 695 $ ; Growth 695 $ + un % des dépenses publicitaires ; Premium sur devis | Essentials : jusqu'à 10 k$ de dépenses publicitaires par mois | PPC uniquement | Pourcentage non publié | — |
| **Services de remboursement** | Carbon6 Seller Investigators : **25 %**, audit gratuit en 48 h ([Carbon6](https://carbon6.io/seller-investigators/)) ; GETIDA : « starting at 20% », sans abonnement, audit sur 18 mois ([GETIDA](https://getida.com/how-we-help/)) ; Refunds Manager : désormais centré sur les déductions *vendor*, sans taux publié ([Refunds Manager](https://refundsmanager.com/)) | — | — | — | — |

### Coût mensuel réel pour 1 000, 5 000 et 20 000 commandes par mois

Calculs de l'auteur, faits uniquement à partir des prix ci-dessus. Les montants sont hors TVA quand l'éditeur le précise, et chaque devise est conservée.

| Outil | 1 000 commandes | 5 000 commandes | 20 000 commandes |
|---|---|---|---|
| sellerboard, mensuel | 19 $ (Standard). Mais 150 demandes d'avis seulement : pour en solliciter 1 000, il faut Professional à 29 $ | 29 $ (Professional, plafond 6 000) | 79 $ (Business plafonne à 15 000, donc Enterprise) |
| sellerboard, annuel | 179/12 = 14,92 $, ou 279/12 = 23,25 $ | 23,25 $ | 759/12 = 63,25 $ |
| Shopkeeper | 45 $, ou 55 $ avec le service de remboursement | 90 $ + 15 % des montants récupérés | Superseller plafonne à 10 000 : Enterprise sur devis |
| SELLERLOGIC BA (3 mois / 12 mois) | 15,00 € / 13,50 € | 50,00 € / 45,00 € | 129,00 € / 116,10 € |
| + Repricer Advanced, 500 SKU | +106 €, ou 106 × 10/12 = 88,33 € en annuel | Exemple : 50 + 106 = 156 € + 25 % des remboursements | 129 + 106 = 235 € |
| AMALYTIX (selon le catalogue, pas les commandes) | 100 ASIN × 4 marketplaces = 400 produits → 69 €, ou 57,50 € en annuel | Idem | 300 ASIN × 4 = 1 200 produits → 149 €, ou 124,17 € en annuel |
| Sellerise | 19,99 $ sans remboursements ; 39,99 $ avec | 39,99 $ (Growing) | 39,99 + 15 × 2 = 69,99 $ (lecture interprétative), ou Advanced 99,99 $ |
| SellerApp, avec automatisation PPC | 149 $ pendant 3 mois, puis 250 $ | Idem (grille réelle non publiée) | Idem |
| Perpetua, PPC seul | 695 $ jusqu'à 10 k$ de dépenses publicitaires | 695 $ | 695 $ + un % non publié au-delà de 10 k$ |

**Analyse : le poids des remboursements.** Prenons 1 000 € récupérés dans le mois. La commission est de :

- 0 € chez Sellerise ;
- 150 € chez Shopkeeper Master ;
- 200 € au minimum chez GETIDA ;
- 250 € chez SELLERLOGIC Lost & Found ou Seller Investigators.

Elle dépasse donc l'abonnement lui-même, d'un facteur 2 à 10 selon l'outil. C'est le premier poste de coût réel caché, devant la mise à niveau automatique de palier. Seuls deux outils gèrent toute la chaîne (profit, stock, remboursements, PPC) pour moins de 80 $ à 20 000 commandes : sellerboard et Sellerise.

### Réputation (Trustpilot, lu le 11/11/2026)

| Outil | Note Trustpilot | Nombre d'avis |
|---|---|---|
| SELLERLOGIC ([lien](https://www.trustpilot.com/review/sellerlogic.com)) | 4,7 | 37 |
| sellerboard ([lien](https://www.trustpilot.com/review/sellerboard.com)) | 4,5 | 164 |
| Sellerise ([lien](https://www.trustpilot.com/review/sellerise.com)) | 4,4 (les étoiles affichent 4,5) | 132 |
| SellerApp ([lien](https://www.trustpilot.com/review/sellerapp.com)) | 4,4 | 130 |
| Perpetua ([lien](https://www.trustpilot.com/review/perpetua.io)) | 2,6 | 63 |
| GETIDA ([lien](https://www.trustpilot.com/review/getida.com)) | 2,3 | 7 |
| Seller Investigators ([lien](https://www.trustpilot.com/review/sellerinvestigators.com)) | 2,1 | 122 |
| Shopkeeper ([lien](https://www.trustpilot.com/review/shopkeeper.com)) | 1,5 | 112 |

**Analyse.** Les deux outils les plus mal notés, Shopkeeper et les services de remboursement à commission, sont aussi ceux dont les conditions sont les plus restrictives : prorata automatique non remboursable, et commissions de 12 à 25 %. C'est une corrélation, pas une preuve de causalité.

À noter pour un positionnement francophone : **sellerboard et Shopkeeper proposent déjà une interface ou un site en français** ([sellerboard](https://sellerboard.com/en/) ; [Shopkeeper](https://shopkeeper.com/terms)). La langue ne différencie donc pas à elle seule.

---

## 5. Le combiné existe déjà : le trou est la boucle prévu-réalisé

### Correction explicite

**Combiner sourcing et gestion de compte n'est pas une idée neuve.** Quatre offres vérifiées le font dans un seul abonnement : Seller 365 Reseller, Jungle Scout Growth Accelerator, Seller Assistant Business et Helium 10 Platinum. La bande de 30 à 129 $ n'est donc pas vide.

**Seller 365 Reseller Standard (69 $, ou 65 $ en annuel)** regroupe Tactical Arbitrage, ScoutIQ, Scoutify, ScoutX, InventoryLab et sa comptabilité, SmartRepricer, FeedbackWhiz (e-mails, alertes, profits), AI Operator et les remboursements Seller 365, avec une commission de **15 %**, ramenée à 5 % sur Reseller Pro à 199 $ ([Threecolts](https://www.threecolts.com/seller-365)). La page se contredit : son tableau indique pour Standard 7 recherches simultanées et 5 000 commandes de profits, mais ses puces annoncent 10 recherches et des profits illimités. Le volet Brands (179 à 1 199 $) retire tous les outils de sourcing et InventoryLab.

**Jungle Scout Growth Accelerator (79 $, ou 49 $ en annuel, 588 $/an)** inclut la recherche de produits illimitée, une base de fournisseurs, Sales Analytics (P&L), Inventory Manager, l'automatisation des avis, et une couche publicitaire limitée à l'analyse et à la récolte de mots-clés négatifs. Il ne propose aucun service de remboursement. Un siège supplémentaire coûte 49 $/mois ([Jungle Scout](https://www.junglescout.com/pricing/catalyst-plans)). La page se contredit aussi : le plan Brand Owner compte 3 utilisateurs dans le tableau et 10 dans la FAQ.

**Seller Assistant Business (79,99 $, ou 69,99 $ en annuel)** couvre le sourcing en arbitrage en ligne et en gros (analyse de listes de prix, vérification des restrictions en masse). Il y ajoute des bons de commande illimités, des entrepôts, le suivi du coût de revient complet (landed cost), un repricer et un module de rentabilité en « beta ». Il ne propose ni remboursements ni PPC ([Seller Assistant](https://sellerassistant.app/pricing)). À ne pas confondre avec l'assistant IA natif d'Amazon, qui porte le même nom.

**Helium 10 Platinum (129 $, ou 99 $ en annuel)** offre la recherche, un rapport de profits « limité », la gestion de stock sur 40 SKU, 5 000 e-mails de Follow-Up et un service de remboursement géré à **15 %** ([Helium 10](https://www.helium10.com/pricing/)). La publicité, via Helium 10 Ads, n'est disponible qu'en **Diamond (359 $, ou 279 $ en annuel), avec 2 % de frais sur les dépenses PPC gérées**. Enterprise démarre à 1 499 $/mois, facturé à l'année.

Helium 10 vend aussi des add-ons :

- MCP : 50 $/mois ;
- Keyword Tracker : dès 19 $ ;
- Market Tracker 360 : dès 650 $ ;
- plusieurs formations ou groupes à 99 $ chacun ;
- des utilisateurs supplémentaires, sans prix affiché.

**Les sources officielles de Helium 10 se contredisent.** Le blog officiel, mis à jour en avril 2026, mentionne encore un plan « Starter from $49/month », absent de la page tarifs. Il annonce 10 000 SKU de stock en Diamond, contre 500 sur la page tarifs. Il décrit Refund Genie comme « Unlimited » sans frais, alors que la page tarifs indique 15 % et 10 % ([blog Helium 10](https://www.helium10.com/blog/pricing-membership-plan-options-how-they-work/)). La page tarifs, plus récente, prévaut.

**InventoryLab seul** est affiché autour de 58 $, avec 69 $ barré. L'option Restocking Insights coûte 25 $/mois ([Threecolts](https://www.threecolts.com/seller-365/inventorylab)).

**Outils de sourcing sans gestion de compte** : SellerAmp (19,95 / 29,95 / 49,95 $ ; [SellerAmp](https://www.selleramp.com/pricing/) ; [fonctions](https://selleramp.com/features/)) et SmartScout (49 / 119 / 299 $, ou 29 / 99 / 239 $, sans libellé de facturation ; [SmartScout](https://www.smartscout.com/pricing)).

**Outils sans recherche de produits** : ZonGuru, devenu « Helix » pour l'optimisation des fiches (149 à 699 $ ; [ZonGuru](https://www.zonguru.com/pricing)), et SoStocked (« Starting at $175 », sans sourcing ; [SoStocked](https://sostocked.com/pricing/)).

### Matrice fonctions × prix (prix officiels vérifiés)

Légende : ✓ inclus ; ~ partiel ; ✗ absent ; ? non vérifié.

| Offre | Mensuel | Annuel/mois | Sourcing | Profit / P&L | Stock | Comptabilité | Remboursements | PPC |
|---|---|---|---|---|---|---|---|---|
| sellerboard Standard → Enterprise | 19 → 79 $ | 15 → 63 $ | ✗ | ✓ | ✓ | ~ (COGS FIFO) | ✓ (commission ?) | ✓ (optimisation) |
| Sellerise Starter → Advanced | 19,99 → 99,99 $ | ? | ✗ | ✓ | ✓ | ~ | ✗ en Starter, ✓ 0 % ensuite | ~ (dashboard) |
| SellerAmp | 19,95 → 49,95 $ | « 2 months free » | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Seller Assistant Pro | 29,99 $ | 24,99 $ | ✓ | ~ (preview) | ~ (3 bons de commande) | ✗ | ✗ | ✗ |
| InventoryLab seul | ~58 $ | ? | ~ (Scoutify) | ✓ | ~ (+25 $) | ✓ | ✗ | ✗ |
| **Seller 365 Reseller Standard** | **69 $** | **65 $** | ✓ | ✓ | ✓ | ✓ | ✓ (15 %) | ✗ |
| **JS Growth Accelerator** | **79 $** | **49 $** | ✓ | ✓ | ✓ | ✗ | ✗ | ~ (analyse) |
| **Seller Assistant Business** | **79,99 $** | **69,99 $** | ✓ | ✓ (beta) | ~ | ~ (landed cost) | ✗ | ✗ |
| **Helium 10 Platinum** | **129 $** | **99 $** | ✓ | ~ (limité) | ~ (40 SKU) | ✗ | ✓ (15 %) | ✗ |
| Seller 365 Reseller Pro | 199 $ | 183 $ | ✓ | ✓ | ✓ | ✓ | ✓ (5 %) | ✗ |
| **Helium 10 Diamond** | **359 $** | **279 $** | ✓ | ✓ | ✓ (500 ou 10 000 SKU selon la source) | ✗ | ✓ (10 %) | ✓ (+2 % des dépenses) |
| Helium 10 Enterprise | dès 1 499 $ (annuel) | — | ✓ | ? | ✓ | ? | ? | ✓ |

Sources : [sellerboard](https://sellerboard.com/en/), [Sellerise](https://sellerise.com/pricing/data), [SellerAmp](https://www.selleramp.com/pricing/), [Seller Assistant](https://sellerassistant.app/pricing), [InventoryLab](https://www.threecolts.com/seller-365/inventorylab), [Seller 365](https://www.threecolts.com/seller-365), [Jungle Scout](https://www.junglescout.com/pricing/catalyst-plans), [Helium 10](https://www.helium10.com/pricing/).

### Le trou vérifié : prévu contre réalisé, par lot d'achat

Aucune des pages et documentations consultées ne décrit de comparaison entre le ROI prévu au moment de l'achat et le profit réalisé, lot d'achat par lot d'achat. Voici ce que chaque outil documente.

**Seller Assistant** est le plus avancé. Ses données d'analyse alimentent le bon de commande : « Data from your analysis carries into the PO, so nothing is re-entered ». Son coût de revient est pondéré : « Weighted across every PO the SKU appeared in ». Son module de rentabilité promet de « Know the profit you actually made, not the profit you planned », avec un P&L par produit, marque et fournisseur, pas par bon de commande ([Seller Assistant](https://sellerassistant.app/)).

**sellerboard** affecte le coût d'achat par lot selon la méthode FIFO, mais ne propose ni sourcing ni ROI prévu ([blog sellerboard, 21/09/2025](https://blog.sellerboard.com/2025/09/21/🎯-smarter-profit-tracking-with-fifo-new-cogs-method-now-in-sellerboard/)).

**Seller 365** réunit le sourcing et InventoryLab dans un même abonnement. Sa page ne décrit pourtant aucun transfert automatique d'un ROI prévu vers un lot d'achat ([Threecolts](https://www.threecolts.com/seller-365)).

**SellerAmp** n'enregistre que des analyses, pas des achats ([SellerAmp](https://selleramp.com/features/)).

Chez **Helium 10** et **Jungle Scout**, les pages tarifs ne montrent aucun lien entre les outils de recherche et un ROI prévu enregistré à l'achat ([Helium 10](https://www.helium10.com/pricing/) ; [Jungle Scout](https://www.junglescout.com/pricing/catalyst-plans)).

**Analyse : portée de ce constat.** C'est une absence documentée, pas une absence prouvée. Aucun centre d'aide ne dit « non pris en charge ». Le centre d'aide de Seller Assistant et celui de Helium 10 Profits n'ont pas été lus.

### Ce qu'Amazon donne gratuitement (éléments vérifiés uniquement)

**Seller Assistant, l'assistant IA d'Amazon.** Amazon le décrit comme « the free conversational AI tool inside Amazon's Seller Central dashboard ». L'outil surveille l'activité en continu, ajuste les prix en arrière-plan, exécute des workflows et mémorise les décisions passées ([Amazon, 29/09/2026](https://sellingpartners.aboutamazon.com/accelerate-2026-recap)).

**Le plugin Amazon Quick / Claude.** Il est « now available in beta for sellers in Amazon's U.S. stores », avec « international expansion to follow » ([Amazon, 23/09/2026](https://www.aboutamazon.com/news/innovation-at-amazon/seller-assistant-plugin-amazon-quick-claude)). Il automatise le réassort et les ajustements de prix. L'annonce ne parle pas de profit. Un abonnement Quick Plus de 12 mois est offert aux titulaires de compte principal jusqu'au 31/12/2026.

**L'IA générative pour les fiches produits** est ouverte aux vendeurs en France, en Allemagne, en Italie, en Espagne et au Royaume-Uni ([Amazon EU](https://www.aboutamazon.eu/news/empowering-small-business/amazon-announces-expansion-of-generative-ai-listing-tools-to-sellers-across-europe)).

**La page des outils Amazon** liste le calculateur de revenus FBA, Product Opportunity Explorer, « the free Amazon Seller app », Veeqo (« free multi-channel shipping software ») et Seller University ([Amazon](https://sell.amazon.com/tools)).

**Analyse.** Amazon couvre gratuitement une part croissante de la gestion de compte : réassort, prix et fiches produits. Rien de ce qui a été vérifié ne montre en revanche un P&L avec le coût d'achat du vendeur, du sourcing hors Amazon, ou une comparaison entre prévu et réalisé. La disponibilité en France des workflows de septembre 2026 n'est pas vérifiée (voir l'annexe).

---

## 6. L'échelle de prix laisse trois cases vides

**Échelle de prix en facturation mensuelle.** Les prix entre parenthèses sont les équivalents mensuels en facturation annuelle.

| Bande | Gestion seule | Sourcing seul | Sourcing + gestion |
|---|---|---|---|
| 0 $ | Outils natifs Amazon, avec le compte Pro (39,99 $ US / 39 € HT FR) | — | — |
| 15–30 $ | sellerboard 19–29 $ (15–23 $) ; Sellerise Starter 19,99 $ ; Shopkeeper Starter 20 $ | SellerAmp 19,95–29,95 $ | **Seller Assistant Pro 29,99 $ (24,99 $), rentabilité en preview seulement** |
| 30–60 $ | Shopkeeper Intermediate 45 $ ; Sellerise Growing 39,99 $ | SellerAmp 49,95 $ ; SmartScout 49 $ | InventoryLab ~58 $ (Scoutify + comptabilité) |
| 60–100 $ | sellerboard Enterprise 79 $ ; Shopkeeper Master 90 $ ; AMALYTIX Essential 69 € | — | **Seller 365 Reseller 69 $ (65 $) ; JS Growth 79 $ (49 $) ; Seller Assistant Business 79,99 $ (69,99 $)** |
| 100–200 $ | AMALYTIX Pro 149 € ; SoStocked dès 175 $ | SmartScout 119 $ | **H10 Platinum 129 $ (99 $)** ; Seller 365 Teams 129 $ ; Seller Assistant Business Plus 189,99 $ ; Seller 365 Pro 199 $ |
| 200–400 $ | SellerApp Smart 250 $ ; Shopkeeper Superseller 250 $ | SmartScout 299 $ | **H10 Diamond 359 $ (279 $) + 2 % des dépenses publicitaires, seul combiné avec PPC** |
| 500 $ et plus | Perpetua 695 $ | — | Seller Assistant Agency dès 999,99 $ ; H10 Enterprise dès 1 499 $ |

Sources : celles des sections 4 et 5.

**Trous vérifiés** :

1. **Sous environ 30 $, aucun combiné complet.** La seule offre hybride, Seller Assistant Pro, n'a qu'une rentabilité en « Preview ». **Analyse** : l'alternative est un empilement, par exemple SellerAmp à 19,95 $ plus sellerboard à 15–19 $, soit environ 35 à 39 $ par mois. On obtient alors deux outils non reliés.
2. **Sourcing et pilotage PPC réunis seulement à partir de 279 à 359 $** (Helium 10 Diamond, plus 2 % des dépenses). En dessous, on ne trouve qu'une couche d'analyse publicitaire, dans Jungle Scout Growth.
3. **Prévu contre réalisé par lot d'achat** : absent de la documentation de tous les outils, quel que soit le prix.
4. **Un marché scindé en deux segments.** Les revendeurs (arbitrage en ligne et grossistes) disposent de Seller 365 Reseller et de Seller Assistant, sans PPC. Les marques en marque propre disposent de Helium 10 et de Jungle Scout, sans sourcing chez les détaillants ou les grossistes. Le volet Brands de Seller 365 retire même le sourcing ([Threecolts](https://www.threecolts.com/seller-365)).

---

## 7. Positionnement recommandé (Analyse)

*Toute cette section est de l'analyse. Les faits qu'elle mobilise sont sourcés dans les sections 2 à 6.*

### Segment cible

Le cœur de cible est le **revendeur francophone, en arbitrage en ligne et en gros, qui vend sur Amazon.fr et sur d'autres places de marché de l'UE**. Trois raisons y conduisent.

1. Ce segment est le seul dont les besoins de sourcing externe sont servis par des suites américaines (Seller 365, Seller Assistant) peu tournées vers l'Europe. Les flux d'affiliation français constituent une source propre qu'aucun concurrent ne documente.
2. Les marketplaces NL, BE, PL et SE sont sans historique Keepa. Un outil qui construit l'historique du vendeur à partir de ses propres relevés SP-API y apporte une donnée introuvable ailleurs.
3. Le vendeur à l'origine du projet appartient à ce segment, ce qui rend la phase 1 directement utile.

La marque propre est déjà couverte par Helium 10 et Jungle Scout. Elle reste hors cible au départ.

### Fonctions différenciantes ancrées dans les trous vérifiés

**1. La boucle prévu-réalisé par lot.**

- À la décision d'achat, figer un instantané : prix d'achat, frais SP-API estimés, Buy Box, ROI et délai de vente prévus.
- Rattacher cet instantané au bon de commande puis au lot reçu.
- Affecter les ventes au lot en FIFO, comme le fait sellerboard pour le coût d'achat.
- Afficher par lot l'écart prévu/réalisé sur la marge, le délai de rotation et les frais.

Cette fonction est le cœur du produit. C'est aussi la seule qui transforme l'outil en outil d'apprentissage des décisions d'achat, et pas seulement en outil de reporting.

**2. Un sourcing par EAN conforme.** Les fichiers fournisseurs et les flux d'affiliation sont convertis via `searchCatalogItems`. Les restrictions et l'éligibilité sont vérifiées compte par compte. Les flux d'affiliation ne viennent qu'après lecture de leurs conditions.

**3. L'historique propre des marketplaces non couvertes par Keepa**, réservé au vendeur concerné, conformément aux articles 4.4 et 4.6.

**4. La transparence des calculs**, qui est de toute façon exigée par l'article 2.4 de l'AUP : afficher la source, la fraîcheur des données et la nature de chaque chiffre (observé, calculé ou estimé).

### Ce qu'il ne faut pas faire

**Reproduire les pratiques que le marché pénalise** :

- mise à niveau automatique non consentie ;
- abonnements non remboursables sans période de grâce ;
- commissions sur les remboursements ;
- add-ons découverts après coup ;
- prix d'appel limités à 3 mois ;
- reconduction annuelle contraire à la page tarifs.

L'engagement inverse est un argument vérifiable : un prix publié tout compris, un plafond qui bloque ou prévient au lieu de facturer, une résiliation mensuelle. Sellerise montre qu'on peut inclure les remboursements à 0 % de commission, mais il les présente lui-même de façon contradictoire selon le plan.

**Ne pas lancer de pilotage PPC.** Cela placerait l'outil face à Perpetua (695 $) et Helium 10 Diamond, hors de la bande de prix visée.

**Ne pas construire de cache partagé ou de base commune** à partir des jetons des clients.

**Ne pas utiliser la Creators API**, et ne pas scraper Amazon.

### Tarification : hypothèses à tester

Ces prix ne sont pas des données. Ils servent à placer l'offre face aux repères vérifiés : Seller Assistant Pro à 24,99–29,99 $, sellerboard à 19–29 $, et les combinés à 65–80 $. Aucun revenu n'est projeté.

**H1, entrée entre 19 et 29 € par mois.** Elle comprend :

- le sourcing SP-API seul (fichiers fournisseurs, frais, restrictions, éligibilité, Buy Box courante) ;
- le P&L FIFO ;
- la boucle prévu-réalisé ;
- un seul compte vendeur.

Elle occupe le trou vérifié « sous 30 $ ». Hypothèse à tester : un revendeur paiera-t-il ce prix pour remplacer l'empilement SellerAmp + sellerboard (35–39 $) ?

**H2, offre complète entre 39 et 59 €.** Elle ajoute :

- les flux d'affiliation et eBay ;
- l'historique propre UE ;
- la détection des écarts de remboursement, sans commission ;
- plusieurs marketplaces et plusieurs utilisateurs.

Elle se place sous les combinés à 65–80 $. Hypothèse à tester : la boucle prévu-réalisé justifie-t-elle de quitter Seller 365 ou Seller Assistant ?

**H3, module Keepa optionnel.** Uniquement si les conditions écrites de Keepa et la position d'Amazon sur l'article 4.3 le permettent. Deux formules sont possibles : la clé Keepa du client (« bring your own key ») ou une option payante distincte. Le prix ne peut pas être fixé tant que le tarif Keepa n'est pas vérifié.

### Coût des données par utilisateur

**SP-API : 0 $ par vendeur.** Le débit croît avec chaque client autorisé ([Amazon](https://developer-docs.amazon/sp-api/docs/usage-plans-and-rate-limits.md)).

**Keepa : coût en tokens connu, prix inconnu.** Une analyse complète consomme environ 1 token pour le produit, 12 pour deux pages d'offres (qui remplacent le token de base) et 2 pour la Buy Box, soit **environ 14 tokens**. Dans l'exemple de la documentation Keepa, 60 tokens par minute représentent au maximum 2 678 400 requêtes de base par mois de 31 jours ([Keepa](https://keepa.com/api-docs/plans-tokens.html)). Cela donne environ 191 000 analyses complètes par mois (2 678 400 / 14). Le coût par utilisateur s'obtiendra en divisant le prix du plan, une fois vérifié, par le nombre d'analyses consommées par chaque utilisateur. Une clé fournie par le client transfère ce coût, mais ne règle pas clairement le risque lié à l'article 4.3, qui vise aussi le fait de « promote ».

**Autres sources** :

- DataForSEO : environ 0,001 $ par GTIN ;
- EAN-Search : 19 à 149 € par mois selon le volume ;
- eBay : 5 000 appels par jour, une limite qui ne suffit pas pour un SaaS tant que le mode d'attribution des quotas n'est pas clarifié.

### Risques

1. **L'extension de l'assistant IA d'Amazon.** Il est déjà gratuit, prend en charge le réassort et les prix, et son plugin doit s'étendre à l'international. Il peut absorber la gestion de compte courante. Le profit par lot et le sourcing externe restent hors de ce qu'Amazon documente.
2. **L'article 4.3 de l'AUP**, en particulier pour toute intégration de Keepa.
3. **La réapparition de frais SP-API.** Amazon a renoncé aux frais « at this time ». Un business plan prudent doit inclure un scénario avec frais.
4. **Le plafond de 25 vendeurs** avant le listing sur l'Appstore, dont les exigences sont inconnues.
5. **La dépendance aux conditions des réseaux d'affiliation**, qui ne sont pas lues.
6. **Des concurrents capables de copier la boucle prévu-réalisé.** Seller Assistant en possède déjà les briques.

---

## 8. Prochaines étapes concrètes

### À vérifier par écrit, avant toute dépendance

1. **Keepa** : écrire à info@keepa.com pour obtenir :
   - les tarifs des plans API ;
   - l'existence ou non d'une offre gratuite ;
   - le droit d'afficher les données Keepa dans une application commerciale tierce ;
   - le modèle de clé fournie par le client ;
   - les conditions de conservation des données.
2. **Amazon** : ouvrir un cas auprès du support développeur SP-API et demander si l'intégration de données Keepa dans une application SP-API, privée puis publique, enfreint l'article 4.3. Conserver la réponse écrite.
3. **Awin et Rakuten** : obtenir les conditions éditeur sur l'usage des flux par un outil d'aide à l'achat pour revente, sur leur stockage et sur leur affichage à des clients tiers. Puis sonder 5 à 10 détaillants français, annonceur par annonceur.
4. **eBay et bol** : lire le contrat de licence eBay API et les conditions générales des affiliés bol.
5. **Grilles officielles** : avec son propre compte Seller Central, relever les grilles FBA 2026 et la taxe sur les services numériques (DST) pour la France, ainsi que la liste des `FeeType` renvoyés par la Product Fees API.
6. **Concurrents** : lire les centres d'aide de Seller Assistant (rapport bon de commande vs réalisé), Helium 10 Profits (coût d'achat par lot) et InventoryLab, pour confirmer ou infirmer l'absence de la boucle prévu-réalisé.
7. **Appstore** : relever les exigences du listing (revue de sécurité, audit DPP) avant de dépasser 25 vendeurs.

### Effets sur la feuille de route de l'outil personnel

**Étape 1.** Créer une application SP-API privée, qui donne droit à 10 auto-autorisations.

**Étape 2.** Brancher, en respectant leurs débits, `searchCatalogItems`, `getItemOffersBatch`, `getMyFeesEstimates`, `getListingsRestrictions` et `getItemEligibilityPreview`. Prévoir une file d'attente : l'éligibilité, à 1 requête par seconde, impose le rythme.

**Étape 3.** Modéliser dès le départ les objets « décision d'achat », « bon de commande » et « lot », avec un instantané figé des données au moment de la décision. C'est la fondation de la boucle prévu-réalisé, et elle ne se rajoute pas après coup.

**Étape 4.** Stocker des relevés horodatés des offres et du BSR des ASIN suivis. Cela construit l'historique propre, notamment pour NL, BE, PL et SE, tout en respectant les règles de conservation de la DPP.

**Étape 5.** Côté profit réalisé, il faut identifier les endpoints financiers et de rapports de la SP-API (règlements, remboursements, inventaire). **Ils n'ont pas été étudiés dans ce dossier** : c'est le prochain chantier documentaire.

**Étape 6.** Garder Keepa derrière une interface séparée et désactivable jusqu'aux réponses des points 1 et 2.

**Étape 7.** Écrire dans l'interface la nature de chaque chiffre (observé, calculé ou estimé), conformément à l'article 2.4 de l'AUP. Cela prépare la phase 2 sans refonte.

---

## Annexe : Points non vérifiés (exclus des conclusions)

Les éléments ci-dessous ont été vus seulement dans des sources secondaires, ou n'ont pas pu être lus. Ils n'ont influencé ni le corps du rapport ni ses conclusions.

### Keepa

| Point | Ce qui a été vu | Pour vérifier |
|---|---|---|
| Prix des plans API (environ 49 €/mois pour 20 tokens/min), paliers jusqu'à environ 11 099 €, absence d'offre gratuite | revenuegeeks, amzfinder (tiers) ; keepa.com est rendu en JavaScript | Écrire à info@keepa.com ; capture de keepa.com/#!api connecté |
| Abonnement « Data » à 29 €/mois (anciennement 19 €), fonctions gratuites de keepa.com | revenuegeeks (tiers) | Idem |
| CGU Keepa sur l'affichage ou la revente dans une application tierce | Introuvables | Réponse écrite de Keepa |

### SP-API et Amazon

| Point | Ce qui a été vu | Pour vérifier |
|---|---|---|
| Plafond exact de 20 offres renvoyées par `getItemOffers` | Connaissance antérieure, chiffre absent de la page lue | Test réel sur son compte |
| Grille des frais SP-API annulés (1 400 $/an, frais d'usage) et chronologie (annonce du 03/11/2025, suspension du 09/03/2026) | ppc.land, novadata (secondaires) ; la page d'origine renvoie une erreur 404 | Archive de developer.amazonservices.com/spp-announcement |
| Grilles FBA 2026 par pays, DST, commissions par catégorie, libellés `FeeType` | Pages d'aide Seller Central derrière connexion | Lecture connectée à Seller Central ; appel de test |
| Code « meltable » dans l'éligibilité FBA ; attributs « dangerous goods » des Product Type Definitions | Non lus | Lecture de la doc Product Type Definitions |
| Ads API : recommandations de mots-clés, impressions | Documentation tierce (python-amazon-ad-api) | Lecture de la doc officielle advertising.amazon.com |
| Conditions d'accès à Product Opportunity Explorer (pays, beta) | Secondaire | Vérification dans Seller Central FR |
| Identification d'Amazon comme vendeur sur un listing (SellerId par marketplace) | Inférence, non documentée sur la page lue | Test SP-API |
| Exigences du listing sur l'Appstore | Page téléchargée, non analysée | Lecture de la doc Appstore |
| Assistant IA d'Amazon : portée de « plus de 90 % des vendeurs dans leur langue » | PPC Land, qui cite Amazon | Communiqué Amazon d'origine |
| Disponibilité en France des workflows de septembre 2026 | Extrait d'un fil du forum Seller Central FR (non lu), decodeur-ia.com, Clubic (2025, « US only ») | Annonce officielle sur sell.amazon.fr ou sellercentral.amazon.fr |
| Pages publiques de Restock Inventory, FBA Capacity, Business Reports | Erreur 404 ou connexion requise | Lecture connectée |
| Date de fin de PA-API 5 (30/04 ou 15/05/2026) | DEV.to | Page de dépréciation Amazon Associates |

### Sources de données externes

| Point | Ce qui a été vu | Pour vérifier |
|---|---|---|
| Awin : « Price comparison Publishers are the main users », 10 flux par programme, délai d'approbation d'1 h ; API « Enhanced feed » | Wiki Awin et developer.awin.com via un moteur de recherche | Lecture directe, puis CG éditeur Awin |
| CJ : requêtes GraphQL `products` / `shoppingProductFeeds`, limite de 1 000 items | Acteur Apify tiers | developers.cj.com, connecté |
| Impact, Webgains, Tradedoubler, Kwanko/Effiliation, Daisycon, TradeTracker : conditions des flux | Non trouvées | Contact des réseaux |
| Walmart via Impact ; plus aucune nouvelle clé pour l'Affiliate API ; recherche Walmart Marketplace par UPC | FAQ vue en résultat de recherche ; PartnerBoost (tiers) | walmart.io, affiliates.walmart.com |
| eBay : Growth Check, « additional license », quota par application ou par utilisateur | Forum eBay ; page developer.ebay.com en erreur 403 | Contrat de licence eBay API et support eBay |
| Bol : endpoints par EAN (formulation exacte) ; CGU affiliés | Secondaire / non lu | affiliate.bol.com/nl/algemene-voorwaarden |
| Allegro : restriction introduite le 01/06/2021 | Actualité développeurs Allegro, vue en résumé | Lecture directe |
| Idealo, PriceRunner, Ledenicheur : absence d'API de données | Sources tierces | Contact partenaires |
| Octopia/Cdiscount, Fnac-Darty, Kaufland, Zalando : API vendeurs uniquement | Non recherché | Lecture des portails développeurs |
| Verified by GS1 : 30 requêtes gratuites par jour ; prix de l'API GS1 France | Résumé de recherche ; non trouvé | GS1 France |
| Prix payants d'UPCitemdb ; conditions de redistribution d'EAN-Search, Barcode Lookup, DataForSEO, SerpApi ; CGU Google | Non lus | CGU respectives |
| Panjiva, Kompass, Europages, Comext (douanes UE) | Non vérifiés | Pages tarifs et documentation |
| ImportGenius à 125 $ ou 149 $ | Capterra, TrustRadius ; contredit par la page officielle | — (la page officielle prévaut) |
| hiQ v. LinkedIn : accord de 500 000 $, injonction (2022) ; abandon de l'appel par Meta contre Bright Data | Proskauer, ZwillGen, TechCrunch | PDF des décisions (PACER / CourtListener) |
| Transposition française (CPI L.341-1 et suivants), jurisprudence française sur le scraping, statut du robots.txt et de l'opt-out TDM | Légifrance inaccessible | Légifrance ; avis d'avocat |
| SourceMogul scannant des sites détaillants ; OAGenius, ProfitPath, Arbitrage Hero | CB Insights / non consultés | Sites officiels |

### Outils de gestion et suites

| Point | Ce qui a été vu | Pour vérifier |
|---|---|---|
| sellerboard : commission éventuelle sur les remboursements, prix des utilisateurs ou comptes au-delà des quotas, sens d'« Additional seller accounts », app mobile | Non publié | Support sellerboard par écrit |
| Shopkeeper : durée de l'essai, prix annuels, prix Enterprise, TVA, prix des services PPC | Non affiché | Contact commercial |
| Sellerise : prix annuels, confirmation de la devise, TVA | Non publié en clair | Support Sellerise |
| SellerApp : grille réelle selon le questionnaire ; CGU (page en 404) | — | Questionnaire, puis CGU |
| Perpetua : pourcentage du plan Growth | Non publié | Contact commercial |
| SELLERLOGIC : interface en français ; module PPC ; Lost & Found à 20 % selon Webretailer (contredit par la page officielle à 25 %) | Webretailer (tiers) | Le prix officiel de 25 % prévaut ; langues à confirmer |
| AMALYTIX : module profit ou remboursement vendeur ; note Trustpilot | Non trouvé | Support / Trustpilot |
| Refunds Manager : « 4.9/5 on Trustpilot » (auto-déclaré) ; notes G2 et Capterra | Site de l'éditeur | Trustpilot, G2 |
| Helium 10 : prix des utilisateurs supplémentaires ; existence d'Inventory Protector ; suppression de Starter et de Ads en Platinum, plafonds Cerebro/Magnet (rapport EcomCrew du 01/04/2026, fondé sur un e-mail) | EcomCrew (tiers) | Support Helium 10 |
| Jungle Scout Cobalt : prix | Non public | Démo commerciale |
| AMZScout : prix actuel (49,99 $ selon le blog officiel du 04/02/2026 ; 59,99 à 79,99 $ selon des agrégateurs) | Page tarifs rendue en JavaScript | Capture de la page tarifs |
| BQool, Forecastly (« dès 49 $ »), GoAura (fonctions) | Erreur 404, JavaScript ou secondaire | Pages tarifs |
| Tarif annuel exact d'InventoryLab seul | Extraction brouillée | Capture de la page |
| Statut officiel de la base de connaissances InventoryLab hébergée sur useresponse.com | Domaine inhabituel, éditeur non indiqué | Support Threecolts |
| Sens exact des libellés mensuel/annuel chez SmartScout (bascule non libellée) | — | Capture de la page |
