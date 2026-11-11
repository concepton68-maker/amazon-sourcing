# Sources de données non-Amazon et innovantes pour un outil de sourcing Amazon (FR/EU d'abord, US) — état au 2026-11-11

Protocole : **VÉRIFIÉ** = lu sur la source primaire (doc officielle / conditions / grille tarifaire / décision de justice) pendant cette session, avec citation. **SECONDAIRE** = vu seulement via résumé de moteur de recherche, blog ou revendeur : non présenté comme un fait. Les éléments non vérifiables sont repris dans la section « NON VÉRIFIÉ » en fin de document. Méthode : WebFetch, curl + extraction de texte, pdftotext sur les PDF officiels. web.archive.org n'était pas joignable depuis cet environnement (« unable to fetch »), donc pas de recours à Wayback possible.

## 1. Flux produits des réseaux d'affiliation (Awin, Rakuten, CJ, Impact, Webgains, Tradedoubler, Kwanko/Effiliation, Daisycon, TradeTracker)

### Takeaway
Les flux d'affiliation sont la source la plus « propre » de prix + EAN/UPC + stock de détaillants, et Awin dit lui-même que les comparateurs de prix sont ses principaux utilisateurs de flux. En revanche l'accès est **par annonceur** : il faut un compte éditeur approuvé et, en général, l'accord de chaque annonceur (Rakuten l'exige explicitement). Les conditions d'usage précises (notamment un outil d'arbitrage qui sert à *racheter* pour revendre sur Amazon, et non à générer des clics affiliés) n'ont pas été trouvées publiquement : c'est un risque contractuel à lever annonceur par annonceur.

