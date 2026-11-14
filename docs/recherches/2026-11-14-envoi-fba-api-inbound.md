# Envoi FBA par l'API Fulfillment Inbound v2024-03-20 — vérification aux sources officielles

Lu le **14/11/2026** (heure de Paris). Cas visé : vendeur professionnel neuf, boutique **amazon.fr**, région SP-API **EU**,
envoi **en colis** (Small Parcel Delivery, SPD) depuis la France vers FBA. Rien de mémoire, aucun blog.

**Règle de lecture**

- **VÉRIFIÉ** : lu en entier sur une page officielle (developer-docs.amazon, modèle JSON `amzn/selling-partner-api-models`,
  sell.amazon.fr, grille tarifaire officielle), avec extrait cité.
- **VÉRIFIÉ (extrait)** : vu seulement dans un extrait de moteur de recherche sur un domaine officiel.
- **NON VÉRIFIÉ** : source officielle illisible, muette ou contradictoire.
- **Analyse** : déduction pour l'outil, pas un fait Amazon.

**Sources lues** (pages `.md` servies par `developer-docs.amazon`, miroir texte de `developer-docs.amazon.com`, date `updatedAt` en tête de page)

| Code | Source | Date |
|---|---|---|
| M | Modèle officiel `https://raw.githubusercontent.com/amzn/selling-partner-api-models/main/models/fulfillment-inbound-api-model/fulfillmentInbound_2024-03-20.json` | lu le 14/11/2026 |
| M0 | Modèle v0 `…/fulfillment-inbound-api-model/fulfillmentInboundV0.json` et https://developer-docs.amazon/sp-api/reference/getlabels.md | 2026-09-10 |
| G1 | https://developer-docs.amazon/sp-api/docs/fulfillment-inbound-api.md | 2026-09-09 |
| G2 | https://developer-docs.amazon/sp-api/docs/create-an-inbound-shipment.md | 2026-09-09 |
| G3 | https://developer-docs.amazon/sp-api/docs/create-amazon-partnered-carrier-shipment.md | 2026-09-09 |
| G4 | https://developer-docs.amazon/sp-api/docs/create-non-partnered-carrier-shipment.md | 2026-09-09 |
| G5 | https://developer-docs.amazon/sp-api/docs/additional-functionality-fulfillment-inbound.md | 2026-09-09 |
| G6 | https://developer-docs.amazon/sp-api/docs/fulfillment-inbound-faq.md | 2026-09-09 |
| G7 | https://developer-docs.amazon/sp-api/docs/fulfillment-inbound-api-rate-limits.md | 2026-09-09 |
| G8 | Pages de référence : `…/reference/getinboundoperationstatus.md`, `listplacementoptions.md`, `createinboundplan.md`, `setpackinginformation.md`, `listtransportationoptions.md`, `cancelinboundplan.md`, `listprepdetails.md`, `setprepdetails.md`, `createmarketplaceitemlabels.md` | 2026-09-10 |
| G9 | https://developer-docs.amazon/sp-api/docs/sp-api-sandbox.md | 2026-10-28 |
| G10 | https://developer-docs.amazon/sp-api/docs/roles-in-the-selling-partner-api.md | 2026-11-12 |
| G11 | https://developer-docs.amazon/sp-api/docs/store-identifiers.md (2026-10-23) et `…/docs/sp-api-endpoints.md` (2026-09-09) | — |
| R1 | Grille officielle « Rate Card — Fulfilment by Amazon (FBA), Effective as of 2 November 2026 », https://m.media-amazon.com/images/G/02/sell/images/261014-FBA-Rate-Card-EN.pdf (et `…-FR.pdf`), page 23 sur 33 | lu le 14/11/2026 |
| T1 | https://sell.amazon.fr/expedie-par-amazon (FR et `/en/`), https://sell.amazon.fr/tarifs, https://sell.amazon.fr/en/solutions-conformite/commerce-international | lu le 14/11/2026 |
| **Illisible** | Pages d'aide Seller Central (`sellercentral.amazon.fr/help/hub/reference/external/G201119120`, `…/G200280260`, `…/GC3Q44PBK8BXQW3Z`, `sellercentral.amazon.co.uk/…/GV6GL3KJRDPT8TNY`, `…/GRND5GXAPBE4Z9PX`, `…/G200141500`) : la page renvoie « You need to enable JavaScript to run this app. » | contenu non lu |

Repères communs (VÉRIFIÉ) :

- Point d'accès EU : `https://sellingpartnerapi-eu.amazon.com` (G11 : « Europe (Ireland, Spain, UK, France, … ) | <https://sellingpartnerapi-eu.amazon.com> | eu-west-1 »).
- amazon.fr : `marketplaceId` = **A13V1IB3VIYZZH** (G11 : « | France | A13V1IB3VIYZZH | FR | »).
- France couverte par la v2024-03-20 (G6 : « available in the following Amazon stores: … Spain · UK · France · … »). Toutes les opérations : « Regions NA, EU, FE » (G1).
- Chemins communs : préfixe `/inbound/fba/2024-03-20` (M).

---

## 1. Déroulé complet des opérations (colis, depuis la France)

### 1.0 Ordre documenté par Amazon

G2 donne 12 étapes quand le contenu des cartons est connu : « Step 1. Create an inbound plan · Step 2. Determine which SKUs can be packed together ·
Step 3. Provide box content information · Step 4. Generate and view options for destination fulfillment centers · Step 5. Input transportation data
and generate transportation options · Step 6. Generate delivery window options · Step 7. Review shipment splits and transportation options ·
Step 8. Select shipping option · Step 9. Select transportation options · Step 10. Print labels · Step 11. Send your shipments … · Step 12. Providing
tracking information ». **VÉRIFIÉ**

Pour un **colis**, le contenu des cartons doit être connu à l'avance : G6 « If you don't know the carton-level information upfront, you can only
create a Less Than Truckload/Full Truckload (LTL/FTL) shipment. » **VÉRIFIÉ**

