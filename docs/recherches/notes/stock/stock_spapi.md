# Stock & réappro — sources SP-API (vérification au 12/11/2026)

Protocole : « VÉRIFIÉ » = lu le 12/11/2026 sur la documentation officielle Amazon (developer-docs.amazon, pages
markdown listées par https://developer-docs.amazon/sp-api/llms.txt ; ou schéma officiel du dépôt GitHub `amzn/selling-partner-api-models`).
URL exacte + citation courte. Tout le reste est en section « NON VÉRIFIÉ ».
Dates de mise à jour des pages lues : 09/09/2026 (FBA Inventory), 10/09/2026 (Sales), 30/09/2026 (Seller Analytics).

## 0. En bref

- **Stock courant par SKU et place de marché** : `getInventorySummaries` (FBA Inventory **v1**, seule version, aucune
  dépréciation listée), `details=true`, `granularityType=Marketplace`, 1 place de marché par appel, 2 req/s, pagination `nextToken` (expire 30 s).
- **Réappro, couverture, âge, risque stockage longue durée, frais de niveau de stock bas** : rapport
  `GET_FBA_INVENTORY_PLANNING_DATA` (« FBA Manage Inventory Health ») — le plus riche ; disponible FR/DE/IT/ES/UK/US
  (exclu NL, PL, SE, BE). Il expose **deux drapeaux** sur les frais de niveau de stock bas, **pas de montant**.
- **Reco Amazon de réassort** : `GET_RESTOCK_INVENTORY_RECOMMENDATIONS_REPORT` (toutes boutiques sauf IN).
- **Ventes par SKU et par jour** : **Data Kiosk, jeu `analytics_sellerAnalytics_2025_03_31`** (`aggregateBy: DAY`,
  `groupByKey { msku }`, `unitsOrdered`/`unitsShipped`), données prêtes à J+2 10 h locale. Alternative :
  `getOrderMetrics` (1 appel par SKU, 0,5 req/s → lent) ou `GET_SALES_AND_TRAFFIC_REPORT` (par SKU **sans date** : 1 rapport par jour).
- **Limites de capacité FBA** : **aucune opération SP-API trouvée**. Seul indice : `GET_FBA_OVERAGE_FEE_CHARGES_DATA`
  (colonne `storage_limit_volume`, a posteriori, lorsqu'il y a dépassement facturé).

## 1. Tableau besoin → source

| Besoin écran | Endpoint / rapport | Champs utiles | Limites | Rôle | Vérifié (URL + citation) |
|---|---|---|---|---|---|
| Disponible | `GET /fba/inventory/v1/summaries` (`getInventorySummaries`), `details=true` | `inventoryDetails.fulfillableQuantity` | 2 req/s, burst 2 ; `marketplaceIds` maxItems 1 | Amazon Fulfillment **ou** Product Listing (au moins un) | https://developer-docs.amazon/sp-api/reference/getinventorysummaries.md — « fulfillableQuantity … The item quantity that can be picked, packed, and shipped. » ; « \| 2 \| 2 \| » |
| En route / réception | idem | `inboundWorkingQuantity`, `inboundShippedQuantity`, `inboundReceivingQuantity` | **changements non détectés par `startDateTime`** | idem | même URL — « Note: Changes in inboundWorkingQuantity, inboundShippedQuantity and inboundReceivingQuantity are not detected. » |
| Réservé | idem | `reservedQuantity.totalReservedQuantity`, `pendingCustomerOrderQuantity`, `pendingTransshipmentQuantity`, `fcProcessingQuantity` | — | idem | même URL — « pendingTransshipmentQuantity … The number of units being transferred from one fulfillment center to another. » |
| Invendable / en recherche | idem | `unfulfillableQuantity.total…` (+ customer/warehouse/distributor/carrierDamaged, defective, expired) ; `researchingQuantity.totalResearchingQuantity` + `researchingQuantityBreakdown` | — | idem | même URL — « totalUnfulfillableQuantity … in unsellable condition. » |
| Identité ligne | idem | `asin`, `fnSku`, `sellerSku`, `condition`, `productName`, `totalQuantity`, `lastUpdatedTime`, `stores` | — | idem | même URL (schéma `InventorySummary`) |
| Stock (alternative fichier) | `GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA` / `GET_FBA_MYI_ALL_INVENTORY_DATA` (incl. archivés) | `afn-fulfillable-quantity`, `afn-reserved-quantity`, `afn-unsellable-quantity`, `afn-inbound-working/shipped/receiving-quantity`, `afn-researching-quantity`, `afn-fc-transfer-quantity`, `per-unit-volume`… | « near real-time » ; à la demande seulement | Pricing, Amazon Fulfillment | https://developer-docs.amazon/sp-api/docs/report-type-values-fba.md — « Contains current details of all (including archived) inventory including condition, quantity, and volume. Content updated in near real-time. » |
| Stock physique par pays (EU) | `GET_AFN_INVENTORY_DATA_BY_COUNTRY` | `country`, `quantity-for-local-fulfillment` | EU seulement ; à la demande | Pricing, Amazon Fulfillment | même URL — « Contains quantity available for local fulfillment by country, helping Multi-Country Inventory sellers in Europe track their FBA inventory. » |
| Ventes 7/30/60/90 j, jours de couverture, qté recommandée, âge, stockage | `GET_FBA_INVENTORY_PLANNING_DATA` | `units-shipped-t7/t30/t60/t90`, `days-of-supply`, `weeks-of-cover-t30/t90`, `historical-days-of-supply`, `Short/Long term historical days of supply`, `Recommended ship-in quantity`, `Recommended ship-in date`, `inv-age-0-to-30…`, `inv-age-181-to-330-days`, `inv-age-331-to-365-days`, `inv-age-366-to-455-days`, `inv-age-456-plus-days` (US/DE/UK/FR/IT/ES), `estimated-storage-cost-next-month`, `quantity-to-be-charged-ais-*` / `estimated-ais-*` (surtaxe âge), `estimated-excess-quantity`, `recommended-action`, `recommended-removal-quantity`, `inbound-working/shipped/received`, `Total Reserved Quantity`, `unfulfillable-quantity`, `is-seasonal-in-next-3-months`… | à la demande seulement ; non disponible NL, PL, SE, BE ; attributs variables par boutique ; `healthy-inventory-level` déprécié | Amazon Fulfillment | même URL — « Provides a consolidated view across your sales (7, 30, 60, and 90 days), shipment statuses (working, received, and shipped), estimated storage and long-term storage fees, and aged and excess units. … Not available in the NL, PL, SE, or BE stores. » |
| Frais niveau de stock bas | `GET_FBA_INVENTORY_PLANNING_DATA` | `fba-minimum-inventory-level`, `fba-inventory-level-health-status`, `Exempted from Low-Inventory-Level fee?`, `Low-Inventory-Level fee applied in current week?` | drapeaux, **pas de montant** | Amazon Fulfillment | même URL — attributs listés : « Exempted from Low-Inventory-Level fee? », « Low-Inventory-Level fee applied in current week? » |
| Reco réassort Amazon | `GET_RESTOCK_INVENTORY_RECOMMENDATIONS_REPORT` | `Country`, `Merchant SKU`, `ASIN`, `Units Sold Last 30 Days`, `Available`, `Inbound`, `Working/Shipped/Receiving`, `FC transfer`, `FC Processing`, `Customer Order`, `Unfulfillable`, `Total Days of Supply` (avec envois ouverts), `Days of Supply at Amazon Fulfillment Network`, `Alert`, `Recommended replenishment qty`, `Recommended ship date`, `Recommended action` (US seulement), `Unit storage size` | toutes boutiques sauf IN ; à la demande ; « near real-time » | Pricing, Amazon Fulfillment | même URL — « Provides recommendations on products to restock, suggested order quantities, and reorder dates. Content updated in near real-time. » ; « All stores except India (IN) » |
| Mouvements / réconciliation | `GET_LEDGER_SUMMARY_VIEW_DATA` | `Date`, `MSKU`, `Disposition`, `Starting/Ending Warehouse Balance`, `Receipts`, `Customer Shipments`, `Customer Returns`, `In Transit Between Warehouses`, `Lost`, `Found`, `Damaged`, `Disposed`, `Location`… | options `aggregateByLocation` (COUNTRY/FC), `aggregatedByTimePeriod` (DAILY/WEEKLY/MONTHLY, défaut MONTHLY) ; dates mal calées → rapport vide | Amazon Fulfillment | même URL — « The Inventory Ledger Report is like a bank statement of your inventory. » ; « If aggregatedByTimePeriod is set as DAILY, Ledger Summary View will return data aggregated at the end of day. » |
| Détail mouvements (18 mois) | `GET_LEDGER_DETAIL_VIEW_DATA` | `Event Type`, `Quantity`, `Fulfillment Center`, `Country`, `Reason`… | option `eventType` | Amazon Fulfillment | même URL — « You can view all historical movements of your inventory for 18 months in this report. » |
| Frais stockage mensuels estimés | `GET_FBA_STORAGE_FEE_CHARGES_DATA` | `asin`, `fnsku`, `country_code`, `fulfillment_center`, `average_quantity_on_hand`, `storage_rate`, `storage_utilization_ratio`, `utilization_surcharge_rate`, `estimated_monthly_storage_fee`, `product_size_tier`, `month_of_charge` | demande **ou planification** ; **par ASIN, pas par SKU** | Pricing, Amazon Fulfillment | même URL — « Contains estimated monthly inventory storage fees for each ASIN … » ; « This report can be requested or scheduled. » |
| Frais stockage longue durée facturés | `GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA` | `sku`, `qty-charged`, `amount-charged`, `surcharge-age-tier`, `rate-surcharge`, `country` | intervalle = 1 mois | Pricing, Amazon Fulfillment | même URL — « the time between the dataStartTime and the dateEndTime … should be equal to one month. » |
| Dépassement de capacité (a posteriori) | `GET_FBA_OVERAGE_FEE_CHARGES_DATA` | `country_code`, `storage_type`, `storage_usage_volume`, `storage_limit_volume`, `overage_volume`, `charged_fee_amount` | à la demande | Amazon Fulfillment | même URL — « Estimated inventory storage overage fees for each storage type of your inventory … that exceeds your storage limits. » |
| Réservé (détail) | `GET_RESERVED_INVENTORY_DATA` | `reserved_qty`, `reserved_customerorders`, `reserved_fc-processing`, `reserved_staging` (US, CA, JP, UK, DE, FR, IT, ES) | near real-time | Pricing, Amazon Fulfillment | même URL |
| Ventes / jour / SKU (recommandé) | Data Kiosk `createQuery`, jeu `analytics_sellerAnalytics_2025_03_31`, vue `sellerAnalyticsView` | `aggregateBy: DAY`, `groupByKey { msku asin marketplaceId fulfillmentChannel }`, `sales { unitsOrdered unitsShipped orderedProductSales }` | `createQuery` 0,0167 req/s, burst 15 ; ≤ 2 ans ; boutiques d'une même région par requête ; données prêtes ~34 h (J+2, 10 h locale) ; sortie JSONL | Brand Analytics (Data Kiosk) + accès « Sales and traffic » | https://developer-docs.amazon/sp-api/docs/seller-analytics-dataset-guide.md — « this dataset allows you to aggregate data at date, ASIN, MSKU, brand, and other granularities in the same query. » ; « Data for a given day is generally available at 10 AM local time two days later. » ; https://developer-docs.amazon/sp-api/reference/createquery.md — « \| 0.0167 \| 15 \| » |
| Ventes agrégées (contrôle) | Sales v1 `getOrderMetrics` | `unitCount`, `orderItemCount`, `orderCount`, `averageUnitPrice`, `totalSales` par intervalle ; filtres `sku` **ou** `asin`, `fulfillmentNetwork=AFN`, `granularity=Day` + `granularityTimeZone` | 0,5 req/s, burst 15 ; 1 place de marché ; **1 SKU par appel** ; ≤ 2 ans | Inventory and Order Tracking ou Product Listing (NA/EU) | https://developer-docs.amazon/sp-api/reference/getordermetrics.md — « Returns aggregated order metrics for given interval, broken down by granularity, for given buyer type. » ; « \| .5 \| 15 \| » ; https://developer-docs.amazon/sp-api/docs/sales-api.md (table des rôles) |
| Ventes par SKU (rapport) | `GET_SALES_AND_TRAFFIC_REPORT`, `asinGranularity=SKU` | `salesByAsin.unitsOrdered`… | 3 demandes / 5 min ; **la partie par ASIN/SKU n'a pas de date** → 1 rapport par jour voulu | Brand Analytics | https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md — « You can request this report up to three times every five minutes. » ; schéma https://raw.githubusercontent.com/amzn/selling-partner-api-models/main/schemas/reports/sellerSalesAndTrafficReport.json — `SalesAndTrafficByAsin` = `parentAsin, childAsin, sku, salesByAsin, trafficByAsin` (aucun champ date) |
| Changements de stock en continu | Notification `FBA_INVENTORY_AVAILABILITY_CHANGES` (SQS) | `SKU`, `FNSKU`, `ASIN`, `FulfillmentInventoryByMarketplace[]` (`Fulfillable`, `Unfulfillable`, `Researching`, `InboundQuantityBreakdown` Working/Shipped/Receiving, `ReservedQuantityBreakdown`…) | — | (non relevé) | https://developer-docs.amazon/sp-api/docs/notification-type-values.md — « sent whenever there is a change in the Fulfillment By Amazon (FBA) inventory quantities. This notification includes a snapshot of the FBA inventory in all eligible Amazon stores in a particular region. » |

## 2. Détails vérifiés

### 2.1 FBA Inventory API (`getInventorySummaries`)
Source : https://developer-docs.amazon/sp-api/docs/fba-inventory-api.md et https://developer-docs.amazon/sp-api/reference/getinventorysummaries.md
- Version : **v1**, « Legacy versions: None », « Sellers only », bac à sable dynamique. Régions NA, EU, FE. « This API is available in all marketplaces. »
- Granularité : enum **`Marketplace` uniquement** ; « if you use Marketplace granularity, the fulfillable quantity will reflect inventory that could be fulfilled in the given marketplace. » La page ne mentionne **pas** de granularité « Pan-European ».
- Trois modes : tout (sans filtre), changements depuis `startDateTime` (≤ 18 mois ; `sellerSkus` alors ignoré ; « use both startDateTime and nextToken to get the next page »), liste `sellerSkus` (≤ 50).
- `details=false` par défaut → **mettre `details=true`** sinon pas d'`inventoryDetails` : « This object will not appear if the details parameter in the request is false. »
- `nextToken` : « The string token will expire 30 seconds after being created. »
- Dépréciation : aucune ligne FBA Inventory dans https://developer-docs.amazon/sp-api/docs/sp-api-deprecations.md (lu le 12/11/2026).

### 2.2 Rapports
Source : https://developer-docs.amazon/sp-api/docs/report-type-values-fba.md
- Fréquence de régénération : « A near real-time FBA report is generated no more than once every 30 minutes » ; « A daily FBA report is generated no more than once every four hours ». La page ne dit pas dans quelle catégorie est `GET_FBA_INVENTORY_PLANNING_DATA`.
- Toutes les sources ci-dessus sont des fichiers TSV « can only be requested », sauf `GET_FBA_STORAGE_FEE_CHARGES_DATA` (demande ou planification).
- **Rapport de vieillissement** : l'ancien `GET_FBA_INVENTORY_AGED_DATA` est **supprimé** (déprécié le 31/03/2022, retiré le 27/06/2022, avec `GET_EXCESS_INVENTORY_DATA` et `GET_FBA_FULFILLMENT_INVENTORY_HEALTH_DATA`) — https://developer-docs.amazon/sp-api/docs/sp-api-deprecations.md. L'âge se lit donc dans `GET_FBA_INVENTORY_PLANNING_DATA`.
- Autres rapports retirés à ne pas utiliser : `GET_FBA_FULFILLMENT_CURRENT_INVENTORY_DATA`, `…_INVENTORY_ADJUSTMENTS_DATA`, `…_INVENTORY_RECEIPTS_DATA`, `…_INVENTORY_SUMMARY_DATA`, `…_MONTHLY_INVENTORY_DATA`, `GET_FBA_RECONCILIATION_REPORT_DATA` (retirés 31/01/2023) → remplacés en pratique par le Ledger.
- Reports API : `createReport` 0,0167 req/s burst 15 ; `getReport` 2 req/s burst 15 ; `getReportDocument` 0,0167 req/s burst 15 ; `getReports` 0,0222 req/s burst 10 ; URL du document « expires after 5 minutes » ; « Reports are retained for a maximum of 90 days » (https://developer-docs.amazon/sp-api/reference/createreport.md, getreport.md, getreportdocument.md, getreports.md).
- `marketplaceIds` de `createReport` : « The report document's contents will contain data for all of the specified marketplaces, unless the report type indicates otherwise. »

### 2.3 Capacité FBA
- Recherche dans l'index complet (`llms.txt`) des termes capacity / storage limit / inventory limit : seuls résultats = services (créneaux) et AWD, **rien pour la capacité FBA**.
- FBA Inbound Eligibility v1 (`getItemEligibilityPreview`, 1 req/s burst 1) : éligibilité d'un article à l'envoi (codes FBA_INB_0004…0465 : dimensions, matières dangereuses, catalogue, code-barres…). **Aucun code lié à la capacité** — https://developer-docs.amazon/sp-api/reference/getitemeligibilitypreview.md.
- Seul signal : `GET_FBA_OVERAGE_FEE_CHARGES_DATA` (`storage_limit_volume`, `storage_usage_volume`) — uniquement en cas de dépassement facturé.

### 2.4 Vitesse de vente — comparaison
- **Data Kiosk Seller Analytics (retenu)** : 1 requête par région et par nuit donne unités/jour/MSKU pour toutes les boutiques de la région. Attention : « read a null in a grouped row as "this metric is not available at this granularity" rather than as "this metric was zero" ». Le jeu `analytics_salesAndTraffic_2023_11_15` est **retiré** (27/03/2026) — ne pas l'utiliser.
- `getOrderMetrics` : bon pour un contrôle global (sans filtre SKU, `fulfillmentNetwork=AFN`) ; par SKU il faut 1 appel par SKU et par boutique (0,5 req/s → 500 SKU × 6 boutiques ≈ 100 min).
- `GET_SALES_AND_TRAFFIC_REPORT` : pas de date dans la section par SKU → 1 rapport par jour ; 3 demandes / 5 min.
- `GET_FBA_INVENTORY_PLANNING_DATA` donne déjà `units-shipped-t7/t30/t60/t90` (unités **expédiées**, pas commandées) : suffisant pour un premier écran sans historique journalier.
- Finances (transactions) : non étudié ici ; source moins directe pour des unités.

## 3. NON VÉRIFIÉ

- **Comportement Pan-EU de `getInventorySummaries`** : la doc dit seulement « inventory that could be fulfilled in the given marketplace ». Qu'une même unité stockée en DE apparaisse dans FR, IT, ES (donc qu'il ne faille **pas additionner** les places de marché EU) est probable mais **non écrit** dans les pages lues. À tester sur un compte réel ; pour le stock physique par pays, utiliser `GET_AFN_INVENTORY_DATA_BY_COUNTRY` ou le Ledger `aggregateByLocation=COUNTRY`.
- UK : présent dans les listes de boutiques des rapports (UK cité pour `reserved_staging`, `inv-age-366…`), mais la région de rattachement (EU) et le comportement Pan-EU/UK n'ont pas été relus ici.
- **Montant** des frais de niveau de stock bas par SKU : aucune colonne de montant trouvée dans les rapports lus (seulement les deux drapeaux). Possible dans les transactions financières (type de frais) : non vérifié.
- **Limites de capacité FBA** (plafond par type de stockage, mensuel) : aucune opération ni rapport SP-API trouvé. Pages d'aide Seller Central essayées (sellercentral.amazon.com et sellercentral-europe.amazon.com, /help/hub/reference/external/…) : réponse = page générique « Amazon » sans contenu (connexion requise) → illisibles.
- Barème et règles des frais (stockage, surtaxe d'âge, niveau de stock bas) : aide Seller Central non lisible sans connexion → non vérifié ; ne rien coder en dur.
- Rôle exigé pour la notification `FBA_INVENTORY_AVAILABILITY_CHANGES` : non relevé.
- Catégorie « near real-time » ou « daily » de `GET_FBA_INVENTORY_PLANNING_DATA` et `GET_LEDGER_SUMMARY_VIEW_DATA` : non indiquée.
- Rôle « Brand Analytics » : la page des rôles dit « Role available to sellers? Yes » mais ne dit pas s'il exige le Registre des marques ; à confirmer à l'inscription de l'application.

## 4. Synchro de nuit proposée (heures de Paris)

Par compte vendeur, par région (EU = FR, DE, IT, ES, UK ; NA = US). Tout est idempotent : chaque exécution écrit un
**instantané daté** `(compte, place de marché, SKU, date_instantané)` en « upsert » ; relancer la même nuit remplace, ne duplique pas.

1. **02:00 — Stock** : pour chaque place de marché, `getInventorySummaries` (`details=true`, `granularityType=Marketplace`,
   `granularityId=marketplaceId`), boucle `nextToken` immédiate (< 30 s), pause ≥ 0,5 s entre pages (2 req/s). Pas de
   `startDateTime` la nuit (il rate les changements inbound) : instantané complet. Clé : `sellerSku` + `condition`.
2. **02:10 — Rapports** (une file, `createReport` ≤ 1/min en régime établi, burst 15) :
   - `GET_FBA_INVENTORY_PLANNING_DATA` par place de marché (FR, DE, IT, ES, UK, US) ;
   - `GET_RESTOCK_INVENTORY_RECOMMENDATIONS_REPORT` par place de marché ;
   - `GET_AFN_INVENTORY_DATA_BY_COUNTRY` (EU) ;
   - `GET_LEDGER_SUMMARY_VIEW_DATA` `aggregatedByTimePeriod=DAILY`, `aggregateByLocation=COUNTRY`, veille 00:00:00 → 23:59:59 ;
   - 1×/mois : `GET_FBA_STORAGE_FEE_CHARGES_DATA` (planifiable), `GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA` (mois exact), `GET_FBA_OVERAGE_FEE_CHARGES_DATA`.
   Suivi : notification `REPORT_PROCESSING_FINISHED` (sinon `getReport` toutes les 30–60 s), `getReportDocument` puis
   téléchargement **dans les 5 min**, décompression si `compressionAlgorithm`. Enregistrer `reportId` + empreinte du
   fichier : un `reportId` déjà traité est ignoré (idempotence). `DONE_NO_DATA` / `CANCELLED` = aucune ligne, pas une erreur.
   Ne pas redemander un même type plus d'une fois toutes les 30 min / 4 h (régénération limitée).
3. **03:00 — Ventes** : Data Kiosk `createQuery` 1 par région, `aggregateBy: DAY`, fenêtre glissante J-3 → J-2 (données
   prêtes à J+2 10 h locale ; la veille est incomplète), `groupByKey { msku asin marketplaceId fulfillmentChannel }`,
   `unitsOrdered`, `unitsShipped`. Upsert `(compte, place, msku, jour)` → les jours tardifs se corrigent seuls.
   Initialisation : 1 requête de 90 jours. Contrôle : `getOrderMetrics` sans SKU, `granularity=Day`, `fulfillmentNetwork=AFN`, comparé à la somme des SKU.
4. **Calculs côté outil** (règles à inscrire au registre avant code, « non sourcé » pour les formules maison) :
   vitesse 30/60/90 j = somme unités / n jours ; jours de couverture = (disponible + en route) / vitesse ; qté à
   commander = vitesse × (délai fournisseur + cible de couverture) − (disponible + en route + réservé transfert).
   Afficher **à côté** les valeurs Amazon (`Recommended replenishment qty`, `days-of-supply`, `Recommended ship-in quantity`) sans les mélanger.
5. **Débit** : respecter `x-amzn-RateLimit-Limit` renvoyé ; sur 429, attente exponentielle. Les seaux de jetons sont
   par couple vendeur × application (et par compte régional) — https://developer-docs.amazon/sp-api/docs/usage-plans-and-rate-limits.md :
   « Most operations' rate limits are per the selling partner and application pair. »
6. **En journée (optionnel)** : abonnement SQS à `FBA_INVENTORY_AVAILABILITY_CHANGES` pour rafraîchir les quantités sans attendre la nuit.

Rôles à demander pour l'application : **Amazon Fulfillment** (inventaire + rapports FBA), **Pricing** (couvre aussi
plusieurs rapports FBA), **Inventory and Order Tracking** (Sales API), **Brand Analytics** (Data Kiosk ventes / Sales and Traffic).
