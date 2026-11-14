# Syllig Pilot, passerelle unique vers Amazon : ce que la SP-API permet (14/11/2026)

Recherche du 14/11/2026 (heure de Paris). Cas visé : vendeur professionnel, marketplace FR (région SP-API **EU**), revente en gros, FBA. Question : tout ce que le vendeur fait dans Seller Central et dans l'application mobile « Amazon Seller » peut-il passer par Syllig Pilot, avec une automatisation poussée et une validation humaine aux étapes engageantes ?

**Règle de lecture**
- **VÉRIFIÉ** : lu le 14/11/2026 sur la page officielle citée (lien + court extrait).
- **VÉRIFIÉ (extrait)** : vu seulement dans un extrait de moteur de recherche, page non ouverte.
- **NON VÉRIFIÉ** : source non lue ou non officielle ; rien n'est affirmé (voir l'annexe).
- **Analyse** : avis, séparé des faits.

**Sources lues.** Les pages `developer-docs.amazon.com/sp-api/...` redirigent (HTTP 301) vers `developer-docs.amazon/sp-api/...` ; les liens ci-dessous sont ceux réellement lus (version `.md` de la même page). Les pages lues portent des dates de mise à jour entre septembre et novembre 2026. Le dépôt `github.com/amzn/selling-partner-api-models` n'a **pas** pu être lu depuis cet environnement (HTTP 403) : les modèles cités le sont d'après les liens « Model » des pages de documentation.

**Interdits du projet respectés dans les propositions** : pas d'aspiration de pages, pas de Keepa, pas de revente ni de mise en commun de données Amazon entre comptes (règlement SP-API, AUP 4.3 et 4.4, cités au point 4).

---

## 1. Le scan de code-barres de l'application « Amazon Seller », et son équivalent web

### 1.1 Ce que fait l'application

| Fait | Statut | Source + extrait |
|---|---|---|
| Le scan utilise l'appareil photo et sert à trouver des produits à vendre. | VÉRIFIÉ | https://sell.amazon.com/blog/scan-barcodes-upc : « Using your smartphone camera, you can scan barcodes to search for and find products to sell. » |
| Le scan affiche les offres en cours, le prix à jour et les vendeurs présents ; Amazon le présente comme une aide pour juger la concurrence et la rentabilité. | VÉRIFIÉ | https://sell.amazon.com/blog/how-to-use-amazon-seller-app : « use the camera of your mobile device to scan a product or the product's barcode » ; « can help you determine how competitive the product is and gauge potential profitability for your business. » |
| Même page : « Top Sellers » et « Hot New Releases » par catégorie, création d'offres et de nouvelles fiches depuis l'application, photos (Amazon Product Photo Studio), ventes, paiements, stock, publicité, messages, santé du compte, changement de région avec une seule connexion. | VÉRIFIÉ | même lien (liste des fonctions de l'article). |
| La page « scan » cite aussi « The profitability of your products », « Up-to-date pricing information », « Rankings for each item you sell », « Competitors who are selling the same products ». | VÉRIFIÉ | https://sell.amazon.com/blog/scan-barcodes-upc |
| Éligibilité (restrictions) et frais au moment du scan : **non mentionnés** par les deux pages du blog Amazon. | VÉRIFIÉ (absence) | les deux liens ci-dessus. |
| Un message du forum vendeurs Europe, signé « Connor_Amazon », dit : « You can scan products while shopping to instantly check profitability, restrictions, and fees. » | VÉRIFIÉ (texte lu) ; le statut d'employé Amazon de l'auteur n'est **pas** confirmé par la page, date « il y a 2 ans » | https://sellercentral-europe.amazon.com/seller-forums/discussions/t/dd99dbc7-ccfa-4a33-8f5e-95b994ca8778 |
| L'application existe sur l'App Store français (éditeur AMZN Mobile LLC), avec « calculer les bénéfices et comparer les coûts du service Expédié par Amazon avec ceux de l'auto-expédition » et « La possibilité de vendre dans toute l'Europe ». La fiche ne mentionne pas le scan. | VÉRIFIÉ (fiche de l'éditeur sur l'App Store, hors liste des domaines Amazon) | https://apps.apple.com/fr/app/amazon-seller/id794141485 |
| Liste officielle des pays où **le scan** est disponible. | NON VÉRIFIÉ | aucune page officielle trouvée ; le blog dit seulement « compatible with both Android phones and iPhones ». |

### 1.2 Reproduire le scan dans une application web (téléphone)

**Lecture du code-barres dans le navigateur**

| Fait | Statut | Source + extrait |
|---|---|---|
| `getUserMedia` (accès caméra) est disponible partout depuis 2017, mais seulement en HTTPS ; la caméra arrière se demande par `facingMode: "environment"`. | VÉRIFIÉ | https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia : « It's been available across browsers since September 2017. » ; « available only in secure contexts (HTTPS) » ; `facingMode: { exact: "environment" }` |
| L'API `BarcodeDetector` est **expérimentale**, pas « Baseline », HTTPS seulement ; formats `ean_13`, `ean_8`, `upc_a`, `upc_e` (et d'autres). | VÉRIFIÉ | https://developer.mozilla.org/en-US/docs/Web/API/Barcode_Detection_API : « This feature is not Baseline because it does not work in some of the most widely-used browsers. » |
| Compatibilité : **Chrome Android 83+ oui** ; Samsung Internet et WebView Android : comme Chrome Android ; **Safari (donc tout navigateur iPhone) : seulement derrière l'option « Shape Detection API »**, donc pas par défaut ; **Firefox : non** ; Chrome ordinateur : macOS et ChromeOS seulement. | VÉRIFIÉ (données de compatibilité MDN) | https://github.com/mdn/browser-compat-data/blob/main/api/BarcodeDetector.json (lu le 14/11/2026) : `safari … flags … "Shape Detection API"`, `firefox: version_added: false`, `chrome_android: 83` |