Le tutoriel « propre transporteur » (G4) fixe l'ordre détaillé suivant (étapes 1 à 20) : createInboundPlan → generatePackingOptions →
listPackingOptions → confirmPackingOption → setPackingInformation → generatePlacementOptions → listPlacementOptions →
generateTransportationOptions → listTransportationOptions → generateDeliveryWindowOptions → listDeliveryWindowOptions → getShipment →
**confirmPlacementOption** → confirmDeliveryWindowOptions → **confirmTransportationOptions** → getShipment → getLabels (v0) →
listInboundPlanBoxes → updateShipmentTrackingDetails. **VÉRIFIÉ** (G4, titres « Step 1 » à « Step 20 »).

Toutes les opérations POST sont asynchrones : G3 « POST operations are asynchronous. Check the status of a POST operation by passing its
`operationId` to `getInboundOperationStatus`. » **VÉRIFIÉ**

### 1.1 Tableau des opérations

Débits : **valeur du modèle M et des pages de référence G8** (requêtes/seconde | rafale). Quand la page G7 donne autre chose, c'est signalé (voir 1.3).

| # | Opération | Méthode et chemin (après `/inbound/fba/2024-03-20`) | Corps / paramètres principaux (M) | Réponse (M) | Débit |
|---|---|---|---|---|---|
| 1 | createInboundPlan | `POST /inboundPlans` | obligatoires : `destinationMarketplaces` (1 seul élément), `items` (1 à 2 000), `sourceAddress` ; facultatif `name` (1-40 car.) | `inboundPlanId` + `operationId` | 2 \| 2 |
| 2 | generatePackingOptions | `POST /inboundPlans/{inboundPlanId}/packingOptions` | aucun corps | `operationId` | 2 \| 2 |
| 3 | listPackingOptions | `GET /inboundPlans/{inboundPlanId}/packingOptions` | `pageSize`, `paginationToken` | `packingOptions[]` | 2 \| 6 |
| 3b | listPackingGroupItems | `GET /inboundPlans/{id}/packingGroups/{packingGroupId}/items` | pagination | articles du groupe | 2 \| 30 |
| 4 | confirmPackingOption | `POST /inboundPlans/{id}/packingOptions/{packingOptionId}/confirmation` | aucun corps | `operationId` | 2 \| 2 |
| 5 | setPackingInformation | `POST /inboundPlans/{id}/packingInformation` | `packageGroupings[]` → `packingGroupId` (ou `shipmentId`) + `boxes[]` | `operationId` | 2 \| 2 |
| 6 | generatePlacementOptions | `POST /inboundPlans/{id}/placementOptions` | corps : `customPlacement` « only used for the India (IN - A21TJRUUN4KGV) marketplace » → vide pour la France | `operationId` | 2 \| 2 |
| 7 | listPlacementOptions | `GET /inboundPlans/{id}/placementOptions` | pagination | `placementOptions[]` (fees, discounts, shipmentIds, expiration, status) | 2 \| 6 |
| 8 | generateTransportationOptions | `POST /inboundPlans/{id}/transportationOptions` | `placementOptionId` + `shipmentTransportationConfigurations[]` (`shipmentId`, `readyToShipWindow.start`, `contactInformation` facultatif) | `operationId` | 2 \| 2 |
| 9 | listTransportationOptions | `GET /inboundPlans/{id}/transportationOptions` | `placementOptionId`, `shipmentId`, pagination | `transportationOptions[]` | 2 \| 6 |
| 10 | generateDeliveryWindowOptions | `POST /inboundPlans/{id}/shipments/{shipmentId}/deliveryWindowOptions` | aucun corps | `operationId` | 2 \| 30 |
| 11 | listDeliveryWindowOptions | `GET /inboundPlans/{id}/shipments/{shipmentId}/deliveryWindowOptions` | pagination | `deliveryWindowOptions[]` | 2 \| 30 |
| 12 | getShipment | `GET /inboundPlans/{id}/shipments/{shipmentId}` | — | `Shipment` | 2 \| 6 |
| 13 | **confirmPlacementOption** | `POST /inboundPlans/{id}/placementOptions/{placementOptionId}/confirmation` | aucun corps | `operationId` | 2 \| 2 |
| 14 | confirmDeliveryWindowOptions | `POST /inboundPlans/{id}/shipments/{shipmentId}/deliveryWindowOptions/{deliveryWindowOptionId}/confirmation` | aucun corps | `operationId` | 2 \| 30 |
| 15 | **confirmTransportationOptions** | `POST /inboundPlans/{id}/transportationOptions/confirmation` | `transportationSelections[]` (`shipmentId`, `transportationOptionId`, `contactInformation` facultatif) | `operationId` | 2 \| 2 |
| 16 | getLabels (**v0**) | `GET /fba/inbound/v0/shipments/{shipmentId}/labels` | `PageType`, `LabelType` obligatoires ; `shipmentId` = **shipmentConfirmationId** | `payload.DownloadURL` | 2 \| 30 |
| 17 | listInboundPlanBoxes / listShipmentBoxes | `GET /inboundPlans/{id}/boxes` · `GET /inboundPlans/{id}/shipments/{shipmentId}/boxes` | pagination | cartons, `boxId` | 2 \| 6 · 2 \| 30 |
| 18 | updateShipmentTrackingDetails | `PUT /inboundPlans/{id}/shipments/{shipmentId}/trackingDetails` | `trackingDetails.spdTrackingDetail.spdTrackingItems[]` (`boxId`, `trackingId`) | `operationId` | 2 \| 2 |
| — | listInboundPlanItems | `GET /inboundPlans/{id}/items` | pagination | `items[]` (asin, fnsku, msku, labelOwner, prepInstructions, quantity…) | 2 \| 6 |
| — | getInboundPlan | `GET /inboundPlans/{id}` | — | `InboundPlan` (status `ACTIVE`, `VOIDED`, `SHIPPED`, `ERRORED`) | 2 \| 6 |
| — | cancelInboundPlan | `PUT /inboundPlans/{id}/cancellation` | aucun corps | `operationId` | 2 \| 2 |
| — | getInboundOperationStatus | `GET /operations/{operationId}` | — | `InboundOperationStatus` | 2 \| 6 |

