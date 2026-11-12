# Remboursements FBA : détection par SP-API et politique d'Amazon — notes vérifiées

Date de lecture : 12/11/2026 (heure de Paris). Marchés visés : UE (FR, DE, IT, ES), UK, US.

Méthode : on a lu les pages Markdown de `developer-docs.amazon` (index `https://developer-docs.amazon/sp-api/llms.txt`), les modèles JSON
officiels `raw.githubusercontent.com/amzn/selling-partner-api-models` et, pour la politique, les annonces officielles du compte
**News_Amazon** sur les forums Seller Central (lisibles sans connexion). Les pages d'aide Seller Central ne s'affichent qu'avec
JavaScript et une connexion : elles n'ont **pas** été lues (voir « NON VÉRIFIÉ »).

Légende : **VÉRIFIÉ** = lu sur une source officielle Amazon, avec son URL et une citation. **ANNONCE** = annonce officielle
News_Amazon lue mot à mot, mais ce n'est pas le texte de la politique en vigueur et elle peut avoir changé depuis.
**NON VÉRIFIÉ** = rien d'officiel n'a pu être lu.

---

## 1. Tableau de synthèse

| Cas à détecter | Données SP-API | Champs / codes | Logique de détection (proposée, pas une règle Amazon) | Vérifié |
|---|---|---|---|---|
| Unités perdues ou abîmées en entrepôt | `GET_LEDGER_DETAIL_VIEW_DATA` (`eventType=Adjustments`) ; `GET_LEDGER_SUMMARY_VIEW_DATA` | Détail : `Date`, `FNSKU`, `MSKU`, `Event Type`, `Reference ID`, `Quantity`, `Fulfillment Center`, `Disposition`, `Reason`, `Reconciled Quantity`, `Unreconciled Quantity`. Synthèse : colonnes `Found`, `Lost`, `Damaged`, `Disposed` | Par FNSKU : Lost + Damaged − Found − unités déjà remboursées (rapport Remboursements) ; le reste est un cas possible. La signification exacte des codes `Reason` et des colonnes `Reconciled`/`Unreconciled` n'est **pas documentée** dans SP-API | VÉRIFIÉ pour les colonnes ([FBA reports](https://developer-docs.amazon/sp-api/docs/report-type-values-fba.md)) ; NON VÉRIFIÉ pour les codes |
| Remboursements déjà reçus (pour ne pas réclamer deux fois) | `GET_FBA_REIMBURSEMENTS_DATA` ; Finances v0 `AdjustmentEvent` `FBAInventoryReimbursement` | `reimbursement-id`, `case-id`, `amazon-order-id`, `reason`, `fnsku`, `quantity-reimbursed-cash`, `quantity-reimbursed-inventory`, `quantity-reimbursed-total`, `original-reimbursement-id`, `original-reimbursement-type` | Rapprocher par FNSKU (pertes en entrepôt) ou par `amazon-order-id` (retours) | VÉRIFIÉ (voir 2.1 et 2.5) |
| Remboursé au client mais article jamais retourné | Finances (`listTransactions` v2024-06-19 avec `ORDER_ID`, ou v0 `RefundEventList`) + `GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA` + `GET_FBA_REIMBURSEMENTS_DATA` | Finances : `description` (exemple `Refund Order`), `relatedIdentifiers` `ORDER_ID`/`REFUND_ID`, `ProductContext.sku` ; v0 : `AmazonOrderId`, `SellerSKU`, `OrderAdjustmentItemId`. Retours : `order-id`, `sku`, `fnsku`, `quantity`, `return-date`, `detailed-disposition`, `status`, `license-plate-number` | Commande remboursée, sans ligne de retour pour la même `order-id` et le même SKU, et sans remboursement avec cette `amazon-order-id`, une fois le délai passé (fenêtre 45–105 jours selon les annonces, voir 3) | VÉRIFIÉ pour les champs ; délais = ANNONCE |
| Retour reçu abîmé (par le transporteur ou l'entrepôt) | `GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA` | `detailed-disposition`, `reason`, `status` | Repérer les dispositions « non vendables » ; liste des valeurs **non documentée** | Colonnes VÉRIFIÉES ; valeurs NON VÉRIFIÉES |
| Envoi entrant reçu incomplet | Fulfillment Inbound **v0** `getShipmentItemsByShipmentId` / `getShipmentItems` (toujours en service) + v0 `getShipments` (statut) ; rapport `GET_FBA_FULFILLMENT_INBOUND_NONCOMPLIANCE_DATA` ; ledger `Receipts` | `QuantityShipped`, `QuantityReceived`, `FulfillmentNetworkSKU`, `SellerSKU` ; statuts `CLOSED`, `RECEIVING`… ; rapport : `expected-quantity`, `received-quantity`, `problem-type`, `problem-quantity` | Quand l'envoi est `CLOSED` : écart = `QuantityShipped − QuantityReceived` par SKU, moins ce qui est déjà remboursé. La v2024-03-20 `listShipmentItems` ne donne que `quantity` (prévu), pas le reçu | VÉRIFIÉ (voir 2.4) |
| Retrait (removal) perdu ou incomplet | `GET_FBA_FULFILLMENT_REMOVAL_ORDER_DETAIL_DATA`, `GET_FBA_FULFILLMENT_REMOVAL_SHIPMENT_DETAIL_DATA` | `requested-quantity`, `cancelled-quantity`, `disposed-quantity`, `shipped-quantity`, `in-process-quantity`, `tracking-number`, `carrier` | Comparer `shipped-quantity` avec ce qui a été réellement reçu (saisi par le vendeur) | Colonnes VÉRIFIÉES |
| Déposer la réclamation | **Aucune opération SP-API** | Support API v2025-02-01 : seulement `listCases`, `getCase`, `listContacts` (lecture) | Préparer le dossier, lien vers Seller Central ; suivre ensuite le cas en lecture (`case-id`) | VÉRIFIÉ (voir 2.7) |

---

## 2. Faits VÉRIFIÉS (SP-API)

### 2.1 `GET_FBA_REIMBURSEMENTS_DATA` (rapport Remboursements)

Source : https://developer-docs.amazon/sp-api/docs/report-type-values-fba.md (page mise à jour le 2026-10-13).

- Rôles : « **Roles**: Pricing, Amazon Fulfillment ». Disponibilité : « **Availability**: FBA sellers ». « This report can only be requested. » Fichier texte à tabulations.
- Contenu : « Contains itemized details of a seller's inventory reimbursements, including the reason for the reimbursement. Content updated daily. »
- Colonnes (dans l'ordre de la doc) : `approval-date`, `reimbursement-id`, `case-id`, `amazon-order-id`, `reason`, `sku`, `fnsku`, `asin`, `product-name`, `condition`, `currency-unit`, `amount-per-unit`, `amount-total`, `quantity-reimbursed-cash`, `quantity-reimbursed-inventory`, `quantity-reimbursed-total`, `original-reimbursement-id`, `original-reimbursement-type`.
- Marchés : la doc ne signale **aucune restriction**. À titre de comparaison, le rapport des remplacements dit lui « Amazon store availability: NA and Amazon IN stores ».
- **Non documenté** : la liste des valeurs de `reason`, et jusqu'où on peut remonter dans le temps (voir 4).
- Fréquence générale des rapports FBA : « A daily FBA report is generated no more than once every four hours. »

### 2.2 `GET_LEDGER_DETAIL_VIEW_DATA` (Inventory Ledger, vue détaillée)

Même source.
- Rôle : Amazon Fulfillment. Le rapport se demande, il ne se programme pas (« can only be requested »).
- « Use the Inventory Ledger Report - Detailed View to analyze your inventory movements to and from Amazon fulfillment centers, including products that are sold, returned, removed/disposed, damaged, lost, and found. You can view all historical movements of your inventory for **18 months** in this report. »
- `reportOptions.eventType` : `""` (tout), `Adjustments`, `CustomerReturns`, `Receipts`, `Shipments`, `VendorReturns`, `WhseTransfers`. Filtres possibles aussi : `FNSKU`, `MSKU`, `ASIN`.
  Exemple de la doc : `"reportOptions":{"eventType":"Adjustments", "FNSKU" : "X00001", "MSKU" : "Test"}`.
- Colonnes : `Date`, `FNSKU`, `ASIN`, `MSKU`, `Title`, `Event Type`, `Reference ID`, `Quantity`, `Fulfillment Center`, `Disposition`, `Reason`, `Country`, `Reconciled Quantity`, `Unreconciled Quantity`, `Date and Time`, `Store`.
- Vue synthèse `GET_LEDGER_SUMMARY_VIEW_DATA` : « like a bank statement of your inventory ». Options `aggregateByLocation` (`COUNTRY` par défaut, ou `FC`) et `aggregatedByTimePeriod` (`MONTHLY` par défaut, `WEEKLY`, `DAILY`). Colonnes : `Date`, `FNSKU`, `ASIN`, `MSKU`, `Title`, `Disposition`, `Starting Warehouse Balance`, `In Transit Between Warehouses`, `Receipts`, `Customer Shipments`, `Customer Returns`, `Vendor Returns`, `Warehouse Transfer In/Out`, **`Found`, `Lost`, `Damaged`**, `Disposed`, `Other Events`, `Ending Warehouse Balance`, `Unknown Events`, `Location`, `Store`.
  → Pour calculer « perdu/abîmé net de retrouvé » par FNSKU, **la vue synthèse donne directement Lost / Damaged / Found** sans avoir à décoder les codes de motif. C'est la voie la plus sûre tant que les codes ne sont pas sourcés.
- **Les codes de motif d'ajustement (M, E, D, F, Q, 5, 6, 7, etc.) n'apparaissent pas dans la documentation SP-API** : aucune occurrence n'a été trouvée dans la page des rapports FBA ni dans l'index `llms.txt`. → NON VÉRIFIÉ.

### 2.3 `GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA` (rapport Retours FBA)

Même source, section « FBA Concessions Reports ».
- Rôles : Pricing, Amazon Fulfillment. Disponibilité : FBA sellers. Le rapport se demande seulement. Fichier à tabulations.
- « Contains customer returned items received at an Amazon fulfillment center, including Return Reason and Disposition. Content updated daily. »
- Colonnes : `return-date`, `order-id`, `sku`, `asin`, `fnsku`, `product-name`, `quantity`, `fulfillment-center-id`, `detailed-disposition`, `reason`, `status`, `license-plate-number`, `customer-comments`.
- Aucune restriction de marché n'est indiquée. Les valeurs de `detailed-disposition`, `reason` et `status` ne sont **pas listées**.
- La page des rapports Retours (https://developer-docs.amazon/sp-api/docs/report-type-values-returns.md) renvoie vers ce rapport pour les retours FBA : « FBA returns. Use the FBA Returns Report (`GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA`) instead. »

### 2.4 Envois entrants : expédié et reçu

- **La v2024-03-20 ne donne pas la quantité reçue.** `listShipmentItems` (https://developer-docs.amazon/sp-api/reference/listshipmentitems.md) : le schéma `Item` contient `asin`, `expiration`, `fnsku`, `labelOwner`, `manufacturingLotCode`, `msku`, `prepInstructions` et `quantity` (« The number of the specified MSKU. »). Débit : 2 requêtes/s, rafale de 30.
- **Les opérations v0 restent en service pour ce besoin.** Guide de migration (https://developer-docs.amazon/sp-api/docs/migrating-fulfillment-inbound-workflows.md), section « Preserved workflows » : « The following v0 operations are **not** deprecated: … `getShipmentItemsByShipmentId` / `getShipmentItems` — Get quantity shipped and quantity received. … `getShipments` — Get shipment status. » Et : « Use `shipmentConfirmationID` in place of `shipmentId` for all v0 operations that are not deprecated. »
- Schéma v0 `InboundShipmentItem` (https://developer-docs.amazon/sp-api/reference/getshipmentitemsbyshipmentid.md) : `ShipmentId`, `SellerSKU`, `FulfillmentNetworkSKU`, `QuantityShipped`, `QuantityReceived`, `QuantityInCase`, `ReleaseDate`, `PrepDetailsList`. Débit : 2 requêtes/s, rafale de 30. `getShipmentItems` permet aussi une recherche par date avec `LastUpdatedAfter` et `LastUpdatedBefore` (« The selection includes updates made by Amazon and by the seller »).
- Statuts d'envoi (FAQ, https://developer-docs.amazon/sp-api/docs/fulfillment-inbound-faq.md) : `CHECKED_IN`, `RECEIVING` (« the fulfillment center is receiving the shipment's contents »), `CLOSED` (« there are no further actions to take on the shipment »), `DELIVERED`, `IN_TRANSIT`, etc.
- **Aucune fonction officielle de rapprochement ni de déclaration d'écart** n'existe dans l'API Inbound. Le seul « discrepancy » de la FAQ concerne les transporteurs, pas les quantités reçues.
- Rapport complémentaire `GET_FBA_FULFILLMENT_INBOUND_NONCOMPLIANCE_DATA` (« FBA Inbound Performance Report ») : « Contains inbound shipment problems by product and shipment. Content updated daily. » Colonnes : `issue-reported-date`, `shipment-creation-date`, `fba-shipment-id`, `fba-carton-id`, `fulfillment-center-id`, `sku`, `fnsku`, `asin`, `product-name`, `problem-type`, `problem-quantity`, `expected-quantity`, `received-quantity`, `performance-measurement-unit`, `coaching-level`, `fee-type`, `currency`, `fee-total`, `problem-level`, `alert-status`.

### 2.5 Finances : remboursement client lié à la commande et au SKU

- v2024-06-19 `listTransactions` (https://developer-docs.amazon/sp-api/reference/listtransactions.md) :
  - `description` : « Describes the reasons for the transaction. **Example:** `Order Payment`, `Refund Order` ». C'est la seule mention documentée du remboursement.
  - `transactionType` : la doc n'indique que « **Possible value:** `Shipment` » (le modèle GitHub `finances_2024-06-19.json` n'en dit pas plus). → La valeur exacte du type pour un remboursement n'est **pas documentée**.
  - `relatedIdentifiers.relatedIdentifierName` : `ORDER_ID`, `SHIPMENT_ID`, `FINANCIAL_EVENT_GROUP_ID`, `REFUND_ID`, `INVOICE_ID`, `DISBURSEMENT_ID`, `TRANSFER_ID`, `DEFERRED_TRANSACTION_ID`, `RELEASE_TRANSACTION_ID`, `SETTLEMENT_ID`. Seuls `ORDER_ID` et `FINANCIAL_EVENT_GROUP_ID` servent de filtre.
  - `items[].contexts` → `ProductContext` : `asin`, `sku`, `quantityShipped`, `fulfillmentNetwork`. `items[].relatedIdentifiers` : `ORDER_ADJUSTMENT_ITEM_ID`, `COUPON_ID`, `REMOVAL_SHIPMENT_ITEM_ID`, `TRANSACTION_ID`.
  - Débit : 0,5 requête/s, rafale de 10 ; « If `PostedAfter` and `PostedBefore` are more than 180 days apart, the response is empty. » ; « Financial events might not include orders from the last 48 hours. »
  - Guide https://developer-docs.amazon/sp-api/docs/list-transactions-by-order.md : utile « for locating events that happened after the original order date, such as refunds… » ; appel avec `relatedIdentifierName=ORDER_ID` ; rôle **Finance and Accounting**.
- v0 (modèle https://raw.githubusercontent.com/amzn/selling-partner-api-models/main/models/finances-api-model/financesV0.json) :
  - `RefundEventList` : « A list of refund events. » (de type `ShipmentEvent` : `AmazonOrderId`, `ShipmentItemAdjustmentList`).
  - `ShipmentItem.SellerSKU`, `OrderAdjustmentItemId` (« defined for refunds, guarantee claims, and chargeback events »), `QuantityShipped`.
  - `AdjustmentEvent.AdjustmentType` = `FBAInventoryReimbursement` : « An FBA inventory reimbursement to a seller's account. This occurs if a seller's inventory is damaged. » `AdjustmentItem` : `Quantity`, `PerUnitAmount`, `TotalAmount`, `SellerSKU`, `FnSKU`, `ASIN`, `TransactionNumber`.
  - → Rapprochement : `RefundEvent(AmazonOrderId, SellerSKU)` ↔ retour `(order-id, sku)` ↔ remboursement `(amazon-order-id, sku)`.

### 2.6 Débits du Reports API (pages de référence)

`createReport` : 0,0167 requête/s, rafale de 15 · `getReports` : 0,0222/s, rafale de 10 · `getReport` : 2/s, rafale de 15 · `getReportDocument` : 0,0167/s, rafale de 15 (index `llms.txt`, résumés des pages `reference/*.md`).
`dataStartTime` : « … The default is now… Not all report types make use of this. » (createreport.md). Aucun débit propre au ledger n'est documenté.

### 2.7 Déposer une réclamation par API : impossible (vérifié)

- Support API v2025-02-01 (https://developer-docs.amazon/sp-api/docs/support-api.md) : « You can list a selling partner's support cases, retrieve the details and status of a specific case, and review the full history of contacts… » Disponible dans tous les magasins, pour les vendeurs seulement, régions NA, EU et FE. Rôle **Selling Partner Support (Restricted)**.
- Modèle officiel `support_2025-02-01.json` (GitHub amzn) : **trois opérations seulement** : `POST /support/2025-02-01/cases` = `listCases` (une **recherche**, pas une création), `GET …/cases/{caseId}` = `getCase`, `GET …/cases/{caseId}/contacts` = `listContacts`. Il n'existe aucune opération pour créer un cas, y répondre ou joindre un fichier. `Case.status` : `RESOLVED`, `TRANSFERRED`, `PENDING_MERCHANT_ACTION`, `PENDING_AMAZON_ACTION`. Débit : 0,1 requête/s, rafale de 10.
  (La page des rôles parle de « retrieve, search, and manage support cases », mais le modèle n'expose aucune écriture.)
- Action Items / Action Plans v2026-06-01 (nouveaux, 28/10/2026) : les modèles ne contiennent aucun type lié aux remboursements, aux réclamations, aux pertes ou aux dommages (recherche dans les modèles JSON).
- → Un outil peut **détecter, préparer et suivre** (avec le `case-id` du rapport Remboursements et `getCase`), mais la réclamation se dépose **à la main dans Seller Central**.

---

## 3. Politique de remboursement : annonces officielles lues (ANNONCE, pas la page de politique)

Toutes ces annonces viennent du compte **News_Amazon** (« News and Announcements ») et ont été lues mot à mot.

1. **US, en vigueur le 10/03/2025** — https://sellercentral.amazon.com/seller-forums/discussions/t/68864b6f-0ab8-41ef-be18-069c33df6336 (même texte côté UE : …/a941ac02-d389-409a-9d62-00ab9db5bc4a)
   - « Effective March 10, 2025, we'll reimburse you based on the product **manufacturing cost** of the affected inventory. » Le coût exclut « shipping, handling, customs duties, or other costs ». Le vendeur peut le déclarer lui-même ; sinon Amazon applique son estimation (« Manage Your Manufacturing Cost » dans l'« Inventory Defect and Reimbursement portal »).
   - « We now offer **automatic reimbursements for items lost in our fulfillment centers** … eliminating the need for you to submit a claim. »
   - « For items that are lost or damaged after a customer order … we'll continue to reimburse you for the sales price on the original order minus applicable fees. »
2. **US, à partir du 09/01/2025 et du 15/01/2025** — https://sellercentral.amazon.com/seller-forums/discussions/t/5ea3aa16-d268-4ec6-af9e-a2af448bb46b
   - « Starting January 15, 2025, we'll proactively reimburse you for … items that are lost in our fulfillment centers … which you can track in the Reimbursements report. »
   - « Almost all reimbursement claims related to warehouse lost and damaged and customer returns cases will now be proactively reimbursed. … if you do not receive an automatic reimbursement … you will need to file a manual claim. Additionally, all removal claims will still need to be filed manually. »
   - Fenêtres : entrepôt « no later than 60 days after the item was reported lost or damaged » ; retours clients « between 45-105 days after the customer refund or replacement date » ; retrait perdu en transit « 15-75 days from the shipment-creation date » ; autres retraits « within 60 days of the shipment being delivered back to you ». Mêmes règles au UK : https://sellercentral.amazon.co.uk/seller-forums/discussions/t/9a92846d-41f8-4ad7-b59a-f946efdcc2b4
3. **Annonce la plus récente trouvée, en vigueur le 15/10/2025** — https://sellercentral.amazon.com/seller-forums/discussions/t/d8f9a56c-882f-437c-ad34-cccd11cfa465
   - « Lost or damaged items: Within 60 days of reported loss or damage · Customer returns: Between 45-105 days after customer refund or replacement · Removal orders lost: Between 15-135 days from shipment creation · Removal orders damaged: 120 days from shipment delivery date · Removal orders grading: 120 days from date item was removed from our fulfilment network · Re-evaluation requests: Within 90 days of initial claim ».
4. **UE, plus ancienne, en vigueur le 05/09/2024** — https://sellercentral-europe.amazon.com/seller-forums/discussions/t/e62a8ace-3875-433c-8ef1-bb27a29b17c4
   - Seul texte officiel lu qui chiffre les **envois entrants** : « Units missing from shipments sent to Amazon fulfillment centers: No sooner than 15 calendar days from the shipment delivery date but no later than 60 calendar days. » Les annonces de 2025 ne reprennent pas ce cas, donc son délai actuel est **NON VÉRIFIÉ**.

**Limites** : ce sont des annonces, pas la page de politique ; le marché auquel s'applique l'annonce du 15/10/2025 n'est pas précisé (elle est publiée sur .com, avec l'orthographe britannique « Fulfilment ») ; aucune annonce de 2026 n'a été trouvée. Elles peuvent avoir été remplacées. **À relire dans Seller Central connecté avant d'en faire une règle**. Elles restent « non bloquantes » au sens du registre.

---

## 4. NON VÉRIFIÉ (et ce qu'on a essayé)

| Point | Ce qu'on a essayé | Résultat |
|---|---|---|
| Page de politique « FBA inventory reimbursement policy » (G200213130) US, UE, UK, FR | `curl` et WebFetch sur sellercentral.amazon.com, sellercentral-europe.amazon.com, .co.uk, .fr `/help/hub/reference/external/G200213130` | La page ne s'affiche qu'avec JavaScript, sans contenu lisible (« You need to enable JavaScript »). L'appel de l'API interne de l'aide a été refusé par le garde-fou de la session : on ne l'a pas contourné. |
| Éligibilité détaillée (bon état du compte, catégories exclues, preuves exigées : factures, preuve d'envoi) | Mêmes pages | Seulement dans des posts de vendeurs ou de prestataires → non retenu |
| Délai actuel pour les **envois entrants** | Annonces de 2025 | Absent ; seule l'annonce UE de 09/2024 donne 15–60 jours |
| Ce qui est automatique ou non pour les entrants, et le calcul exact par marché (UE et US) | Annonces | Seules les règles générales du point 3 sont connues |
| Codes de motif d'ajustement du ledger (M, E, D, F, Q, 5, 6, 7…) et leur sens | Doc des rapports FBA, `llms.txt`, dossier `schemas/reports` du dépôt GitHub (API GitHub non autorisée pour ce dépôt dans la session ; page HTML sans liste) | Absents de la doc SP-API → **ne pas coder en dur** ; utiliser la vue synthèse (`Lost`, `Damaged`, `Found`) |
| Sens de `Reconciled Quantity` / `Unreconciled Quantity` | Doc des rapports FBA | Seuls les noms des colonnes sont donnés |
| Valeurs de `reason` (Remboursements), de `detailed-disposition`, `reason`, `status` (Retours) | Doc des rapports FBA | Non listées |
| Historique du rapport Remboursements et du rapport Retours (jusqu'où remonter) | Doc des rapports, FAQ du Reports API | Non indiqué (seul le ledger dit 18 mois) |
| Valeur de `transactionType` d'un remboursement (v2024-06-19) | Référence et modèle GitHub | Seul `Shipment` est documenté ; « Refund Order » n'est qu'un exemple de `description` |

---

## 5. Conséquences pour l'outil (à porter au registre des règles avant le code)

- Règles de **détection** sourçables dès maintenant (VÉRIFIÉ) : écart entrant v0 `QuantityShipped − QuantityReceived` sur un envoi `CLOSED` ; Lost + Damaged − Found (ledger synthèse) − déjà remboursé ; remboursement client sans retour ni remboursement correspondant.
- **Délais de réclamation** : « non sourcé » au sens strict (annonces seulement) → affichage indicatif, jamais bloquant.
- **Montants** : ne pas les calculer ; afficher ce qu'Amazon a versé (`amount-total`). La règle « coût de fabrication » ne vient que d'une annonce.
- **Dépôt** : manuel dans Seller Central ; suivi possible par `getCase` (rôle restreint, à demander) et par la colonne `case-id` du rapport Remboursements.
- Rôles à prévoir : Amazon Fulfillment (rapports), Finance and Accounting (Finances), Selling Partner Support (Restricted) (suivi des cas, facultatif).
