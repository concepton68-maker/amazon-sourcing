# Fournisseurs connectables par API ou flux — recherche approfondie (14/11/2026)

Complète `2026-11-14-sources-fournisseurs.md`. Périmètre **élargi à toutes les familles de produits** (consigne de Sam du 14/11 : Amazon peut ouvrir une catégorie à tout moment). Classement par **utilité métier** : qualité de l'API ou du flux, largeur du catalogue, stock en UE, revente Amazon autorisée.

Légende des preuves :
- **VÉRIFIÉ** : page officielle lue, avec l'URL et une citation courte exacte.
- **VÉRIFIÉ (extrait)** : vu seulement dans un extrait de moteur de recherche, ou dans une page officielle lue indirectement (copie d'un intégrateur).
- **NON VÉRIFIÉ** : rien d'officiel lu.

Aucune valeur n'est inventée. Quand une information manque, c'est écrit « non indiqué ». Rien n'a été vérifié sur l'acceptation des factures par Amazon pour l'ouverture d'une catégorie : **aucun fournisseur ne le dit officiellement** dans les pages lues.

---

## 1. Classement (top 24)

| # | Fournisseur (pays) | Familles | API / flux | Accès | Amazon | Intérêt |
|---|---|---|---|---|---|---|
| 1 | **BigBuy** (ES) | Généraliste : maison, jouets, beauté, sport, électronique, animaux, bricolage… | API REST (Bearer) + CSV/XML par FTP, avec l'EAN | Abonnement (pack), clé API sur demande | FBA prévu officiellement | Très fort, toutes familles |
| 2 | **vidaXL** (NL) | Maison, jardin, meubles, bricolage, animaux, sport | API + flux | Compte pro, abonnement | Autorisé (extrait FAQ) | Très fort : maison/jardin |
| 3 | **Qogita** (NL) | Beauté, santé, hygiène, entretien | API JWT ; API interne fermée fin janvier 2027 → « Public API (Buyers) » | Compte acheteur pro | non indiqué (déjà étudié) | Très fort : beauté/santé |
| 4 | **BTSwholesaler** (ES) | Parfums, cosmétiques | API REST JWT v2.0 (catalogue, stock+prix, changements, commandes) | Inscription pro, jeton généré dans l'espace client | **Intégration Amazon SP-API officielle (bêta)** | Fort : beauté (souvent à approuver) |
| 5 | **Puckator** (UK + site UE) | Cadeaux, maison, cuisine, jouets/nouveautés, bagagerie légère | Flux CSV/XML/JSON : EAN, stock, prix par palier, **minimum imposé** | Compte grossiste, minimum £50 | **FBA pris en charge officiellement**, envoi aux centres UE | Fort : maison/jouets |
| 6 | **Ingram Micro** (Xvantage) | Informatique, électronique | API REST v6 OAuth2 : catalogue, prix et dispo (50 réf./appel), commandes | Compte revendeur Ingram + historique d'achats | NON VÉRIFIÉ | Fort pour l'informatique, si le compte est ouvert |
| 7 | **api Computerhandels** (DE/AT/NL) | Informatique, électronique, biens de consommation | Liste de prix en temps réel (CSV/XML/BMEcat/PRICAT) avec EAN, stock et prix ; XML/EDI ; expédition au nom du revendeur (ViND) | Client pro (inscription « nouveau client ») | NON VÉRIFIÉ | Fort : flux simple à brancher |
| 8 | **Nedis** (NL) | Électronique grand public, câbles, petit électroménager, maison, accessoires informatiques | Nedis Connect API (OAuth2, liste blanche d'adresses IP) : prix client et stock en temps réel + flux articles + EDI | Via le bureau Nedis local | NON VÉRIFIÉ | Fort : électronique et informatique |
| 9 | **TD SYNNEX** (EU) | Informatique, électronique | Portail développeur UE : Catalogue API (produit, prix, dispo), Order Management | Compte revendeur | NON VÉRIFIÉ | Moyen à fort |
| 10 | **ITscope** (DE, agrégateur) | Informatique : plus de 400 fournisseurs | API 2.1 + OpenAPI 3.0 publique | Payant : 5 000 appels/mois inclus dans « ERP Integration » | sans objet (source de données) | Moyen : comparer les prix des distributeurs DE |
| 11 | **ALSO** (FR/DE/CH) | Informatique, électronique | Listes de prix FTP (TXT/CSV), configurables (DE : 49 € à l'ouverture) | Ouverture de compte en ligne ; 1re commande payée d'avance (CGV FR) | NON VÉRIFIÉ ; listes confidentielles | Moyen |
| 12 | **Warmako** (NL) | Animalerie premium (plus de 5 000 articles) | « EDI or API connections » | Clients pros en Europe, dont la vente en ligne | NON VÉRIFIÉ | Moyen à fort : animaux |
| 13 | **Kosatec** (DE) | Informatique, Apple, réseau, périphériques | CSV de prix par URL (n° client + clé EDI, source tierce), EDI, envoi direct au client final | Réservé aux entreprises | NON VÉRIFIÉ | Moyen |
| 14 | **Brandsdistribution** (IT) | Mode, chaussures, accessoires | API Rewix (catalogue, réservation, commandes) | 99 €/mois ou 990 €/an | Ambigu ; Sparco exclu | Moyen : mode |
| 15 | **BrandsGateway** (SE) | Mode luxe | API REST (documentation nova.shopwoo.com) | Abonnement dropshipping (extrait) | Via les applis de plateforme (extrait) | Moyen |
| 16 | **CJdropshipping** (CN + entrepôt DE) | Généraliste | API documentée (stock, entrepôts, commandes) | Compte gratuit, clé API | Service FBA annoncé (extrait) | Moyen : qualité et marques à contrôler |
| 17 | **Spocket** (fournisseurs UE/US) | Généraliste | Pas d'API retailer publique trouvée | Abonnement | **Amazon autorisé** (aide officielle) | Moyen, surtout en vente expédiée par le vendeur (FBM) |
| 18 | **Inter Cars** (PL) | Pièces auto | IC API REST (documentation en ligne) | Client B2B Inter Cars | NON VÉRIFIÉ | Moyen : auto |
| 19 | **EPROLO** (CN + entrepôts UE annoncés) | Généraliste | API sur demande (document envoyé par le support) | Compte gratuit | Amazon listé (extrait) | Faible à moyen |
| 20 | **Avasam** (UK) | Généraliste UK | API + intégration Amazon | Abonnement | Intégration Amazon (extrait) | Faible : stock surtout au Royaume-Uni |
| 21 | **Matterhorn** (PL) | Mode femme, lingerie | API citée sur leur blog, sans documentation publique | Compte | NON VÉRIFIÉ | Faible à moyen |
| 22 | **Ikonka** (PL) | Gadgets, maison, jouets | Fichier XML « léger » (code, stock, prix) via api2.html (extrait) | Compte client | NON VÉRIFIÉ | Faible à moyen |
| 23 | **Doba** (US) | Généraliste US | Retailer API v2.0 + CSV | Abonnement | Intégration Amazon officielle | Faible : stock aux États-Unis |
| 24 | **Syncee** | Agrégateur | Pas d'intégration Amazon directe | Abonnement | Indirect seulement (officiel) | Faible |

Écartés ou sans API trouvée : Esprinet, Komsa, Jarltech, Wortmann (EDI seulement), Exertis (flux via le chargé de compte, UK), EET (connecteurs tiers seulement), Foxway (reconditionné ; Amazon Renewed est sur approbation), Tradeinn (c'est une place de marché, pas un grossiste), Griffati (rien trouvé), AliExpress DS API (rien d'officiel lu). Ankorstore, Faire et Creoate restent interdits (déjà établi).

Familles **sans fournisseur API vérifié** dans cette recherche : épicerie et boissons, bijoux, bébé spécialisé, sport de marque (Nike, Adidas), bagagerie spécialisée. Pour ces familles, BigBuy et Qogita restent les seules pistes généralistes.

---

## 2. Détails par fournisseur

### 2.1 BigBuy (Espagne) — généraliste
- API : RESTful, en JSON, avec un jeton Bearer ; hôte de production api.bigbuy.eu, hôte de test api.sandbox.bigbuy.eu ; documentation api.bigbuy.eu/rest/doc ; endpoints `/rest/catalog/products.json`, `/rest/catalog/productsvariations.json` et un stock par délai de préparation `productsstockbyhandlingdays.json`. **VÉRIFIÉ (extrait)** du guide officiel https://www.bigbuy.eu/public/doc/Guia_API_BigBuy_EN.pdf
- Fichiers CSV/XML avec « Product code, EAN code » — **VÉRIFIÉ (extrait)** https://bigbuy.eu/file-csv-xml.html. Une formule n'a pas l'API : « not compatible with API, FTP, CSV, XML » — **VÉRIFIÉ (extrait)** https://www.bigbuy.eu/en/solutions.html
- Amazon : « All BigBuy products are from top brands with sales and distribution authorisation granted by the brand » ; pour FBA, « buying stock from BigBuy while directly managing the Amazon account » ; « Our warehouse is included in the Amazon Prime programme ». **VÉRIFIÉ (extrait)** https://www.bigbuy.eu/academy/en/selling-marketplaces-faqs/ et https://www.bigbuy.eu/fr/dropshipping-amazon.html (pages anciennes, de 400 à 1 569 jours).
- En cas de plainte d'une marque, BigBuy demande d'exclure le produit ou la marque de la sélection — **VÉRIFIÉ (extrait)**, même FAQ.

### 2.2 vidaXL (Pays-Bas) — maison, jardin, meubles
- FAQ : les dropshippers enregistrés peuvent vendre sur des places de marché, eBay et Amazon cités ; un abonnement de 30 €/mois. **VÉRIFIÉ (extrait)** https://dropshipping.vidaxl.com/dropshipping-faqs/ (page bloquée en 403 à la lecture ; FAQ ancienne, environ 2 300 jours).
- API : annonce « Get Product Through API » ; une commande vers un pays non autorisé échoue. **VÉRIFIÉ (extrait)** https://dropshipping.vidaxl.com/announcement/get-product-through-api/
- Comptes réservés aux entreprises (« personal-use accounts will be terminated », extrait) — https://dropshipping.vidaxl.com/terms-conditions/

### 2.3 Qogita (Pays-Bas) — beauté, santé : compléments à la documentation API
developers.qogita.com renvoie toujours une erreur 403 (Cloudflare). **Autre voie officielle trouvée** : la page Notion publique de Qogita https://qogita.notion.site/Qogita-API-Internal-556b22869bcb47d2bffac8d2a8c7076a, lue par l'API publique de Notion. **VÉRIFIÉ** :
- « All paths below are relative to https://api.qogita.com. Paths must end with a trailing slash »
- « Authentication uses JWT bearer tokens, and you can obtain one by posting your Qogita credentials to /auth/login/ »
- Limites : « the response status is 429 Too Many Requests and a Retry-After header »
- Catalogue complet asynchrone par webhook : « Subscribe a webhook endpoint to both catalog_download.completed and catalog_download.failed »
- Rubriques de la page : Search products, Offers for a product, A specific supplier's offer, Search a supplier's offers, panier (`/carts/active/`, `/buyers/carts/active/`), « MOV progress » (minimum de commande par fournisseur).
- **Important** : « This API stops working at the end of January 2027. It is the internal API behind our website and can change without notice. For buyer integrations, use the Qogita Public API (Buyers), which is built for your systems and has its own API credentials. Questions? Write to api@qogita.com. »
- Prérequis : « You must be a registered buyer on www.qogita.com. Qogita serves businesses ».
- Les chemins exacts des endpoints d'offres ne sont pas lisibles (blocs repliés) : **NON VÉRIFIÉ**. La page d'aide https://help.qogita.com/developer-hub renvoie vers https://developers.qogita.com/reference/ (403). **VÉRIFIÉ**.
- Conséquence pour l'outil : se brancher sur la « Public API (Buyers) » et non sur l'API interne, qui ferme fin janvier 2027.

### 2.4 BTSwholesaler (Espagne) — parfums, cosmétiques
- **VÉRIFIÉ** https://www.btswholesaler.com/en/site/api : « API Connection v2.0 », mise à jour le « 3 December 2025 » ; « Authentication via JWT tokens » ; « generate your JWT token from your client panel » ; getListProducts « Up to 500 products per page » ; getProductChanges « Only products modified since the last synchronization » ; getProductStock « Real-time stock and prices » ; createOrder, getOrderStatus, getShippingRates ; 5 langues. L'EAN n'est pas cité sur la page (NON VÉRIFIÉ, à voir dans le flux).
- Accès : formulaire d'inscription (activité Perfumery, Drugstore, Online store, Wholesaler…) ; aucuns frais ni minimum indiqués.
- Amazon : **VÉRIFIÉ** https://api.btswholesaler.com/en/site/amazon-info : « Amazon Seller Integration BETA », par l'API officielle SP-API avec OAuth 2.0 ; 8 places de marché UE ; « We ship directly to your Amazon customers ». C'est donc de la vente expédiée par le vendeur (FBM) en dropshipping ; la règle d'Amazon (vendeur de référence) s'applique. Achat en gros pour FBA : non indiqué.
- Beauté et parfums : catégories souvent soumises à approbation sur Amazon. La facture BTS pour l'approbation : NON VÉRIFIÉ.

### 2.5 Puckator (Royaume-Uni, site UE) — cadeaux, maison, jouets, nouveautés
- Flux **VÉRIFIÉ** https://puckator.co.uk/customer-product-data-feed : « EU or UK csv format » puis « CSV/XML/JSON » ; champs EAN « Unique barcode identifier », « Stock Level », « Our standard 1st tier net (ex vat) price in GBP », « Enforced » (minimum d'achat), Tier 1/Tier 2 (prix par quantité), quantités par carton ; flux réservé aux comptes connectés.
- Amazon **VÉRIFIÉ** https://www.puckator.co.uk/amazon-fulfilment : « Many of our customers sell Puckator products through Amazon UK and European marketplaces » ; « We can dispatch to Amazon fulfilment centres across the UK and Europe » ; « We can print and apply Amazon barcode labels » ; « MINIMUM ORDER £50 » ; « you need a wholesale account ».
- Limites : prix en GBP ; les droits de douane et la TVA à l'import depuis le Royaume-Uni sont à vérifier ; le site UE n'a pas été examiné (NON VÉRIFIÉ).

### 2.6 Ingram Micro (Xvantage Reseller API) — informatique
- **VÉRIFIÉ** https://developer.ingrammicro.com/reseller/getting-started : prérequis « An active Ingram Micro account number with account in good standing » et « Current sales history » ; « The Product Catalog endpoints are for catalog searches and finding real-time price and availability information » ; « The Orders endpoints to create and list orders ».
- **VÉRIFIÉ** https://developer.ingrammicro.com/reseller/getting-started/authentication : « uses the OAuth 2.0 protocol », grant « client_credentials », jeton `https://api.ingrammicro.com:443/oauth/oauth20/token`.
- SDK officiel (npm xi_sdk_resellers, documentation https://unpkg.com/xi_sdk_resellers@1.2.0/docs/ProductCatalogApi.md) **VÉRIFIÉ** : `POST /resellers/v6/catalog/priceandavailability` ; en-têtes IM-CustomerNumber et IM-CountryCode (« Two-character ISO country code ») ; « Pricing, Availability, discounts, Inventory Location, Reserve Inventory for the products upto 50 products ». Dépôts GitHub officiels : github.com/ingrammicro-xvantage (non lus, accès GitHub non activé dans la session).
- France couverte par l'API : NON VÉRIFIÉ (une annonce d'octobre 2024, vue en extrait, cite la France pour le cloud). Conditions d'ouverture d'un compte en France : NON VÉRIFIÉ. Clause sur la revente via Amazon : NON VÉRIFIÉ.
- Point bloquant : l'exigence d'un « historique d'achats » exclut un compte tout neuf.

### 2.7 api Computerhandels GmbH (Allemagne, Autriche, Pays-Bas) — informatique et biens de consommation
- **VÉRIFIÉ** documentation officielle https://pricelist.api.de/RealTimePricelist_Documentation_EN.pdf (CONTINUE Software, 2021) : domaines pricelist.api.de / pricelist.api-oesterreich.at / pricelist.apibv.nl ; téléchargement `https://BaseURL/pricelist/?cid=CustomerNumber&shop=Shop` avec authentification basique « [CustomerNumber]:[password] » ; préréglage « full » = « sku;stock;currency;price;title;manufacturer;msku;ean;… » ; formats « csv, xml, html, bmecat, pricat » ; « The price list can be accessed a maximum of 3 times within 15 minutes ».
- **VÉRIFIÉ** https://api.de/en/addedvalue/fulfillment : « ViND - Shipping on Behalf of Third Parties » (envoi neutre au client final) ; listes d'articles en CSV et XML ; commandes en XML/EDI (OpenTrans).
- Accès : inscription « New customer » (conditions non lues) ; Amazon : NON VÉRIFIÉ.

### 2.8 Nedis (Pays-Bas) — électronique grand public, maison, accessoires informatiques
- **VÉRIFIÉ** documentation officielle https://nedis.notion.site/Real-Time-Request-P-A-Check-763472c680454898ac5b5cc867c16d5b : « The NEDIS API is the gateway to usage of the NEDIS Connect services » ; jeton OAuth2 par `api.nedis-connect.com/oauth2/token.json`, valable 60 minutes ; « We accept only requests from pre listed IP addresses » ; un quota quotidien « communicated to you » ; un prix client « includes customer specific price agreements / discounts » (`articles/price.json`) ; identifiant « NedisArtlid as being communicated in the Article Datafeeds » ; accès en contactant le bureau Nedis local.
- EDI via Onetrail — **VÉRIFIÉ (extrait)** https://nedis.com/en-us/business/edi
- Point à noter : il faut une adresse IP fixe déclarée, donc une contrainte d'hébergement pour l'outil.
- Amazon : NON VÉRIFIÉ.

### 2.9 TD SYNNEX (Europe)
- **VÉRIFIÉ** https://developer.api.tdsynnex.com/eu : Catalogue « Explore and access product, pricing, and availability details across our entire catalogue » ; Order Management ; Quotes « Under Construction ». Type d'authentification non indiqué.
- Prix et dispo en temps réel par un code d'autorisation fourni par TD SYNNEX (UK, BE, FR, NL) — **VÉRIFIÉ (extrait)** du guide tiers QuoteWerks.
- Conditions d'ouverture en France et clause Amazon : NON VÉRIFIÉ.

### 2.10 ITscope (Allemagne) — agrégateur de données informatiques
- **VÉRIFIÉ** https://guide.itscope.com/en/kb/introduction/ : « allows the integration of aggregated and processed product data from distributors listed on ITscope » ; « https://api.itscope.com/2.1 ». OpenAPI publique `https://api.itscope.com/2.1/openapi.json` ; plus de 3 millions de produits et plus de 400 fournisseurs — **VÉRIFIÉ (extrait)** https://guide.itscope.com/en/kb/interactive-api/
- **VÉRIFIÉ** https://www.itscope.com/en/solutions/itscope-erp-integration/individual-api/ : « up to 5,000 API calls per month » inclus ; au-delà, « pricing is available on request ».
- Usage : comparer les prix d'achat entre distributeurs allemands. Il faut un compte chez chaque distributeur pour acheter. Amazon : sans objet.

### 2.11 ALSO (France, Allemagne)
- CGV ALSO France (2020) **VÉRIFIÉ** https://www.also.com/ec/cms5/media/documents/2000_1/legal_3/legal_also_2020/cgv_also_01072020.pdf : « L'Acheteur devra remplir le formulaire d'ouverture de compte en ligne afin de recevoir ses codes d'accès » ; « La première commande sera impérativement réglée par l'Acheteur avant livraison ». Aucune clause sur les places de marché trouvée dans le texte.
- Liste de prix configurable, ALSO Deutschland **VÉRIFIÉ** https://www.also.com/ec/cms5/media/documents/1010_1/services_16/it_services_5/ftp_preislisten_1/preislisten_vereinbarung.pdf : « einmalige Freischaltungsgebühr in Höhe von 49,- € » ; formats « TXT oder CSV » ; récupération sur FTP ; « Ausgeschlossen ist somit u.a. die Weitergabe der Preislisten an Preisvergleichsplattformen » (pas de diffusion des listes à des tiers).
- Page de la boutique : « Prices and availability of all products are updated by the second » — **VÉRIFIÉ** https://www.also.com/ec/cms5/en_6000/6000/web-shop/services/index.jsp. Pas d'API publique trouvée.

### 2.12 Warmako (Pays-Bas) — animalerie
- **VÉRIFIÉ** https://www.warmako.com/en/pages/about : « EDI or API connections, or directly by phone and email » ; clients « pet shops, retail chains, garden centres, online retailers » ; « more than 5,000 items from leading brands in the pet industry ». Documentation API non publique ; Amazon : NON VÉRIFIÉ.

### 2.13 Kosatec (Allemagne) — informatique
- **VÉRIFIÉ** https://shop.kosatec.de/ : offre « richtet sich ausschließlich an Unternehmen, Gewerbetreibende, Behörden und Freiberufler » ; « E-Services und EDI-Schnittstellen » ; expédition directe possible au client final.
- URL du flux `http://data.kosatec.de/<n° client>/<clé EDI>/preisliste.csv` : **VÉRIFIÉ (extrait)**, source tierce https://salesbuildr.featurebase.app/p/distributer-kosatec. Amazon : NON VÉRIFIÉ.

### 2.14 Brandsdistribution (Italie) — mode
- **VÉRIFIÉ** https://www.brandsdistribution.com/en/cms/dropshipping-terms : « The Dropshipping service requires no minimum purchase order » ; avec emballage par le revendeur, « cumulative orders (min. 500€) » ; « it is forbidden to use the registered logo or trademark without the brand owner's authorization » ; Sparco exclu de la revente en ligne ; 99 €/mois ou 990 €/an. Amazon n'est pas cité dans ces conditions. Un ancien PDF exclut les places de marché, alors que le guide actuel cite Amazon (extraits) : **à faire confirmer par écrit** (dropshipment@brandsdistribution.com).
- API Rewix : https://developer.rewixecommerce.com/ **VÉRIFIÉ** (catalogue, réservation, commandes ; compte de test via le support).

### 2.15 BrandsGateway (Suède) — mode luxe
- **VÉRIFIÉ** https://helpdesk.brandsgateway.com/en/article/do-you-have-a-solution-for-custom-built-websites-e5balp : « we can generate credentials for Rest API integration » ; documentation https://nova.shopwoo.com/api/v1/docs ; « automated order forwarding and real-time inventory synchronization » (page de 2022).
- Amazon via les applications des plateformes — **VÉRIFIÉ (extrait)** https://brandsgateway.com/blog/amazon-dropshipping

### 2.16 CJdropshipping (Chine, entrepôt en Allemagne)
- API **VÉRIFIÉ** https://developers.cjdropshipping.com/en/api/start/Orders-Synchronization-Processing.html : `GET /product/stock/getInventoryByPid`, `GET /warehouse/detail`, `POST /order/createOrderV2`, `POST /pay/payBalanceV2`, `GET /logistic/trackInfo`.
- Amazon et FBA (« bulk purchasing… shipping arrangements to designated FBA warehouses ») : **VÉRIFIÉ (extrait)** https://cjdropshipping.com/integrations/amazon (page protégée, lecture bloquée). Entrepôt de Francfort : extrait du blog CJ.
- Acceptation de la facture CJ par Amazon : NON VÉRIFIÉ (une simple question sur le forum vendeurs). Produits souvent sans marque : contrôler la conformité CE et le GPSR.

### 2.17 Spocket
- **VÉRIFIÉ** https://help.spocket.co/en/articles/3018488-where-can-i-sell-spocket-products : Amazon et eBay dans les canaux autorisés ; Etsy, Wish, Groupon, Facebook Marketplace et Google Shopping interdits, sous peine de fermeture du compte. Pas d'API retailer publique trouvée. Achat en gros pour FBA : NON VÉRIFIÉ.

### 2.18 Inter Cars (Pologne) — pièces auto
- API REST « IC API » : https://docs.webapi.intercars.eu/ic-api/en/docs/documentation/Intro (lecture en 403) ; pages officielles « API & CSV » — **VÉRIFIÉ (extrait)**. Conditions d'accès et clause Amazon : NON VÉRIFIÉ.

### 2.19 EPROLO
- API : « Your support agent will send the API document to you » ; entrepôts « USA, UK, EU » ; Amazon cité dans les intégrations — **VÉRIFIÉ (extrait)** https://eprolo.com/eprolo-api

### 2.20 Avasam (Royaume-Uni)
- Intégration Amazon (fiches, commandes, stock) et une API (JSON/XML/CSV/EDI) — **VÉRIFIÉ (extrait)** https://www.avasam.com/enterprise/ ; fournisseurs surtout au Royaume-Uni.

### 2.21 Matterhorn, Ikonka, Doba, Syncee
- Matterhorn : une API citée sur son blog, sans documentation publique — **VÉRIFIÉ (extrait)** https://matterhorn-wholesale.com/blog/?p=5737
- Ikonka : fichier XML (code, stock, prix) configurable sur https://www.ikonka.com.pl/api2.html — **VÉRIFIÉ (extrait)** via la FAQ base.com.
- Doba : « Doba houses thousands of wholesale dropship suppliers based in the USA and globally » ; aucune place de marché UE précisée — **VÉRIFIÉ** https://www.doba.com/integrations/amazon ; Retailer API v2.0 (extrait de la page tarifs).
- Syncee : « Syncee does not have a direct integration with Amazon or Amazon fulfillment » — **VÉRIFIÉ** https://help.syncee.com/en/articles/8949761-amazon-fba

### 2.22 Agrégateur de connexion : base.com (BaseLinker)
- Grossistes reliés par fichier XML ou CSV, ou par API ; « In some cases, simply enabling the module is sufficient » ; 50 PLN HT par mois pour chaque grossiste standard au-delà du premier ; Base Connect sans supplément. **VÉRIFIÉ** http://base.com/en-EN/help/knowledgebase/wholesalers/ (la liste des grossistes n'est visible que dans l'application). Utile pour repérer les grossistes surtout polonais (Inter Cars, Ikonka, EET, Eurotoys…).

---

## 3. Liste NON VÉRIFIÉ (à confirmer avant de s'engager)

1. Acceptation par Amazon des factures d'**un seul** de ces fournisseurs pour ouvrir une catégorie : rien d'officiel lu.
2. Clauses de revente sur Amazon chez Ingram Micro France, TD SYNNEX France, ALSO, Nedis, Kosatec, api, Warmako, Inter Cars, Matterhorn, Ikonka.
3. Couverture de la France par l'API Ingram Micro (catalogue, prix et dispo).
4. Chemins exacts des endpoints d'offres de Qogita, et documentation de la « Public API (Buyers) ».
5. Présence de l'EAN dans l'API BTSwholesaler (non citée sur la page).
6. Brandsdistribution : Amazon autorisé ou non aujourd'hui (sources contradictoires).
7. vidaXL : les conditions actuelles (FAQ ancienne, page bloquée).
8. CJdropshipping : service FBA et entrepôt UE (page Amazon bloquée).
9. Conditions financières de TD SYNNEX, Ingram Micro, Nedis, api et Warmako (frais, minimum, crédit).
10. Inter Cars : conditions d'accès à l'IC API (documentation bloquée).
11. Puckator : coût de l'import du Royaume-Uni vers l'UE et contenu du site UE.
12. Familles épicerie, bijoux, sport de marque, bébé, bagagerie : aucun grossiste UE avec API vérifié.
13. Esprinet, Komsa, Jarltech, Wortmann, EET, Exertis, Griffati : aucune API publique trouvée.
