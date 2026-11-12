# SP-API : ventes, frais et versements réels par commande et par SKU (état au 12/11/2026)

> Le protocole : est marqué **VÉRIFIÉ** seulement ce qui a été lu le 12/11/2026 sur la documentation officielle
> `developer-docs.amazon/sp-api/...` (pages lues au format markdown à partir de l'index `https://developer-docs.amazon/sp-api/llms.txt`).
> Chaque fait vérifié donne l'adresse et une courte citation en anglais. Tout le reste est rangé en
> **§ 9 NON VÉRIFIÉ**, avec ce qui a été tenté.
> Pour abréger, `D/` = `https://developer-docs.amazon/sp-api/docs/` et `R/` = `https://developer-docs.amazon/sp-api/reference/`.

---

## 0. L'essentiel en 10 lignes

1. **La source à utiliser est l'API Finances v2024-06-19, opération `listTransactions`** (version « Current »). La v0 est « Legacy ».
   `listFinancialEvents`, `listFinancialEventsByGroupId` et `listFinancialEventsByOrderId` sont **dépréciées depuis le 21/07/2025 et seront supprimées le 27/08/2027**.
   `listFinancialEventGroups` (v0) **ne figure pas** dans la liste de suppression et reste le moyen documenté d'obtenir les identifiants de groupe (versements).
2. Chaque transaction a un **`transactionId` unique**. On y trouve le marché, `postedDate`, `totalAmount` (montant et devise), des ventilations `breakdowns` imbriquées,
   et, par article, `items[].contexts[]` avec **`asin`, `sku`, `quantityShipped`, `fulfillmentNetwork`**.
3. Limites : 0,5 requête/s, rafale de 10, jusqu'à 500 transactions par page, fenêtre de **180 jours au plus** (au-delà, la réponse est vide),
   données des **dernières 48 h** possiblement absentes. On peut filtrer par `ORDER_ID`, `FINANCIAL_EVENT_GROUP_ID` ou `SETTLEMENT_ID`, et par statut (`DEFERRED`, `RELEASED`, `DEFERRED_RELEASED`).
4. **Rôle nécessaire : « Finance and Accounting »**. Il **n'est pas** « Restricted ». Un développeur privé peut le demander dans son profil (§ 5).
5. Pour les **frais de stockage par ASIN**, il faut le rapport `GET_FBA_STORAGE_FEE_CHARGES_DATA` (montants **estimés**, mensuels, par ASIN, FNSKU et centre de distribution),
   et pour le stockage de longue durée `GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA` (montant facturé, par SKU).
6. Pour les **remboursements d'inventaire par SKU**, il y a le rapport `GET_FBA_REIMBURSEMENTS_DATA` et l'événement v0 `AdjustmentEvent` de type `FBAInventoryReimbursement` (avec SellerSKU, ASIN et quantité).
7. Pour les **mouvements de stock** (base du FIFO), il y a `GET_LEDGER_DETAIL_VIEW_DATA` : 18 mois d'historique, rôle « Amazon Fulfillment ».
8. **Rapport de règlement** : `GET_V2_SETTLEMENT_REPORT_DATA_FLAT_FILE_V2`. Les anciennes versions `..._FLAT_FILE` et `..._XML` sont **supprimées depuis le 11/11/2026**.
   Ces rapports sont générés par Amazon (on ne peut pas les demander) et les rapports ne sont conservés que **90 jours** : il faut les récupérer à temps.
9. **L'API Orders n'est pas indispensable** pour la marge, car les transactions portent déjà le SKU, l'ASIN, la quantité et les montants.
   Si on l'utilise : v2026-01-01 (la v0 est supprimée le 27/03/2027). Il ne faut **jamais** demander `includedData=BUYER` ni `RECIPIENT` (données personnelles).
10. **TVA (UE)** : la documentation de l'API Finances ne dit pas si `Principal` inclut la TVA (NON VÉRIFIÉ). Le détail « TTC / taxe / HT » n'existe que dans des rapports **restreints** (rôle « Tax Invoicing (Restricted) »).

---

## 1. Versions de l'API Finances, ce qui est recommandé, dépréciations

| Élément | Fait | Source (VÉRIFIÉ) |
|---|---|---|
| Version actuelle | v2024-06-19 « Current version », v0 « Legacy versions », « Sellers only » | `D/finances-api.md` : tableau « Current version \| Legacy versions » |
| Opérations v2024-06-19 | `listTransactions`, `listBalances`, `listSummary` | `D/finances-api-v2024-06-19-reference.md` : « Operations: listTransactions, listBalances, listSummary » |
| `listSummary` et `listBalances` sont nouvelles | ajoutées le 29/07/2026, avec le filtre `SETTLEMENT_ID` sur `listTransactions` | `D/sp-api-release-notes.md` (29/07/2026) : « Added the `listSummary` operation… Added the `listBalances` operation… Added the `SETTLEMENT_ID` value for the `relatedIdentifierName` query parameter » |
| Historique des filtres | statut (25/06/2025) ; `FINANCIAL_EVENT_GROUP_ID` (03/12/2025) ; `ORDER_ID` (28/01/2026) ; `DEFERRED_RELEASED` (30/04/2025) | `D/sp-api-release-notes.md`, sections datées correspondantes |
| Dépréciation v0 | `listfinancialevents`, `listFinancialEventsByGroupId`, `listFinancialEventsByOrderId` : dépréciées le **21/07/2025**, supprimées le **27/08/2027** | `D/sp-api-deprecations.md`, tableau « Finances API » : « July 21, 2025 \| August 27, 2027 » |
| `listFinancialEventGroups` | absente du tableau de suppression ; elle sert toujours d'étape 1 dans le tutoriel v2024 sur les versements | `D/determine-payment-transactions.md` : « Call the `listFinancialEventGroups` operation of the Finances API v0… » puis « Call the `listTransactions` operation… `relatedIdentifierName = FINANCIAL_EVENT_GROUP_ID` » |
| Évolution récente | depuis le 06/11/2026, nouvelle valeur `AMAZON_FBA_FROM_ORIGIN` pour `BusinessContext.storeName`, en plus de `AMAZON_HAUL` | changelog « …New Enum Value for Finances API » : « Starting 6 November 2026, the `BusinessContext.storeName` field… will include a new possible value: `AMAZON_FBA_FROM_ORIGIN` » |
| Versements (payouts) | API Transfers v2024-06-01, `listPayouts` et `listExpectedPayouts` (ajoutées le 29/07/2026) | `D/sp-api-release-notes.md` (29/07/2026) : « Added the `listPayouts` operation that enables you to retrieve payouts by date or settlement » |

**Conclusion** : on construit sur `listTransactions` (v2024-06-19) dès maintenant. N'utiliser la v0 que pour `listFinancialEventGroups`, et éventuellement comme filet de lecture jusqu'au 27/08/2027.

---

## 2. Modèle de données

### 2.1 v2024-06-19 : `Transaction` (VÉRIFIÉ, `D/finances-api-v2024-06-19-reference.md`)

- `transactionId` : « The unique identifier of the transaction. »
- `transactionType` : la doc ne donne qu'**une** valeur : « **Possible value:** `Shipment` ». La liste complète des types n'est pas publiée (→ § 9).
- `transactionStatus` : `DEFERRED`, `RELEASED` ou `DEFERRED_RELEASED` (« the transaction was deferred in the past, but is now released »).
- `description` : par exemple « `Order Payment`, `Refund Order` ».
- `postedDate` (date ISO 8601), `totalAmount` (`currencyCode` ISO 4217 et `currencyAmount`).
- `sellingPartnerMetadata` (`sellingPartnerId`, `accountType`, `marketplaceId`) et `marketplaceDetails` (`marketplaceId`, `marketplaceName`).
- `relatedIdentifiers[]` : `ORDER_ID`, `SHIPMENT_ID`, `FINANCIAL_EVENT_GROUP_ID`, `REFUND_ID`, `INVOICE_ID`, `DISBURSEMENT_ID`, `TRANSFER_ID`, `DEFERRED_TRANSACTION_ID`, `RELEASE_TRANSACTION_ID`, `SETTLEMENT_ID`.
- `items[]` : `description`, `totalAmount`, `breakdowns[]`, `contexts[]`, et `relatedIdentifiers[]` (`ORDER_ADJUSTMENT_ITEM_ID` : « defined for refunds, guarantee claims, and chargeback events » ; `COUPON_ID`, `REMOVAL_SHIPMENT_ITEM_ID`, `TRANSACTION_ID`).
- `Context` (`contextType` est obligatoire) : `asin`, `sku`, `quantityShipped`, `fulfillmentNetwork` (ProductContext) ; `storeName`, `orderType`, `channel` ; `paymentType` et autres champs de paiement ;
  `deferralReason` (« `B2B` (invoiced orders), `DD7` (delivery date policy) ») et `maturityDate` (DeferredContext) ; `startTime` et `endTime` (TimeRangeContext).
- `Breakdown` : `breakdownType` (texte), `breakdownAmount` (Currency), `breakdowns[]` (imbrication possible).
  Sur `D/get-latest-transactions.md` : « `breakdownType` is an open-ended string; Amazon does not publish a closed list of values, and new values are added as needed. Build your integration to handle unknown values. »
  Valeurs citées en exemple : `CSBAFee`, `MPFRegulatoryFee` et `MarketplaceFacilitatorRegulatoryFee-Principal`, `OurPriceRegulatoryFee`.

**Conséquence pour nous** : il faut stocker les ventilations **brutes** (arbre complet) et faire le classement (vente, commission, frais FBA, taxe, promotion…) dans une **table de correspondance tenue chez nous**, avec une catégorie « inconnu » signalée.

### 2.2 v0 : événements (VÉRIFIÉ, schéma OpenAPI de `R/listfinancialevents.md`)

- `FinancialEvents` contient notamment : `ShipmentEventList`, `RefundEventList`, `GuaranteeClaimEventList`, `ChargebackEventList`, `RetrochargeEventList`, `ServiceFeeEventList`, `AdjustmentEventList`,
  `SAFETReimbursementEventList`, `FBALiquidationEventList`, `RemovalShipmentEventList`, `RemovalShipmentAdjustmentEventList`, `CouponPaymentEventList`, `SellerDealPaymentEventList`, `ProductAdsPaymentEventList`,
  `ValueAddedServiceChargeEventList`, `CapacityReservationBillingEventList`, `DebtRecoveryEventList`, `LoanServicingEventList`… (34 listes).
- `ShipmentEvent` (« A shipment, refund, guarantee claim, or chargeback ») : `AmazonOrderId`, `MarketplaceName`, `PostedDate`, `ShipmentItemList` et `ShipmentItemAdjustmentList`, plus les frais au niveau commande ou envoi.
- `ShipmentItem` : **`SellerSKU`**, `OrderItemId`, `OrderAdjustmentItemId`, `QuantityShipped`, `ItemChargeList` / `ItemChargeAdjustmentList` (ChargeComponent), `ItemFeeList` / `ItemFeeAdjustmentList` (FeeComponent), `PromotionList`, `ItemTaxWithheldList`.
  **Il n'y a pas d'ASIN dans `ShipmentItem`.**
- Valeurs de `ChargeType` (liste dans la description de ChargeComponent) : `Principal` (« The selling price of the order item, which is equal to the selling price of the item multiplied by the quantity ordered »), `Tax` (« The tax on the principal that is collected by the seller »),
  `MarketplaceFacilitatorTax-Principal`, `-Shipping`, `-Giftwrap` et `-Other`, `ShippingCharge`, `ShippingTax`, `Giftwrap`, `GiftwrapTax`, `Discount`, `Goodwill`, `RestockingFee`, `ReturnShipping`, `GenericDeduction`, `PaymentMethodFee`, `ExportCharge`, `SAFE-TReimbursement`…
- `FeeComponent.FeeType` : texte **sans liste fermée** ; la doc renvoie aux grilles tarifaires de Seller Central. `Commission` et `FBAPerUnitFulfillmentFee` → § 9.
- `AdjustmentEvent` : `AdjustmentType` (`FBAInventoryReimbursement` : « An FBA inventory reimbursement to a seller's account. This occurs if a seller's inventory is damaged », `ReserveEvent`, `PostageBilling`, `PostageRefund`, `LostOrDamagedReimbursement`…), `PostedDate`, `AdjustmentAmount`, et
  `AdjustmentItem` (`Quantity`, `PerUnitAmount`, `TotalAmount`, **`SellerSKU`, `FnSKU`, `ASIN`**, `TransactionNumber`).
- `ServiceFeeEvent` : `AmazonOrderId`, `FeeReason`, `FeeList`, `SellerSKU`, `FnSKU`, `FeeDescription`, `ASIN`. **Il n'a pas de `PostedDate`** dans le schéma.
- `RetrochargeEvent` : `Retrocharge` ou `RetrochargeReversal`, `BaseTax`, `ShippingTax`, `MarketplaceName`.
- `FBALiquidationEvent` : « This event is used only in the US marketplace. »
- **Aucun identifiant unique d'événement en v0** : aucun champ de ce type dans `ShipmentEvent` ni dans `AdjustmentEvent`. Pour éviter les doublons, il faudrait une clé composite (§ 7). C'est une raison de plus de passer à la v2024 (`transactionId`).
- « Deferred events don't show up in responses until they are released. » (`R/listfinancialevents.md`)

### 2.3 TVA en UE

- VÉRIFIÉ : le rapport `GET_VAT_TRANSACTION_DATA` et le rapport `SC_VAT_TAX_REPORT` (colonnes « OUR_PRICE Tax Inclusive Selling Price », « OUR_PRICE Tax Amount », « OUR_PRICE Tax Exclusive Selling Price », par ASIN et SKU, pour FR, DE, IT, ES, UK et d'autres)
  sont des « **restricted report type** ». Ils demandent un jeton de données restreintes (RDT) et le rôle « Tax Invoicing (Restricted) ». Citation : « Some report types require restrictions because they contain customer PII data. These report types require passing an additional security review. » (`D/report-type-values-tax.md`)
- NON VÉRIFIÉ : savoir si `Principal` (v0) ou la ventilation équivalente (v2024) est **TTC** dans les marchés UE (§ 9).

---

## 3. Limites, fenêtres, pagination, délai, profondeur d'historique

| Opération | Débit / rafale | Fenêtre | Taille de page | Source (VÉRIFIÉ) |
|---|---|---|---|---|
| `listTransactions` | 0,5 / 10 | « If `PostedAfter` and `PostedBefore` are more than 180 days apart, the response is empty. » `postedAfter` est obligatoire sans `relatedIdentifier` ; les bornes doivent être à « more than two minutes before the time of the request » | « up to 500 transactions » ; `nextToken` ; « this operation can return empty pages » | `R/listtransactions.md`, `D/get-latest-transactions.md` |
| `listTransactions` + `ORDER_ID` | idem | aucune date nécessaire | 500 et `nextToken` | `D/list-transactions-by-order.md` : « You do not need to know the exact dates… refunds, chargebacks, or order adjustments, which can occur days, weeks, or even months later. » |
| `listSummary`, `listBalances` | 0,5 / 10 | — | `nextToken` (500 pour les soldes) | référence v2024 ; « Financial summaries are calculated based on the marketplace timezone of the seller, not UTC. » (`D/retrieve-financial-summary.md`) |
| v0 `listFinancialEvents` | 0,5 / 30 | 180 jours, sinon réponse vide | `MaxResultsPerPage` de 1 à 100 (100 par défaut) ; « If the response exceeds the maximum number of transactions or 10 MB, the response is `InvalidInput`. » | `R/listfinancialevents.md` |
| v0 `listFinancialEventGroups` | 0,5 / 30 | 180 jours, sinon aucun groupe | de 1 à 100 (10 par défaut) | `R/listfinancialeventgroups.md` |
| `listPayouts` (Transfers) | 0,5 / 10 | `createdAfter` / `createdBefore` | `nextToken` | `R/listpayouts.md` |
| Reports `getReports` | 0,0222 / 10 | « Reports are retained for a maximum of 90 days. » | — | `R/getreports.md` |
| Reports `createReport` et `getReportDocument` | 0,0167 / 15 | URL du document : « expires after 5 minutes » | — | `R/createreport.md`, `R/getreportdocument.md` |
| Orders v2026 `searchOrders` / `getOrder` | 0,0056 / 20 et 0,5 / 30 | « Orders more than two years old don't show in the API response. » | — | `D/orders-api-rate-limits.md`, `D/orders-api.md` |

- **Délai d'apparition** (VÉRIFIÉ) : « Financial events might not include orders from the last 48 hours. » (`R/listtransactions.md`)
- **Algorithme de limitation** (VÉRIFIÉ) : seau à jetons, par paire compte vendeur × application et par région (`D/usage-plans-and-rate-limits.md`). L'en-tête `x-amzn-RateLimit-Limit` n'est pas toujours présent : « you must not depend on this header being present ».
- **Rapports FBA** (VÉRIFIÉ, `D/report-type-values-fba.md`) : un rapport « near real-time » est régénéré au plus toutes les 30 min, un rapport « daily » au plus toutes les 4 h.
  Une demande répétée trop tôt peut être annulée (`D/reports-faq.md`).
- **Profondeur d'historique de `listTransactions`** : NON VÉRIFIÉ, la doc ne le dit pas (§ 9). Ce qui est vérifié : ledger 18 mois, Orders 2 ans, Deferred Transaction Report jusqu'à 10 ans.

---

## 4. Rapports (API Reports v2021-06-30)

| Rapport (`reportType`) | Contenu utile | Disponibilité, contraintes | Rôle(s) | Source (VÉRIFIÉ) |
|---|---|---|---|---|
| `GET_V2_SETTLEMENT_REPORT_DATA_FLAT_FILE_V2` | une ligne par montant : `settlement-id`, dates, `deposit-date`, `total-amount`, `currency`, `transaction-type`, `order-id`, `adjustment-id`, `shipment-id`, `marketplace-name`, **`amount-type`, `amount-description`, `amount`**, `posted-date(-time)`, `order-item-code`, **`sku`**, `quantity-purchased`, `promotion-id` | « Settlement reports cannot be requested or scheduled. They are automatically scheduled by Amazon. » Montants au format local (« `95,00` for EU »). Conservation de 90 jours | Finance and Accounting (Tax Invoicing figure aussi dans la table des correspondances) | `D/report-type-values-settlement.md` |
| `GET_V2_SETTLEMENT_REPORT_DATA_FLAT_FILE` et `_XML` | — | **supprimés le 11/11/2026** | — | `D/sp-api-deprecations.md` : « March 17, 2025 \| November 11, 2026 » |
| `GET_DATE_RANGE_FINANCIAL_HOLDS_DATA` (Deferred Transaction Report) | transactions différées : `order-id`, `sku`, `quantity`, `product-sales`, `product-sales-tax`, `selling-fees`, `fba-fees`, `other-transaction-fees`, `total`… | « up to 10 years of data » ; il faut d'abord le demander dans Seller Central (« Payments Reports Repository ») | Finance and Accounting | `D/report-type-values-payment.md` |
| « Date Range Financial Transaction » (`GET_DATE_RANGE_FINANCIAL_TRANSACTION_DATA`) | — | **introuvable** dans la doc lue (§ 9) | — | — |
| `GET_FBA_STORAGE_FEE_CHARGES_DATA` | « **estimated** monthly inventory storage fees for each ASIN » : `asin`, `fnsku`, `fulfillment_center`, `country_code`, `average_quantity_on_hand`, `month_of_charge`, `storage_rate`, `estimated_monthly_storage_fee`, `currency`, majorations… | peut être demandé ou planifié | Pricing ou Amazon Fulfillment | `D/report-type-values-fba.md` |
| `GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA` | `snapshot-date`, **`sku`**, `fnsku`, `asin`, `country`, `qty-charged`, **`amount-charged`**, `surcharge-age-tier` | demande seulement ; l'intervalle entre `dataStartTime` et `dataEndTime` doit être d'un mois | Pricing ou Amazon Fulfillment | idem |
| `GET_FBA_OVERAGE_FEE_CHARGES_DATA` | frais de dépassement des limites de stockage, par type de stockage (pas par SKU) : `charged_date`, `charged_fee_amount` | demande seulement | Amazon Fulfillment | idem |
| `GET_FBA_REIMBURSEMENTS_DATA` | `approval-date`, **`reimbursement-id`**, `case-id`, `amazon-order-id`, `reason`, **`sku`, `fnsku`, `asin`**, `amount-per-unit`, `amount-total`, `quantity-reimbursed-cash` / `-inventory` / `-total`, `original-reimbursement-id` / `-type` | « Content updated daily » ; demande seulement | Pricing ou Amazon Fulfillment | idem |
| `GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA` | retours FBA : `return-date`, `order-id`, `sku`, `asin`, `fnsku`, `quantity`, `detailed-disposition`, `reason`, `status`, `license-plate-number`, `customer-comments` (aucun montant) | mis à jour chaque jour | Pricing ou Amazon Fulfillment | idem |
| `GET_LEDGER_DETAIL_VIEW_DATA` | mouvements de stock : `Date`, `FNSKU`, `ASIN`, `MSKU`, `Event Type`, `Reference ID`, `Quantity`, `Fulfillment Center`, `Disposition`, `Reason`, `Country`, `Reconciled` / `Unreconciled Quantity`… | « all historical movements of your inventory for 18 months » ; filtres `eventType`, `FNSKU`, `MSKU`, `ASIN` | Amazon Fulfillment | idem |
| `GET_LEDGER_SUMMARY_VIEW_DATA` | soldes de stock par période (journalière, hebdomadaire, mensuelle), par pays ou par centre | demande seulement | Amazon Fulfillment | idem |
| `GET_FBA_FULFILLMENT_REMOVAL_ORDER_DETAIL_DATA` | retraits : `sku`, `fnsku`, quantités, **`removal-fee`**, `currency` | quasi temps réel | Pricing ou Amazon Fulfillment | idem |
| `GET_FBA_ESTIMATED_FBA_FEES_TXT_DATA` | frais **estimés** par SKU (pour l'aide à l'achat, pas pour la marge réalisée) | « can only be requested once per day per seller » | Pricing ou Amazon Fulfillment | idem |
| `GET_FLAT_FILE_ALL_ORDERS_DATA_BY_LAST_UPDATE_GENERAL` | commandes : `sku`, `asin`, `quantity`, `item-price`, `item-tax`… « does not include customer identifying information » | demande seulement | Pricing, Amazon Fulfillment, Inventory and Order Tracking… | idem |
| `GET_AMAZON_FULFILLED_SHIPMENTS_DATA_GENERAL` | **contient des données personnelles** (`buyer-email`, `buyer-name`, adresses) | 12 demandes / 8 h ; **à éviter** | Pricing, Amazon Fulfillment, Inventory and Order Tracking | idem |

**Ce qu'il faut pour les frais de stockage et les remboursements par SKU** :
- stockage mensuel par ASIN : `GET_FBA_STORAGE_FEE_CHARGES_DATA` (estimation ventilée). Le montant réellement prélevé arrive dans les transactions financières et le règlement, en principe sans SKU (§ 9) :
  il faut **répartir le montant réel au prorata de l'estimation**.
- stockage de longue durée : `GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA` (`amount-charged` par SKU).
- remboursements : `GET_FBA_REIMBURSEMENTS_DATA` (identifiant `reimbursement-id`, SKU, quantités) et, côté argent, `AdjustmentEvent/FBAInventoryReimbursement` (v0) ou la transaction v2024 équivalente.

---

## 5. Rôles et accès d'un développeur privé

- VÉRIFIÉ (`D/roles-in-the-selling-partner-api.md`) : « *Restricted* means that the role requires sensitive information, which might include personally identifiable information (PII). »
  Les rôles restreints portent la mention « (Restricted) » dans leur nom : Direct-to-Consumer Shipping, Tax Invoicing, Tax Remittance, Professional Services.
  **Finance and Accounting**, **Amazon Fulfillment**, **Pricing** et **Inventory and Order Tracking** ne portent pas cette mention.
- Finance and Accounting : « provides access to operations that create accounting and financial statements », « Role available to sellers? Yes ».
- Rôles par opération (VÉRIFIÉ, `D/finances-api.md` et `D/role-mappings.md`) :
  - `listTransactions`, `listSummary`, `listBalances`, `listFinancialEventsByOrderId` et `listPayouts` : Finance and Accounting.
  - `listFinancialEvents` : également AISP (UE seulement) ou Amazon Fulfillment (NA et FE seulement).
- **Développeur privé** (VÉRIFIÉ, `D/register-as-a-private-developer.md`) : « Private developers build applications that integrate only their company with Amazon Services APIs. »
  Le profil se remplit dans Seller Central (Apps and Services > Develop Apps) avec les rôles, les cas d'usage et les contrôles de sécurité ; ensuite, « Amazon will evaluate your information ».
  L'accord n'est **pas garanti** : « We cannot provide detailed information about how we determine Selling Partner API eligibility ». Il faut répondre sous 5 jours aux questions d'Amazon.
- Autorisation (VÉRIFIÉ, `D/self-authorization.md`, `D/application-authorization-limits.md`) : auto-autorisation possible « in draft status » ; « To self-authorize a Seller Central account, you must be the Primary User » ; **10 auto-autorisations au maximum** pour une application privée.
- Régions (VÉRIFIÉ, `D/sp-api-endpoints.md`) : FR, DE, IT, ES et UK passent par `sellingpartnerapi-eu.amazon.com` ; US par `sellingpartnerapi-na.amazon.com`.
  Il faut donc des jetons et des appels **séparés par région**. Identifiants de marché (`D/store-identifiers.md`) : FR `A13V1IB3VIYZZH`, DE `A1PA6795UKMFR9`, IT `APJ6JRA9NG5V4`, ES `A1RKKUPIHCS9HS`, UK `A1F83G8C2ARO7P`, US `ATVPDKIKX0DER`.
- Ensemble minimal de rôles pour notre outil : **Finance and Accounting + Amazon Fulfillment** (Pricing comme alternative pour les rapports FBA). Ne demander **aucun** rôle « Restricted ».

---

## 6. L'API Orders est-elle nécessaire ?

- Pour la marge réalisée, **non** : les transactions v2024 portent `ORDER_ID`, SKU, ASIN, `quantityShipped`, les montants et le marché.
- Elle peut servir à connaître une commande **avant** que les mouvements financiers n'apparaissent (48 h et plus), par exemple pour réserver le lot FIFO dès l'expédition.
  Le rapport `GET_FLAT_FILE_ALL_ORDERS_DATA_BY_LAST_UPDATE_GENERAL` fait de même, sans données personnelles et sans RDT.
- Si on l'utilise (VÉRIFIÉ, `D/orders-api.md`, `D/orders-api-migration-guide.md`) : v2026-01-01 avec `includedData=PROCEEDS` (« Revenue and financial breakdown »), plus éventuellement `EXPENSE` ou `PROMOTION`.
  La v0 est dépréciée le 28/01/2026 et supprimée le 27/03/2027. Il ne faut **jamais** utiliser `BUYER`, `RECIPIENT` ni `TAX` (enregistrements fiscaux de l'acheteur).
  En v2026, « Restricted Data Tokens (RDTs) are not required to access PII… you only need the appropriate roles assigned » : l'accès aux données personnelles dépend donc des rôles. Ne pas demander de rôle restreint suffit à les tenir à l'écart.
- Notre recommandation : ne pas utiliser Orders au lot 1 ; utiliser le rapport « All Orders by last update » si un rapprochement anticipé devient utile.

---

## 7. Synchronisation de nuit recommandée

### 7.1 Tâches (par compte vendeur × région UE ou NA)

1. **Transactions (cœur)** : `listTransactions` avec `postedAfter = curseur − 7 jours` (fenêtre glissante qui couvre le délai de 48 h et les publications tardives) et `postedBefore = maintenant − 5 min`.
   Pages successives jusqu'à `nextToken` nul, sans s'arrêter sur une page vide. Pas de filtre `marketplaceId` : on ventile ensuite par `marketplaceDetails.marketplaceId`.
   Seule la **vente FBM aux US** exige d'omettre ce filtre : « If you want to retrieve MFN orders in the US store, do not supply the `marketplaceId` parameter ».
2. **Relecture par commande** : pour chaque commande dont un lot n'est pas clos, ou qui a eu un retour ou un remboursement, `listTransactions?relatedIdentifierName=ORDER_ID` une fois par semaine pendant 90 à 180 jours (choix interne).
   Cela rattrape les remboursements, réclamations A-to-Z et rétrofacturations publiés plus tard (citation du § 3).
3. **Groupes et versements** : v0 `listFinancialEventGroups` sur les 180 derniers jours, puis `listTransactions` avec `FINANCIAL_EVENT_GROUP_ID` ou `SETTLEMENT_ID` pour les groupes `Closed` ; `listPayouts` pour le virement.
4. **Règlement** : `getReports(reportTypes=GET_V2_SETTLEMENT_REPORT_DATA_FLAT_FILE_V2, createdSince=dernier passage)`, puis télécharger **chaque** rapport nouveau. Les rapports sont gardés 90 jours ; l'URL expire au bout de 5 minutes.
   Ce rapport sert de **contrôle** : la somme des transactions d'un `settlement-id` doit égaler `total-amount`.
5. **Rapports FBA** : `createReport`, puis attente de `REPORT_PROCESSING_FINISHED` (notification) ou interrogation régulière, puis `getReportDocument`.
   Chaque nuit : `GET_FBA_REIMBURSEMENTS_DATA` (30 derniers jours), `GET_LEDGER_DETAIL_VIEW_DATA` (veille et 7 jours glissants), `GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA`.
   Une fois par mois : `GET_FBA_STORAGE_FEE_CHARGES_DATA` (mois écoulé) et `GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA` (un mois exactement).
6. **Débit** : client à seau à jetons local (0,5/s, rafale 10 pour Finances), reprise exponentielle sur l'erreur 429, en-tête `x-amzn-RateLimit-Limit` lu s'il est présent.

### 7.2 Clés d'idempotence (ne jamais compter deux fois)

| Source | Clé proposée | Fondement |
|---|---|---|
| v2024 transaction | `(sellingPartnerId, transactionId)` | « The unique identifier of the transaction » (VÉRIFIÉ) |
| v2024 ligne article | `(transactionId, rang de l'item)`, plus `ORDER_ADJUSTMENT_ITEM_ID` / `TRANSACTION_ID` si présents | identifiants d'item (VÉRIFIÉ) ; stabilité du rang NON VÉRIFIÉE |
| Différé → libéré | lier `DEFERRED_TRANSACTION_ID` et `RELEASE_TRANSACTION_ID` ; ne compter l'argent **qu'une fois** (on garde le statut et on le met à jour) | identifiants (VÉRIFIÉ) ; règle exacte de doublon NON VÉRIFIÉE → tester en réel |
| Règlement | `(settlement-id, hash de la ligne entière)` ; un `settlement-id` déjà importé est ignoré | colonnes (VÉRIFIÉ) |
| Remboursement FBA | `reimbursement-id` (+ `original-reimbursement-id` pour les annulations) | colonnes (VÉRIFIÉ) |
| Ledger | `(Date and Time, FNSKU, Event Type, Reference ID, Fulfillment Center, Disposition, Quantity)` | colonnes (VÉRIFIÉ) ; unicité NON VÉRIFIÉE |
| v0 (si utilisée) | hash de `(type de liste, AmazonOrderId, PostedDate, OrderItemId ou OrderAdjustmentItemId, contenu)` | la v0 n'a pas d'identifiant unique (VÉRIFIÉ par lecture du schéma) |

### 7.3 Ajustements qui arrivent tard

- Toujours **ajouter**, jamais écraser : un remboursement est une nouvelle transaction (signée) rattachée à `ORDER_ID` et au SKU, qui vient corriger le lot FIFO **d'origine** de la vente (et non le lot courant).
- Le résultat d'un lot reste **provisoire** tant que la dernière vente n'a pas dépassé N jours (paramètre interne, par exemple 90 jours) ni passé un règlement clos.
- Les frais non rattachés à un SKU (abonnement, dépassement de stockage, publicité…) vont dans une ligne « frais de compte », répartie selon une clé choisie (par exemple les unités en stock moyennes).
- Le stockage mensuel réel se répartit au prorata de `estimated_monthly_storage_fee` par ASIN du mois concerné.
- Rapprochement mensuel : somme des transactions = `listSummary` de la période (fuseau du marché) = règlement(s) ; tout écart est signalé, jamais corrigé en silence.

---

## 8. Tableau de synthèse : besoin → source → champs → limites → rôle → vérifié

| Besoin | Endpoint ou rapport | Champs clés | Limites | Rôle | Vérifié (URL + citation) |
|---|---|---|---|---|---|
| Vente encaissée par SKU, marché et date | `GET /finances/2024-06-19/transactions` | `transactionId`, `postedDate`, `marketplaceDetails`, `items[].contexts[].sku/asin/quantityShipped`, `breakdowns` | 0,5/s, rafale 10 ; 180 j ; 500 par page ; 48 h de délai | Finance and Accounting | `R/listtransactions.md` : « If `PostedAfter` and `PostedBefore` are more than 180 days apart, the response is empty » |
| Frais Amazon réellement prélevés (commission, FBA…) | idem (`breakdowns` imbriqués) | `breakdownType`, `breakdownAmount` | liste de types ouverte | idem | `D/get-latest-transactions.md` : « Amazon does not publish a closed list of values » |
| Retours et remboursements (argent) | idem, filtre `ORDER_ID` | `description` (« Refund Order »), `REFUND_ID`, `ORDER_ADJUSTMENT_ITEM_ID` | 500 par page | idem | `D/list-transactions-by-order.md` : « refunds, chargebacks, or order adjustments, which can occur days, weeks, or even months later » |
| Retours (physique, état) | `GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA` | `order-id`, `sku`, `quantity`, `detailed-disposition`, `status` | quotidien | Pricing / Amazon Fulfillment | `D/report-type-values-fba.md` : « including Return Reason and Disposition. Content updated daily. » |
| Stockage mensuel par ASIN | `GET_FBA_STORAGE_FEE_CHARGES_DATA` | `asin`, `fnsku`, `month_of_charge`, `estimated_monthly_storage_fee`, `currency` | estimation | Pricing / Amazon Fulfillment | idem : « Contains estimated monthly inventory storage fees for each ASIN » |
| Stockage de longue durée par SKU | `GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA` | `sku`, `qty-charged`, `amount-charged` | fenêtre d'un mois | Pricing / Amazon Fulfillment | idem : « should be equal to one month » |
| Remboursements d'inventaire par SKU | `GET_FBA_REIMBURSEMENTS_DATA` (+ v0 `AdjustmentEvent`) | `reimbursement-id`, `sku`, `amount-total`, quantités | quotidien | Pricing / Amazon Fulfillment | idem : « itemized details of a seller's inventory reimbursements, including the reason » |
| Mouvements de stock (FIFO, pertes, inventaire retrouvé) | `GET_LEDGER_DETAIL_VIEW_DATA` | `MSKU`, `FNSKU`, `Event Type`, `Reference ID`, `Quantity` | 18 mois | Amazon Fulfillment | idem : « all historical movements of your inventory for 18 months » |
| Versement bancaire | v0 `listFinancialEventGroups` + `listTransactions(FINANCIAL_EVENT_GROUP_ID)` ; Transfers `listPayouts` | `FinancialEventGroupId`, `FundTransferDate`, `OriginalTotal` | 180 j, 100 par page | Finance and Accounting | `D/determine-payment-transactions.md` |
| Contrôle de règlement | `GET_V2_SETTLEMENT_REPORT_DATA_FLAT_FILE_V2` ; `listSummary(SETTLEMENT_ID)` | `settlement-id`, `amount-type`, `amount`, `sku` | auto-généré ; conservation de 90 j | Finance and Accounting | `D/report-type-values-settlement.md` : « cannot be requested or scheduled » |
| Fonds retenus (différé) | `listTransactions(transactionStatus=DEFERRED)` ; `GET_DATE_RANGE_FINANCIAL_HOLDS_DATA` | `maturityDate`, `deferralReason` | rapport à demander d'abord dans Seller Central | Finance and Accounting | `D/report-type-values-payment.md` : « up to 10 years of data » |
| TVA ventilée (UE) | `GET_VAT_TRANSACTION_DATA` / `SC_VAT_TAX_REPORT` | TTC, taxe et HT par ASIN et SKU | **restreint** (RDT, revue de sécurité) | Tax Invoicing (Restricted) | `D/report-type-values-tax.md` : « This is a restricted report type » |

---

## 9. NON VÉRIFIÉ (à tester sur un vrai compte ou à confirmer)

| Point | Ce qui a été tenté | Statut |
|---|---|---|
| Liste complète des `transactionType` v2024 (Refund, ServiceFee, Adjustment, FBA storage…) | référence v2024 et guides lus : seule « Possible value: `Shipment` » est documentée | NON VÉRIFIÉ : il faut l'observer dans les réponses réelles |
| Noms `Commission`, `FBAPerUnitFulfillmentFee`, `FBAStorageFee`… (FeeType v0, breakdownType v2024) | recherche dans toutes les pages téléchargées : aucune occurrence ; FeeType renvoie aux grilles de Seller Central | NON VÉRIFIÉ (souvenir non utilisé comme fait) |
| `Principal` TTC ou HT en UE ; présence de la TVA dans les ventilations v2024 | recherche « VAT » et « Tax » dans les pages Finances : rien d'explicite | NON VÉRIFIÉ : le comparer sur une commande réelle avec le rapport de règlement ou la facture |
| Profondeur d'historique de `listTransactions` (combien d'années en arrière) | rien dans la référence ni dans les guides | NON VÉRIFIÉ |
| Frais de stockage dans les transactions : SKU présent ou non | aucun exemple dans la doc | NON VÉRIFIÉ : on suppose « sans SKU », d'où la répartition |
| Rapport `GET_DATE_RANGE_FINANCIAL_TRANSACTION_DATA` | grep sur l'index `llms.txt` et sur les pages de rapports Payment, Settlement et FBA : introuvable | NON VÉRIFIÉ (probablement absent de l'API Reports) |
| Fréquence de génération des rapports de règlement (environ 14 jours ?) | page Settlement : seulement « automatically scheduled by Amazon » | NON VÉRIFIÉ |
| Différé → libéré : nouvelle transaction (nouvel identifiant) ou même transaction mise à jour | seuls l'existence de `DEFERRED_RELEASED` et des identifiants liés sont documentés | NON VÉRIFIÉ : tester avant de fixer la règle anti-doublon |
| Stabilité de l'ordre des `items[]` d'une transaction | rien | NON VÉRIFIÉ |
| Délai d'approbation du rôle Finance and Accounting pour un développeur privé | page d'inscription : évaluation au cas par cas, sans délai | NON VÉRIFIÉ |
| Pages HTML non lisibles en markdown (`D/finance-and-accounting-role`, `D/finances-api-v0-use-case-guide`) | renvoient une page HTML générique | non exploitées |

---

## 10. Pages lues (12/11/2026)

`D/finances-api.md` · `D/finances-api-v2024-06-19-reference.md` (mise à jour 05/11/2026) · `R/listtransactions.md` · `R/listsummary.md` · `D/get-latest-transactions.md` · `D/list-transactions-by-order.md` ·
`D/determine-payment-transactions.md` · `D/retrieve-financial-summary.md` · `D/retrieve-financial-events-in-group.md` · `R/listfinancialevents.md` · `R/listfinancialeventsbyorderid.md` · `R/listfinancialeventgroups.md` ·
`R/listpayouts.md` · `D/sp-api-deprecations.md` · `D/sp-api-release-notes.md` (mise à jour 04/11/2026) · changelog « New Enum Value for Finances API » · `D/report-type-values-settlement.md` · `D/report-type-values-payment.md` ·
`D/report-type-values-fba.md` · `D/report-type-values-tax.md` · `D/reports-faq.md` · `R/getreports.md` · `R/createreport.md` · `R/getreportdocument.md` · `D/roles-in-the-selling-partner-api.md` · `D/role-mappings.md` ·
`D/role-mappings-for-types.md` · `D/register-as-a-private-developer.md` · `D/self-authorization.md` · `D/application-authorization-limits.md` · `D/usage-plans-and-rate-limits.md` · `D/orders-api.md` · `D/orders-api-migration-guide.md` ·
`D/orders-api-rate-limits.md` · `D/sp-api-endpoints.md` · `D/store-identifiers.md`.