**Analyse.** Sur Android, `getUserMedia` + `BarcodeDetector` suffisent. Sur iPhone, il faut une bibliothèque de décodage en JavaScript (exécutée dans la page) en secours : aucune source officielle lue ici sur ces bibliothèques (voir annexe). La saisie manuelle de l'EAN reste le secours universel.

**Interrogation d'Amazon après le scan (une chaîne de 4 appels SP-API)**

| Étape | Opération | Statut | Source + extrait | Rôle requis | Débit par défaut |
|---|---|---|---|---|---|
| EAN/UPC → ASIN, titre, image, rang de vente | `searchCatalogItems` (Catalog Items v2022-04-01), `identifiersType` = `EAN`, `UPC`, `GTIN`, `ISBN`, `JAN`, `MINSAN`, `SKU`, `ASIN` ; `includedData` dont `salesRanks`, `summaries`, `images`, `dimensions` | VÉRIFIÉ | https://developer-docs.amazon/sp-api/reference/searchcatalogitems.md : « You can search by identifier or by keywords. » ; « `identifiersType` is required when `identifiers` is in the request. » | Product Listing | 2 req/s, rafale 2 |
| Puis-je vendre cet ASIN ? | `getListingsRestrictions` (Listings Restrictions v2021-08-01), raisons `APPROVAL_REQUIRED`, `ASIN_NOT_FOUND`, `NOT_ELIGIBLE`, filtrable par `conditionType` | VÉRIFIÉ | https://developer-docs.amazon/sp-api/reference/getlistingsrestrictions.md : « Approval is required to create a listing for the specified ASIN. A path forward link will be provided… » ; lien type « Approval via Seller Central. » | Product Listing | 5 req/s, rafale 10 |
| Offres, prix Buy Box, nombre d'offres, rangs | `getItemOffers` (Product Pricing v0) ; aussi `getItemOffersBatch`, `getCompetitiveSummary` et `getFeaturedOfferExpectedPriceBatch` (v2022-05-01) | VÉRIFIÉ | https://developer-docs.amazon/sp-api/reference/getitemoffers.md : « Returns the lowest priced offers for a single item based on ASIN. » (champs `BuyBoxPrices`, `NumberOfOffers`, `SalesRankings`) | Pricing ou Product Listing | 0,5 req/s, rafale 1 |
| Frais Amazon (commission, FBA) | `getMyFeesEstimateForASIN` (Product Fees v0), `IsAmazonFulfilled` vrai = FBA ; `getMyFeesEstimates` pour un lot | VÉRIFIÉ | https://developer-docs.amazon/sp-api/reference/getmyfeesestimateforasin.md : « You can call `getMyFeesEstimateForASIN` for an item on behalf of a selling partner before the selling partner sets the item's price. » ; « Actual costs may vary. » | Pricing ou Product Listing | 1 req/s, rafale 2 |

Les rôles viennent de https://developer-docs.amazon/sp-api/docs/role-mappings.md (VÉRIFIÉ, régions NA, EU, FE pour ces quatre opérations).

**Analyse.** L'équivalent web est faisable avec les seules données du compte du vendeur (pas d'aspiration, pas de Keepa). Limite principale : `getItemOffers` à 0,5 requête/seconde, donc un scan toutes les 2 secondes au plus par compte ; un historique de prix ne peut venir que de ce que Syllig Pilot enregistre lui-même pour ce compte. L'éligibilité donne un **lien** vers Seller Central, pas une demande d'approbation (voir point 2.2).

---

## 2. Les API de la SP-API, utiles au vendeur européen

