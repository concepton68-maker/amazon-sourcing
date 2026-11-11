# Valider l'ingestion grossiste avant tout développement

*Note d'analyse stratégique. Date de contexte : 11 novembre 2026. Statut : exploration, aucun développement autorisé.*

On peut techniquement construire, avec une approche de développement pilotée par l'IA, un SaaS crédible pour vendeurs Amazon. En revanche, **le dossier ne démontre aujourd'hui aucune raison concrète et prouvée pour laquelle un vendeur quitterait ses outils actuels**. La seule piste qui mérite une validation payante est un **copilote d'ingestion de catalogues fournisseurs pour vendeurs grossistes**. Il s'agit de normaliser des fichiers de prix hétérogènes, d'apparier les EAN/UPC et les lots aux ASIN, puis d'expliquer chaque décision d'achat à partir des données du vendeur lui-même. C'est le terrain où l'IA apporte un travail qu'Amazon n'a pas de raison de faire, et où le coût d'inférence se compte en centimes par fichier. Trois faits structurent ce verdict.

1. **L'interface « IA + MCP » ne différencie plus personne.** Amazon donne gratuitement aux vendeurs américains un agent (Seller Assistant) et un plugin MCP officiel. Les grands acteurs installés (Helium 10, Jungle Scout, SmartScout, AMZScout, Seller Assistant app) ont tous livré leur MCP en 2026.
2. **Les fonctions d'analyse de deal sont banalisées.** Calcul de profit, éligibilité, alertes PI et historique Keepa se vendent entre environ 8 et 55 $ par mois.
3. **Les règles d'Amazon contraignent l'architecture.** La politique d'usage acceptable (AUP) de la SP-API interdit de mutualiser les données entre clients (articles 4.4 et 4.6). Elle proscrit aussi les services tiers qui revendent des données extraites des sites d'Amazon (article 4.3), ce qui vise potentiellement Keepa.

La plainte la mieux documentée du marché porte sur la **politique commerciale des acteurs installés** (hausses de prix, fonctions déplacées vers des offres plus chères, renouvellements automatiques), pas sur un manque fonctionnel. Un nouvel entrant ne peut pas en faire un produit, seulement un positionnement. Recommandation : **« go conditionnel » pour une validation terrain à faible coût**, assortie de critères d'arrêt explicites. **« No-go » pour tout développement** tant que trois conditions ne sont pas réunies : une réponse écrite d'Amazon sur l'article 4.3, des conditions Keepa vérifiées, et une démonstration de volonté de payer par de vrais grossistes.

## Méthode, conventions et limites qui bornent ces conclusions

Ce rapport synthétise six dossiers de recherche documentaire constitués le 11 novembre 2026. Ils couvrent la voix des vendeurs, les outils d'arbitrage, les suites et outils grossistes, l'IA et les outils natifs Amazon, la faisabilité des données et API, et la spécialisation européenne. Chaque affirmation importante porte une étiquette de nature :

- **[Fait]** : vérifié sur source primaire ou sur plusieurs sources concordantes ;
- **[Témoignage]** : avis d'utilisateur ou déclaration d'un vendeur ou d'un éditeur sur lui-même ;
- **[Hypothèse]** : inférence de l'analyste ;
- **[Reco]** : recommandation.

Chaque affirmation porte aussi un niveau de fiabilité :

- **haute** : source primaire lue directement ;
- **moyenne** : source secondaire datée, ou source primaire d'une partie intéressée ;
- **faible** : source unique, affilié, concurrent ou source non datée.

Les données sont qualifiées d'**observées** (renvoyées par Amazon ou constatées), de **calculées** (dérivées de façon déterministe) ou d'**estimées** (produites par un modèle).

Les limites sont sérieuses et orientent la lecture.

- **Reddit, les groupes Facebook et YouTube étaient inaccessibles.** Reddit a refusé l'outil de recherche. Seuls des titres de fils, via un agrégateur tiers, ont pu être lus ([redditmaster](https://www.redditmaster.com/reddit-intelligence/helium-10)). Or les communautés d'arbitrage et de vente en gros vivent précisément sur ces canaux et sur Discord. **L'absence de plainte sur SellerAmp, Tactical Arbitrage, BuyBotPro ou Keepa traduit donc un trou dans la collecte, pas une satisfaction.**
- **G2 n'a pas été récupéré** (erreur 403) : seuls des extraits de résultats de recherche ont été vus.
- **Les conditions d'utilisation de l'API Keepa n'ont pas pu être lues** : keepa.com est une application JavaScript, et aucune page statique n'est disponible.
- **L'annulation des frais développeur SP-API repose uniquement sur des sources secondaires.** La page d'annonce originale d'Amazon renvoie une erreur 404 ([developer.amazonservices.com](https://developer.amazonservices.com/spp-announcement)).
- **Les audiences du Chrome Web Store proviennent d'extraits de recherche.** Aucune donnée Similarweb ou Crunchbase n'était disponible.
- **La plupart des comparatifs du secteur sont rédigés par des affiliés ou des concurrents.** Ils sont signalés comme tels.
- **Les comptages de vendeurs par pays européen datent de 2017.**

Aucun prix de vente, nombre de clients ni chiffre d'affaires n'est avancé pour le futur produit. Les seuils figurant dans le plan de validation sont des **règles de décision proposées**, pas des données.

## 1. Cartographie concurrentielle : un marché qui se consolide, monte en gamme et banalise l'IA

### Des tarifs relevés sur les pages officielles, une adoption surtout autodéclarée

Le tableau ci-dessous recense les acteurs demandés et les forces structurantes du marché. Les prix ont été relevés le 11 novembre 2026 sur les pages officielles quand c'était possible ; sinon, la source est indiquée. La colonne « adoption vérifiée » ne retient que des indicateurs semi-indépendants, principalement les utilisateurs du Chrome Web Store. Ces chiffres incluent les installations inactives et les essais : ils surestiment donc le nombre de clients payants.