Tout le tableau : **VÉRIFIÉ** (M, chemins `paths`, `operationId`, schémas de réponse, tableaux « Usage Plan » des descriptions).

### 1.2 Détail par étape

**1. createInboundPlan** — **VÉRIFIÉ** (M)

- `CreateInboundPlanRequest` : « required: destinationMarketplaces, items, sourceAddress ». `destinationMarketplaces` : « Currently only one marketplace can be selected in this request. » (minItems 1, maxItems 1).
- `ItemInput` : « required: labelOwner, msku, prepOwner, quantity ».
  - `msku` 1-255 car. ; `quantity` 1 à 500 000 ;
  - `labelOwner` et `prepOwner` : `AMAZON`, `SELLER`, `NONE` ;
  - `expiration` facultatif, format `YYYY-MM-DD` : « Items with the same MSKU but different expiration dates cannot go into the same box. » ;
  - `manufacturingLotCode` facultatif, 1-256 car. (« The manufacturing lot code. »).
- `AddressInput` : « required: addressLine1, city, countryCode, name, phoneNumber, postalCode » ; `countryCode` ISO 3166-1 alpha-2 (« ^[A-Z]{2}$ ») ; `companyName`, `email`, `addressLine2`, `stateOrProvinceCode` facultatifs ; `city` 30 car. max, `name` 50 car. max, `phoneNumber` 20 car. max.
- Réponse : `inboundPlanId` (38 car.) et `operationId`.
- G2 : « Multiple expiration dates per SKU on a single inbound plan are not supported. » et « createInboundPlan generates initial shipment IDs … These IDs are different from the `shipmentConfirmationIDs` that are generated with the confirmPlacementOption operation. The `shipmentConfirmationID` is the identifier that appears on labels (for example, `FBA1234ABCD`). »

**2-4. Options d'emballage** — **VÉRIFIÉ** (G2, G3, G6, M)

- G2 : « A `packingGroup` represents SKUs that can be packed together, while SKUs with different requirements go into separate packing groups. »
- `PackingOption` (M) : `packingOptionId`, `packingGroups[]`, `fees[]`, `discounts[]`, `expiration`, `status` (« `OFFERED`, `ACCEPTED`, `EXPIRED` »), `supportedConfigurations[]` (`boxPackingMethods`, `boxRequirements.weight` {minimum, maximum, unit}, `shippingRequirements` {modes, solution}).
- G6 : « `listPackingOptions` returns one option because it is designed to provide the most optimized packing solution based on the input criteria. This is the expected behavior. »
- G3 : « You can only confirm one option per inbound plan. »

**5. setPackingInformation** — **VÉRIFIÉ** (M, G2, G3)

- `PackageGroupingInput` : `boxes` (1 à 5 000) + `packingGroupId` **ou** `shipmentId` : « The `PackingGroupId` can only be provided before placement confirmation … The `ShipmentId` can only be provided after placement confirmation ».
- `BoxInput` : « required: contentInformationSource, dimensions, quantity, weight » ; `quantity` 1 à 10 000 (« The number of containers where all other properties like weight or dimensions are identical. ») ; `items[]` = `ItemInput` (msku, quantity, labelOwner, prepOwner, expiration, manufacturingLotCode).
- `Dimensions` : `length`, `width`, `height`, `unitOfMeasurement` = `IN` ou `CM`. `Weight` : `value`, `unit` = `LB` ou `KG`.
- `contentInformationSource` : `BOX_CONTENT_PROVIDED` ; `MANUAL_PROCESS` (« This service incurs charges. ») ; `BARCODE_2D`. G2 : avec `BARCODE_2D` ou `MANUAL_PROCESS`, « You must leave `items` empty ».
- G2 : « If you do not call setPackingInformation, there may be defects in the receiving process and fees for manual processing. »
- G2 : modifier les cartons après génération du placement oblige à rappeler `generatePlacementOptions` ; « Discarding packing information is not currently supported. » (il faut un nouveau plan).

**6-7. Placement** — **VÉRIFIÉ** (G2, M) — détail des frais au point 4.

- G2 : « Each option can include fees or discounts determined by an algorithm during shipment creation, not calculated using set rates. »
- G2 : « Call the `generatePlacementOptions` operation to regenerate placement options when they expire. »

**8-9. Transport** — **VÉRIFIÉ** (G3, G4, M)

- Corps SPD minimal (G3) : `{"placementOptionId": "pl…", "shipmentTransportationConfigurations": [{"readyToShipWindow": {"start": "yyyy-mm-ddT00:00:00Z"}, "shipmentId": "sh…"}]}`. G4 ajoute `contactInformation` {name, phoneNumber, email}.
- `readyToShipWindow` (M) : « This is the pick-up date or 'ready to ship' date, not an estimated delivery date. »
- G3 : « Include all shipment IDs within the selected placement option. »
- `TransportationOption` (M) : `carrier` {name, alphaCode}, `shippingMode` (`GROUND_SMALL_PARCEL`, `FREIGHT_LTL`, … `AIR_SMALL_PARCEL`, `AIR_SMALL_PARCEL_EXPRESS`), `shippingSolution` (`AMAZON_PARTNERED_CARRIER`, `USE_YOUR_OWN_CARRIER`), `quote` {cost, expiration, voidableUntil}, `preconditions[]`.
- Pour un colis : G4 « For small parcel deliveries, choose the option where `shippingMode` is `GROUND_SMALL_PARCEL` » ; propre transporteur : « ensure that `shippingSolution` is `USE_YOUR_OWN_CARRIER` ».
- G3 : « Transportation options are paginated with a default pageSize of 10 and a maximum of 20 results. Always review all pages using nextToken before concluding that PCP options are unavailable for a shipment. »
- G3 : « For small parcel deliveries, ensure that all shipments use the same carrier. »

**10-11, 14. Fenêtre de livraison** (obligatoire avec son propre transporteur) — **VÉRIFIÉ** (G2, G4, M)