Liste officielle des API et versions : https://developer-docs.amazon/sp-api/docs/sp-api-models.md (VÉRIFIÉ). Rôles et régions par opération : https://developer-docs.amazon/sp-api/docs/role-mappings.md (VÉRIFIÉ, mise à jour 28/10/2026). Définition des rôles : https://developer-docs.amazon/sp-api/docs/roles-in-the-selling-partner-api.md (VÉRIFIÉ) : « If you call an operation for which you don't have the required roles, you get a 403 error. » Le mot « (Restricted) » signifie données personnelles (PII), avec exigences de sécurité supplémentaires.

### 2.1 Tableau des API

« Ce que ça permet » reprend l'introduction de la page de chaque API (`https://developer-docs.amazon/sp-api/docs/<api>.md`), VÉRIFIÉ sauf mention. La colonne « Seller Central » est une **analyse** (correspondance avec les menus), sauf mention.

| API (version actuelle) | Ce que ça permet | Rôle(s) (au moins un) | Régions | Fonction Seller Central correspondante |
|---|---|---|---|---|
| Catalog Items v2022-04-01 | Chercher et lire les fiches du catalogue (par EAN, mots-clés…) | Product Listing | NA, EU, FE | Ajouter un produit → recherche |
| Listings Items v2021-08-01 | Créer, modifier, supprimer, lire ses offres et fiches (`putListingsItem`, `patchListingsItem`, `searchListingsItems`…) | Product Listing ; Inventory and Order Tracking | NA, EU, FE | Gérer l'inventaire, modifier offre et prix |
| Listings Restrictions v2021-08-01 | « check if there are any restrictions that prevent the creation of a listing » | Product Listing | NA, EU, FE | Statut d'éligibilité / « Demander l'approbation » (lecture seule) |
| Product Type Definitions v2020-09-01 | Schémas JSON des attributs exigés par type de produit | Product Listing ; Inventory and Order Tracking | NA, EU, FE | Formulaire de création de fiche |
| Product Pricing v2022-05-01 et v0 | Prix et offres concurrentes ; « designed to help you develop automated solutions that sellers can use to update and manage their prices » | Pricing (v0 aussi Product Listing) | NA, EU, FE | Tarification, Buy Box |
| Product Fees v0 | Estimation des frais avant fixation du prix | Pricing ; Product Listing | NA, EU, FE | Calculateur de revenus |
| Feeds v2021-06-30 | Envoi de données en masse (fiches, stocks, prix, commandes) | selon le type de flux | NA, EU, FE | Chargements de fichiers en masse |
| Reports v2021-06-30 | Rapports : stock, commandes, retours, frais, taxes… | selon le type de rapport | NA, EU, FE | Rapports |
| Orders v2026-01-01 (v0 « deprecated ») | Lire les commandes (`searchOrders`, `getOrder`) | plusieurs, dont Inventory and Order Tracking ; Direct-to-Consumer Shipping (Restricted) pour les données de livraison | NA, EU, FE | Gérer les commandes |
| Sales v1 | Indicateurs de commandes agrégés par période (`getOrderMetrics`) | plusieurs, dont Inventory and Order Tracking | NA, EU, FE | Tableau de bord des ventes |
| FBA Inventory v1 | Stock FBA par marketplace (disponible, réservé, en réception…) | Amazon Fulfillment ; Product Listing | NA, EU, FE | Gérer l'inventaire FBA |
| FBA Inbound Eligibility v1 | Aperçu d'éligibilité d'un article à l'envoi FBA | Amazon Fulfillment | NA, EU, FE | Contrôle avant envoi |
| Fulfillment Inbound v2024-03-20 | Créer et suivre les envois vers les entrepôts (plan, colisage, placement, transport, étiquettes) | Amazon Fulfillment | NA, EU, FE | Envoyer vers Amazon |
| Fulfillment Outbound v2026-07-04 (MCF) | Commandes Multi-Channel Fulfillment depuis le stock FBA | Amazon Fulfillment ; Product Listing | NA, EU, FE | Expédition multicanale |
| Amazon Warehousing and Distribution v2024-05-09 | Stock et envois AWD | AWD | **NA seulement** | AWD (hors Europe) |
| Finances v2024-06-19 (et v0) | Transactions, soldes, événements financiers sans attendre la clôture | Finance and Accounting | NA, EU, FE | Paiements, transactions |
| Finance Remittance v2026-03-17 | En-têtes et détails de versements | Finance and Accounting | NA, EU, FE | Relevés de versement |
| Transfers v2024-06-01 | Moyens de paiement, déclencher un virement (`initiatePayout`) | Finance and Accounting ; Payment Initiation Service Provider | NA, EU, FE | Demander un versement |
| Seller Wallet v2024-03-01 | Comptes Seller Wallet, soldes, transactions et virements programmés | AISP ; Payment Initiation Service Provider | NA, EU, FE | Seller Wallet |
| Sellers v1 | Compte vendeur et marketplaces ouvertes | AISP ; Finance and Accounting | EU (tableau) | Paramètres du compte |
| Notifications v1 | S'abonner aux événements (point 3) | selon le type | NA, EU, FE | Alertes |
| Messaging v1 | Messages au client par modèles autorisés | Buyer Communication (et autres) | NA, EU, FE | Messages acheteurs (envoi limité aux modèles) |
| Messaging Automations v2026-04-20 | Règles de réponse automatique aux messages clients | Buyer Communication | NA, EU, FE | Réponses automatiques |
| Solicitations v1 | Demande d'avis produit + évaluation vendeur | Buyer Solicitation ; Product Listing | NA, EU, FE | Bouton « Demander un avis » |
| Customer Feedback 2024-06-01 | Thèmes d'avis et de retours ; « the same information as the Product Opportunity Explorer (OX) » pour avis et retours | Brand Analytics ; Selling Partner Insights | US, ES, UK, **FR**, DE, IT, JP | Partie avis/retours d'Opportunity Explorer |
| Data Kiosk v2023-11-15 | Requêtes GraphQL ; « currently hosts Seller Sales and Traffic Data » | Brand Analytics | NA, EU, FE | Rapports ventes et trafic |
| Brand Analytics (rapports, via Reports) | `GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT`, `…SEARCH_TERMS…`, `…SEARCH_CATALOG_PERFORMANCE…`, `…MARKET_BASKET…`, `…REPEAT_PURCHASE…` ; « Sellers who have the Brand Analytics Selling Partner API role and are registered in Amazon Brand Registry » | Brand Analytics + **Brand Registry** | — | Brand Analytics, Search Query Performance (inaccessible à un revendeur sans marque) |
| A+ Content 2020-11-01 | Créer, modifier, soumettre du contenu A+ | Brand Analytics ; Product Listing | NA, EU, FE | Gestionnaire de contenu A+ (marques) |
| Promotions 2025-12-01 | Opérations `searchPromotions`, `getPromotion`, `getSelection` (deals, coupons, remises) | Pricing ; Product Listing | NA, EU, FE | Promotions, coupons, offres éclair : **lecture seulement** (aucune opération de création listée) |
| Replenishment v2022-11-07 | Indicateurs « Subscribe & Save » | Brand Analytics ; Inventory and Order Tracking | NA, EU, FE | Prévoyez et Économisez |
| Supply Sources v2020-07-01 | Gérer les sources d'approvisionnement (entrepôts, magasins) | Selling Partner Insights | NA, EU, FE | Paramètres d'expédition locale |
| Easy Ship v2022-03-23 | Programmer l'enlèvement Easy Ship | Direct-to-Consumer Shipping (Restricted) | Pays listés : MX, IN, TR, AU, SG, JP, NL, PL — **pas la France** | sans objet en FR |
| Merchant Fulfillment v0 | Acheter des étiquettes « Buy Shipping » pour les commandes expédiées par le vendeur | Direct-to-Consumer Shipping (Restricted) ; Buyer Communication | NA, EU, FE | Acheter l'expédition (FBM) |
| Shipping v2 | Tarifs, achat d'expédition, suivi, documents | Direct-to-Consumer Shipping (Restricted) ; Product Listing ; Amazon Logistics | NA, EU, FE | Acheter l'expédition (FBM) |
| Support v2025-02-01 | « list a selling partner's support cases, retrieve the details and status of a specific case, and review the full history of contacts » ; opérations `getCase`, `listCases`, `listContacts` | Selling Partner Support (Restricted) | NA, EU, FE | Journal des cas : **lecture seulement, pas d'ouverture de cas** |
| Action Items v2026-06-01 | Tâches et recommandations publiées par Amazon (lire, écarter) | Selling Partner Insights | NA, EU, FE | Tâches et recommandations du tableau de bord |
| Action Plans v2026-06-01 | Plans d'action à partir de modèles ; exemple `EXPAND_CROSS_STORE` (extension vers une autre boutique européenne) | Selling Partner Insights | NA, EU | Expansion internationale guidée |
| App Integrations v2024-04-01 | Afficher une notification de l'application dans Seller Central | Notifications in Seller Central | NA, EU, FE | Tableau des notifications Appstore |
| Uploads v2020-11-01 | Destination de téléversement (ex. fichiers pour A+ ou messages) | Product Listing | NA, EU, FE | Téléversement de fichiers |
| Tokens v2021-03-01 | Jeton pour lire les données personnelles (RDT) | plusieurs | NA, EU, FE | — (technique) |
| Vendor (Vendor Orders, Invoices, Shipments, Direct Fulfillment…) | Pour les fournisseurs Vendor Central | rôles vendeur | — | **hors sujet** (vendeur tiers) |
| Invoices v2024-06-19, Shipment Invoicing v0 | Factures fiscales | Tax Invoicing (Restricted) | **NA seulement** | hors Europe |
| Amazon Business | Pas d'API séparée dans la liste SP-API ; commandes B2B lues par l'API Orders (tutoriel « Get all Amazon Business orders ») ; rapports Amazon Business ; l'AUP 5.5 cite une « Amazon Business API » soumise à ses propres conditions | — | — | Amazon Business (prix B2B : non établi, voir annexe) |

