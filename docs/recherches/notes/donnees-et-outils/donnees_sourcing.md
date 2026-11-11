# Données d'un outil de sourcing Amazon (SellerAmp / Keepa / Tactical Arbitrage / Seller Assistant) : sources, coûts, limites, droits (vérification primaire, 2026-11-11)

Note de méthode : SP-API docs ont migré de `developer-docs.amazon.com` vers `developer-docs.amazon` (301). Toutes les pages SP-API ci-dessous ont été lues en version markdown officielle (`<page>.md`, indiquée par l'index officiel https://developer-docs.amazon/sp-api/llms.txt). Les anciennes URL `developer-docs.amazon.com/...` redirigent. Les textes AUP/DPP ont été lus sur sellercentral.amazon.com (lien officiel depuis la page "Policies and Agreements"). Les docs Keepa ont été lues sur le nouveau site officiel https://keepa.com/api-docs/ (et le dépôt officiel github.com/keepacom/api_backend, dernier commit 25/07/2026). Wayback Machine était inaccessible depuis cet environnement (connexion réinitialisée), donc aucune alternative archive n'a pu être utilisée.

## 0. Tableau de synthèse : donnée → source → gratuit/payant → coût → limites → droits → vérifié

### Takeaway
Les données "observées" en temps réel (Buy Box, offres, frais, restrictions, catalogue, BSR courant, éligibilité FBA/hazmat) sont accessibles gratuitement via SP-API (les frais SP-API annoncés ont été annulés), mais seulement au nom d'un vendeur ayant autorisé l'app, avec des débits faibles par paire vendeur/app et une interdiction de mutualiser les données entre clients. L'historique (prix/BSR), le "bought in past month" historisé et les estimations de ventes ne viennent pas d'Amazon : il faut Keepa (payant ; tarifs non vérifiables en primaire) ou une collecte propre. Le volume de recherche par mot-clé n'existe officiellement que via Brand Analytics (Brand Registry requis), en rang de fréquence et non en volume.

### Cited Findings

| # | Donnée | Source / endpoint | Gratuit / payant | Coût exact | Limites (débit par défaut, batch) | Qui y accède / droits | Nature | Vérifié |
|---|---|---|---|---|---|---|---|---|
| 1a | Offres (20 plus basses), Buy Box price, nb d'offres par canal FBA/FBM, IsBuyBoxWinner, IsFulfilledByAmazon, SalesRankings | SP-API Product Pricing v0 `getItemOffers` (ASIN) | Gratuit (aucun frais SP-API en vigueur) | 0 $ | 0,5 req/s, burst 1 | Vendeur ayant autorisé l'app (ou soi-même) ; usage limité par AUP 4.4/4.6 | Observé | OUI : [getItemOffers](https://developer-docs.amazon/sp-api/reference/getitemoffers.md) "Returns the lowest priced offers for a single item based on ASIN." / "| 0.5 | 1 |" |
| 1b | Idem en lot | `getItemOffersBatch` | Gratuit | 0 $ | 0,1 req/s, burst 1 ; 1 à 20 requêtes par lot (`"minItems": 1, "maxItems": 20`) | idem | Observé | OUI : [getItemOffersBatch](https://developer-docs.amazon/sp-api/reference/getitemoffersbatch.md) |
| 1c | Offres par SKU (ses propres listings) | `getListingOffersBatch` | Gratuit | 0 $ | 0,5 req/s, burst 1 | idem | Observé | OUI : [getListingOffersBatch](https://developer-docs.amazon/sp-api/reference/getlistingoffersbatch.md) |
| 1d | Offres mises en avant (featured buying options), prix de référence, lowestPricedOffers, similarItems | Product Pricing 2022-05-01 `getCompetitiveSummary` | Gratuit | 0 $ | 0,033 req/s (≈ 1 lot / 30 s), burst 1 ; 20 ASIN par lot ; jusqu'à 5 filtres lowestPricedOffers | idem | Observé | OUI : [getCompetitiveSummary](https://developer-docs.amazon/sp-api/reference/getcompetitivesummary.md) enum `"featuredBuyingOptions","referencePrices","lowestPricedOffers","similarItems"` |
| 1e | Prix "attendu" pour décrocher l'offre mise en avant (FOEP) | `getFeaturedOfferExpectedPriceBatch` | Gratuit | 0 $ | 0,033 req/s, burst 1 ; jusqu'à 40 requêtes par lot | idem (SKU du vendeur) | Calculé par Amazon | OUI : [FOEP](https://developer-docs.amazon/sp-api/reference/getfeaturedofferexpectedpricebatch.md) "batched list of up to 40 requests" |
| 2a | Frais estimés (commission, FBA, etc.) par ASIN | Product Fees v0 `getMyFeesEstimateForASIN` | Gratuit | 0 $ | 1 req/s, burst 2 | idem ; frais = estimation | Calculé (estimation Amazon) | OUI : [getMyFeesEstimateForASIN](https://developer-docs.amazon/sp-api/reference/getmyfeesestimateforasin.md) "| 1 | 2 |" ; "Actual costs may vary" |
| 2b | Frais estimés en lot | `getMyFeesEstimates` | Gratuit | 0 $ | 0,5 req/s, burst 1 ; 20 articles par lot | idem | Calculé | OUI : [getMyFeesEstimates](https://developer-docs.amazon/sp-api/reference/getmyfeesestimates.md) + [batch doc](https://developer-docs.amazon/sp-api/docs/get-product-fees-batch.md) "allows up to 20 product requests in a single batch" |
| 2c | Barèmes publics (abonnement, commissions) | sell.amazon.com/pricing, sell.amazon.fr/tarifs, sell.amazon.co.uk/pricing | Gratuit (public) | US : Individual 0,99 $/article, Pro 39,99 $/mois ; FR : 0,99 €/unité ou 39 € HT/mois ; UK : 0,75 £/unité ou 25 £ HT/mois ; US clôture média 1,80 $ | Pages marketing, pas d'API | Public | Barème officiel | OUI (voir section 2) |
| 3 | Restrictions de vente / approbation (ungating) | Listings Restrictions 2021-08-01 `getListingsRestrictions` | Gratuit | 0 $ | 5 req/s, burst 10 ; chaque marketplace d'une requête compte comme une requête | Vendeurs uniquement, rôle "Product Listing" ; résultat propre au compte vendeur | Observé (spécifique au compte) | OUI : [getListingsRestrictions](https://developer-docs.amazon/sp-api/reference/getlistingsrestrictions.md) reasonCode `APPROVAL_REQUIRED / ASIN_NOT_FOUND / NOT_ELIGIBLE` |
| 4 | Éligibilité FBA, hazmat/dangerous goods, expiration, restrictions régionales | FBA Inbound Eligibility `getItemEligibilityPreview` | Gratuit | 0 $ | 1 req/s, burst 1 | Vendeur autorisé | Observé (classement Amazon) | OUI : [getItemEligibilityPreview](https://developer-docs.amazon/sp-api/reference/getitemeligibilitypreview.md) codes FBA_INB_0007…0016, 0097 "Fully regulated dangerous good." |
| 5a | Catalogue : EAN/UPC/ISBN/JAN/GTIN→ASIN, dimensions, images, salesRanks (BSR), relations, types | Catalog Items 2022-04-01 `searchCatalogItems` | Gratuit | 0 $ | 2 req/s, burst 2 ; max 20 identifiants par requête ; pageSize max 20 ; identifiers et keywords non combinables | Vendeur autorisé | Observé | OUI : [searchCatalogItems](https://developer-docs.amazon/sp-api/reference/searchcatalogitems.md) |
| 5b | Détail d'un ASIN | `getCatalogItem` | Gratuit | 0 $ | 2 req/s, burst 2 | idem | Observé | OUI : [getCatalogItem](https://developer-docs.amazon/sp-api/reference/getcatalogitem.md) |
| 6a | Historique prix/BSR/offres, stats 30/90/180 j, Buy Box historique, sales rank drops | Keepa API `/product` (`stats`, `offers`, `buybox`, `stock`) | Payant | Prix des plans : NON VÉRIFIÉ en primaire (secondaire : 49 €/mois pour 20 tokens/min) ; coût en tokens : vérifié | Bucket = rate×60 tokens ; tokens expirent après 60 min | Abonné API ; conditions d'usage/revente NON VÉRIFIÉES | Observé (collecté par Keepa) + stats calculées | OUI pour tokens : [Plans & Tokens](https://keepa.com/api-docs/plans-tokens.html), [Product Request](https://keepa.com/api-docs/product.html) |
| 6b | Marketplaces Keepa | Keepa domain IDs | — | — | 1 com, 2 co.uk, 3 de, 4 fr, 5 co.jp, 6 ca, 8 it, 9 es, 10 in, 11 com.mx, 12 com.br. Pas NL, BE, PL, SE | — | — | OUI : [Product Request, Domain IDs](https://keepa.com/api-docs/product.html) |
| 7 | "Bought in past month" | Keepa `monthlySold` + `monthlySoldHistory` | Payant (Keepa) | Inclus dans la requête produit (1 token) | Présent seulement sur une minorité d'ASIN ; tranches (10+, 100+…) | Abonné Keepa | Observé (badge Amazon relevé par Keepa), pas une estimation | OUI : [Product Object](https://keepa.com/api-docs/product-object.html) "It is not an estimate." ; pas d'équivalent SP-API trouvé |
| 8a | Rang de fréquence des termes de recherche (top clics/conversions) | Report `GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT` | Gratuit | 0 $ | Rapport | Rôle Brand Analytics + Brand Registry + représentant de marque | Calculé par Amazon (rang, pas volume) | OUI : [Analytics Reports](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md) |
| 8b | Search Query Performance | `GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT` | Gratuit | 0 $ | Rapport | Rôle Brand Analytics + Brand Registry | Observé (requêtes associées à ses ASIN) | OUI : idem |
| 8c | Product Opportunity Explorer (niches, volume de recherche) | Seller Central (UI) | Inclus dans le plan Pro | 39,99 $/mois (US) = coût du plan Pro | Pas d'API officielle trouvée | Compte Professional | Calculé par Amazon | PARTIEL : [sell.amazon.com POE](https://sell.amazon.com/tools/product-opportunity-explorer) "*A Professional selling account is $39.99/month + selling fees." |
| 9 | Coût SP-API | Annonce officielle | Gratuit | Frais annuels 1 400 $ et frais d'usage annulés | Débits par défaut ci-dessus ; plans dynamiques pour certaines opérations | — | — | OUI : [Cancellation of SP-API Fees](https://developer.amazonservices.com/cancellation-of-sp-api-fees) |
| 10 | Règles d'usage des données | AUP / DPP (EN = version contractuelle) | — | — | Plafonds d'autorisations : privé 10 ; public non listé 25 (vendeurs) ; listé illimité | — | — | OUI : [AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US), [DPP](https://sellercentral.amazon.com/mws/static/policy?documentType=DPP&locale=en_US), [Authorization Limits](https://developer-docs.amazon/sp-api/docs/application-authorization-limits.md) |
| — | Marketplaces SP-API | Store identifiers | — | — | US ATVPDKIKX0DER ; UK A1F83G8C2ARO7P ; FR A13V1IB3VIYZZH ; DE A1PA6795UKMFR9 ; IT APJ6JRA9NG5V4 ; ES A1RKKUPIHCS9HS ; NL A1805IZSGTT6HS ; BE AMEN7PMS3EDWL ; PL A1C3SOZRARQ6R3 ; SE A2NODRKZP88ZB9 ; IE A28R8C7NBKEWEA | — | — | OUI : [Store identifiers](https://developer-docs.amazon/sp-api/docs/store-identifiers.md) |

### Inferences
- Un outil multi-clients peut fonctionner gratuitement côté Amazon s'il appelle SP-API avec le jeton de chaque vendeur client. Les débits sont accordés par paire vendeur/app, donc la capacité grandit avec le nombre de clients. En revanche, aucune donnée (même publique, comme les offres) récupérée pour le vendeur A ne doit servir au vendeur B (AUP 4.4/4.6), ce qui interdit un cache partagé "à la Keepa" alimenté par SP-API.
- Pour NL, BE, PL et SE, Keepa ne fournit aucun historique (domaines absents). L'historique doit donc être construit soi-même, à partir des snapshots SP-API de chaque vendeur, et uniquement pour ce vendeur.

### Gaps
- Barème DST (Digital Services Fee) et grilles FBA 2026 par pays : pages Seller Central derrière login, non lues (voir section 2).
- Prix des plans Keepa et CGU Keepa : application JavaScript, non lisibles en primaire (voir section 6).

## 1. Buy Box, offres, nombre de vendeurs FBA/FBM, Amazon sur le listing : Product Pricing API

### Takeaway
`getItemOffers` (0,5 req/s) et `getItemOffersBatch` (20 ASIN/lot, 0,1 req/s, soit environ 2 ASIN/s en régime établi) donnent les 20 offres les plus basses, le résumé Buy Box, le nombre d'offres par condition et canal, ainsi que les rangs de vente. `getCompetitiveSummary` (20 ASIN/lot, 0,033 req/s) donne les offres mises en avant et les prix de référence. Tout est gratuit, avec un débit par paire vendeur/application.

### Cited Findings
- getItemOffers : "Returns the lowest priced offers for a single item based on ASIN." Plan d'usage "| 0.5 | 1 |" (rate/burst). — [getItemOffers](https://developer-docs.amazon/sp-api/reference/getitemoffers.md)
- Le schéma contient `NumberOfOffers` (par `condition` + `fulfillmentChannel` "Merchant"/"Amazon"), `BuyBoxPrices`, `LowestPrices`, `ListPrice`, `SalesRankings`, `BuyBoxEligibleOffers`, `OffersAvailableTime`, et par offre `IsBuyBoxWinner`, `IsFulfilledByAmazon`. `ItemCondition` (requis) : "New, Used, Collectible, Refurbished, Club". — [getItemOffers](https://developer-docs.amazon/sp-api/reference/getitemoffers.md)
- getItemOffersBatch : "Returns the lowest priced offers for a batch of items based on ASIN." "| 0.1 | 1 |" ; requêtes `"minItems": 1, "maxItems": 20`. — [getItemOffersBatch](https://developer-docs.amazon/sp-api/reference/getitemoffersbatch.md)
- getListingOffersBatch (par SKU) : "| 0.5 | 1 |". — [getListingOffersBatch](https://developer-docs.amazon/sp-api/reference/getlistingoffersbatch.md)
- getCompetitiveSummary : "Returns the competitive summary response, including featured buying options for the ASIN and `marketplaceId` combination." "| 0.033 | 1 |" ; lot `"maxItems": 20` ; `includedData` enum "featuredBuyingOptions","referencePrices","lowestPricedOffers","similarItems" ; jusqu'à 5 `lowestPricedOffersInputs`. — [getCompetitiveSummary](https://developer-docs.amazon/sp-api/reference/getcompetitivesummary.md)
- getPricing (prix de ses propres offres par SKU/ASIN) : "| 0.5 | 1 |". — [getPricing](https://developer-docs.amazon/sp-api/reference/getpricing.md)
- Les débits par défaut peuvent être supérieurs pour certains vendeurs : "Selling partners whose business demands require higher throughput may see higher rate and burst values than those shown here." — [getItemOffers](https://developer-docs.amazon/sp-api/reference/getitemoffers.md)
- Portée du débit : "Most operations' rate limits are per the selling partner and application pair." ; "Usage plans are specific to the application and selling partner pair, so that your throughput grows naturally with your clients." Les plans dynamiques "automatically adjusted to each selling partner based on the current and historical business needs". — [Usage Plans and Rate Limits](https://developer-docs.amazon/sp-api/docs/usage-plans-and-rate-limits.md)
- AUP 3.10 : "Do not attempt to circumvent throttling quotas through the creation of multiple Solution Provider accounts or applications." — [AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)

### Inferences
- "Amazon sur le listing" se déduit des offres. Il n'existe pas de champ booléen dédié dans v0 : il faut repérer le SellerId d'Amazon (propre à chaque marketplace) dans la liste des offres. Le SellerId d'Amazon n'est pas documenté sur la page lue.
- Débit théorique par vendeur client : getItemOffersBatch à 0,1 lot/s × 20 ASIN = 2 ASIN/s ≈ 7 200 ASIN/h ; getItemOffers ≈ 1 800 ASIN/h.

### Gaps
- Liste exacte des offres retournées (top 20) : le texte "20" n'a pas été trouvé dans la page de référence lue (seulement "lowest priced offers"). Le plafond de 20 offres relève de la connaissance antérieure, NON VÉRIFIÉ ici.

## 2. Frais Amazon (commission, FBA, clôture, DST) : Product Fees API et barèmes publics

### Takeaway
Product Fees API (gratuit) renvoie une estimation des frais par ASIN ou SKU, avec un débit de 1 req/s ou des lots de 20 à 0,5 req/s. Les barèmes publics d'abonnement sont vérifiés pour US, FR et UK. Les grilles FBA détaillées 2026 et le DST se trouvent dans l'aide Seller Central (connexion requise) et n'ont pas été lus.

### Cited Findings
- getMyFeesEstimateForASIN : "Returns the estimated fees for the item indicated by the specified ASIN in the marketplace specified in the request body." "| 1 | 2 |". "Actual costs may vary. Search "fees" in Seller Central and consult the store-specific fee schedule for the most up-to-date information." ; "these estimates use the item's catalog size, which might not always match the actual size of the item sent to Amazon." — [getMyFeesEstimateForASIN](https://developer-docs.amazon/sp-api/reference/getmyfeesestimateforasin.md)
- getMyFeesEstimates : "Returns the estimated fees for a list of products." "| 0.5 | 1 |" ; "allows up to 20 product requests in a single batch". — [getMyFeesEstimates](https://developer-docs.amazon/sp-api/reference/getmyfeesestimates.md), [Get product fees batch](https://developer-docs.amazon/sp-api/docs/get-product-fees-batch.md)
- US : "Individual $0.99 / item sold | Professional $39.99 / month" ; "media items incur a closing fee $1.80 per item." — [sell.amazon.com/pricing](https://sell.amazon.com/pricing)
- FR : "Le plan Individuel coûte 0.99€ par unité vendue, et le plan Professionnel coûte 39€ (hors TVA) par mois" ; "La plupart des produits dont le prix est inférieur ou égal à €20 sont désormais éligibles aux tarifs Prix bas Expédié par Amazon" ; bandeau "Frais réduits en 2026". — [sell.amazon.fr/tarifs](https://sell.amazon.fr/tarifs)
- UK : "The Individual plan costs £0.75 per unit sold, and the Professional plan costs £25 (excl. VAT) per month" ; "Most products priced at or below £20 are now eligible for Low-Price FBA rates". — [sell.amazon.co.uk/pricing](https://sell.amazon.co.uk/pricing)
- Revenue Calculator : `sellercentral.amazon.com/revenuecalculator` redirige vers la connexion Seller Central (constaté le 2026-11-11). — [sellercentral.amazon.com/revenuecalculator](https://sellercentral.amazon.com/revenuecalculator)
- Keepa expose aussi `fbaFees` (pick & pack) et `referralFeePercentage`, calculés sur le prix d'offre courant, sinon le dernier prix connu, sinon un défaut de 100,00. — [Keepa Product Object](https://keepa.com/api-docs/product-object.html)

### Inferences
- Pour un calcul de rentabilité, la source fiable est l'estimation SP-API par vendeur, car elle tient compte de son compte. Le barème public sert de repli ou de contrôle.

### Gaps
- Grilles FBA 2026 (par taille et poids, par pays), DST (FR/IT/ES/UK…) et pourcentages de commission par catégorie : pages d'aide Seller Central (connexion requise), NON VÉRIFIÉ. Les pages `sell.amazon.de/preise` et `sell.amazon.com/tools/fba-calculator` ont renvoyé 404.
- Le libellé exact des `FeeType` renvoyés (ReferralFee, VariableClosingFee, FBAFees, DigitalServicesFee…) n'est pas énuméré dans la référence lue : NON VÉRIFIÉ.

## 3. Restrictions de vente / ungating : Listings Restrictions API

### Takeaway
`getListingsRestrictions` (5 req/s, burst 10, gratuit) indique si un vendeur précis peut lister un ASIN (code `APPROVAL_REQUIRED`, `NOT_ELIGIBLE` ou `ASIN_NOT_FOUND`) et fournit un lien pour demander l'approbation. L'API est réservée aux vendeurs, nécessite le rôle Product Listing et dépend du compte.

### Cited Findings
- "check if there are any restrictions that prevent the creation of a listing for an item in the Amazon catalog… Each Amazon store ID in a request counts as a separate request against the rate limit… When approval is required, the API returns next step links". Tableau : "Sellers only". Rôle : "Product Listing". Régions "NA, EU, FE". — [Listings Restrictions API](https://developer-docs.amazon/sp-api/docs/listings-restrictions-api.md)
- Débit "| 5 | 10 |" ; paramètres `asin`, `conditionType`, `sellerId`, `marketplaceIds`, `reasonLocale`, `productType` ("When provided with the brand name, the API evaluates GTIN exemption restrictions in addition to brand restrictions") ; `APPROVAL_REQUIRED` : "Approval is required to create a listing for the specified ASIN. A path forward link will be provided…" — [getListingsRestrictions](https://developer-docs.amazon/sp-api/reference/getlistingsrestrictions.md)

### Inferences
- Le statut "ungated" est propre à chaque compte. Un outil ne peut l'afficher qu'au vendeur concerné, pas comme donnée générale par ASIN.

### Gaps
- Aucune.

## 4. Hazmat, dangerous goods, meltable, listes de plaintes PI

### Takeaway
Les données officielles se limitent au statut d'éligibilité FBA par article et par vendeur (`getItemEligibilityPreview`), dont les codes FBA_INB couvrent hazmat, examen dangerous goods, expiration et zone. Aucune API officielle trouvée ne fournit de liste de marques à risque PI (plaintes) ni d'indicateur "meltable" par ASIN.

### Cited Findings
- "With this API you can find out if an item is eligible for inbound shipment to Amazon's fulfillment centers in a specific marketplace." Programmes INBOUND ou COMMINGLING ; "| 1 | 1 |". — [getItemEligibilityPreview](https://developer-docs.amazon/sp-api/reference/getitemeligibilitypreview.md)
- Codes (extraits verbatim) : FBA_INB_0014 "Product Under Dangerous Goods (Hazmat) Review… The review process generally takes 4 - 7 business days" ; FBA_INB_0015 "Dangerous goods (Hazmat). The product is regulated as unfulfillable and not eligible for sale with Amazon." ; FBA_INB_0016 "regulated as a fulfillable dangerous good (Hazmat). You may need to be in the FBA dangerous good (Hazmat) program" ; FBA_INB_0097 "Fully regulated dangerous good." ; FBA_INB_0035/0036/0103 (expiration et lot) ; FBA_INB_0055 "media region restrictions". — [getItemEligibilityPreview](https://developer-docs.amazon/sp-api/reference/getitemeligibilitypreview.md)
- Keepa expose `isAdultProduct` (pas de hazmat dans les champs relevés). — [Keepa Product Object](https://keepa.com/api-docs/product-object.html)

### Inferences
- "Meltable" (stockage saisonnier) et les listes de marques "IP complaint" vendues par les outils sont, selon toute vraisemblance, des bases propriétaires et collaboratives. Aucune source officielle Amazon n'a été trouvée.

### Gaps
- Aucun code "meltable" n'a été relevé dans les codes FBA_INB (recherche limitée aux termes hazmat/dangerous/expir/restrict/regulat). NON VÉRIFIÉ que l'API l'ignore totalement.
- Product Type Definitions (attributs `supplier_declared_dg_hz_regulation`, etc.) : non lu.

## 5. Catalogue, EAN/UPC→ASIN, dimensions, BSR : Catalog Items 2022-04-01

### Takeaway
`searchCatalogItems` (2 req/s, burst 2) convertit jusqu'à 20 identifiants (EAN, UPC, GTIN, ISBN, JAN, MINSAN, SKU, ASIN) par appel. Il renvoie, via `includedData`, les dimensions et le BSR courant (`salesRanks`), mais pas d'historique.

### Cited Findings
- `identifiers` : "A comma-delimited list of product identifiers… You cannot include `identifiers` and `keywords` in the same request." `"maxItems": 20`. `identifiersType` enum "ASIN","EAN","GTIN","ISBN","JAN","MINSAN","SKU","UPC". `includedData` enum "attributes","classifications","dimensions","identifiers","images","productTypes","relationships","salesRanks","summaries","vendorDetails". `pageSize` maximum 20. Débit "| 2 | 2 |". — [searchCatalogItems](https://developer-docs.amazon/sp-api/reference/searchcatalogitems.md)
- getCatalogItem : "Retrieves details for an item in the Amazon catalog." "| 2 | 2 |". — [getCatalogItem](https://developer-docs.amazon/sp-api/reference/getcatalogitem.md)
- Keepa `/product` accepte aussi "UPC, EAN, GTIN and ISBN-13 codes" (1 token par code, même s'il n'existe pas). — [Keepa Product Request](https://keepa.com/api-docs/product.html)

### Inferences
- Le débit théorique est de 2 × 20 = 40 EAN/s par vendeur client, ce qui suffit pour scanner des fichiers fournisseurs.

### Gaps
- Aucune.

## 6. Historique prix/BSR et estimations de ventes : Keepa API

### Takeaway
Les coûts en tokens sont vérifiés : 1 token par produit, 6 par page d'offres, +2 pour Buy Box, 10 pour une recherche ou le Product Finder, 5 pour les deals, 50 pour les best sellers. Le modèle est un bucket de rate×60 tokens. Keepa couvre US, UK, DE, FR, IT, ES (plus JP, CA, IN, MX, BR) mais pas NL, BE, PL ni SE. Les prix des plans, l'offre gratuite, l'abonnement "data" à 29 € et les CGU de redistribution n'ont pas pu être lus en primaire (application JavaScript).

### Cited Findings
- "Keepa's API plans are all billed monthly in advance… The plans differentiate by the number of tokens that are generated per minute. Unused tokens expire after 60 minutes." ; "the bucket can hold at most rate × 60 tokens" ; exemple : 60 tokens/min donne un maximum de 2 678 400 produits par mois de 31 jours ; "A downgrade is possible as well, but only once every 28 days" ; "Keepa does not offer discounts." ; paiement Stripe. Les montants 10 EUR / 25 EUR de la page sont un exemple de proration, pas des tarifs réels. — [Keepa Plans & Tokens](https://keepa.com/api-docs/plans-tokens.html)
- Table officielle des coûts : Product Request "1 token per product (more with optional parameters)" ; Product Search "10 tokens per search (up to 20 results)" ; Product Finder "10 + 1 per 100 ASINs" ; Browsing Deals "5 tokens per request (up to 150 deals)" ; Best Sellers "50 tokens per request" ; Category Lookup "1 token per request (up to 10 categories)" ; Seller Information "1 token per seller (+9 for storefront)" ; Seller Finder "10 + 1 per 100 seller IDs" ; Most Rated Sellers 50 ; Lightning Deals "1 token per ASIN · 500 tokens for the full list" ; Graph Image "1 token per image" ; Tracking "varies". — [Keepa Plans & Tokens](https://keepa.com/api-docs/plans-tokens.html)
- Options du Product Request : `offers` "6 for every found offer page (contains up to 10 offers) per product, with a minimum of 5 tokens if the retrieval succeeds but no offer page is found… When using the offers parameter, the basic 1 token cost per ASIN… does not apply" ; `buybox` "+2 tokens per product" ; `stock` "+2" (sous conditions) ; `rating` "up to +1" ; `historical-variations` "+1" ; `update=0` "+1 extra token" si la dernière mise à jour a moins d'1 h ; "`stats`, `history`, `days`… no extra token cost" ; "If our last update is older than ~1 hour, it will be automatically refreshed before being delivered". — [Keepa Product Request](https://keepa.com/api-docs/product.html)
- Product Search avec `stats=1` : "30 tokens + 1 token for every 1,000,000 products returned by the query as a whole". — [Keepa Product Search (md)](https://keepa.com/api-docs/product-search.md)
- Deals : "a single query can provide up to 10,000 ASINs this way" (pagination, 5 tokens par page). — [Keepa Deals (md)](https://keepa.com/api-docs/deals.md)
- Domain IDs : "1 com, 2 co.uk, 3 de, 4 fr, 5 co.jp, 6 ca, 8 it, 9 es, 10 in, 11 com.mx, 12 com.br". — [Keepa Product Request](https://keepa.com/api-docs/product.html) ; même liste dans l'enum `AmazonLocale { RESERVED, US, GB, DE, FR, JP, CA, RESERVED2, IT, ES, IN, MX, BR }` — [keepacom/api_backend AmazonLocale.java](https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/AmazonLocale.java)
- Keepa propose aussi un serveur MCP hébergé, "authenticated with the same API key, metered by the same tokens". — [Keepa API Overview](https://keepa.com/api-docs/)
- Le dépôt GitHub est sous licence Apache 2.0, mais cette licence couvre le code client, pas les données. — [keepacom/api_backend README](https://github.com/keepacom/api_backend)

### Inferences
- Exemple d'outil de type SellerAmp, par scan : produit + stats + offres (environ 2 pages) + buybox ≈ 12 + 2 = 14 tokens. Avec 20 tokens/min, cela fait environ 1,4 scan complet par minute, d'où l'intérêt d'utiliser `update` et `offers` avec parcimonie.
- Les "estimations de ventes" des outils sont dérivées : rank drops (Keepa stats), monthlySold, modèles BSR→ventes propriétaires. Aucune n'est une donnée officielle Amazon.

### Gaps (NON VÉRIFIÉ)
- Prix des plans API (secondaire concordant : 49 €/mois pour 20 tokens/min, sans tier gratuit) : keepa.com/#!api/pricing est rendu en JS et le contenu n'a pas été trouvé dans les bundles téléchargés (cdn/20261120). Sources secondaires seulement : [revenuegeeks](https://revenuegeeks.com/software/keepa/api), [amzfinder](https://www.amzfinder.com/blog/keepa-api/).
- Abonnement Keepa "Data/Pro" à 29 €/mois (anciennement 19 €) et accès gratuit à keepa.com : seulement des sources secondaires ([revenuegeeks](https://revenuegeeks.com/keepa-pricing/)). NON VÉRIFIÉ.
- CGU Keepa sur l'affichage ou la revente des données Keepa dans une app commerciale tierce : introuvables en primaire (page #!terms en JS ; recherche web sans résultat officiel). À demander par écrit à info@keepa.com avant tout usage commercial.

## 7. Badge "Bought in past month"

### Takeaway
Le badge est relevé par Keepa (`monthlySold`, historisé). Aucune opération SP-API exposant cette métrique n'a été trouvée dans les références lues.

### Cited Findings
- `monthlySold` : "How often this product was bought in the past month. This field represents the *bought past month* metric found on Amazon search result pages. It is not an estimate. Amazon only provides the data in bracketed ranges such as "10+" or "100+"… Most ASINs do not have this value set. The value is variation specific." ; `monthlySoldHistory` "[ keepaTime, monthlySold, … ]" ; Stats `deltaPercent90_monthlySold` ; Product Finder filtres `monthlySold_gte/lte`. — [Keepa Product Object](https://keepa.com/api-docs/product-object.html) ; [Product.java](https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/Product.java)

### Inferences
- Le badge apparaît sur les pages de résultats de recherche Amazon (dixit Keepa). La seule manière "légitime" d'y accéder par API est donc Keepa ou un autre fournisseur tiers. Le scraper soi-même se heurte aux Conditions d'utilisation d'Amazon (non lues ici) et, si les données sont revendues via un outil SP-API, à l'AUP 4.3.

### Gaps
- Absence de champ SP-API équivalent : déduite d'une lecture des schémas Catalog et Pricing, non affirmée par Amazon.

## 8. Volume de recherche / mots-clés

### Takeaway
Officiellement, il existe (a) les rapports Brand Analytics via SP-API, gratuits mais réservés au Brand Registry et au rôle Brand Analytics, qui donnent un rang de fréquence ou des requêtes associées et non un volume absolu, et (b) le Product Opportunity Explorer, en interface Seller Central pour les comptes Pro, sans API trouvée. Pour l'Ads API, aucune page officielle n'a été lue.

### Cited Findings
- `GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT` : "Availability: Sellers and vendors who have the Brand Analytics Selling Partner API role, are registered in Amazon Brand Registry, and are a brand representative." — [Analytics Reports](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md)
- `GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT` et `GET_BRAND_ANALYTICS_SEARCH_CATALOG_PERFORMANCE_REPORT` : "Sellers who have the Brand Analytics Selling Partner API role and are registered in Amazon Brand Registry." — [Analytics Reports](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md)
- Product Opportunity Explorer (page Amazon) : "*A Professional selling account is $39.99/month + selling fees." — [sell.amazon.com POE](https://sell.amazon.com/tools/product-opportunity-explorer)
- Keepa Product Search `stats=1` renvoie un "Search Insights Object" (moyennes Buy Box, etc. sur les résultats d'une requête), qui n'est pas un volume de recherche. — [Keepa Product Search (md)](https://keepa.com/api-docs/product-search.md)

### Gaps (NON VÉRIFIÉ)
- Amazon Ads API (recommandations de mots-clés, `searchTermImpressionShare`, estimations d'impressions) : seules des sources tierces ont été trouvées ([python-amazon-ad-api](https://python-amazon-ad-api.readthedocs.io/en/latest/sp/ranked_keywords_recommendations.html)). La doc advertising.amazon.com n'a pas été lue. Il n'y a pas de champ "search volume" connu.
- Les conditions d'accès exactes à POE (pays, statut beta) relèvent de sources secondaires uniquement.

## 9. SP-API est-il gratuit en novembre 2026 ?

### Takeaway
Oui. Amazon a officiellement annulé les frais annuels (1 400 $) et d'usage annoncés pour 2026. La page officielle reste en ligne (publiée le 11/06/2026, modifiée le 01/07/2026), avec la réserve "at this time".

### Cited Findings
- "Cancellation of Third-Party Developer Selling Partner API (SP-API) Fees… After careful consideration, we have decided that we will not move forward with the SP-API usage and annual fees at this time." ; "In the coming weeks, we will be making updates to the Solution Provider Portal (SPP) to reflect this decision, such as removing the fee preview dashboard. If you previously provided a credit card, you can delete it now". Métadonnées : datePublished 2026-06-11T01:50:05Z, dateModified 2026-07-01T21:33:27Z. — [developer.amazonservices.com/cancellation-of-sp-api-fees](https://developer.amazonservices.com/cancellation-of-sp-api-fees)
- Chronologie secondaire, cohérente : annonce le 3/11/2025 (1 400 $/an dès le 31/01/2026, frais d'usage dès le 30/04/2026), report en janvier, suspension le 9/03/2026, annulation communiquée les 12-14/05/2026. — [ppc.land](https://ppc.land/amazon-drops-sp-api-fees-after-developer-pushback), [novadata](https://novadata.io/resources/news/amazon-sp-api-subscription-fees-2026) (secondaire)
- Aucune mention de frais dans le changelog SP-API, les pages d'inscription publique/privée ni la FAQ générale lues le 2026-11-11. — [General FAQ](https://developer-docs.amazon/sp-api/docs/general-faq.md)
- Pas de frais Amazon pour l'API, mais il faut un compte vendeur Pro pour les données vendeur (plan Pro 39,99 $ US / 39 € FR / 25 £ UK, voir section 2).

### Inferences
- L'expression "at this time" laisse la porte ouverte à de futurs frais. Un business plan prudent devrait prévoir un scénario chiffré sur l'ancienne grille (1 400 $/an + usage).

### Gaps
- L'ancienne page `developer.amazonservices.com/spp-announcement` renvoie 404 : le texte original de la grille tarifaire n'a pas été lu en primaire.

## 10. Acceptable Use Policy et Data Protection Policy, développeur public/privé, plafonds d'autorisation

### Takeaway
L'AUP interdit d'agréger les données de plusieurs vendeurs pour les fournir à d'autres (4.4), de divulguer les informations d'un utilisateur à d'autres utilisateurs de l'app (4.6), d'utiliser ou de promouvoir des services externes qui vendent des données des sites Amazon (4.3), et de partager des insights sur le business d'Amazon (4.5). Une app privée est limitée à 10 auto-autorisations. Une app publique non listée sur l'Appstore est plafonnée à 25 vendeurs. Le listing Appstore lève ce plafond.

### Cited Findings
- AUP 1.1 : "Use the Amazon Services API only to perform acceptable Amazon activities, and only for Authorized Users who have authorized you to perform these activities on their behalf." — [AUP (EN-US)](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)
- AUP 4.3 : "Do not use, offer or promote external (non-Amazon) data services that vend information or data retrieved from Amazon's websites." — [AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)
- AUP 4.4 : "Do not aggregate data across Authorized Users' businesses or customers obtained through the Amazon Services API to provide or sell to any parties, including competing Authorized Users." — [AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)
- AUP 4.5 : "Do not promote, publish or share insights about Amazon's business. Do not use insights about Amazon's business for your own business purposes." — [AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)
- AUP 4.6 : "Do not disclose Information, individually labelled or aggregated, to other Application users, affiliated entities or any outside parties, unless required to perform acceptable Authorized User activities for Authorized Users that authorized your Application." — [AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)
- Définition : "'Information' means any information that is exposed through the Amazon Services API, Amazon Portals or Amazon's public-facing websites. This data can be public or non-public". — [AUP §6](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)
- AUP 2.4 : "Be explicit about any calculations and the use of models such as artificial intelligence in the service you provide, their accuracy and data freshness." ; 3.5 : les clés sans appel réussi en 90 jours sont supprimées ; 3.6 : "Do not ask Authorized Users to share information retrieved from Amazon Portals manually or programmatically to circumvent Amazon policies." ; 3.8 : ne demander que les données nécessaires. — [AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)
- AUP : "The version of this AUP in English is the definitive legal version". — [AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US) ; traductions FR/DE/IT/ES/NL/PL/SE listées sur [Policies and Agreements](https://developer-docs.amazon/sp-api/docs/policies-and-agreements.md) (mise à jour 2026-09-16)
- DPP : "Solution Provider must retain Information only for so long as… strictly necessary" ; suppression "within thirty (30) days of the earliest of… (ii) the Amazon Solution Provider Customer revokes authorization… (iv) termination" ; PII : "retain PII for no longer than 30 days after order delivery" ; logs conservés "at least twelve (12) months". — [DPP (EN-US)](https://sellercentral.amazon.com/mws/static/policy?documentType=DPP&locale=en_US)
- Plafonds : "Private | 10 | Not available" ; "Public (not listed on Selling Partner Appstore) | 10 | Seller: 25 / Vendor: Unlimited" ; "Public (listed on Selling Partner Appstore) | 10 | Unlimited". "Private applications are available only to your organization." — [Authorization Limits](https://developer-docs.amazon/sp-api/docs/application-authorization-limits.md) (mise à jour 2026-09-09)
- Inscription publique et privée : [Register as a Public Developer](https://developer-docs.amazon/sp-api/docs/register-as-a-public-developer.md), [Register as a Private Developer](https://developer-docs.amazon/sp-api/docs/register-as-a-private-developer.md) (téléchargées ; aucune mention de frais).

### Inferences
- Combiner dans un même produit SP-API des données Keepa (un "external data service" qui vend des données récupérées sur les sites Amazon) est en tension directe avec l'AUP 4.3 ("use, offer or promote"). Pourtant de nombreux outils listés le font : le risque est contractuel (suspension de l'accès SP-API) et l'application réelle par Amazon est inconnue. C'est l'élément juridique le plus important pour un nouvel outil.
- L'AUP 4.4 et 4.6 interdisent de réutiliser des réponses SP-API (même des offres publiques) obtenues avec le jeton d'un vendeur pour servir un autre client, ce qui exclut un cache partagé. La définition d'"Information" inclut explicitement les données publiques.
- Un SaaS commercial au-delà de 25 vendeurs doit être listé sur l'Appstore (ou rester public non listé, plafonné à 25).

### Gaps
- Les exigences de listing Appstore (revue sécurité, audit DPP) n'ont pas été détaillées : la page [What is the Selling Partner Appstore](https://developer-docs.amazon/sp-api/docs/what-is-the-selling-partner-appstore.md) a été téléchargée mais pas analysée en profondeur.

## 11. Ce qu'un vendeur obtient 100 % gratuitement, et ce qui est impossible sans payer

### Takeaway
Avec son propre compte Pro (39,99 $ / 39 € / 25 £ par mois, payés de toute façon pour vendre), une app privée SP-API gratuite donne pour son compte la Buy Box et les offres, les frais estimés, les restrictions, l'éligibilité hazmat/FBA, le catalogue avec conversion EAN→ASIN et BSR courant, et Brand Analytics si le vendeur est en Brand Registry. Sans payer un tiers, il est impossible d'obtenir l'historique prix/BSR, le "bought past month" historisé, des estimations de ventes et le volume de recherche absolu, et la couverture Keepa reste absente pour NL, BE, PL et SE.

### Cited Findings
- SP-API sans frais Amazon : [Cancellation of SP-API Fees](https://developer.amazonservices.com/cancellation-of-sp-api-fees).
- App privée : 10 auto-autorisations — [Authorization Limits](https://developer-docs.amazon/sp-api/docs/application-authorization-limits.md).
- Endpoints et débits : sections 1 à 5 ci-dessus (références officielles).
- Brand Analytics réservé au Brand Registry : [Analytics Reports](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md).
- POE inclus dans le compte Pro (UI) : [sell.amazon.com POE](https://sell.amazon.com/tools/product-opportunity-explorer).
- Keepa API payante, plans au mois ("billed monthly in advance") : [Keepa Plans & Tokens](https://keepa.com/api-docs/plans-tokens.html) ; pas de tier gratuit (secondaire seulement).
- Revenue Calculator : accès redirigé vers la connexion Seller Central — [revenuecalculator](https://sellercentral.amazon.com/revenuecalculator).

### Inferences
- Le seul moyen gratuit et conforme d'obtenir de l'historique est d'enregistrer ses propres snapshots SP-API dans le temps, pour son propre compte. La couverture se limite alors aux ASIN interrogés, sans rétroactivité.

### Gaps (récapitulatif NON VÉRIFIÉ)
- Prix des plans Keepa API, abonnement Keepa 29 €/mois, fonctionnalités gratuites de keepa.com : app JavaScript ; seulement des sources secondaires (revenuegeeks, amzfinder).
- CGU Keepa (affichage ou revente dans une app tierce) : introuvables en primaire.
- Grilles FBA 2026 par pays et DST : aide Seller Central derrière connexion ; Wayback inaccessible depuis l'environnement.
- Amazon Ads API (mots-clés et impressions) : doc officielle non lue.
- Accès au Revenue Calculator sans compte (des versions publiques ont existé) : non confirmé.