- G2 : « You must confirm transportation options for all shipment types. For non-partnered shipments, you must also specify a delivery window. »
- G4 : « You must generate delivery windows for all `shipmentId`s within the inbound plan. » ; « You must schedule your shipment delivery within **45 days** for domestic shipments and **75 days** for international shipments. … sellers must specify a delivery window of **7 days** for domestic shipments or **14 days** for international shipments. »
- `DeliveryWindowOption` (M) : `deliveryWindowOptionId`, `startDate`, `endDate`, `validUntil`, `availabilityType` (« `AVAILABLE`, `BLOCKED`, `CONGESTED`, `DISCOUNTED` »), `discounts[]`.
- Description de confirmDeliveryWindowOptions (M) : « A placement option must be confirmed prior to use of this API. Once confirmed, new delivery window options cannot be generated, but the chosen delivery window option can be updated before shipment closure. »

**12. getShipment** — **VÉRIFIÉ** (M, G2)

- `Shipment` : `shipmentId`, `shipmentConfirmationId` (« which shows up on labels (for example, `FBA1234ABCD`) »), `placementOptionId`, `destination` {destinationType `AMAZON_OPTIMIZED` | `AMAZON_WAREHOUSE`, address, warehouseId}, `source`, `status`, `selectedTransportationOptionId`, `selectedDeliveryWindow`, `trackingDetails`, `dates`.
- `status` (M) : « typically start as `UNCONFIRMED`, then transition to `WORKING` after a placement option has been confirmed, and then to `READY_TO_SHIP` once labels are generated. » Liste complète des statuts : G6 (ABANDONED, CANCELED, CHECKED_IN, CLOSED, DELETED, DELIVERED, IN_TRANSIT, MIXED, READY_TO_SHIP, RECEIVING, SHIPPED, UNCONFIRMED, WORKING).

**13. confirmPlacementOption** — **VÉRIFIÉ** (M, G2)

- M : « Confirms the placement option for an inbound plan. Once confirmed, it cannot be changed for the Inbound Plan. »
- G2 : « This option cannot be reversed after it is selected. » ; il crée les `shipmentConfirmationId`.
- G2 : « You cannot provide packing information using Send to Amazon after confirming placement options. »

**15. confirmTransportationOptions** — **VÉRIFIÉ** (M, G2)

- M : « Once confirmed, new transportation options can not be generated or confirmed for the Inbound Plan. »
- G2 : « For Amazon-partnered transportation options, this operation confirms that you accept the Amazon-partnered shipping estimate, agree to allow Amazon to charge your account for the shipping cost, and request that the Amazon-partnered carrier ship the inbound shipment. » ; « The estimated delivery date (delivery window) is a requirement for non-partnered carrier options and should not be populated for partnered carrier options. »
- G2 : « For non-partnered carrier shipments, you must confirm the anticipated delivery window … before you book your fulfillment center appointment. »

**16. getLabels (étiquettes de carton, API v0)** — **VÉRIFIÉ** (G1, G2, G6, M0)

- G1 : « The following v0 operations are not deprecated: getLabels, getBillOfLading, … Of these, `getLabels` and `getBillOfLading` are necessary to create shipments because they print box labels ».
- G2 : « The value of `shipmentId` in the `getLabels` request must be the `shipmentId` (from v0) or the `shipmentConfirmationId` (from v2024-03-20). Do not use the `shipmentId` from v2024-03-20. »
- Paramètres (M0) : `PageType` (obligatoire), `LabelType` (obligatoire : `BARCODE_2D`, `UNIQUE`, `PALLET`), `NumberOfPackages`, `PackageLabelsToPrint` (doit correspondre aux `boxID` de listShipmentBoxes, sinon erreur `IncorrectPackageIdentifier`), `NumberOfPallets`, `PageSize` (max 1000), `PageStartIndex`.
- `PageType` utiles hors US (M0) : « PackageLabel_A4_2 | Two labels per A4 label sheet. », « PackageLabel_A4_4 | Four labels per A4 label sheet. », « PackageLabel_Thermal_NonPCP | For use of a thermal printer. Supports non-Amazon-partnered shipments. ». « Submitting a PageType value that is not supported in your marketplace returns an error. »
- Réponse (M0) : `payload.DownloadURL` — « URL to download the label for the package. Note: The URL will only be valid for 15 seconds ».
- G2 : « Retrieving carton labels with `getLabels` does not change the shipment status to `ready_to_ship`. For a shipment status to become `ready_to_ship`, you must generate labels on Send to Amazon. »
- Code-barres unique par carton (G2) : « Append `U` and `000001` in the shipment ID … `FBA1MMD8D0U000001`, `FBA1MMD8D0U000002` … ».
- **Format PDF** : le mot « PDF » n'apparaît ni dans la page getLabels ni dans le modèle v0 pour les étiquettes (seul `getBillOfLading` dit « returns PDF document data »). **NON VÉRIFIÉ**.

**18. Suivi (propre transporteur)** — **VÉRIFIÉ** (G2, G4, M)

- G2 : « For small parcel shipments, you must provide an array of box IDs and associated tracking IDs. »
- G4 : « You must update the tracking IDs for all of the boxes within your inbound plan. » ; `trackingId` 1-64 car. (M).

**listInboundPlanItems** — **VÉRIFIÉ** (G5) : « A successful response includes item information such as MSKU, ASIN, FNSKU, label owner, quantity, expiration date, manufacturing lot code, prep instructions, and packing group. »

**cancelInboundPlan** — **VÉRIFIÉ** (M, G5, G6)

- M : « Charges may apply if the cancellation is performed outside of a void window. The window for Amazon Partnered Carriers is 24 hours for Small Parcel Delivery (SPD) and one hour for Less-Than-Truckload (LTL) ».
- G6 : « The charge restrictions don't apply for non-partnered carrier options. »
- G5 : vérification possible aussi par `getInboundPlan` (statut `VOIDED`).

**Modification après confirmation** — **VÉRIFIÉ** (G5) : generate/list/confirm `ShipmentContentUpdatePreview` ; « you can edit the number of units in a shipment by up to five percent or six units per SKU per shipment, whichever is greater. … To make changes beyond these limits, you must cancel the inbound plan and create a new one. »

**Interopérabilité Send to Amazon** — **VÉRIFIÉ** (G1) : « If you switch from the API to STA before you confirm your options (with `confirmPlacementOption` and `confirmTransportationOptions`), new options are generated in STA and all previous options are discarded. »