Sources des lignes particulières (toutes VÉRIFIÉ) :
- Customer Feedback : https://developer-docs.amazon/sp-api/docs/customer-feedback-api.md
- Support : https://developer-docs.amazon/sp-api/docs/support-api.md
- Promotions : https://developer-docs.amazon/sp-api/docs/promotions-api.md (« search, retrieve, and manage promotions… monitor promotion status, review item selections, and identify validation issues ») et liste des opérations dans role-mappings.md
- Easy Ship : https://developer-docs.amazon/sp-api/docs/easy-ship-api.md (tableau des boutiques)
- Brand Analytics : https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md
- Action Items / Plans : https://developer-docs.amazon/sp-api/docs/action-items-api.md
- Amazon Business : https://developer-docs.amazon/sp-api/docs/get-all-amazon-business-orders.md
- Données « End User Data Report » (UE, dont la France) : https://developer-docs.amazon/sp-api/docs/amazon-seller-data-access.md

### 2.2 Fonctions Seller Central sans API trouvée

| Fonction | Ce qui a été trouvé | Statut |
|---|---|---|
| **Demande d'approbation de catégorie ou de marque** | `getListingsRestrictions` renvoie seulement un lien « Approval via Seller Central » ; aucune opération de demande dans la liste des API. | VÉRIFIÉ (absence dans role-mappings.md) |
| **Ouvrir un cas au support** (« Contacter le support vendeur ») | Support API = `getCase`, `listCases`, `listContacts` : lecture et historique seulement. | VÉRIFIÉ |
| **Product Opportunity Explorer** (niches, volumes de recherche) | Seule la partie avis/retours est couverte par Customer Feedback API. | VÉRIFIÉ (partiel) |
| **Publicité (Sponsored Products…)** | Hors SP-API : **API Amazon Ads séparée**, avec sa propre demande d'accès. https://advertising.amazon.com/about-api : « The Amazon Ads API enables you to manage the advertising resources associated with an Amazon advertiser using a REST API. » ; « requires an application and approval process before access is granted. » ; « There are no additional fees from Amazon Ads to use the API. » | VÉRIFIÉ |
| **Créer une promotion, un coupon, une offre éclair** | Promotions API : recherche et lecture seulement. | VÉRIFIÉ (liste des opérations) |
| **Brand Analytics / Search Query Performance** | Existe par API, mais réservé aux vendeurs inscrits au Brand Registry : inaccessible pour un revendeur sans marque. | VÉRIFIÉ |
| **Réclamations FBA (stock perdu ou endommagé), contestations, appel de santé du compte (plan d'action)** | Lecture seulement : rapport `GET_FBA_REIMBURSEMENTS_DATA` (« itemized details of a seller's inventory reimbursements »), notification `ACCOUNT_STATUS_CHANGED` ; aucune opération de dépôt de réclamation ou d'appel trouvée. | VÉRIFIÉ (lecture) ; absence d'API de dépôt = résultat de recherche dans l'index https://developer-docs.amazon/sp-api/llms.txt |
| **Ordres de retrait FBA (création)** | Rapports de retrait seulement (`GET_FBA_FULFILLMENT_REMOVAL_ORDER_DETAIL_DATA`, `GET_FBA_RECOMMENDED_REMOVAL_DATA`) ; création non trouvée. | VÉRIFIÉ (rapports) ; création : NON VÉRIFIÉ |
| **Inscription / paramètres du compte, Brand Registry, Vine, Manage Your Experiments** | Aucune API trouvée dans la liste. | VÉRIFIÉ (absence dans sp-api-models.md) |
| **Easy Ship en France** | Pays non listé. | VÉRIFIÉ |