| Acteur | Clientèle et fonctions clés | Prix constatés (date, fiabilité) | Adoption déclarée | Adoption vérifiée / indicateur | Réputation | Dynamique 2025-2026 |
|---|---|---|---|---|---|---|
| **Helium 10** (Assembly / Pacvue) | Marque propre et marques : mots-clés (Cerebro, Magnet), recherche produit, publicité, profits, « Helium Agent », MCP | Platinum 129 $/mois (99 $ en annuel), Diamond 359 $ (279 $), Enterprise à partir de 1 499 $. MCP inclus en Diamond jusqu'à 1 000 appels, module complémentaire à partir de 50 $ ailleurs. Frais de 2 % sur la dépense publicitaire gérée. [Fait, haute, 2026-11-11] ([pricing](https://www.helium10.com/pricing/)) | Extension « trusted by over 4,000,000 sellers » [Témoignage éditeur, faible] ([Spocket](https://www.spocket.co/blogs/helium-10-review)) | Aucun indicateur indépendant | Trustpilot 2,0/5 (717 avis, dont 48 sur 12 mois) [Fait, haute] ([Trustpilot](https://www.trustpilot.com/review/helium10.com)) ; G2 ≈ 4,2 (184), vu en extrait seulement | Suppression de l'offre à 39 $, outil publicitaire réservé au Diamond, montée en gamme |
| **Jungle Scout** | Catalyst (vendeurs < 1 M$) ; Cobalt (entreprise, intelligence de marché, MCP, six agents lancés le 2026-11-11) | Catalyst Starter ≈ 49 $/mois ou 29 $ en annuel [faible, tiers] ; Cobalt sur devis ; pas d'essai gratuit, garantie de remboursement de 7 jours [Fait, haute] ([pricing](https://www.junglescout.com/pricing/)) | 40 000+ intégrations vendeurs, 600 M+ produits suivis [Témoignage éditeur] ([communiqué 2026-09-10](https://www.einpresswire.com/article/941275851/jungle-scout-launches-ai-solutions-putting-amazon-insights-just-a-question-away)) | Aucun | Trustpilot 4,0 (3 940 avis, mais 9 seulement sur 12 mois) ([Trustpilot](https://www.trustpilot.com/review/junglescout.com)) | IA et MCP réservés à Cobalt sur démonstration ; recentrage sur l'entreprise |
| **SmartScout** | Grossistes, agences, marques : graphe des marques et des vendeurs, historique de Buy Box | Basic 49 $ (29 $), Essentials 119 $ (99 $), Business 299 $ (239 $) ; hausse d'environ 60 à 70 % en septembre 2026 [Fait, haute/moyenne] ([pricing](https://www.smartscout.com/pricing) ; [FrontDeskReview](https://frontdeskreview.com/software/amazon-seller-tools/smartscout/)) | 30 M+ produits, 500 K+ marques, 2 M+ vendeurs [Témoignage éditeur] | Aucun | G2 4,7, cité par l'éditeur lui-même [faible] | MCP « Snapshot » réservé au palier Business ; estimations recoupées avec l'API Keepa |
| **AMZScout** | Recherche produit, vendeurs débutants | AI Toolset 59,99 $/mois ou 399,99 $/an ; MCP autonome 39, 99 ou 199 $ [moyenne/faible, concurrent] ([SellerSonar](https://sellersonar.com/blog/compare/amzscout-review/)) | — | Extension PRO ≈ 100 K utilisateurs, 4,7 (878 notes) | Agrégat 4,7 (854 avis, toutes plateformes) [faible] | MCP inclus en annuel |
| **Keepa** | Couche de données d'historique prix, BSR et offres, utilisée par presque tous | Abonnement de 29 €/mois (contre 19 €) depuis le 2026-02-03, sans maintien de l'ancien tarif ; API à partir de 49 €/mois pour 20 jetons/min [moyenne] ([officialolsons](https://officialolsons.substack.com/p/keepa-just-changed-the-rules-heres) ; [RevenueGeeks](https://revenuegeeks.com/software/keepa/api)) | — | Extension ≈ 4 M utilisateurs, 4,7 [moyenne] ([CWS](https://chromewebstore.google.com/detail/keepa-amazon-price-tracke/neebplgakaahbhdphmkckjjcegoiijjo)) | Pas de signal négatif récent collecté | Hausse de 52,6 % ; conditions de revente inconnues |
| **SellerAmp SAS** | Arbitrage en ligne et en magasin (OA/RA), vente en gros : profit, éligibilité, PI, historiques, Buy Box, panneau UE, TVA | 19,95 / 29,95 / 49,95 $/mois, 14 jours d'essai [Fait, haute] ([pricing](https://www.selleramp.com/pricing/)) | — | ≈ 100 000 utilisateurs, 4,3 (83 notes) [moyenne] ([CWS](https://chromewebstore.google.com/detail/selleramp-sas-amazon-fba/kidmffepbniamfbibhfgdakkggchipjl)) | Trustpilot 3,9 (3 avis) ; l'extension « ne se charge pas souvent » | Stable, maintenu ; leader des extensions d'analyse |
| **Seller Assistant (sellerassistant.app)** | OA, vente en gros, dropshipping : Price List Analyzer, Bulk Restriction Checker, recherche de fournisseurs par IA, repricer, API, MCP | Pro 29,99 $ (24,99 $), Business 79,99 $, Business Plus 189,99 $, Agency à partir de 999,99 $ ; « We do not offer refunds » [Fait, haute] ([pricing](https://sellerassistant.app/pricing)) | 45 k+ utilisateurs de l'extension, 1 M+ ASIN analysés par mois [Témoignage éditeur] | Note CWS 4,9 (261 à 267), nombre d'utilisateurs inconnu | Trustpilot 2,6 (11 avis : facturation, remboursements) | Entrée de gamme passée d'environ 159,99 $/an à 299,99 $/an ; évolution vers une suite |
| **BuyBotPro** | OA et vente en gros : analyse de deal, TVA UE, BuyBotWholesale, « Suspension Safeguard » | US 39,95 / 54,95 / 129,95 $ ; UK 24,95 / 34,95 / 99,95 £ HT [Fait, haute, page incohérente] ([site](https://www.buybotpro.com/)) | — | 4,2 (76 notes), nombre d'utilisateurs inconnu | Trustpilot 2,3 (37, IE) et 3,0 (39, AU) ; 0 avis sur 12 mois | Signaux de stagnation (page /pricing en 404, grilles contradictoires) |
| **RevSeller** | OA/RA aux États-Unis : calculateur, restrictions, alertes | 99,99 $/an ou 19,99 $/mois [Fait, haute] ([site](https://revseller.com/)) | — | Note 4,8, effectif inconnu [faible] | — | .com et .ca seulement ; pas de date sur le site |
| **AZInsight (AsinZen)** | OA/RA, Walmart | 7,95 / 19,95 $ [faible, affilié] ([RevenueGeeks](https://revenuegeeks.com/software/asinzen)) | — | ≈ 30 000+ utilisateurs, 4,9 (123 à 127) [faible/moyenne] | — | — |
| **Tactical Arbitrage (Threecolts)** | Scan de sites marchands et de listes grossistes | Vendu uniquement dans le bundle Seller 365 Reseller à 69 / 129 / 199 $/mois [Fait, haute] ([Threecolts](https://www.threecolts.com/seller-365)) | — | Application web, pas d'indicateur | Trustpilot 3/5 (113) d'après un extrait ([Trustpilot](https://dk.trustpilot.com/review/tacticalarbitrage.com)) contre 2,8 selon un concurrent : conflit non résolu | Absorbé dans un bundle de dix applications ; plafonds d'usage ajoutés en août 2026 |
| **SourceMogul** | OA | Indéterminé : la page tarifs renvoyait une erreur 503 le 2026-11-11 | — | — | — | Fermé, cédé ou relancé : les sources se contredisent ([Arbitrage Hero](https://arbitragehero.com/blog/sourcemogul-alternative/) ; [Trustpilot](https://ca.trustpilot.com/review/sourcemogul.com)) |
| **ProfitPath** | OA et vente en gros orientés UE/UK : scanner jusqu'à 150 000 lignes (CSV, XLSX, PDF), A2A, TVA, GPSR | Wholesale 63 / 79 € HT ; Automation 159 à 503 € HT ; ProfitGo 16 / 24 € [moyenne/faible, éditeur] ([blog](https://profitpath.com/en/blog/best-online-arbitrage-tools)) | 36 000 marques « ungating » [Témoignage éditeur] | — | Avis Trustpilot possiblement sollicité contre SellerAmp [faible] | Se positionne sur le créneau UE |
| **Analyzer.Tools** | Analyse de listes grossistes | Web 49 $, Pro 69 $, pass de 2 jours à 15 $ et de 5 jours à 25 $ ; application Windows à 39 $ en fin de vie [Fait, haute] ([pricing](https://www.analyzer.tools/pricing)) | — | — | — | Réduction des coûts (fin de l'application Windows) |
| **Scan Unlimited** | Analyse de listes grossistes | Gratuit (1 fichier/mois, 10 000 lignes) ; 70 $/mois (60 $ en annuel), 100 000 lignes/fichier ; « 300 000+ produits/heure » [Fait, haute, autodéclaré] ([pricing](https://www.scanunlimited.com/pricing)) | — | — | — | La page mentionne encore MWS, abandonné par Amazon : signe de page non mise à jour |
| **Amazon Seller Assistant + Selling Partner plugin** | Tous les vendeurs américains : agent pour l'inventaire, la santé du compte, la conformité, la publicité, les automatisations de prix et la sélection produit ; MCP hébergé pour Claude et Amazon Quick | **Gratuit** [Fait, haute] ([Amazon, 2025-09-17](https://www.aboutamazon.com/news/innovation-at-amazon/seller-assistant-agentic-ai) ; [Accelerate 2026](https://sellingpartners.aboutamazon.com/accelerate-2026-recap)) | Recommandations suivies « environ 90 % du temps » [Témoignage Amazon, non défini] | Dépôt GitHub de la boîte à outils : 39 étoiles | — | Disponible aux États-Unis ; en Europe, seulement en Allemagne depuis mi-2026 ; plugin en bêta américaine depuis le 2026-09-23 |
| **Nouveaux acteurs MCP** (Nova, DataDoe, Sellerboard, Seller Labs, Atomic One…) | Accès LLM aux données du compte et du marché | Nova 49 $/mois ; Sellerboard ≈ 19 à 79 $ ; plusieurs offres gratuites [faible, comparatif d'éditeur] | 32 serveurs MCP liés à Amazon recensés au 2026-11-04 ([Nova](https://novadata.io/resources/blog/best-mcp-servers-ecommerce-2026)) | Dépôts communautaires à quelques dizaines d'étoiles | — | Saturation rapide |

Un point de vocabulaire évite une confusion fréquente. **« Seller Assistant » désigne deux produits distincts** : l'agent gratuit d'Amazon intégré à Seller Central, et l'application tierce payante sellerassistant.app.

### Ce que révèle la carte : tout le monde monte en gamme, et Keepa tient la donnée

La carte décrit un marché **mature, en consolidation et en montée en gamme**.

- **Rachats [Fait, moyenne/haute].** Pacvue a absorbé Helium 10. SPS Commerce a racheté Carbon6 en février 2025 pour environ 144,9 M$ ([SEC 10-Q](https://www.sec.gov/Archives/edgar/data/0001092699/000109269926000043/spsc-20260331.htm)). Worldeye aurait repris DataHawk puis Viral Launch [faible]. Threecolts a intégré Tactical Arbitrage dans son bundle Seller 365.
- **Hausses de prix synchrones en 2026 [Fait].** Helium 10, SmartScout, Keepa et Seller Assistant app ont tous augmenté leurs tarifs.
- **Offres d'entrée supprimées ou restreintes [Fait].** Helium 10 a supprimé sa formule Starter ; Jungle Scout a limité Catalyst aux vendeurs de moins de 1 M$.

**[Hypothèse, moyenne]** Les acteurs installés extraient davantage de revenu par client d'une base qui se resserre. Cette lecture concorde avec les données de Marketplace Pulse :

- environ **165 000 nouveaux vendeurs** sur Amazon.com en 2025, soit **−44 %** sur un an ;
- **1,65 M de vendeurs actifs** dans le monde fin 2025, contre 2,4 M en 2021 ;
- mais **plus de 100 000 vendeurs au-dessus de 1 M$** de ventes annuelles, contre environ 60 000 auparavant.

Source : [Fait, haute comme estimation, contestée par Amazon] ([Marketplace Pulse](https://marketplacepulse.com/articles/amazon-seller-registrations-hit-decade-low-in-2025) ; [Modern Retail](https://www.modernretail.co/operations/marketplace-briefing-amazons-seller-count-falls-as-revenue-concentrates-among-top-sellers/)).

Les avantages des acteurs installés doivent être nommés sans complaisance.

- **Amazon donne gratuitement, aux États-Unis, ce que beaucoup d'outils vendaient.** Tableau de bord du compte, alertes d'inventaire, explication des problèmes de santé du compte, brouillons de campagnes et automatisations de prix sont désormais inclus. Amazon dispose aussi d'un accès en écriture qu'aucun tiers n'obtient sans enregistrement SP-API [Fait, haute] ([Accelerate 2026](https://sellingpartners.aboutamazon.com/accelerate-2026-recap)).
- **Les acteurs installés possèdent la seule donnée qu'Amazon n'expose pas.** Estimations de ventes, volumes de mots-clés et historiques en font partie. Jungle Scout l'assume dans son communiqué du jour : « General AI tools can't do this work because they don't have Amazon market intelligence » [Témoignage éditeur] ([communiqué 2026-11-11](https://www.einpresswire.com/article/956048717/jungle-scout-launches-jungle-scout-agents-ai-teammates-that-bring-intelligence-to-every-commerce-decision)).
- **Keepa est la couche de données commune.** SellerAmp affiche des graphiques Keepa, Scan Unlimited vend des « Keepa Charts », SmartScout recoupe ses estimations avec l'API Keepa, et Seller Assistant app revendique fusionner Keepa et SP-API ([Seller Assistant API](https://www.sellerassistant.app/blog/seller-assistant-api/) ; [Scan Unlimited](https://www.scanunlimited.com/pricing)).

**[Hypothèse]** Un entrant qui dépend de Keepa achète la même matière première que ses concurrents, au même prix. Celui-ci a augmenté de 52,6 % en 2026, et les droits de revente sont inconnus.

L'image européenne contredit l'intuition d'un vide à combler. Les outils nés au Royaume-Uni gèrent déjà la TVA, la TVA sur les frais Amazon, les programmes EFN et Pan-EU, et comparent les places de marché du « big 5 » : SellerAmp dispose d'un panneau européen et de régimes de TVA, BuyBotPro de bascules EFN et Pan-EU, ProfitPath de la TVA, du GPSR et de l'A2A [Fait, haute] ([SellerAmp KB](https://support.selleramp.com/portal/en/kb/articles/the-european-marketplaces-panel) ; [BuyBotPro help](https://intercom.help/feature-help/en/articles/6988785-which-marketplaces-does-buybotpro-service)). Les outils allemands Sellerboard, SellerLogic et AMALYTIX couvrent l'analytique. **Aucun éditeur français notable n'a été identifié** [Fait, moyenne ; recherche non exhaustive].

## 2. Besoins non satisfaits : la colère vise les pratiques commerciales, pas les fonctions

### Classement des problèmes selon les preuves disponibles

La « fréquence » mesure ici le nombre de sources indépendantes accessibles qui soulèvent le problème. **Ce n'est pas une prévalence dans la population**, et Reddit, Facebook et YouTube en sont absents. Le classement pondère la fréquence observée, la gravité, le coût économique et le signal de volonté de payer.

| Rang | Problème | Fréquence observée | Gravité | Coût pour le vendeur | Volonté de payer | Fiabilité | Nature |
|---|---|---|---|---|---|---|---|
| 1 | **Rapport valeur/prix dégradé** : hausses, offre d'entrée supprimée, fonctions déplacées vers un palier supérieur (Helium 10 surtout, Jungle Scout vers Enterprise) | Élevée : environ 9 avis Helium 10 entre avril et octobre 2026, plus des avis Jungle Scout ([Trustpilot H10](https://www.trustpilot.com/review/www.helium10.com)) | Élevée : provoque des départs | L'utilisateur d'un seul outil passe de 39 à 129 $/mois ; Diamond coûte 359 $ | **Négative en haut de gamme** : les vendeurs partent vers SellerSprite, SoldScope, AdLabs ou AskJeffy plutôt que de payer ; positive pour des outils étroits et bon marché | Haute sur l'existence, moyenne sur l'ampleur | Témoignages + faits tarifaires |
| 2 | **Facturation hostile** : débit après résiliation, renouvellement annuel sans rappel, remboursement refusé | Élevée : environ 8 avis Helium 10 sur 20 en première page, environ 4 chez Jungle Scout ; politique « no refunds » chez Seller Assistant app | Moyenne à élevée : rétrofacturations | Un vendeur à environ 5 000 $/an renouvelé contre son gré | Aucune : c'est un **prérequis**, pas une fonction | Haute | Témoignages |
| 3 | **Risque de plainte PI et de restriction de marque invisible avant l'achat** (OA, RA, vente en gros) | Nombreuses sources d'éditeurs, témoignages indépendants inaccessibles | **Élevée** : menace la santé du compte, stock bloqué | Non quantifié | **Démontrée pour la catégorie** : IP-Alert payant, vérificateur de BuyBotPro | Moyenne | Fait (offre existante) + hypothèse |
| 4 | **Estimations de ventes et de volumes inexactes** | Moyenne : 3 avis Jungle Scout (2025-2026) ; études d'éditeurs contradictoires | **Élevée en cas de lancement raté** (avis du 2026-07-08) | Coût d'une commande ratée, non chiffré | C'est la raison même de l'abonnement | Moyenne | Témoignages + études d'éditeurs |
| 5 | **Mécanique des frais FBA 2025-2026** : frais de placement, frais de stock bas mesurés par FNSKU depuis le 2026-01-15, plafonds de réapprovisionnement depuis avril 2025 | Structurelle (sources de cabinets), aucun témoignage | Moyenne à élevée pour la vente en gros et la marque propre | De 0,14 à 1,90 $ par unité selon les sources pour le placement | Non mesurée | Moyenne | Fait (règles) + hypothèse (besoin) |
| 6 | **Complexité UE** : TVA multi-pays, TVA sur frais, EPR (UIN en France, LUCID en Allemagne), GPSR, DSF en France, frais en hausse aux Pays-Bas, en Suède, en Belgique, en Irlande et en Pologne | Complexité prouvée, **aucune plainte d'utilisateur trouvée** | Moyenne : blocages d'annonces, « Pay on Behalf » | Services payés de 150 à 1 800 €/an (EPR) et de 49 à 119 € par pays et par mois (TVA) | **Démontrée pour des services qui portent la responsabilité**, pas pour du SaaS | Moyenne | Fait (règles) + hypothèse |
| 7 | **IA et MCP réservés aux paliers élevés** | Faible : 1 avis | Moyenne pour les utilisateurs avancés | Oblige à passer à 279 $/mois et plus | Positive, mais **déjà comblée** à 0-49 $ par de nombreux MCP | Moyenne | Témoignage + faits tarifaires |
| 8 | **Historique perdu ou plafonné, pas d'export** | Faible à moyenne : 1 avis + un concurrent | Moyenne : enfermement | Perte d'analyse longitudinale | Hypothèse | Faible à moyenne | Témoignage |
| 9 | **Support faible** (Tactical Arbitrage, Jungle Scout, Helium 10) | Moyenne | Moyenne | Temps perdu | n/a | Moyenne | Témoignages |
| 10 | **Fichiers fournisseurs désordonnés** : colonnes incohérentes, conditionnements, EAN manquants ou invalides, lots à apparier aux ASIN | **Aucun témoignage collecté** | Inconnue | Inconnu | Catégorie payante existante (39 à 190 $/mois) | Faible | **Hypothèse** |

Sources des lignes 3 à 6 : [Seller Assistant IP-Alert](https://www.sellerassistant.app/features/ip-alert/) ; [Trustpilot Jungle Scout](https://www.trustpilot.com/review/junglescout.com) ; [Goat Consulting](https://www.goatconsulting.com/amazon-fulfillment/amazon-fba-fee-changes-for-2026) ; [SPS Commerce](https://www.spscommerce.com/community/articles/amazon-restock-limits-seller-updates-2025-04-25) ; [Amazon FR EPR](https://sell.amazon.fr/conformite-a-la-responsabilite-elargie-des-producteurs?lang=en-GB) ; [AVASK](https://avask.com/blog/best-vat-compliance-software/).

### Pourquoi les plaintes les plus nombreuses ne désignent pas une opportunité

Les deux premiers rangs ne sont pas des opportunités produit, et c'est la principale leçon de cette section. **[Hypothèse, moyenne]** Les vendeurs qui quittent Helium 10 ne réclament pas une meilleure fonction. Ils **éclatent leur pile d'outils** et gardent un outil bon marché par tâche. Un avis du 2026-04-04 le résume : « the tools themselves are fine » ([Trustpilot](https://www.trustpilot.com/review/www.helium10.com)). Un entrant qui gagnerait seulement sur le prix affronterait SellerSprite, SmartScout et les MCP gratuits, sur un terrain sans marge.

Le volume de plaintes reste modeste au regard de la base installée : 48 avis Helium 10 en douze mois. Ce n'est pas une révolte de masse.

**[Fait, moyenne pour la direction]** L'enquête EcomCrew (décembre 2025 à janvier 2026) montre en outre une **désaffection pour les outils tiers dans certaines catégories**, comme le montre la part de vendeurs qui n'utilisent aucun outil tiers :

| Catégorie | Sans outil tiers | Point de comparaison |
|---|---|---|
| Repricing | 60 % | 33 % en 2021 |
| Remboursements | 30 % | 13 % l'année précédente |
| Lancement de produit | 80 % | — |

Davantage de vendeurs ont réduit leurs dépenses logicielles qu'ils ne les ont augmentées ([EcomCrew](https://www.ecomcrew.com/how-amazon-quietly-replaced-your-favorite-seller-tools/)). La taille de l'échantillon n'est pas publiée.

Les rangs 3 à 6 sont des **besoins structurels réels**, mais pour aucun d'eux la volonté de payer un nouvel entrant n'est démontrée. Le rang 10, sur lequel repose la recommandation finale, est **une hypothèse non testée**. La catégorie existe et se paie, mais rien ne prouve que les vendeurs souffrent des limites des outils actuels sur les fichiers désordonnés. C'est précisément ce que la validation doit établir.

## 3. Données et API : la SP-API est gratuite et propre, le reste est juridiquement gris

### Un cadre réglementaire qui dicte l'architecture

**La SP-API est la seule source sanctionnée par Amazon pour les données propres à un vendeur** [Fait, haute] : frais, restrictions de mise en vente, offres et Buy Box, prix attendu pour remporter l'offre mise en avant (FOEP). Une application publique doit obtenir l'autorisation OAuth de chaque vendeur. Elle est limitée à 25 autorisations tant qu'elle n'est pas listée sur l'Appstore, et devient illimitée une fois listée. L'enregistrement exige un site public décrivant le service. Les rôles donnant accès aux données personnelles déclenchent un audit d'architecture et de sécurité ([Register as a Public Developer](https://developer-docs.amazon/sp-api/docs/register-as-a-public-developer.md) ; [Authorization Limits](https://developer-docs.amazon/sp-api/docs/application-authorization-limits.md)). Aucune des fonctions envisagées ici ne requiert ces rôles.

L'AUP pose quatre contraintes de conception, toutes lues dans le texte le 2026-11-11 [Fait, haute] ([AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)) :

- **4.4 et 4.6** interdisent d'agréger ou de divulguer à d'autres utilisateurs les données obtenues via un client. Impossible, donc, de bâtir une base partagée d'historiques à partir des jetons des clients, ou de mettre en cache pour le client B ce qui a été lu pour le client A.
- **3.10** interdit de contourner les quotas en multipliant comptes ou applications.
- **4.3** proscrit d'« use, offer or promote external (non-Amazon) data services that vend information or data retrieved from Amazon's websites ».
- **2.4** impose d'expliciter les calculs, l'usage de modèles d'IA, leur précision et la fraîcheur des données.

S'y ajoute la **Data Protection Policy** : rétention limitée au strict nécessaire, suppression dans les 30 jours sur demande, marquage de l'origine des données ([DPP](https://sellercentral.amazon.com/mws/static/policy?documentType=DPP&locale=en_US)).

L'article 4.3 est le **risque central**. Un développeur rapporte que l'équipe SP-API lui a répondu que « third-party product data cannot be incorporated into an SP-API application ». Le modérateur Amazon du forum a renvoyé vers l'article 4.3 sans l'interpréter [Témoignage, moyenne/faible, fil non daté] ([Seller Forums](https://sellercentral.amazon.com/seller-forums/discussions/t/a7961c30-b453-4dcc-9a31-e1b6312d36b0)). Les acteurs installés (SellerAmp, Seller Assistant app) combinent visiblement Keepa et SP-API.

**[Hypothèse]** L'application de la règle paraît donc incohérente. C'est une tolérance dont un nouvel entrant ne peut pas présumer : il expose son application à une suspension sans l'antériorité ni le poids des acteurs en place.

Le reste du paysage se résume ainsi.

- **SP-API sans frais aujourd'hui, mais sans garantie.** Amazon avait annoncé le 2025-11-03 un abonnement développeur de 1 400 $/an et des paliers d'appels GET (2,5 M inclus, puis 0,40 $ les 1 000 appels). L'annonce a été reportée, puis abandonnée en mai 2026, avec la formule « will not move forward [...] at this time » [Fait, moyenne, sources secondaires uniquement] ([PPC Land](https://ppc.land/amazon-drops-sp-api-fees-after-developer-pushback) ; [Novadata](https://novadata.io/resources/news/amazon-cancels-sp-api-fees-may-2026)).
- **PA-API 5 morte.** Les appels renvoient une erreur 403 « deprecated » [Fait, haute]. Son successeur, la Creators API, est réservé aux affiliés et ne convient pas comme source de données d'un outil vendeur ([Amazon Associates](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation)).
- **Brand Analytics et SQP réservés au vendeur autorisé.** Ces rapports exigent le Brand Registry et livrent un rang de fréquence de recherche, pas un volume ([Analytics Reports](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md)).
- **Scraping légalement risqué.** Il n'est pas pénal en soi aux États-Unis. Mais les Conditions d'utilisation d'Amazon interdisent les outils d'extraction. hiQ a perdu sur le terrain contractuel (jugement d'accord de 500 000 $) ([Proskauer](https://newmedialaw.proskauer.com/2022/12/08/hiq-and-linkedin-reach-proposed-settlement-in-landmark-scraping-case/)). L'arrêt Ryanair de la CJUE permet des interdictions contractuelles ([SCL](https://www.scl.org/3280-the-cjeu-takes-flight-databases-and-air-fares/)). Amazon poursuit activement Perplexity : le 9e circuit a levé l'injonction le 2026-08-04 par une motivation étroite, et l'affaire continue ([Decrypt](https://decrypt.co/374996/perplexity-amazon-ai-agent-lawsuit?amp=1)). Le droit *sui generis* européen sur les bases de données reste une exposition non analysée ici.

### Les quotas de la SP-API limitent la vitesse d'un produit 100 % conforme

Les quotas sont fixés par paire vendeur-application [Fait, haute]. À débit par défaut, on obtient les capacités horaires suivantes par client [**calculé**] ([Usage Plans](https://developer-docs.amazon/sp-api/docs/usage-plans-and-rate-limits.md)) :

| Opération | Débit par défaut | Capacité horaire par client |
|---|---|---|
| getItemOffers | 0,5 requête/s | ≈ 1 800 ASIN |
| getListingsRestrictions | 5 requêtes/s | ≈ 18 000 ASIN |
| getMyFeesEstimates | 0,5 requête/s par lots de 20 | ≈ 36 000 articles |
| FOEP | 0,033 requête/s par lots de 40 | ≈ 4 750 ASIN |

**[Calculé]** Interroger les offres d'un fichier de 10 000 ASIN appariés prend donc environ 5,5 heures par client. **[Hypothèse]** Scan Unlimited revendique « 300 000+ produits/heure ». Ce chiffre autodéclaré n'est atteignable qu'avec d'autres sources que les offres SP-API en temps réel, ou à partir de données partielles. Un produit strictement conforme sera plus lent sur les gros fichiers. Il devra en faire un argument (des données fraîches, propres au vendeur, expliquées) ou trier les lignes avant d'interroger l'API.

Keepa ajoute une contrainte de capacité [**calculé**, moyenne/faible sur le barème]. Le plan API à 49 € donne 20 jetons/min, soit environ 28 800 jetons/jour **partagés entre tous les utilisateurs** si l'éditeur porte la clé. Une requête produit de base coûte environ 1 jeton, davantage avec les offres. L'abonnement Keepa à 29 € n'inclut que 1 jeton/min ([RevenueGeeks](https://revenuegeeks.com/software/keepa/api) ; [officialolsons](https://officialolsons.substack.com/p/keepa-just-changed-the-rules-heres)).

**[Hypothèse]** Une architecture où chaque utilisateur apporte sa propre clé Keepa réduit le risque de revente au regard de Keepa, et peut-être au regard de l'article 4.3. Mais elle impose au vendeur un abonnement API supplémentaire à partir de 49 €/mois, ce qui alourdit la proposition.

### Une architecture conceptuelle à deux silos étanches

**[Reco]** L'architecture la moins risquée sépare strictement deux silos, sans imposer de pile technique.

Le **premier silo** est une application SP-API publique, listée sur l'Appstore et strictement mono-locataire. Chaque client autorise l'application ; aucune donnée lue avec son jeton n'est partagée, mise en cache pour autrui ni réutilisée pour entraîner un modèle commun. Ce silo porte les frais, les restrictions, les offres et la Buy Box, le FOEP et la recherche catalogue par identifiant.

Le **second silo** traite les fichiers fournisseurs que le client téléverse. Ce sont ses propres données, pas celles d'Amazon, et elles peuvent alimenter une **mémoire d'appariement propre au client**. L'historique de marché n'y entre qu'avec la clé Keepa personnelle de l'utilisateur, et seulement après une confirmation écrite d'Amazon Developer Support sur l'article 4.3.

Le LLM n'intervient que sur des tâches de transformation : normalisation des colonnes, détection des conditionnements, appariement assorti d'un score de confiance, explication de la décision. Chaque décision étiquette ses entrées comme observées, calculées ou estimées, ce qui répond aussi à l'article 2.4. Aucune extraction de données de Seller Central par navigateur automatisé n'est prévue.

### Tableau par fonction : source, légalité, coût, fiabilité

| Fonction | Source principale | Type de donnée | Légalité et conformité | Coût d'accès | Fiabilité | Fraîcheur | Droit de commercialiser | Alternative |
|---|---|---|---|---|---|---|---|---|
| Calcul de profit et de frais | SP-API getMyFeesEstimate(s) + prix des offres ([réf.](https://developer-docs.amazon/sp-api/reference/getmyfeesestimateforasin.md)) | **Calculé** par Amazon (« actual costs may vary », taille catalogue) | Conforme, par vendeur autorisé | 0 € aujourd'hui ; frais éventuels si Amazon les réintroduit | Haute, avec un écart possible sur la taille réelle | À la demande | Oui, pour ce vendeur seulement | Grilles tarifaires publiques + calcul propre |
| Restrictions et éligibilité | getListingsRestrictions ([réf.](https://developer-docs.amazon/sp-api/reference/getlistingsrestrictions.md)) | **Observé**, propre au vendeur | Conforme | 0 € | Haute | À la demande, 5 requêtes/s | Oui, pour ce vendeur | Aucune équivalente |
| Offres et Buy Box | getItemOffers, getCompetitiveSummary ([réf.](https://developer-docs.amazon/sp-api/reference/getcompetitivesummary.md)) | **Observé** (instantané) | Conforme ; pas de mutualisation entre clients | 0 € | Haute | Instantané, débit faible | Oui, pour ce vendeur | Historique Keepa |
| Prix attendu pour la Buy Box (FOEP) | getFeaturedOfferExpectedPriceBatch | **Calculé** par Amazon, « not guaranteed » | Conforme | 0 € | Moyenne | Instantané | Oui, pour ce vendeur | — |
| Appariement EAN/UPC → ASIN | searchCatalogItems par identifiant + LLM pour les cas ambigus | Observé (catalogue) + **estimé** (appariement par IA) | Conforme, côté catalogue ; fichiers fournisseurs appartenant au client | 0 € (API) + LLM de l'ordre de 0,10 à 2 $ pour 5 000 lignes (calculé) | À mesurer : c'est **la** question ouverte | À la demande, 2 requêtes/s | Oui | Appariement des outils existants |
| Historique prix, BSR et offres | API Keepa (clé de l'utilisateur) ; scrapers | **Observé** par un tiers (échantillonnage) | **Gris** : AUP 4.3 dans une application SP-API ; conditions Keepa inconnues | 49 € à 459 €+/mois (Keepa) ; scrapers ≈ 0,3 à 1,5 $ les 1 000 enregistrements | Moyenne à haute | Selon l'échantillonnage | **Inconnu** | Renvoi vers Keepa hors de l'application |
| Estimation de ventes | Courbe BSR → ventes + badge « X+ bought » | **Estimé** | AUP 2.4 : divulguer modèle, précision et fraîcheur | Dépend de Keepa ou du scraping | Faible à moyenne (études d'éditeurs contradictoires ; biais d'environ −51 % dans un petit test) ([EcomCrew](https://www.ecomcrew.com/helium10-vs-junglescout/)) | Mensuelle (badge) | Inconnu | Ne pas en faire un argument central |
| Volume de mots-clés | DataForSEO (≈ 132 $ par million de mots-clés) ; Brand Analytics (sa propre marque) | **Estimé** (tiers) ; rang de fréquence (Amazon) | Brand Analytics : Brand Registry obligatoire, pas de mutualisation | Paiement à l'usage ([DataForSEO](https://dataforseo.com/pricing/dataforseo-labs/dataforseo-amazon-api)) | Faible à moyenne | Hebdomadaire, environ 48 h après la clôture (BA) | Conditions DataForSEO non lues | Hors périmètre recommandé |
| Alerte PI et hazmat | Aucune API Amazon pour les plaintes d'autres vendeurs ; hazmat en partie via restrictions et catalogue | **Estimé** ou issu de la communauté | Provenance floue | — | Faible | — | — | Renvoyer vers un outil existant |
| Marge nette UE (TVA, TVA sur frais, DSF, EPR) | Estimation de frais SP-API par place de marché + règles fiscales publiques | **Calculé** | Conforme ; la responsabilité fiscale reste au vendeur | 0 € (API) + maintenance humaine des règles | Moyenne : règles changeantes, sources contradictoires sur les frais UE 2026 | À chaque changement de règle | Oui | SellerAmp, BuyBotPro, ProfitPath |
| Statut de conformité (GPSR, EPR) | Santé du compte via SP-API (preuve GPSR) ([changelog](https://developer-docs.amazon/sp-api/lang-us/changelog/sellers-can-prove-their-gpsr-compliance-on-their-account-health-page)) | Observé | Conforme | 0 € | Moyenne (périmètre de l'endpoint non vérifié) | — | Oui, pour ce vendeur | Prestataires TVA/EPR |

**[Hypothèse, moyenne]** L'économie unitaire est dominée par la donnée tierce, la SP-API étant aujourd'hui gratuite. Sans Keepa, le produit perd l'historique, que tout vendeur en gros consulte. Avec Keepa, il hérite du risque lié à l'article 4.3 et de conditions de revente inconnues.

## 4. Trois concepts crédibles, deux écartés, aucun clone moins cher

La preuve disponible soutient **trois concepts**, pas cinq. Deux idées fréquemment avancées sont examinées puis écartées, parce qu'elles ne résistent pas à la confrontation avec les faits.

### Concept A : copilote d'ingestion de catalogues fournisseurs pour grossistes

**Proposition de valeur [Hypothèse].** Le vendeur en gros reçoit des listes de prix hétérogènes : XLSX aux colonnes variables, PDF, conditionnements (« 6x », « carton de 12 »), EAN absents ou invalides, lots à rapprocher d'ASIN unitaires. L'outil normalise le fichier, apparie chaque ligne à un ASIN avec un score de confiance, puis donne pour chaque ligne une décision d'achat expliquée. Celle-ci s'appuie sur l'éligibilité réelle du vendeur, les frais Amazon et le prix d'achat du fournisseur. L'outil mémorise enfin les appariements validés pour les fichiers suivants du même fournisseur.

**Concurrents [Fait].**

- Seller Assistant app : Price List Analyzer et Bulk Restriction Checker, de 29,99 à 189,99 $/mois.
- ProfitPath : jusqu'à 150 000 lignes en CSV, XLSX ou PDF, 63 à 79 € HT.
- Scan Unlimited : gratuit, puis 70 $.
- Analyzer.Tools : 49 à 69 $ et pass journaliers.
- Tactical Arbitrage : appariement UPC, dans un bundle à partir de 69 $.
- BuyBotWholesale.

Sources : [Seller Assistant](https://sellerassistant.app/pricing) ; [ProfitPath](https://profitpath.com/en/blog/best-online-arbitrage-tools) ; [Scan Unlimited](https://www.scanunlimited.com/pricing) ; [Analyzer.Tools](https://www.analyzer.tools/pricing).

**Différenciation possible [Hypothèse].** Elle viendrait de la tolérance aux entrées désordonnées et de l'appariement des lots, de l'explication de chaque décision, et d'une mémoire d'appariement propre à chaque client, qui crée un coût de sortie légitime. **Aucune source n'établit que les outils actuels échouent sur ces points.** Aucune donnée publique sur leur précision d'appariement n'a été trouvée.

**Faisabilité.** Elle est élevée côté IA : de l'ordre de 0,10 $ (Haiku 5.5) à 2 $ (Sonnet 5.5) pour 5 000 lignes, selon les hypothèses de jetons [**calculé** à partir des [prix publiés par Anthropic](https://platform.claude.com/docs/en/about-claude/pricing)]. Elle est moyenne côté données, à cause des quotas SP-API et de la question Keepa.

**Risques.**

- Catégorie banalisée à prix bas, et vendeurs habitués à des pass à 15 $.
- Imitation rapide par Seller Assistant app, qui dispose déjà d'un MCP et d'une « AI Supplier Finder ».
- Dépendance à Amazon, via l'AUP et l'éventuel retour des frais.
- Segment rendu inobservable par l'inaccessibilité de Reddit et Facebook.

**À valider.** Les fichiers réels sont-ils aussi désordonnés que supposé ? Les outils actuels échouent-ils dessus ? Combien de temps les vendeurs y perdent-ils, et combien paieraient-ils pour le récupérer ?

### Concept B : couche « marge nette et conformité » pour vendeurs francophones et UE multi-places de marché

**Proposition de valeur [Hypothèse].** L'outil calcule une marge nette par ASIN et par place de marché qui intègre ce que les outils d'origine britannique couvrent mal ou pas du tout, d'après la recherche :

- la surtaxe DSF en France ;
- l'éco-contribution EPR et le « Pay on Behalf » d'Amazon ;
- les frais FBA des petites places de marché (Pays-Bas, Suède, Belgique, Irlande, Pologne), en hausse en 2026 alors qu'ils baissaient dans le « big 5 » ([About Amazon EU](https://www.aboutamazon.eu/news/empowering-small-business/update-to-european-referral-and-fulfilment-by-amazon-fees-for-2026)).

Le tout serait présenté avec un statut de conformité (UIN, LUCID, GPSR) intégré à la décision d'approvisionnement, et une interface en français.

**Concurrents [Fait].** SellerAmp, BuyBotPro, ProfitPath et Seller Assistant app gèrent déjà la TVA et le Pan-EU. Sellerboard et SellerLogic couvrent l'analytique. Les prestataires TVA/EPR (hellotax, Lovat, Taxually, AVASK) portent la responsabilité réglementaire ([AVASK](https://avask.com/blog/best-vat-compliance-software/)).

**Différenciation [Hypothèse, faible].** Langue, spécificités françaises, petites places de marché. **Aucune plainte d'utilisateur ne documente ces manques**, et aucune preuve ne montre que la langue soit un critère d'achat. Selon Marketplace Pulse (2017), 56 à 59 % des vendeurs actifs en France vendent aussi au Royaume-Uni ou en Allemagne ([Marketplace Pulse](https://www.marketplacepulse.com/articles/in-amazon-europe-most-sellers-sell-in-more-than-one-marketplace)), donc dans des interfaces étrangères.

**Faisabilité.** Techniquement simple, mais **coûteuse à maintenir** : les règles changent, et les sources sur les frais UE 2026 se contredisent ([Shoplazza](https://www.shoplazza.com/blog/amazon-fba-fee-increase-us-eu)). Une erreur engage la crédibilité de l'outil.

**Risques.** La base adressable est étroite : 55 % des meilleurs vendeurs d'Amazon.fr sont basés en Chine ([Marketplace Pulse](https://marketplacepulse.com/articles/sellers-from-china-are-getting-better)). Les acteurs installés peuvent ajouter la DSF en quelques semaines. Enfin, la volonté de payer pour la conformité va à des services qui portent la responsabilité, pas à du SaaS.

**À valider.** Les vendeurs français se trompent-ils réellement de marge aujourd'hui ? Paieraient-ils pour une couche qui ne dépose aucune déclaration ?

### Concept C : vigie des frais FBA et du réapprovisionnement par SKU pour vendeurs UE

**Proposition de valeur [Hypothèse].** À partir des seules données SP-API du vendeur, l'outil anticiperait l'exposition aux frais de stock bas (mesurés par FNSKU depuis le 2026-01-15), aux frais de placement et aux plafonds de réapprovisionnement. Il proposerait des brouillons d'envoi à approuver. Il exploiterait le **retard de déploiement européen** de l'agent d'Amazon : en Europe, celui-ci n'existe qu'en Allemagne depuis mi-2026 ([AMALYTIX](https://www.amalytix.com/en/knowledge/ai/amazon-ai-tools/) ; [valuezon](https://valuezon.de/en/news/amazon-seller-assistant-germany/)).

**Concurrents [Fait].** Amazon Seller Assistant signale déjà les produits à rotation lente et arbitre entre FBA et AWD aux États-Unis, gratuitement ([Amazon](https://www.aboutamazon.com/news/innovation-at-amazon/seller-assistant-agentic-ai)). Sellerboard et l'inventaire Helium 10 (Diamond) couvrent aussi ce terrain.

**Différenciation [Hypothèse].** Elle est temporelle (couverture UE) et non structurelle.

**Faisabilité.** Élevée : la donnée est sanctionnée et propre au vendeur.

**Risque principal.** **La fenêtre se ferme au rythme du déploiement d'Amazon.** L'hypothèse d'un décalage de 6 à 18 mois repose sur le calendrier 2024-2026 et n'a rien de garanti. C'est un concept d'opportunité temporaire, pas une entreprise durable.

### Idées écartées et pourquoi

**« Accès MCP abordable aux données de marché pour les petits vendeurs exclus du Diamond. »** L'idée est séduisante, car Helium 10 réserve son MCP au Diamond et Jungle Scout à Cobalt. Mais au moins 32 serveurs MCP liés à Amazon existent déjà : Nova à 49 $, Sellerboard, l'offre gratuite de Seller Labs, Atomic One gratuit, AMZScout à partir de 39 $, et le plugin gratuit d'Amazon aux États-Unis ([Nova](https://novadata.io/resources/blog/best-mcp-servers-ecommerce-2026) ; [SellerSonar](https://sellersonar.com/blog/compare/amzscout-review/)). Surtout, la valeur réside dans la donnée de marché propriétaire, que l'entrant ne possède pas. **C'est un clone moins cher sans actif. Écarté.**

**« Prédiction du risque de plainte PI. »** C'est le besoin le plus grave du segment arbitrage, et la volonté de payer est démontrée par l'existence d'IP-Alert. Mais **Amazon ne publie aucune liste des marques plaignantes**. Aucune API n'expose les plaintes visant d'autres vendeurs. Les outils existants reposent sur des listes ou sur la contribution communautaire ([vovaeven](https://vovaeven.com/blog/how-to-avoid-amazon-products-with-intellectual-property-complaints)). Un nouvel entrant partirait sans données. Un faux négatif peut coûter un compte au client et engager la réputation de l'éditeur. **Écarté comme produit autonome**, mais à conserver comme module alimenté par les signalements des clients du concept A, sous réserve des articles 4.4 et 4.6 de l'AUP.

## 5. Classement argumenté : le concept A devance les autres, sans marge confortable

### Grille de notation

Chaque critère est noté de 1 à 5 ; **5 est toujours le plus favorable au projet**. Ainsi, 5 en « intensité concurrentielle » signifie une concurrence faible, et 5 en « difficulté de commercialisation » une commercialisation facile. Le total n'est pas pondéré. **[Reco]** La demande démontrée et l'accessibilité des données doivent être lues comme éliminatoires : une note de 1 sur l'une d'elles disqualifie le concept, quel que soit son total.

| Critère | A. Ingestion grossiste | B. Marge et conformité UE/FR | C. Vigie frais UE | Écarté : MCP abordable | Écarté : prédiction PI |
|---|---|---|---|---|---|
| Demande démontrée | 3 | 2 | 2 | 2 | 3 |
| Intensité concurrentielle | 2 | 2 | 2 | 1 | 3 |
| Accessibilité des données | 3 | 3 | 4 | 2 | 1 |
| Faisabilité technique | 4 | 3 | 4 | 4 | 2 |
| Coûts d'exploitation | 4 | 3 | 4 | 2 | 3 |
| Potentiel de monétisation | 3 | 2 | 2 | 2 | 3 |
| Difficulté de commercialisation | 2 | 3 | 2 | 2 | 3 |
| Durabilité de l'avantage | 2 | 2 | 1 | 1 | 2 |
| **Total (sur 40)** | **23** | **20** | **21** | **16** | **20 (éliminé : données = 1)** |

### Justification des notes

| Critère | A | B | C | MCP abordable | Prédiction PI |
|---|---|---|---|---|---|
| Demande démontrée | Catégorie payante et fournie (6 éditeurs ou plus, 39 à 190 $/mois), mais aucune preuve que l'amélioration soit attendue | Complexité réglementaire prouvée, aucune plainte d'utilisateur | Règles de frais nouvelles prouvées, aucun témoignage | Un seul avis de départ pour cause de plafond MCP | Gravité élevée, outils payants existants, témoignages inaccessibles |
| Intensité concurrentielle | Seller Assistant app, ProfitPath, Scan Unlimited, Analyzer.Tools, Tactical Arbitrage, BuyBotWholesale | Outils UK compétents en TVA, outils allemands, prestataires | Amazon gratuit (US, DE), Sellerboard, Helium 10 | 32 MCP, plusieurs gratuits, plugin Amazon | Quelques outils spécialisés, catégorie moins encombrée |
| Accessibilité des données | SP-API propre ; historique bloqué par l'article 4.3 et les conditions Keepa | SP-API + règles publiques, mais sources contradictoires | Données propres au vendeur, sanctionnées | Exige une donnée de marché propriétaire ou sous licence | Aucune source officielle |
| Faisabilité technique | Le LLM excelle en normalisation ; quotas SP-API lents (≈ 5,5 h pour 10 000 offres) | Moteur de règles multi-pays fragile | CRUD sur rapports SP-API | Simple techniquement | Modèle sans vérité terrain |
| Coûts d'exploitation | LLM en centimes à dollars par fichier ; SP-API à 0 € | Veille réglementaire humaine continue | Faibles | Coût de licence de données | Modération des signalements |
| Monétisation | Grossistes plus gros et en croissance (100 000+ vendeurs au-dessus de 1 M$), mais habitués à 39-190 $ | Base francophone étroite, forte part de vendeurs basés en Chine | Valeur bornée par le gratuit d'Amazon | Plafond de prix bas (0 à 49 $) | Valeur d'assurance perçue |
| Commercialisation | Communautés Discord et Facebook, formateurs : canaux non observés | Écosystème de formateurs français identifié ([Torregrossa](https://josephtorregrossa.com/blogs/amazon/online-arbitrage-amazon-france-astuces-pour-debutants-2026)) | Nécessite de convaincre avant l'arrivée d'Amazon | Marché saturé de messages | Message simple, besoin compris |
| Durabilité | Seule la mémoire d'appariement est un actif ; fonction copiable | Copiable en quelques semaines par les acteurs installés | Fenêtre fermée par Amazon | Nulle | Possible effet de réseau, mais risque juridique |

**[Hypothèse]** L'écart entre A (23) et les autres (20-21) est faible et repose surtout sur la faisabilité et les coûts, pas sur la demande. **A n'est pas une opportunité démontrée : c'est la meilleure hypothèse à tester.**

## 6. Économie des concepts A et B : hypothèses explicites, aucun prix inventé

Seuls les éléments sourcés ou calculés sont chiffrés. Tout le reste est marqué comme inconnu. Aucun prix de vente ni volume de clients n'est proposé : ils doivent sortir des tests de la section 7.

| Dimension | Concept A : ingestion grossiste | Concept B : marge et conformité UE/FR |
|---|---|---|
| Cible | Vendeurs en gros sur Amazon (US/UK/UE) qui reçoivent des listes fournisseurs. Le segment au-dessus de 1 M$ croît selon Marketplace Pulse. Taille du sous-segment grossiste : **inconnue** | Vendeurs francophones multi-places de marché UE. Comptage par pays : **2017 seulement** (France : 27 672 vendeurs actifs) ([MP](https://www.marketplacepulse.com/articles/in-amazon-europe-most-sellers-sell-in-more-than-one-marketplace)) |
| Fréquence d'usage | [Hypothèse] À chaque liste fournisseur reçue : fréquence **inconnue**, à mesurer en entretien | [Hypothèse] À chaque décision d'approvisionnement et à chaque changement de règle |
| Valeur créée | [Hypothèse] Temps de préparation économisé + achats erronés évités (mauvais lot, mauvais ASIN). **Non chiffré** | [Hypothèse] Marge mal estimée évitée ; pénalités EPR et GPSR évitées. **Non chiffré** |
| Dépense actuelle de référence | [Fait] Analyseurs grossistes : 39 à 190 $/mois ; Keepa 29 €/mois ; pass à 15-25 $ | [Fait] Outils de sourcing 20 à 130 $/mois ; services TVA 49 à 119 € par pays et par mois ; EPR 150 à 1 800 €/an ; représentant UE ≈ 400 € ([AVASK](https://avask.com/blog/best-vat-compliance-software/) ; [EaseCert](https://easecert.com/fr/pages/affordable-eu-responsible-person-amazon-etsy-gpsr-compliance)) |
| Coûts de données | SP-API 0 € aujourd'hui. Risque latent : 1 400 $/an + 0,40 $ les 1 000 GET au-delà de 2,5 M/mois si Amazon réactive ses frais. **[Calculé]** 100 clients à 50 000 lectures d'offres par jour représenteraient ≈ 150 M de GET/mois, soit le palier à 10 000 $/mois ([PPC Land](https://ppc.land/amazon-drops-sp-api-fees-after-developer-pushback)). Keepa : à la charge de l'utilisateur (≥ 49 €/mois) ou de l'éditeur (49 à 879 €+/mois) | SP-API 0 € ; grilles tarifaires publiques ; pas de dépendance à Keepa obligatoire |
| Coût LLM | **[Calculé]** ≈ 0,10 à 2 $ pour 5 000 lignes, ≈ 1 $ avec la Batch API sur Sonnet 5.5 ; session de questions-réponses ≈ 0,50 $ ([Anthropic](https://platform.claude.com/docs/en/about-claude/pricing)) | Marginal (explications) |
| Infrastructure | Non chiffrée dans les sources. [Hypothèse] Stockage des fichiers et files d'attente de requêtes SP-API à débit limité par client | Non chiffrée |
| Support | [Fait] Le support faible fait partir les clients (Tactical Arbitrage, Jungle Scout). [Hypothèse] Appariements contestés = support à forte intensité au départ | [Hypothèse] Questions fiscales hors du champ d'un SaaS : risque de responsabilité implicite |
| Dépendance Amazon | Élevée : AUP 4.3/4.4/4.6, éventuel retour des frais, révocation de l'application | Élevée : règles UE et grilles de frais changeantes |
| Dépendance Keepa | Moyenne à élevée si l'historique est inclus : conditions inconnues, hausse de 52,6 % en 2026 sans maintien de l'ancien tarif | Faible |
| Barrières à l'entrée | Enregistrement développeur public, listing Appstore, site public ; mesure de la précision d'appariement | Connaissance réglementaire multi-pays |
| Copiabilité | Élevée pour la fonction ; modérée pour la mémoire d'appariement propre à chaque client | Élevée |

**[Hypothèse, moyenne]** Dans les deux cas, le coût marginal d'inférence est négligeable devant n'importe quel prix plausible. **L'IA n'est ni une barrière de coût ni un fossé défensif.** Le vrai coût est humain : qualité de l'appariement et support pour A, veille réglementaire pour B. Le vrai risque est contractuel : Amazon et Keepa.

## 7. Recommandation finale : « go conditionnel » pour valider, « no-go » pour construire

**[Reco] Décision : go conditionnel pour une validation du concept A, d'une durée et d'un budget fixés par le client ; no-go pour tout développement produit à ce stade.** Le concept B peut servir de variante de segmentation dans les mêmes tests (vendeurs en gros UE/francophones contre US/UK), pas de projet distinct. Le concept C est à reconsidérer seulement si Amazon annonce un report explicite du déploiement de son agent dans l'UE.

**Première fonctionnalité à prouver.** Il s'agit de *l'appariement fiable d'un fichier fournisseur réel et désordonné*, mesuré sur les fichiers des vendeurs eux-mêmes. Le livrable compte trois éléments : le taux de lignes correctement appariées à l'ASIN, y compris les lots ; le taux de lignes signalées comme incertaines ; et la comparaison ligne à ligne avec la sortie de l'outil qu'ils utilisent déjà. L'explication de la décision d'achat vient ensuite. Si l'appariement ne bat pas nettement l'existant, le concept n'a pas de raison d'être.

**Obstacles qui peuvent rendre le projet non viable.**

1. **Amazon confirme par écrit que l'article 4.3 interdit la combinaison avec Keepa.** Le produit perd alors l'historique ou doit l'externaliser.
2. **Les conditions Keepa interdisent l'usage par un tiers, même avec la clé de l'utilisateur.**
3. **Les outils existants apparient déjà correctement les fichiers réels.** La différenciation disparaît.
4. **Les vendeurs refusent de payer au-delà des prix de la catégorie (39 à 190 $) ou du pass journalier.** L'économie ne couvre plus le support.
5. **Amazon réintroduit ses frais SP-API.**
6. **Seller Assistant app ou ProfitPath ajoutent un appariement par LLM en quelques semaines.** C'est probable : Seller Assistant app a déjà un MCP et une recherche de fournisseurs par IA.

**Preuves manquantes à obtenir avant toute décision de construction.**

- Témoignages de vendeurs en gros sur Reddit, Facebook et Discord.
- Précision mesurée des appariements actuels.
- Fréquence et volume des fichiers reçus.
- Dépense réelle par vendeur, et non les prix catalogue.
- Conditions Keepa.
- Position écrite d'Amazon sur l'article 4.3.
- Formats réels des catalogues grossistes européens (non trouvés).
- Notes G2 complètes.
- Nombre de vendeurs par pays UE en 2025-2026.

### Méthode de validation avec de vrais vendeurs

Les seuils ci-dessous sont des **règles de décision proposées**, à ajuster par le client avant de lancer chaque étape. Ce ne sont pas des données.

| Étape | Méthode | Recrutement | Ce qui est mesuré | Critère d'arrêt proposé |
|---|---|---|---|---|
| 0. Levée des verrous juridiques (en parallèle) | Demande écrite à Amazon Developer Support sur l'article 4.3 (architecture à deux silos, clé Keepa de l'utilisateur) ; demande écrite à Keepa sur l'usage par un tiers ; avis d'un juriste sur le droit *sui generis* UE | — | Réponses écrites | Interdiction explicite → retirer l'historique du périmètre ou arrêter |
| 1. Entretiens de découverte | Entretiens semi-directifs sur le dernier fichier fournisseur réellement traité (pas d'opinion sur un produit hypothétique) | Grossistes recrutés via des formateurs (dont l'écosystème français identifié), groupes Facebook et Discord, annonces ciblées ; mélange UE et US/UK | Temps passé par fichier, erreurs déjà subies, outils et dépense réelle (relevé bancaire ou facture), fréquence des fichiers | Si la majorité déclare que l'outil actuel suffit et ne cite aucune erreur coûteuse → arrêt |
| 2. MVP conciergerie | L'équipe traite à la main, assistée d'un LLM, les vrais fichiers de quelques vendeurs, et rend un fichier apparié et expliqué ; comparaison ligne à ligne avec leur outil | Volontaires de l'étape 1 | Précision d'appariement contre l'outil actuel, lignes corrigées par le vendeur, décisions d'achat modifiées | Pas de gain net de précision ou de temps reconnu par le vendeur → arrêt |
| 3. Test de fumée tarifaire | Page d'atterrissage décrivant le service, avec plusieurs formules de prix en test A/B (abonnement contre paiement au fichier, pour coller à l'habitude du pass journalier) ; aucun produit promis à une date ferme | Trafic issu des mêmes communautés + publicité ciblée « wholesale Amazon » | Taux d'inscription par formule, clics sur « payer » | Signal d'intention faible sur toutes les formules → arrêt ou repositionnement |
| 4. Prévente | Engagement payé : pilote payant de traitement de fichiers, ou acompte remboursable pour un accès anticipé | Participants des étapes 2 et 3 | Nombre de paiements réels, montant accepté, renouvellement du pilote | Aucun paiement réel → no-go définitif ; paiements récurrents → réexamen d'une décision de développement |

**[Reco]** Deux principes protègent l'intégrité du test. D'abord, ne jamais présenter le produit comme existant : le test de fumée doit dire « en préparation ». Ensuite, se distinguer dès le départ sur la loyauté commerciale (résiliation en un clic, rappel avant renouvellement, remboursement au prorata). Ce sont les griefs n° 1 et n° 2 du marché, et ils ne coûtent rien à respecter.

## Conclusion

La question initiale, « que pourrait-on construire de mieux ? », se révèle moins décisive que « qu'est-ce qui reste hors de portée d'Amazon et des données de Keepa ? ». L'IA a déplacé la valeur. L'interface conversationnelle est devenue gratuite ou banale. La donnée de marché reste chez les acteurs installés et chez Keepa. Ce qui reste ouvert, ce sont les **données que le vendeur détient lui-même et qu'Amazon n'a aucun intérêt à traiter** : ses catalogues fournisseurs, ses appariements, ses décisions. C'est aussi le seul endroit où un nouvel entrant peut accumuler un actif propre sans enfreindre les articles 4.4 et 4.6 de l'AUP.

L'enseignement le moins intuitif tient au mécontentement. Le mécontentement massif visible contre Helium 10 et Jungle Scout ne constitue pas un marché à prendre : il signale une **fragmentation des achats** vers des outils étroits et bon marché, sur un marché de vendeurs qui se contracte par le bas et se concentre par le haut. Un nouvel acteur n'a de chance qu'en résolvant une tâche précise et mesurable mieux que l'existant, et en le prouvant sur les fichiers des clients avant d'écrire du code. Si la validation échoue, ce sera une économie, pas un échec.