### 1.3 Quotas : écarts entre deux pages officielles

| Opération | Modèle M et page de référence (G8) | Page « Rate Limits » (G7) | Statut |
|---|---|---|---|
| getShipment | 2 \| 6 | 5 \| 6 | **NON VÉRIFIÉ** (contradiction) |
| listTransportationOptions | 2 \| 6 | 5 \| 6 | **NON VÉRIFIÉ** |
| getInboundOperationStatus | 2 \| 6 | 5 \| 6 | **NON VÉRIFIÉ** |
| listShipmentBoxes, listDeliveryWindowOptions | 2 \| 30 | 5 \| 30 | **NON VÉRIFIÉ** |
| listPrepDetails | aucun tableau dans M ; page G8 « \| n \| n \| » | 2 \| 30 | **NON VÉRIFIÉ** |
| getLabels (v0) | 2 \| 30 (M0, page de référence) | 5 \| 30 | **NON VÉRIFIÉ** |

G8 : « Selling partners whose business demands require higher throughput may have higher rate and burst values than those shown here. » et G7 : « The `x-amzn-RateLimit-Limit` response header, if available, specifies the operation's rate limits per account-application pair. » **VÉRIFIÉ**

**Analyse** : se régler sur la valeur la plus basse (2 req/s) et lire l'en-tête `x-amzn-RateLimit-Limit` ; les créations/confirmations ont une rafale de 2.

---

## 2. Opérations asynchrones (getInboundOperationStatus)

- Chemin : `GET /inbound/fba/2024-03-20/operations/{operationId}` ; `operationId` 36-38 car. **VÉRIFIÉ** (M)
- Réponse `InboundOperationStatus` : « required: operation, operationId, operationProblems, operationStatus ». **VÉRIFIÉ** (M)
- États `operationStatus` : « SUCCESS — Indicates a request has successfully finished processing. » ; « FAILED — Indicates a request has finished processing but is in a failed state. » ; « IN_PROGRESS — Indicates a request is still processing. » **VÉRIFIÉ** (M)
- `operationProblems[]` : `code`, `message`, `details`, `severity` (« Possible values: `WARNING`, `ERROR`. »). **VÉRIFIÉ** (M)
- G2 : « The response returns the request status and any non-blocking errors. Non-blocking errors are warnings that can be ignored (for example, when the address is suspected to be wrong, but progression is allowed anyway). » **VÉRIFIÉ**
- **Délai conseillé entre deux interrogations : aucune page lue n'en donne.** Ni G1-G8 ni M ne contiennent de durée d'attente ou de « polling ». **NON VÉRIFIÉ**. Seul repère officiel : le quota (2 req/s, rafale 6 selon M).
- Durée de validité des options : chaque option porte son `expiration` (packing, placement), `quote.expiration` (transport), `validUntil` (fenêtre). **VÉRIFIÉ** (M). Aucune durée chiffrée n'est donnée dans la doc. **NON VÉRIFIÉ**

---

## 3. Préparation (prep) et étiquetage des articles

### 3.1 listPrepDetails / setPrepDetails — **VÉRIFIÉ** (M, G5, G1)

- `GET /inbound/fba/2024-03-20/items/prepDetails?marketplaceId=…&mskus=…` ; `POST /inbound/fba/2024-03-20/items/prepDetails`.
- Corps setPrepDetails : `marketplaceId` + `mskuPrepDetails[]` (1 à 100) de { `msku`, `prepCategory`, `prepTypes[]` }.
- `prepCategory` : ADULT, BABY, FC_PROVIDED (non saisissable), FRAGILE, GRANULAR, HANGER, LIQUID, PERFORATED, SET, SHARP, SMALL, TEXTILE, UNKNOWN (non saisissable), NONE.
- `prepTypes` : ITEM_BLACK_SHRINKWRAP, ITEM_BLANKSTK, ITEM_BOXING, ITEM_BUBBLEWRAP, ITEM_CAP_SEALING, ITEM_DEBUNDLE, ITEM_HANG_GARMENT, ITEM_LABELING (« The FNSKU label must be applied to the item. »), ITEM_NO_PREP, ITEM_POLYBAGGING, ITEM_RMOVHANG, ITEM_SETCREAT, ITEM_SETSTK, ITEM_SIOC, ITEM_SUFFOSTK, ITEM_TAPING.
- Réponse listPrepDetails (`MskuPrepDetail`) : `prepCategory`, `prepTypes`, `prepOwnerConstraint` / `labelOwnerConstraint` (`AMAZON_ONLY`, `NONE_ONLY`, `SELLER_ONLY`), `allOwnersConstraint` (`MUST_MATCH`).
- G5 : « You can use `listPrepDetails` to determine which `prepOwner` and `labelOwner` values can be used in the createInboundPlan operation. … If these fields are empty in the response, you can select `AMAZON` or `SELLER`. If `allOwnersConstraint` is `MUST_MATCH`, `prepOwner` and `labelOwner` must match. »
- G5 : « Sellers must provide this information once for each MSKU in an Amazon store. Amazon saves this information for future shipments ».
- G5 : « If `PrepType` is `ITEM_NO_PREP`, you may still need to include a prep owner or label owner when you call `createInboundPlan`. »
- G1 : « You must call the `setPrepDetails` operation in order to retrieve prep details with the `listPrepDetails` operation. Prep details you add in Seller Central are not returned by `listPrepDetails`. »
- G5 : « Inventory that arrives at a fulfillment center without proper preparation or labeling might incur a preparation fee. »

### 3.2 labelOwner AMAZON vs SELLER — **VÉRIFIÉ**

- M (`LabelOwner`) : « `AMAZON` is not an accepted value in the US marketplace. » → accepté hors US.
- G2 : « `AMAZON_LABEL` is available only when you are enrolled in the FBA Label Service. »
- G2 : l'arrêt du service d'étiquetage concerne les **US** : « Starting January 1, 2026, the prep and item label services will no longer be available for FBA in the Amazon US store. »
- `PrepInstruction` (M, dans listInboundPlanItems / listShipmentItems) contient un champ `fee` (Currency) à côté de `prepType` et `prepOwner`.