---

## 3. Notifications en temps réel

Source principale : https://developer-docs.amazon/sp-api/docs/notification-type-values.md (VÉRIFIÉ) ; rôles et régions : https://developer-docs.amazon/sp-api/docs/role-mappings-for-types.md (VÉRIFIÉ). Deux modes de livraison : file **Amazon SQS** ou **Amazon EventBridge**, selon le type (« Workflow » indiqué pour chacun). Il faut un compte AWS et une file SQS à laquelle la SP-API a le droit d'écrire (https://developer-docs.amazon/sp-api/docs/set-up-notifications-with-amazon-sqs.md). Amazon recommande une solution de secours : « we recommend that you have a means to retrieve needed information in the event of an unexpected outage or delay in notification delivery » (https://developer-docs.amazon/sp-api/docs/notifications-api.md).

| Type | Ce qui déclenche | Mode | Région EU | Rôle | Utilité pour le pilotage (analyse) |
|---|---|---|---|---|---|
| `ANY_OFFER_CHANGED` | Changement dans les 20 premières offres, du prix externe, du gagnant ou du prix de la Buy Box ; « only … for items for which you have active offers » | SQS | EU\* | Pricing | Réajuster le prix (repricer) |
| `PRICING_HEALTH` | Offre inéligible à l'offre vedette pour prix non compétitif | SQS | EU\* | Pricing | Alerte Buy Box perdue |
| `B2B_ANY_OFFER_CHANGED` | Changement des meilleures offres B2B | SQS | EU | Pricing | Prix Amazon Business |
| `FBA_INVENTORY_AVAILABILITY_CHANGES` | Changement de stock FBA (instantané de toutes les boutiques de la région) | SQS | EU | Amazon Fulfillment | Réassort, rupture |
| `ORDER_CHANGE` | Changement important de commande (statut, annulation demandée) | SQS | EU | Amazon Fulfillment ; Inventory and Order Tracking ; DTC Shipping (R) | Suivi des ventes |
| `REPORT_PROCESSING_FINISHED` | Rapport terminé (`DONE`, `CANCELLED`, `FATAL`) | SQS | EU\* | selon rapport | Enchaîner sans interroger en boucle |
| `FEED_PROCESSING_FINISHED` | Flux terminé | SQS | EU\* | selon flux | Confirmer une mise à jour en masse |
| `LISTINGS_ITEM_STATUS_CHANGE` | Fiche créée, supprimée ou achetabilité modifiée | **EventBridge** | EU | Product Listing | Fiche bloquée |
| `LISTINGS_ITEM_ISSUES_CHANGE` | Problème de fiche créé, corrigé ou modifié (dont suppression de la recherche) | **EventBridge** | EU | Product Listing | Corriger une fiche |
| `LISTINGS_ITEM_MFN_QUANTITY_CHANGE` | Quantité FBM modifiée | **EventBridge** | EU | Product Listing | — (FBA surtout) |
| `ACCOUNT_STATUS_CHANGED` | Compte entre `NORMAL`, `AT_RISK`, `DEACTIVATED` | SQS | EU | Selling Partner Insights | Alerte santé du compte |
| `FEE_PROMOTION` | Promotion temporaire sur les frais | SQS | EU | Finance and Accounting ; Product Listing | Profiter d'une baisse de frais |
| `TRANSACTION_UPDATE` | Nouvelle transaction sur le compte | SQS | non indiqué dans role-mappings-for-types | non indiqué | Rapprochement financier |
| `FULFILLMENT_ORDER_STATUS` | Statut des commandes MCF | SQS | EU\* | Amazon Fulfillment | MCF |
| `DETAIL_PAGE_TRAFFIC_EVENT`, `ITEM_SALES_EVENT_CHANGE`, `ITEM_INVENTORY_EVENT_CHANGE` | Trafic, ventes, stock par ASIN, chaque heure | SQS | EU | **Brand Analytics** | Probablement inaccessible sans marque (à vérifier) |
| `BRANDED_ITEM_CONTENT_CHANGE`, `ITEM_PRODUCT_TYPE_CHANGE` | Modification du contenu ou du type de produit d'un ASIN de marque | EventBridge | EU | Product Listing (et Pricing) | Réservé aux relations de marque |
| `PRODUCT_TYPE_DEFINITIONS_CHANGE` | Nouveau type de produit ou nouvelle version | EventBridge | EU | Product Listing | Mettre à jour les formulaires |
| `DATA_KIOSK_QUERY_PROCESSING_FINISHED` | Requête Data Kiosk terminée | non relevé | EU | Brand Analytics ; AWD | — |
| Hors Europe | `FBA_OUTBOUND_SHIPMENT_STATUS` (Brésil seulement), `TAX_INVOICE_*` (Brésil et Mexique, région NA), `SHIPMENT_TRACKING_MILESTONE_CHANGED` (US seulement) | — | **non** | — | — |