### Cited Findings
- **Awin — VÉRIFIÉ** : la « Product Feed List Download » liste les flux « from advertisers you've joined » **et** ceux des annonceurs qui « let you promote their products before you join » ; une colonne « Membership Status » indique l'adhésion. Il faut un Publisher ID + une « data feed key » (« The Publisher API key doesn't work for this »). Chaque flux « Includes only the columns the advertiser has filled in » → la présence de l'EAN/stock dépend de l'annonceur. — [Awin Developer Docs – Product Feed List Download](https://help.awin.com/developers/docs/product-feed-list-download)
- **Awin — SECONDAIRE (extrait du wiki Awin via moteur de recherche, page non chargée car redirigée)** : « Price comparison Publishers are the main users of our data feed platform » ; un annonceur peut avoir jusqu'à 10 flux par programme ; une nouvelle approbation peut mettre jusqu'à 1 h à se refléter dans Create-a-Feed. — [wiki.awin.com Create-a-feed](https://wiki.awin.com/index.php/Create-a-feed) ; [Awin FAQ publishers](https://help.awin.com/developers/docs/faqs-for-publishers)
- **Awin API « Enhanced (Google) feed »** : récupération par GET authentifié par annonceur, vertical « retail » uniquement (SECONDAIRE, résumé de recherche). — [developer.awin.com](https://developer.awin.com/apidocs/retail-publisher-productapidocumentation-1)
- **Rakuten Advertising — VÉRIFIÉ (PDF officiel « Product Catalog Data Feed: Implementation Guidelines for Publishers », 34 p.)** : « First, you will need to be approved and set up for the technical implementation of the product data feeds, and then you will need to be approved by each of your participating advertiser partners to use their Product Catalog data feed ». Livraison par **SFTP**, fichiers XML ou pipe-delimited, fichier complet ou delta, et aussi par catégorie. Champs : « Sale Price » (optionnel), « Retail Price » (requis), « Availability » (« ‘instock’, ‘out-of-stock’, ‘preorder’ or ‘backorder’ »), « Universal Product Code. May be UPC, EAN or JAN » (optionnel), « Currency » (requis). — [Rakuten pubhelp PDF](https://pubhelp.rakutenadvertising.com/hc/en-us/article_attachments/22365119792013)
- **CJ (Commission Junction) — SECONDAIRE uniquement** : selon la doc d'un acteur Apify tiers, l'API GraphQL CJ (ads.api.cj.com/query) a des requêtes `products`/`shoppingProducts` qui ne renvoient que les produits des annonceurs rejoints (403 si aucun), alors que `shoppingProductFeeds` liste tous les flux du réseau ; 1 000 items max par requête. La doc officielle developers.cj.com n'a renvoyé qu'un titre de page (rendu JS). — [Apify CJ actor (tiers)](https://apify.com/viralanalyzer/cj-affiliate-products)
- **Impact** : il existe une page d'aide officielle « Download product catalogs as a partner » (vue en japonais dans les résultats) mais son contenu n'a pas pu être extrait (rendu JS). — [help.impact.com (JA)](https://help.impact.com/partner/ja/nitsuitebitaidesuka/platform-features/marketing-content/product-marketplace-and-catalogs/download-product-catalogs-as-a-partner)
- **Walmart (US)** passe par Impact pour l'affiliation (SECONDAIRE, FAQ affiliates.walmart.com vue dans les résultats) ; un tiers affirme que Walmart « no longer releases new API keys » pour l'Affiliate API — non vérifié. — [affiliates.walmart.com FAQ](https://affiliates.walmart.com/faqs) ; [doc tierce PartnerBoost](https://docs.partnerboost.com/developers/publisher-api/walmart/)
- **Kwanko/Effiliation, Webgains, Tradedoubler, Daisycon, TradeTracker** : aucune documentation éditeur officielle trouvée/lue sur les conditions des flux produits (cf. NON VÉRIFIÉ).

### Inferences
- Pour un outil SaaS, le modèle viable est que **chaque utilisateur** (ou la société éditrice de l'outil, en tant qu'éditeur affilié) obtienne l'accès ; redistribuer à des clients tiers des flux obtenus sous son propre compte éditeur est probablement hors du cadre « promouvoir les produits de l'annonceur » — à confirmer dans les CG Awin/Rakuten (non lues).
- Bonus économique : si l'outil renvoie l'utilisateur vers le détaillant via le lien affilié du flux, l'éditeur de l'outil touche une commission sur les achats de sourcing — un modèle différenciant (outil moins cher, monétisé par l'affiliation). Les annonceurs peuvent toutefois refuser ou exclure les achats « revendeurs » ; non vérifié.
- Couverture FR : Awin (ex-Zanox/Affilinet) et Rakuten sont présents en France ; les gros comptes FR (Fnac, Darty, Cdiscount, Boulanger…) et leur réseau d'affiliation n'ont pas été vérifiés ici.

### Gaps
- CG éditeur Awin/Rakuten/CJ sur l'usage des flux (redistribution, usage en outil B2B, stockage) : non lues.
- Kwanko/Effiliation (FR), Webgains, Tradedoubler, Daisycon, TradeTracker : aucune source primaire consultée.

## 2. API publiques de détaillants / marketplaces (eBay, Walmart, Best Buy, Bol.com, Cdiscount/Octopia, Fnac-Darty, Kaufland, Allegro, Zalando)

### Takeaway
Seuls **eBay Browse API** (US + EU, 5 000 appels/jour par défaut, gratuit) et **Bol.com Marketing Catalog API** (NL/BE, réservée aux affiliés bol) sont de vraies API publiques de lecture de prix exploitables. **Best Buy** interdit explicitement l'usage pour analyser les prix Best Buy au profit de tiers et limite le cache à 72 h. **Allegro** a fermé la recherche d'offres aux seules « verified applications ». Les autres (Octopia/Cdiscount, Fnac-Darty, Kaufland, Zalando) n'exposent, d'après ce qui a été trouvé, que des API vendeur (gestion de son propre catalogue), pas de lecture du catalogue concurrent.

### Cited Findings
- **eBay Browse API — VÉRIFIÉ (page officielle, extraction curl)** : « All methods except getItems: 5000 API calls per day » ; « getItems: 5000 API calls per day » ; ressource item_snapshot du Feed API : « 75,000 API calls per day ». — [eBay Buy API call limits](https://developer.ebay.com/develop/api/buy/api_call_limits)
- eBay Browse API permet la recherche « by keyword, category, GTIN, product… or image » et « All methods in the Browse API require an Application access token » (client credentials) — VÉRIFIÉ (même page). — [eBay Buy APIs](https://developer.ebay.com/develop/api/buy/api_call_limits)
- Hausse des quotas via « Application Growth Check » (SECONDAIRE : modérateur forum eBay). Les Buy APIs « require an additional license » pour certains usages (SECONDAIRE, résumé). — [eBay community](https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/About-API-limit-calls/m-p/34673055)
- **Best Buy API (US) — VÉRIFIÉ (conditions officielles)** : quotas 50 000 appels/jour et 5/seconde ; interdiction de « store or cache any Content except on a temporary basis not to exceed seventy-two (72) hours » ; interdiction de permettre à des tiers d'utiliser le service « for the purposes of analyzing, receiving or reviewing information regarding Best Buy pricing » ; attribution et logo Best Buy obligatoires ; usage commercial lié à « offers to sell or sales of our products and services » ; pas d'accès tiers sans autorisation. — [Best Buy Developer legal](https://developer.bestbuy.com/legal)
- **Bol.com Marketing Catalog API — VÉRIFIÉ** : « The Marketing Catalog API refers to the combined set of API functions which we are offering to all affiliates that are registered with the affiliate program » ; Step 1 « Get an Affiliate Account » ; la spec OpenAPI contient des champs `offer`, `price`, `deliveryDescription` et des tris `PRICE_ASC/PRICE_DESC` ; endpoints par EAN (SECONDAIRE pour la formulation exacte). Les CGU renvoient vers affiliate.bol.com/nl/algemene-voorwaarden (non lues). — [bol Marketing Catalog API](https://api.bol.com/marketing/docs/catalog-api/index.html) ; [OpenAPI spec](https://api.bol.com/marketing/docs/api-reference/catalog-api-v1.html)
- **Allegro (PL) — VÉRIFIÉ** : endpoint `/offers/listing` « Search offers — Access for verified applications only » ; restriction introduite le 1er juin 2021 (SECONDAIRE : actualité Allegro dev). — [Allegro offers-listing docs](https://developer.allegro.pl/docs/offers-listing) ; [annonce 2021](https://developer.allegro.pl/news/wprowadzilismy-ograniczenia-dla-get-offers-listing-WvGz1qOlxc6)
- **Idealo** : l'API officielle (Partner Web Service 2.0) sert aux boutiques à pousser leurs offres ; pas d'API publique de données de prix trouvée (SECONDAIRE). — [idealo partner-web-service docs](https://idealo.github.io/partner-web-service/docs/v2)
- **Walmart** : l'API Marketplace `/v3/items/walmart/search` (recherche par UPC/GTIN) est documentée côté vendeur (SECONDAIRE). — [developer.walmart.com](https://developer.walmart.com/us-marketplace/docs/get-item-details)

### Inferences
- eBay = meilleure source « non-Amazon » gratuite pour des prix de revente/achat (US + FR/DE/UK) recherchables par GTIN ; 5 000 appels/jour suffisent pour un MVP mono-utilisateur mais pas pour un SaaS sans Growth Check.
- Best Buy est exploitable pour afficher des produits Best Buy avec lien, mais un outil d'arbitrage qui « analyse » les prix Best Buy pour des revendeurs est au minimum en zone grise vis-à-vis de la clause citée.
- Pour la France, aucun grand détaillant FR (Cdiscount, Fnac, Darty, Boulanger, Leclerc) n'a été trouvé offrant une API publique de prix ; la voie FR passe par les flux d'affiliation ou le scraping.

### Gaps
- CGU eBay API License Agreement (clauses comparateur/stockage) : page non extraite.
- Octopia, Kaufland, Zalando, Fnac-Darty : pas de recherche aboutie ; supposés API vendeurs uniquement (non vérifié).
- Walmart Affiliate/Product Lookup API (walmart.io) : statut 2026 des clés non vérifié.

## 3. Comparateurs de prix et SERP Google Shopping

### Takeaway
Pas d'API ouverte chez Idealo/PriceRunner/Ledenicheur trouvée. Google Shopping est accessible via des fournisseurs SERP : **DataForSEO** (0,001 $/page de 40 produits en file standard) et **SerpApi** (à partir de 25 $/mois pour 1 000 recherches), tarifs VÉRIFIÉS. C'est la manière la moins chère d'obtenir « qui vend ce GTIN et à quel prix » en FR et US.

### Cited Findings
- **DataForSEO Google Shopping (Merchant API) — VÉRIFIÉ** : `/merchant/google/products/*` « Standard queue … Up to 45 minutes Per SERP 40 products $0.001 $1,000 per 1M units » ; Priority queue 0,002 $ ; `/merchant/google/product_info/*` 0,001 $ par produit ; `/merchant/google/sellers/*` « Per SERP 10 sellers $0.001 » ; « a single request can return up to 120 results (three SERPs) ». — [DataForSEO Google Shopping pricing](https://dataforseo.com/pricing/merchant/google-shopping-api)
- DataForSEO vend aussi des données Amazon : « AMAZON ASINS … Standard queue … $0.0015 » par produit, Live 0,005 $ (VÉRIFIÉ). — [DataForSEO Merchant API](https://dataforseo.com/apis/merchant-api)
- **SerpApi — VÉRIFIÉ** : Free 0 $/mois « 250 searches per month » ; Starter 25 $ « 1,000 searches » ; Developer 75 $ « 5,000 searches » ; Production 150 $ « 15,000 searches » ; mention d'une « U.S. Legal Shield … up to $2 million in coverage for the scraping and parsing of search engine data ». — [SerpApi pricing](https://serpapi.com/pricing)
- Idealo : API réservée aux marchands listés (SECONDAIRE) ; des scrapers Apify tiers non officiels existent. — [idealo technical integration FAQ](https://partner.idealo.com/uk/learning-center/faq-technical-integration)

### Inferences
- Coût indicatif : 100 000 GTIN interrogés/mois sur Google Shopping via DataForSEO ≈ 100 $ (file standard, 1 SERP chacun) — calcul dérivé du tarif vérifié.
- Le risque juridique de collecte est porté par le fournisseur (contrat), mais la redistribution des résultats Google reste soumise aux CGU Google (non analysées).

### Gaps
- PriceRunner / Ledenicheur (Klarna) : aucune API partenaire trouvée ni conditions lues.
- CGU DataForSEO/SerpApi sur la redistribution commerciale des résultats : non lues.

## 4. Identité produit / données EAN (GS1, Open Food Facts / Open Products Facts, UPCitemdb, EAN-Search, Barcode Lookup)

### Takeaway
Pour réconcilier un produit fournisseur/détaillant ↔ ASIN par EAN, les API commerciales sont bon marché (EAN-Search dès 19 €/mois, UPCitemdb gratuit 100 req/jour). Open Food Facts est réutilisable commercialement mais sous **ODbL (share-alike)** et limité à 15 req/min → usage par dump. Verified by GS1 n'est accessible en API qu'en passant par une organisation membre GS1, prix non publié.

### Cited Findings
- **Open Food Facts — VÉRIFIÉ (CGU)** : « The Open Food Facts database is available under the Open Database License » ; contenus individuels sous DbCL ; images CC BY-SA ; usage « for all purposes, including commercial use, under certain conditions » ; « Derivative works must be shared under the same conditions » ; attribution + lien obligatoires ; « Other rights of third parties may apply ». — [OFF terms of use](https://world.openfoodfacts.org/terms-of-use)
- **Open Food Facts API — VÉRIFIÉ** : « 15 req/min/IP address for all read product queries » ; « 10 req/min/IP address for all sear[ch] » ; « If you need to fetch more than a few hundred products, we ask you to download the data as a CSV or JSONL file directly ». — [OFF API docs](https://openfoodfacts.github.io/openfoodfacts-server/api/)
- **UPCitemdb — VÉRIFIÉ** : « plan FREE allows total of 100 combined requests per day … SearchRequest is limited up to 40 per day … for plan DEV, you can send 2,000 SearchRequest and 20,000 LookupRequest everyday ». Prix des plans payants non extraits. — [UPCitemdb rate limits](https://www.upcitemdb.com/wp/docs/main/development/api-rate-limits/)
- **EAN-Search.org — VÉRIFIÉ** : Trial « 1 EUR for the first month then 9 EUR / month » ; Pro « 5,000 queries / month 19 EUR / month » ; Bronze « 50,000 queries / month 39 EUR » ; Silver « 150,000 … 99 EUR » ; Gold « 300,000 … 149 EUR » ; « 10% discount if you pay yearly » ; « Prices include all applicable taxes ». — [EAN-Search API](https://www.ean-search.org/ean-database-api.html)
- **Barcode Lookup — VÉRIFIÉ** : Starter « 5,000 API calls $99 / month » ; Advanced 25 000 → 249 $ ; Professional 100 000 → 499 $ ; Enterprise 500 000 → 949 $ ; « Pay month to month ». — [Barcode Lookup API](https://www.barcodelookup.com/api)
- **Verified by GS1 — VÉRIFIÉ (gs1.org)** : « Enterprise-level capabilities are also available for retrieving data such as batch querying and API connection. Contact your local GS1 office ». Le quota gratuit « 30 queries per day » est SECONDAIRE (résumé de recherche de pages gs1.org). — [Verified by GS1](https://www.gs1.org/services/verified-by-gs1) ; [CGU PDF](https://gs1.org/docs/verified-by-gs1/public-verified-by-gs1-tou.pdf)

### Inferences
- Utiliser OFF/OPF comme base interne de matching n'oblige au share-alike que si l'on publie une base dérivée ; l'usage interne et l'affichage d'« œuvres produites » sont en principe permis sous ODbL (interprétation de la licence, non vérifiée sur le texte ODbL lui-même). Open Products Facts (non alimentaire) a une couverture limitée (non quantifiée).
- EAN-Search (Gold 149 €/300 k requêtes) est l'option la moins chère par requête parmi celles vérifiées (~0,0005 €/requête) vs Barcode Lookup (~0,0019 $/requête au palier 500 k).

### Gaps
- Prix et conditions de l'API GS1 France (Codification / « GS1 France » Verified) : non trouvés.
- CGU EAN-Search / Barcode Lookup sur la redistribution des données dans un SaaS : non lues.

## 5. Découverte grossistes / fournisseurs (annuaires B2B, données douanières, salons)

### Takeaway
Les données douanières US niveau connaissement (Bill of Lading) sont disponibles commercialement (ImportGenius dès 229 $/mois, ou 183 $/mois en annuel — VÉRIFIÉ) et permettent d'identifier importateurs/distributeurs d'une marque aux US. Il n'existe pas d'équivalent public niveau expédition en UE (recherche non aboutie). Kompass/Europages et listes d'exposants n'ont pas pu être vérifiés.

### Cited Findings
- **ImportGenius — VÉRIFIÉ (page tarifs officielle)** : « USA Essentials … $229 per month starting price Cancel anytime » ou « $183 … per month billed $2,198/yr » ; « USA Pro … $449 per month » ou « $359 … billed $4,310/yr » ; « Global Enterprise $1999 per month starting price » ; données « U.S. Customs at the Bill of Lading level » ; « Datasets starting from $159 ». — [ImportGenius pricing](https://www.importgenius.com/pricing)
- Des fiches Capterra/TrustRadius donnent d'autres prix (125 $, 149 $…) — obsolètes/contradictoires par rapport à la page officielle. — [Capterra](https://www.capterra.com/p/10032153/ImportGenius/) ; [TrustRadius](https://www.trustradius.com/products/importgenius/pricing)

### Inferences
- Croiser « importateur US d'une marque » (douane) avec « vendeurs Amazon de cette marque » est une combinaison originale pour trouver des distributeurs autorisés aux US ; inapplicable telle quelle en France faute de données douanières publiques au niveau expédition (inférence, non confirmée par une source).

### Gaps
- Panjiva (S&P Global) : prix non publics (non vérifié).
- Kompass, Europages : existence/prix d'une API non vérifiés.
- Données douanières UE (Comext Eurostat = statistiques agrégées par code NC/pays, pas par entreprise) : non vérifié dans cette session.
- Listes d'exposants (ex. salons Paris) : pas de source sur les droits de réutilisation.

## 6. Scraping de sites détaillants (approche Tactical Arbitrage) : droit UE/FR, US, coûts

### Takeaway
En UE, le scraping systématique d'un site détaillant pour indexer/rechercher son catalogue constitue une « extraction / réutilisation » au sens du droit sui generis des bases de données, **interdite par le producteur seulement si elle porte atteinte à son investissement** (CJUE CV-Online, 2021) ; et si la base n'est pas protégée, le site peut imposer des limites purement contractuelles (CJUE Ryanair, 2015). Aux US, le scraping de données publiques en mode déconnecté a été jugé hors du champ des CGU de Meta (Meta v. Bright Data, 2024), mais hiQ a fini par une injonction et une reconnaissance de responsabilité contractuelle (2022). Coût proxies résidentiels : 2–8 $/GB selon fournisseur et volume (VÉRIFIÉ).

### Cited Findings
- **CJUE C-762/19 CV-Online Latvia (3 juin 2021) — VÉRIFIÉ (EUR-Lex, dispositif)** : l'art. 7(1)-(2) de la directive 96/9/CE doit être interprété en ce sens qu'« an Internet search engine specialising in searching the contents of databases, which copies and indexes the whole or a substantial part of a database freely accessible on the Internet and then allows its users to search that database on its own website according to criteria relevant to its content, is 'extracting' and 're-utilising' that content … which may be prohibited by the maker of such a database where those acts adversely affect its investment in the obtaining, verification or presentation of that content, namely that they constitute a risk to the possibility of redeeming that investment through the normal operation of the database in question, which it is for the referring court to verify ». Points 41-42 : juste équilibre avec l'intérêt des utilisateurs/concurrents ; les agrégateurs « contribute to the smooth functioning of competition ». — [EUR-Lex CELEX 62019CJ0762](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62019CJ0762)
- **CJUE C-30/14 Ryanair v PR Aviation (15 janv. 2015) — VÉRIFIÉ (dispositif)** : la directive 96/9 « is not applicable to a database which is not protected either by copyright or by the sui generis right … so that Articles 6(1), 8 and 15 of that directive do not preclude the author of such a database from laying down contractual limitations on its use by third parties without prejudice to the applicable national law ». — [EUR-Lex CELEX 62014CJ0030](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62014CJ0030)
- **Meta Platforms v. Bright Data, N.D. Cal. 3:23-cv-00077-EMC, Doc. 181, 23 janv. 2024 — VÉRIFIÉ (PDF de l'ordonnance)** : « the Court DENIES Meta's cross-motion for partial summary judgment and GRANTS Bright Data's motion for summary judgment » ; « Meta has not presented evidence sufficient to raise a reasonable inference that Bright Data scraped data while logged into an account and thereby accessed non-public data ». — [Ordonnance (CourtListener RECAP)](https://storage.courtlistener.com/recap/gov.uscourts.cand.406956/gov.uscourts.cand.406956.181.0.pdf)
- Meta a ensuite abandonné la demande restante et renoncé à l'appel (SECONDAIRE). — [TechCrunch 26/02/2024](https://techcrunch.com/2024/02/26/meta-drops-lawsuit-against-web-scraping-firm-bright-data-that-sold-millions-of-instagram-records/)
- **hiQ v. LinkedIn (N.D. Cal. 17-cv-03301) — SECONDAIRE** : stipulation déposée le 6 déc. 2022, jugement d'accord et injonction permanente ; 500 000 $ contre hiQ ; hiQ reconnaît que LinkedIn peut établir sa responsabilité (CFAA, trespass to chattels, misappropriation) ; obligation de cesser le scraping et détruire données/code. PDF primaire (DocumentCloud) bloqué par Cloudflare. — [Proskauer](https://newmedialaw.proskauer.com/2022/12/08/hiq-and-linkedin-reach-proposed-settlement-in-landmark-scraping-case/) ; [ZwillGen](https://www.zwillgen.com/alternative-data/hiq-v-linkedin-wrapped-up-web-scraping-lessons-learned/)
- **Tactical Arbitrage — VÉRIFIÉ (site officiel)** : « Tactical Arbitrage provides 1,400+ online retail sites » / « 1392 sourcing sites available » ; Quick Search sur « cached retailer data » ; fonctionne « entirely on our servers (in the cloud) » ; aucune mention de flux d'affiliation. — [tacticalarbitrage.com](https://tacticalarbitrage.com/)
- **Proxies résidentiels — VÉRIFIÉ (pages officielles, 11/2026)** :
  - Bright Data : « PAY AS YOU GO $8 $4 /GB » (promo -50 % affichée), 141 GB inclus à 499 $/mois (« $7 $4 /GB »), 332 GB à 999 $, 798 GB à 1 999 $. — [Bright Data residential pricing](https://brightdata.com/pricing/proxy-network/residential-proxies)
  - Oxylabs : 6 $/GB (≤2 GB) → 5 $ (≤20 GB) → 4 $ (≤125 GB) → 2,50 $ (1K+ GB) ; plans Starter 15 $, Basic 100 $, Flexible 500 $, Enterprise dès 2 500 $ ; incohérence interne (FAQ « start at $30 per month »). — [Oxylabs residential](https://oxylabs.io/products/residential-proxy-pool)
  - Decodo (ex-Smartproxy) : PAYG 4 $/GB ; 3 GB 3,75 $/GB … 100 GB 2,75 $/GB ; 1 000 GB 2,00 $/GB ; HT. — [Decodo residential](https://decodo.com/proxies/residential-proxies)

### Inferences
- Pour un outil type Tactical Arbitrage visant des sites FR : réindexer **une partie substantielle** du catalogue d'un détaillant FR et la rendre interrogeable constitue une extraction/réutilisation ; le risque juridique dépend de l'atteinte à l'investissement du détaillant (CV-Online). Un outil qui renvoie vers le détaillant (trafic acheteur) a de meilleurs arguments qu'un outil qui se substitue à son site — inférence.
- Les CGU des sites (interdisant robots) restent opposables contractuellement si la base n'est pas protégée (Ryanair) ; en France l'opposabilité de CGU « browsewrap » n'a pas été vérifiée.
- Coût brut : une page produit détaillant ≈ quelques centaines de Ko à quelques Mo ; à ~4 $/GB, 1 M de pages ≈ quelques centaines à quelques milliers de $ / mois (ordre de grandeur, non mesuré).

### Gaps
- Transposition française (CPI art. L.341-1 s., L.342-1 « droit du producteur de bases de données ») : Légifrance non accessible (contenu non extrait) → NON VÉRIFIÉ.
- Jurisprudence française spécifique au scraping de détaillants (ex. Leboncoin v. Entreparticuliers) : non vérifiée.
- robots.txt : pas de statut juridique contraignant vérifié ; la réserve « opt-out » de l'art. 4 directive 2019/790 (TDM) n'a pas été examinée.

## 7. Signaux côté Amazon utilisables légalement (badge « bought in past month », Creators API, Keepa)

### Takeaway
**Point bloquant majeur (VÉRIFIÉ)** : la Licence Associates interdit, sans accord écrit d'Amazon, d'utiliser la Creators API / PA-API « in connection with any software or other application intended for use by persons or entities that offer products on an Amazon Site » — c'est-à-dire précisément un outil pour vendeurs Amazon. Elle interdit aussi le suivi/alerte de prix et la revente du contenu. La Creators API (successeur de PA-API 5) n'est donc **pas** une source légale pour un outil de sourcing. Keepa reste la voie licite (API payante), tarifs non vérifiables sur source primaire (site en JS).

### Cited Findings
- **Creators API — VÉRIFIÉ** : « The Creators API is a REST-based API that provides programmatic access to Amazon's product catalog data » ; éligibilité : « Have at least 10 qualifying sales within the past 30 days to access the PA API through the Creators API » ; opérations SearchItems, GetItems, GetVariations, GetBrowseNodes. — [Creators API introduction](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction)
- Champs OffersV2 — VÉRIFIÉ : `price`, `availability`, `merchantInfo`, `isBuyBoxWinner` (« Returns whether the given offer for the product is buy box winner »), `condition`, `type`, `dealDetails` ; GetItems jusqu'à 10 ASIN/requête. — [GetItems reference](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/operations/get-items)
- Quotas — VÉRIFIÉ : « an initial usage limit up to a maximum of one request per second (one TPS) and a cumulative daily maximum of 8640 requests per day (8640 TPD) for the first 30-day period » ; puis « one TPD for every five cents or one TPS (up to a maximum of ten TPS) for every $4320 of shipped item revenue generated via the use of Creators API … previous 30-day period » ; perte d'accès si pas de vente qualifiée pendant 30 jours consécutifs ; erreur 429. — [Creators API rates](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/api-rates)
- **Licence/Politiques Associates — VÉRIFIÉ** :
  - « (e) You will not, without our express prior written approval, access or use Creators API, PA API or Data Feeds for the purpose of aggregating, analyzing, extracting, or repurposing any Product Advertising Content or in connection with any software or other application intended for use by persons or entities that offer products on an Amazon Site, or in the direct training or fine-tuning of a machine learning and/or foundational model. »
  - « (y) Unless otherwise agreed by Amazon, your Site must not have price tracking and/or price alerting functionality. »
  - « (b) You will not sell, resell, redistribute, sublicense, or transfer any Program Content or any application that uses, incorporates, or displays any Program Content, Creators API, PA API, or Data Feeds. »
  - Cache max 24 h, puis rafraîchissement obligatoire ; usage autorisé seulement s'il a « the principal purpose of advertising and marketing an Amazon Site and driving sales ».
  - Licence : « This license does not include … any use of data mining, robots, or similar data gathering » ; interdiction de contourner CAPTCHAs / mesures anti-agents.
  - En format comparateur, obligation d'afficher le plus bas prix neuf (et occasion si fourni). — [Amazon Associates Program Policies](https://affiliate-program.amazon.com/help/operating/policies)
- Date de dépréciation PA-API 5 : sources contradictoires (30 avril 2026 vs 15 mai 2026) — SECONDAIRE. — [DEV.to](https://dev.to/th3nate/amazon-pa-api-v5-is-shutting-down-april-30-2026-here-is-what-changes-at-the-auth-layer-22ek)
- **Keepa API — SECONDAIRE** : 49 €/mois pour 20 tokens/minute ; ~1 token par ASIN ; tokens expirant après 60 min ; paliers jusqu'à 11 099 €. Page officielle keepa.com rendue en JS, non extraite. — [revenuegeeks (tiers)](https://revenuegeeks.com/software/keepa/api)

### Inferences
- Un outil de sourcing doit obtenir les données Amazon via **SP-API** (données de l'utilisateur vendeur lui-même, avec son autorisation — hors périmètre de cette note) et/ou **Keepa** (licence payante), pas via la Creators API.
- Le badge « bought in past month » n'est disponible que sur les pages Amazon ; le collecter par scraping est contraire aux conditions d'utilisation d'Amazon (Conditions of Use non lues ici) — non recommandé.

### Gaps
- Exposition du badge « X+ bought in past month » via une API officielle (SP-API Catalog / Creators API) : non vérifié.
- Tarifs officiels Keepa et éventuel « free tier » : non vérifiés sur source primaire.

## 8. Outils existants utilisant des flux d'affiliation pour l'arbitrage Amazon

### Takeaway
Aucun des outils cités (Tactical Arbitrage, SourceMogul, OAGenius, ProfitPath, Arbitrage Hero) ne documente publiquement l'usage de flux d'affiliation dans ce qui a été consulté. Tactical Arbitrage décrit un scan de 1 400+ sites avec cache serveur. **Un outil fondé sur des flux d'affiliation + EAN serait donc différenciant** (sous réserve des CG des réseaux).

### Cited Findings
- Tactical Arbitrage : 1 400+ sites, données retailer en cache, rien sur l'affiliation (VÉRIFIÉ). — [tacticalarbitrage.com](https://tacticalarbitrage.com/)
- SourceMogul : décrit par CB Insights comme scannant les sites détaillants ; aucune mention d'affiliation (SECONDAIRE). — [CB Insights](https://www.cbinsights.com/company/profitsourcery/)

### Inferences
- L'absence de mention n'est pas une preuve d'absence ; certains outils utilisent peut-être des flux sans le dire.

### Gaps
- OAGenius, ProfitPath, Arbitrage Hero : sites non consultés faute de budget d'appels.

## Synthèse — combinaisons faisables vs non faisables pour une petite équipe

### Takeaway
Faisable et différenciant : **flux d'affiliation (Awin/Rakuten, FR/EU/US) + matching EAN (EAN-Search/UPCitemdb/OFF dump) + eBay Browse (GTIN) + Google Shopping via DataForSEO + Keepa/SP-API pour le côté Amazon**, monétisable en partie par les commissions d'affiliation. Non faisable légalement : Creators API pour un outil vendeurs ; Best Buy API pour analyse de prix ; Allegro listing sans vérification. Scraping massif de détaillants FR : possible techniquement (2–4 $/GB), juridiquement à risque mesurable (CV-Online), à limiter.

### Cited Findings
- Coûts vérifiés pour un MVP mensuel : EAN-Search Bronze 39 € (50 k requêtes) [source](https://www.ean-search.org/ean-database-api.html) ; DataForSEO ≈ 0,001 $ par page Google Shopping [source](https://dataforseo.com/pricing/merchant/google-shopping-api) ; eBay Browse gratuit 5 000 appels/jour [source](https://developer.ebay.com/develop/api/buy/api_call_limits) ; OFF gratuit (ODbL, dump) [source](https://world.openfoodfacts.org/terms-of-use) ; proxies Decodo 4 $/GB PAYG [source](https://decodo.com/proxies/residential-proxies) ; données douane US ImportGenius 229 $/mois [source](https://www.importgenius.com/pricing).
- Interdictions vérifiées : Creators API pour outils vendeurs [Associates policies](https://affiliate-program.amazon.com/help/operating/policies) ; Best Buy analyse de prix par tiers + cache 72 h [Best Buy legal](https://developer.bestbuy.com/legal) ; Allegro « verified applications only » [Allegro](https://developer.allegro.pl/docs/offers-listing).

### Inferences
- **Combo A (FR, faible coût, ~50–150 €/mois hors Keepa)** : flux Awin/Rakuten des détaillants FR qui acceptent l'éditeur → EAN → ASIN (via Keepa ou SP-API de l'utilisateur) → marge calculée. Différenciation : prix + stock « officiels » et lien affilié rémunérateur. Risque : approbations annonceurs, couverture EAN variable.
- **Combo B (US/EU, découverte)** : Google Shopping (DataForSEO) par GTIN pour lister tous les vendeurs d'un produit, + eBay Browse pour prix de revente/liquidation. ~100 $ pour 100 k GTIN/mois.
- **Combo C (wholesale US)** : douane US (ImportGenius) → importateurs d'une marque → prospection distributeurs ; coût fixe 183–229 $/mois, pas d'équivalent FR vérifié.
- **Non recommandé** : Creators API comme source de prix Amazon ; scraping d'Amazon ; revente de flux affiliés à des tiers sans accord ; Best Buy API pour un outil d'arbitrage.

### Gaps
- Conditions contractuelles d'utilisation des flux d'affiliation par un outil d'arbitrage (cœur du modèle Combo A) : à obtenir par écrit auprès d'Awin/Rakuten/Kwanko.

## NON VÉRIFIÉ (récapitulatif, avec tentatives)

### Takeaway
Les éléments suivants n'ont pas pu être lus sur source primaire ; ne pas les présenter comme des faits.

### Cited Findings
- CJ Product Search / GraphQL : developers.cj.com renvoie une page JS vide (WebFetch) ; seule source = acteur Apify tiers. — [Apify](https://apify.com/viralanalyzer/cj-affiliate-products)
- Impact, Webgains, Tradedoubler, Kwanko/Effiliation, Daisycon, TradeTracker (conditions des flux) : recherche FR/EN sans résultat primaire ; page Impact non extractible. — [recherche Lengow (tiers)](https://www.lengow.com/fr/solutions/netamplify/affiliate-ads/)
- Keepa : tarifs 49 €/20 tokens/min — keepa.com en JS (curl/WebFetch sans contenu) ; Wayback indisponible. — [revenuegeeks (tiers)](https://revenuegeeks.com/software/keepa/api)
- Verified by GS1 : 30 requêtes/jour gratuites (résumé de recherche de pages gs1.org, non relu) ; prix API GS1 France inconnu. — [gs1.org](https://www.gs1.org/services/verified-by-gs1)
- hiQ v. LinkedIn : PDF de la stipulation (DocumentCloud) bloqué par Cloudflare ; CourtListener : mauvais numéro de document → résumé Proskauer/ZwillGen uniquement. — [Proskauer](https://newmedialaw.proskauer.com/2022/12/08/hiq-and-linkedin-reach-proposed-settlement-in-landmark-scraping-case/)
- eBay : quota par appli ou par utilisateur, et procédure Growth Check (forum modérateur uniquement) ; page developer.ebay.com/develop/get-started/api-call-limits → 403 au WebFetch. — [eBay community](https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/About-API-limit-calls/m-p/34673055)
- Walmart Affiliate API : « no longer releases new API keys » (doc tierce). — [PartnerBoost](https://docs.partnerboost.com/developers/publisher-api/walmart/)
- Idealo : pas d'API publique de données (sources tierces). — [idealo.github.io](https://idealo.github.io/partner-web-service/docs/v2)
- Date de fin PA-API 5 (30/04 vs 15/05/2026) : non confirmée sur page Amazon. — [DEV.to](https://dev.to/th3nate/amazon-pa-api-v5-is-shutting-down-april-30-2026-here-is-what-changes-at-the-auth-layer-22ek)

### Inferences
- Aucune.

### Gaps
- Non recherchés faute de budget : Octopia/Cdiscount, Fnac-Darty, Kaufland, Zalando (API), PriceRunner/Ledenicheur, Panjiva, Kompass, Europages, OAGenius, ProfitPath, Arbitrage Hero, Comext/douane UE, CPI français (Légifrance bloqué), prix payants UPCitemdb.