### 3.3 Frais (Europe) — **VÉRIFIÉ** (R1, p. 23 « Optional Service Fees … Effective as of 2 November, 2026 »)

| Service | FR/DE/IT/ES/PL/NL/BE/IE (€) | Extrait |
|---|---|---|
| Service d'étiquetage, enveloppes (33 x 23 x 6 cm, < 960 g) | 0,38 | « Label service 0.38 0.38 4.23 » |
| Service d'étiquetage, colis (45 x 34 x 26 cm, < 11,9 kg) | 0,78 | « Label service 0.78 0.78 8.68 » |
| Service d'étiquetage, hors gabarit (< 31,5 kg) | 0,94 | « Label service 0.94 0.94 16.93 » |
| Ensachage / ensachage opaque / papier bulle / ruban (colis) | 0,75 / 0,84 / 1,00 / 0,59 | lignes « Bagging 0.75 », « Opaque bagging 0.84 », « Bubble wrap 1.00 », « Taping 0.59 » |
| Frais de traitement manuel (pas de contenu de carton) | 0,18 | « Manual processing fee1,2 0.15 0.18 » ; « You are charged for the number of units received » |

R1 : « If you use the FBA Prep Service, we'll prep your products for a per-unit fee. » (montants par unité.)

### 3.4 createMarketplaceItemLabels (étiquettes produit FNSKU imprimées par le vendeur) — **VÉRIFIÉ** (M, G5)

- `POST /inbound/fba/2024-03-20/items/labels`, débit 2 | 30.
- Corps : obligatoires `labelType` (`STANDARD_FORMAT`, `THERMAL_PRINTING`), `marketplaceId`, `mskuQuantities[]` (1 à 100 ; quantité 1 à 10 000) ; facultatifs `pageType` (A4_21, A4_24, A4_24_64x33, A4_24_66x35, A4_24_70x36, A4_24_70x37, A4_24i, A4_27, A4_40_52x29, A4_44_48x25, Letter_30), `width`/`height` (25 à 100, unité non précisée), `localeCode` (`fr_FR`).
- Réponse directe (pas d'`operationId`) : `documentDownloads[]` { `downloadType` « Possible values: `URL` », `uri`, `expiration` }.
- G5 : « Using this operation you can get item labels in the Amazon store language. »
- Frais : aucun frais mentionné pour cette opération. Format du fichier (PDF ?) non précisé. **NON VÉRIFIÉ**.

---

## 4. Frais de placement (placement fee)

- Champ API (M, `PlacementOption`) : `fees[]` et `discounts[]` de type `Incentive` { `description`, `target` (« Possible values: 'Placement Services', 'Fulfillment Fee Discount'. »), `type` (« `FEE`, `DISCOUNT` »), `value` {amount, code ISO 4217} }. **VÉRIFIÉ**
- Exemple officiel (G3/G4, en USD) : « "description": "Placement service fee represents service to inbound with minimal shipment splits and destinations of skus", "type": "FEE", "value": {"amount": 1.10, "code": "USD"}, "target": "Placement Services" ». **VÉRIFIÉ** (exemple US)
- G2 : « Each option can include fees or discounts determined by an algorithm during shipment creation, not calculated using set rates. … The rebate that your shipment is eligible for is provided during shipment creation. » **VÉRIFIÉ**
- G2 : « As of February 20, 2025, partial shipment splits are not available on the Send to Amazon workflow for standard-sized products. … refer to 2025 FBA inbound placement service fee » — lien vers `sellercentral.amazon.com` (US), illisible. **VÉRIFIÉ** (texte) / page liée **NON VÉRIFIÉE**
- **« Amazon-optimized » vs « envoi minimal »** : le modèle ne contient **aucun champ** qui nomme le type d'option de placement ; seule la `description` du frais (texte libre) et le nombre de `shipmentIds` les distinguent. `AMAZON_OPTIMIZED` n'existe que comme `destinationType` d'un envoi : « This can be empty if the destination type is `AMAZON_OPTIMIZED`. » (M). G1 : « If the seller selects a partnered carrier, meaning that `destinationType` is `AMAZON_OPTIMIZED`, then the destination fulfillment center address may differ from the actual address, or this field may be empty. Refer to the carton label for the correct address. » **VÉRIFIÉ**
- **Remise « emballage recommandé par Amazon »** (packing, pas placement) — G1 : « Sellers can … receive a fulfillment discount by following Amazon's packing recommendations. The recommended packing is only available when you pack in small parcel deliveries with each parcel weighing less than 15 kg (LTL/FTL not supported). » ; « available in the following Amazon stores: Spain · UK · France · Germany · Italy ». **VÉRIFIÉ**. Montant de la remise : page Seller Central `GV6GL3KJRDPT8TNY` illisible → **NON VÉRIFIÉ**.
- **Europe / France** : la grille UE 2026 (R1, 33 p.) ne contient pas de frais de placement à l'envoi (constat déjà fait dans `2026-11-14-frais-fba-europe.md`). **VÉRIFIÉ pour l'absence dans R1** ; existence d'un frais de placement facturé en France : **NON VÉRIFIÉ** (pages d'aide illisibles).

**Analyse** : ne jamais calculer ce frais ; afficher tel quel `fees[]` et `discounts[]` renvoyés par `listPlacementOptions` (et ceux de `listPackingOptions`), avec la devise renvoyée.

---

## 5. Transporteur partenaire Amazon (PCP) en France / UE

Les pages officielles **se contredisent** :