\* = « Functionality might not be entirely available in this region. » (role-mappings-for-types.md, VÉRIFIÉ).

Filtrage : plusieurs types acceptent `eventFilter` (ex. `marketplaceIds` pour `ANY_OFFER_CHANGED`, `orderChangeTypes` pour `ORDER_CHANGE`) ou des expressions CEL `filterExpression` (VÉRIFIÉ, même page).

---

## 4. Ce que disent l'AUP et la DPP sur l'automatisation

Sources (VÉRIFIÉ) : liste officielle https://developer-docs.amazon/sp-api/docs/policies-and-agreements.md ; texte anglais (« definitive legal version ») lu à https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_GB et https://sellercentral.amazon.com/mws/static/policy?documentType=DPP&locale=en_GB (version française : `locale=fr_FR`).

**Aucune interdiction générale de l'automatisation n'a été trouvée.** L'automatisation des prix est même présentée comme un usage prévu :
- https://developer-docs.amazon/sp-api/docs/pricing-faq.md : « The Product Pricing API enables apps to automate updating and managing prices on behalf of sellers » ; « One of the key benefits of the Product Pricing API is its ability to support the development of repricers. » (VÉRIFIÉ)

**Limites qui s'appliquent à une automatisation (AUP, VÉRIFIÉ, extraits)**
- 1.1 : « Use the Amazon Services API only to perform acceptable Amazon activities and only for Authorised Users who have authorised you… »
- 1.2 : « Do not facilitate or promote violation of any agreement between Authorised Users and Amazon (such as the Amazon Services Business Solutions Agreement)… » → une action automatique doit respecter les règles vendeur (prix, avis, messages).
- 2.4 : « Be explicit about any calculations and the use of models such as artificial intelligence in the service you provide, their accuracy and data freshness. »
- 2.8 : « Identify and mitigate any negative Authorised User impact before launching new features, especially for business-critical tasks. »
- 2.9 : « Design your Application to respect per-Authorised User throttling quotas… »
- 2.10 : « Implement data integrity and validation checks within your Application for any analytical processing (e.g. AI models for insights, automated decision-making) that has material impact on an Authorised User's business. »
- 2.11 : soumissions et communications « accurate, policy-compliant and do not result in frivolous or non-compliant contacts or degradation of Amazon support systems. »
- 3.3 et 3.6 : ne pas demander les identifiants Seller Central ; « Do not ask Authorised Users to share information retrieved from Amazon Portals manually or programmatically to circumvent Amazon policies. »
- 3.7 : si un accès au portail est nécessaire, passer par les « secondary user permissions ».
- 3.10 : « Do not attempt to circumvent throttling quotas through the creation of multiple Solution Provider accounts or applications. »
- 4.1 : données personnelles des clients seulement pour l'expédition par le vendeur ou les obligations légales.
- 4.3 : « Do not use, offer or promote external (non-Amazon) data services that vend Information or data retrieved from Amazon's websites. »
- 4.4 : « Do not aggregate data across Authorised User's businesses or Customers obtained through the Amazon Services API to provide or sell to any parties, including competing Authorised Users. »
- 5.1 et 5.2 : la messagerie acheteur suit les « Communication Guidelines » (dont France) et les modèles approuvés.

**DPP (VÉRIFIÉ)** : exigences de sécurité pour tout système qui traite des données de la SP-API (« applicable to all systems that store, process or otherwise handle data vended and retrieved from the Amazon Services API ») ; aucune règle propre aux actions automatiques n'a été trouvée dans le texte lu (recherche des mots « automat », « price », « bot »).

**Analyse.** L'AUP 2.10 et 2.8 vont dans le sens de la validation humaine voulue par Sam : contrôles de cohérence avant toute action qui engage le compte (prix, envoi FBA, message), journal des décisions, plafonds. Les règles de tarification propres à la marketplace (prix équitables, etc.) n'ont pas été lues ici : à vérifier avant d'automatiser les prix.

---

## Tableau final : Fonction Seller Central → API → déjà dans Syllig Pilot ?

| Fonction Seller Central / app Amazon Seller | API (opérations) | Déjà dans Syllig Pilot ? |
|---|---|---|
| Scanner un code-barres (app) | navigateur : `getUserMedia` + `BarcodeDetector` (ou bibliothèque) ; puis `searchCatalogItems` (EAN/UPC) | |
| Voir offres, prix Buy Box, nombre de vendeurs | Product Pricing `getItemOffers`, `getItemOffersBatch`, `getCompetitiveSummary` | |
| Prix attendu pour l'offre vedette | Product Pricing `getFeaturedOfferExpectedPriceBatch` | |
| Calculer les frais / la rentabilité | Product Fees `getMyFeesEstimateForASIN`, `getMyFeesEstimates` | |
| Vérifier si je peux vendre (éligibilité) | Listings Restrictions `getListingsRestrictions` | |
| Demander l'approbation catégorie / marque | **aucune API** (lien vers Seller Central) | |
| Créer une offre sur un ASIN existant / une fiche | Listings Items `putListingsItem` + Product Type Definitions | |
| Modifier prix, quantité, attributs | Listings Items `patchListingsItem` ; Feeds (`JSON_LISTINGS_FEED`) | |
| Gérer l'inventaire (liste des offres) | Listings Items `searchListingsItems` ; Reports | |
| Problèmes de fiches / fiches supprimées | `LISTINGS_ITEM_ISSUES_CHANGE`, `LISTINGS_ITEM_STATUS_CHANGE` ; `getListingsItem` | |
| Stock FBA | FBA Inventory `getInventorySummaries` ; `FBA_INVENTORY_AVAILABILITY_CHANGES` | |
| Créer un envoi vers Amazon (FBA) | Fulfillment Inbound v2024-03-20 | |
| Éligibilité d'un article à FBA | FBA Inbound Eligibility `getItemEligibilityPreview` | |
| Commandes | Orders v2026-01-01 `searchOrders`, `getOrder` ; `ORDER_CHANGE` | |
| Ventes (tableau de bord) | Sales `getOrderMetrics` ; Data Kiosk (ventes et trafic) | |
| Paiements, transactions, versements | Finances v2024-06-19 ; Finance Remittance ; Transfers ; `TRANSACTION_UPDATE` | |
| Rapports (stock, retours, frais, remboursements FBA) | Reports `createReport` (ex. `GET_FBA_REIMBURSEMENTS_DATA`) | |
| Réclamation FBA (stock perdu) | **aucune API de dépôt trouvée** (rapport en lecture) | |
| Ordre de retrait FBA | rapports seulement ; création non trouvée | |
| Expédition multicanale | Fulfillment Outbound v2026-07-04 | |
| Acheter une étiquette (FBM) | Merchant Fulfillment v0 ; Shipping v2 | |
| Messages acheteurs | Messaging v1 ; Messaging Automations v2026-04-20 | |
| Demander un avis | Solicitations `createProductReviewAndSellerFeedbackSolicitation` | |
| Santé du compte | `ACCOUNT_STATUS_CHANGED` ; Action Items ; appel : **aucune API** | |
| Tâches et recommandations Amazon | Action Items, Action Plans | |
| Cas au support (consulter) | Support `listCases`, `getCase`, `listContacts` | |
| Cas au support (ouvrir) | **aucune API** | |
| Promotions, coupons (consulter) | Promotions `searchPromotions`, `getPromotion` | |
| Promotions, coupons (créer) | **aucune API trouvée** | |
| Product Opportunity Explorer | **aucune API** (sauf avis/retours : Customer Feedback) | |
| Brand Analytics / Search Query Performance | Reports `GET_BRAND_ANALYTICS_*` (Brand Registry requis) | |
| Contenu A+ | A+ Content (marques) | |
| Publicités | **hors SP-API** : API Amazon Ads (accès séparé) | |
| Prévoyez et Économisez | Replenishment | |
| Seller Wallet | Seller Wallet v2024-03-01 | |
| Compte, marketplaces ouvertes | Sellers `getMarketplaceParticipations` | |
| Afficher une alerte Syllig dans Seller Central | App Integrations `createNotification` | |