| Ce qui est écrit | Source | Statut |
|---|---|---|
| « Amazon-partnered carrier shipments are available only in the contiguous United States. For shipments outside this region, you must use your own carrier (non-partnered). » | G3 et G4 (note en tête) | VÉRIFIÉ (texte) |
| « In the EU region, you must first review and accept the terms and conditions of the carrier and the terms and conditions of Amazon's PCP. You can do this on Seller Central. If you attempt to use Amazon Selling Partner APIs to create an inbound shipment by using an Amazon-partnered carrier before accepting these terms and conditions, the service returns an error. » | G2 | VÉRIFIÉ (texte) |
| « refer to the Amazon's PCP to ensure that you follow the program instructions and guidelines for Europe (sellercentral.amazon.co.uk/gp/help/201119120) and US » | G2 | VÉRIFIÉ (texte) ; page liée illisible |
| « 90 € de crédits pour les frais d'expédition via le programme de transporteurs partenaires Amazon » (incitation nouveaux vendeurs FBA) | T1 sell.amazon.fr/expedie-par-amazon | VÉRIFIÉ |
| « Levier 4 — Programme des Transporteurs Partenaires Amazon : Amazon a négocié des tarifs avec des transporteurs partenaires pour l'envoi de votre stock vers les centres de distribution FBA. » | T1 sell.amazon.fr/tarifs | VÉRIFIÉ |
| « UPS — Ship small parcels with UPS from your domestic storage facility, cross-border UK<>EU into an FBA Fulfilment Centre and receive discounted partnered carrier rates » | T1 sell.amazon.fr/en/solutions-conformite/commerce-international | VÉRIFIÉ (cas Royaume-Uni ↔ UE) |

Conclusion : le PCP existe côté programme pour amazon.fr (T1), mais **sa disponibilité par l'API v2024-03-20 pour un envoi France → France n'est pas établie** (G3/G4 disent « US seulement », G2 décrit une condition UE). **NON VÉRIFIÉ**.