---

## Annexe : non vérifié

- **Pays où le scan de l'application Amazon Seller fonctionne** (et en particulier en France) : aucune page officielle trouvée. Un guide tiers (sellerengine.com, 2022) cite 8 marketplaces dont la France : source non officielle, non retenue.
- **Ce qu'affiche exactement le scan en Europe** (éligibilité et frais) : seulement un message de forum signé « Connor_Amazon », statut non confirmé.
- **Bibliothèques JavaScript de décodage** pour iPhone (secours à `BarcodeDetector`) : non recherchées sur source officielle.
- **Prix B2B (Amazon Business) par API** : non établi (la mention « Amazon Business API » dans l'AUP 5.5 n'a pas été suivie).
- **Notifications Brand Analytics** (`DETAIL_PAGE_TRAFFIC_EVENT`, `ITEM_SALES_EVENT_CHANGE`…) sans Brand Registry : la page dit « Sellers and vendors can subscribe », le rôle Brand Analytics est requis ; l'accès réel d'un revendeur sans marque n'est pas établi.
- **Création d'ordres de retrait FBA par API**, **dépôt de réclamations FBA** : non trouvés dans l'index ; une absence de résultat n'est pas une preuve d'absence.
- **Règles de prix de la marketplace** (politique de prix équitables) et **Business Solutions Agreement** : non lus ; à lire avant d'automatiser les prix.
- **Modèles GitHub** `amzn/selling-partner-api-models` : non lus (HTTP 403 depuis cet environnement).
- **Accès d'un vendeur à l'API Amazon Ads pour son propre compte** : la page parle d'« advertisers » (« Request registration to access the Amazon Ads API on behalf of your own advertising account ») ; conditions détaillées non lues.