**Analyse** : l'outil ne doit rien supposer. Il affiche ce que `listTransportationOptions` renvoie (toutes les pages) ; si aucune option `AMAZON_PARTNERED_CARRIER` n'apparaît, seul le propre transporteur est proposé. Test à faire sur le vrai compte (lecture seule jusqu'à `listTransportationOptions`, puis `cancelInboundPlan`).

---

## 6. Rôle SP-API et sandbox

- Rôle : toutes les opérations v2024-03-20 → « Required roles (need at least one) | Amazon Fulfillment » (45 opérations listées dans G1). **VÉRIFIÉ**
- Le tutoriel G2 demande **aussi** le rôle Product Listing : « Approval for the Amazon Fulfillment role and the Product Listing role in your developer profile. » **VÉRIFIÉ**
- G10 : « The Amazon Fulfillment role provides access to Amazon fulfillment operations and shipping services such as Fulfillment by Amazon (FBA) … Role available to sellers? Yes ». **VÉRIFIÉ**
- Disponibilité : G1 « Availability: Sellers only ». **VÉRIFIÉ**
- Sandbox : G1 colonne « Sandbox : Static » ; G9 tableau « Fulfillment Inbound API | Static ». G9 : « The SP-API static sandbox uses pattern matching to return static, mock responses. » ; « Calling the sandbox endpoints returns static, mock responses … You can refer to these mock responses in the Swagger model JSON file ». Point d'accès : `https://sandbox.sellingpartnerapi-eu.amazon.com`. Débit sandbox : « rate = five requests per second; burst = 15 ». **VÉRIFIÉ**
- Le modèle M contient 90 blocs `x-amzn-api-sandbox` (réponses figées). **VÉRIFIÉ**

**Analyse** : le sandbox ne sert qu'à tester le format des appels ; aucune vraie option de placement, de transport ni de frais. Les vrais tests demandent le compte réel, avec annulation (`cancelInboundPlan`) avant toute confirmation.

---

## 7. Limites

| Limite | Valeur | Source et extrait | Statut |
|---|---|---|---|
| Boutiques par plan | 1 | M : « Currently only one marketplace can be selected in this request. » | VÉRIFIÉ |
| Lignes d'articles par createInboundPlan | 1 à 2 000 | M : `items` « maxItems: 2000 » | VÉRIFIÉ |
| Quantité par ligne | 1 à 500 000 | M : `quantity` « maximum: 500000 » | VÉRIFIÉ |
| SKU par plan / unités par SKU | **1 500 SKU, 10 000 unités par SKU** | G6 : « For one inbound plan, you can add a maximum of 1,500 SKUs and a maximum of 10,000 items for each SKU. » | VÉRIFIÉ — **contredit le modèle** (2 000 / 500 000) → retenir le plus strict |
| Dates d'expiration par SKU dans un plan | 1 | G6 : « Multiple expiration dates per SKU within a single inbound plan is not supported. » | VÉRIFIÉ |
| Types de cartons par groupe | 1 à 5 000 entrées `boxes` | M : `boxes` « maxItems: 5000 » | VÉRIFIÉ |
| Cartons identiques par entrée | 1 à 10 000 | M : `BoxInput.quantity` « maximum: 10000 » | VÉRIFIÉ |
| Dimensions / poids dans le schéma | 0 à 100 000 (bornes techniques, pas des règles logistiques) | M : `Dimensions`, `Weight` « maximum: 100000 » | VÉRIFIÉ |
| Poids de carton admis | **donné par l'API, option par option** | M : `PackingConfiguration` « Non-standard minimum and maximum box weights might be enforced. » ; `boxRequirements.weight` {minimum, maximum, unit} | VÉRIFIÉ |
| Emballage recommandé par Amazon | colis < 15 kg | G1 : « each parcel weighing less than 15 kg » | VÉRIFIÉ |
| Poids et dimensions maximum d'un carton en Europe (règle générale) | — | G6 renvoie à « Small-parcel delivery to Amazon » (`sellercentral.amazon.com/gp/help/G200280260`, US) ; versions FR illisibles | **NON VÉRIFIÉ** |
| Fenêtre de livraison (propre transporteur) | 7 jours (national), 14 jours (international) ; livraison sous 45 / 75 jours | G4 | VÉRIFIÉ |
| Annulation sans frais (PCP colis) | 24 h après confirmation | M (cancelInboundPlan), G5, G6 | VÉRIFIÉ |
| Modification après confirmation | ± 5 % ou 6 unités par SKU et par envoi (le plus grand) | G5 | VÉRIFIÉ |
| Validité de l'URL d'étiquettes getLabels | 15 secondes | M0 : « The URL will only be valid for 15 seconds » | VÉRIFIÉ |

---

## 8. Déroulé proposé pour l'outil (Analyse)

Principe : **rien n'est confirmé chez Amazon sans un clic explicite de l'utilisateur**, avec le montant affiché juste au-dessus. Les étapes de
lecture (generate/list) peuvent s'enchaîner seules ; les confirmations jamais.

| Écran | Appels | Ce que l'écran montre | Validation humaine |
|---|---|---|---|
| 0. Préparation des articles (une fois par SKU) | listPrepDetails ; setPrepDetails si vide ; listItemComplianceDetails si besoin | catégorie de prep, types, propriétaires autorisés | **Oui** : choix de `prepCategory` (enregistré chez Amazon pour tous les envois futurs) |
| 1. Brouillon d'envoi | — (local) | SKU, quantités, adresse d'expédition (adresse du compte), propriétaire prep/étiquette (filtré par les contraintes), date d'expiration et lot si utile | Oui : « Créer le plan chez Amazon » |
| 2. Création | createInboundPlan → getInboundOperationStatus | état ; avertissements `WARNING` affichés, `ERROR` bloquant | — |
| 3. Groupes d'emballage | generatePackingOptions → listPackingOptions → listPackingGroupItems | groupes de SKU à emballer ensemble, frais/remises, poids min/max de carton | **Oui** : confirmPackingOption (une seule option possible) |
| 4. Cartons | setPackingInformation | saisie par groupe : dimensions (cm), poids (kg), nombre de cartons identiques, contenu (`BOX_CONTENT_PROVIDED` par défaut) ; contrôle local du poids contre `boxRequirements` | Oui : « Envoyer les cartons » (modifiable tant que le placement n'est pas confirmé, avec régénération) |
| 5. Répartition | generatePlacementOptions → listPlacementOptions → getShipment par envoi | pour chaque option : nombre d'envois, destinations, **frais et remises renvoyés tels quels**, date d'expiration | Choix d'une option (pas encore de confirmation) |
| 6. Transport | generateTransportationOptions (date « prêt à expédier ») → listTransportationOptions (toutes les pages) | options colis (`GROUND_SMALL_PARCEL`), transporteur, partenaire ou non, devis et `voidableUntil` | Choix (pas encore de confirmation) ; même transporteur pour tous les envois colis |
| 7. Fenêtre de livraison (propre transporteur) | generateDeliveryWindowOptions → listDeliveryWindowOptions | fenêtres, disponibilité, remises, `validUntil` | Choix |
| 8. Récapitulatif et engagement | — | total : frais de placement + devis de transport + remises, irréversibilité, délai d'annulation | **Oui, deux clics distincts** : (a) **confirmPlacementOption** — irréversible ; (b) confirmDeliveryWindowOptions puis **confirmTransportationOptions** — engage le coût du transporteur partenaire |
| 9. Étiquettes | getShipment (→ `shipmentConfirmationId`) → listShipmentBoxes → getLabels v0 (`PageType` A4 ou thermique) ; createMarketplaceItemLabels si étiquetage vendeur | téléchargement immédiat (URL 15 s) ; rappel : statut « prêt à expédier » seulement via Send to Amazon | Impression |
| 10. Suivi | updateShipmentTrackingDetails (propre transporteur : un numéro par carton) ; getShipment pour l'état | état de l'envoi (WORKING → … → CLOSED) | Oui : saisie des numéros de suivi |
| — Annulation | cancelInboundPlan | délai restant avant frais (24 h si partenaire colis) | **Oui**, avec rappel des frais possibles |

Points de conception :

- File d'attente des appels réglée à ≤ 2 req/s, rafale 2 pour les créations et confirmations ; interroger `getInboundOperationStatus` avec attente croissante (délai non documenté par Amazon).
- Conserver `inboundPlanId`, `operationId`, les identifiants d'options et les `expiration` ; une option expirée se régénère, on ne la confirme pas.
- Si l'utilisateur passe sur Send to Amazon avant confirmation, les options de l'outil deviennent caduques (G1).
- Aucune valeur réglementaire ni tarif en dur : frais lus dans la réponse de l'API, sinon « non sourcé ».
- Tests : sandbox statique pour le format ; puis compte réel jusqu'à l'écran 7 compris, suivi d'un `cancelInboundPlan`, **avant** toute confirmation réelle.

---

## Annexe — non vérifié

- **Délai conseillé** entre deux appels `getInboundOperationStatus` et durée de traitement typique : aucune page officielle lue n'en parle.
- **Format des étiquettes** : PDF (ou ZIP) pour `getLabels` et `createMarketplaceItemLabels` non écrit dans la doc ; à constater sur un vrai appel.
- **PCP pour un envoi France → France par l'API** : contradiction G3/G4 (« contiguous United States ») contre G2 (conditions UE) et T1 (crédits PCP de 90 € sur amazon.fr).
- **Frais de placement facturés en France** : absents de la grille UE 2026 ; pages Seller Central illisibles.
- **Montant de la remise « emballage recommandé par Amazon »** en France : page `GV6GL3KJRDPT8TNY` illisible.
- **Poids et dimensions maximum d'un carton en Europe** : vus seulement dans des **forums** Seller Central (pas des pages d'aide) via un moteur de recherche — « Maximum box size: 63.5 cm on any side », « Weight range: 0.15 kg to 23 kg », « Boxes weighing 15 kg or more require "Team Lift" / "Heavy Package" labels » (https://sellercentral-europe.amazon.com/seller-forums/discussions/t/3c8efab2-0704-434f-bc9f-69d5eed30996). Message de forum ancien, non officiel : **ne pas utiliser comme règle**.
- **Quotas exacts** : écarts entre G7 et M/G8 (point 1.3).
- **Limites SKU par plan** : 1 500 (G6) contre 2 000 lignes (M).
- **Ordre generateDeliveryWindowOptions / confirmPlacementOption** : G4 place la génération avant la confirmation du placement, alors que la confirmation de fenêtre exige un placement confirmé ; à constater sur le compte réel.
- **Exemple d'article `labelOwner: AMAZON`** dans G3 : suppose l'inscription au service d'étiquetage FBA (G2) ; condition d'inscription en France non lue.
