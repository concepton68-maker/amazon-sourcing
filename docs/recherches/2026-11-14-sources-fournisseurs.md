# Sources fournisseurs automatisables pour la revente Amazon (14/11/2026)

Objet : trouver des fournisseurs (grossistes B2B, distributeurs, dropshipping) qui offrent une **API ou un flux** (CSV/XML) de prix, utilisables pour simuler « achat fournisseur → revente Amazon » (vendeur tiers FBA, France, Europe d'abord).

Méthode : pages officielles seulement (site de l'éditeur, documentation développeur, conditions d'utilisation, centre d'aide).
- **VÉRIFIÉ** : page officielle lue, avec l'URL et une courte citation.
- **VÉRIFIÉ (extrait)** : texte officiel vu dans l'extrait du moteur de recherche, mais la page complète n'a pas pu être chargée (protection anti-robot Cloudflare ou 403 sur faire.com, bigbuy.eu, qogita.com, developers.qogita.com, dropshipping.vidaxl.com). À relire dans un navigateur avant de s'en servir comme règle.
- **NON VÉRIFIÉ** : pas de page officielle trouvée ou lisible.

Rien ici ne remplace la lecture des conditions au moment de signer : elles changent.

---

## 1. Tableau classé

| # | Source | API / flux | Accès | Données | Revente Amazon autorisée | Intérêt pour nous |
|---|---|---|---|---|---|---|
| 1 | **Qogita** (NL, hygiène-beauté, parfums, Europe) | API acheteur (doc developers.qogita.com, « en développement, sans versionnage ») + export Excel du catalogue | Compte acheteur pro (TVA UE vérifiée VIES) ; coût de l'API non trouvé | GTIN, prix par offre, stock, MOV (minimum de commande), prix par paliers, historique 90 j | **Oui, visée explicitement** : factures « marketplace » et lettre de chaîne d'approvisionnement pour Amazon ; filtre des fournisseurs qui acceptent de les fournir | **Très fort** : clé GTIN = appariement direct à l'ASIN ; seul acteur trouvé qui vise ouvertement le revendeur Amazon en Europe |
| 2 | **BigBuy** (ES, généraliste, UE/EEE) | API REST JSON + bac à sable ; flux CSV/XML ; connecteur Amazon (MIP) | Pack payant : API et CSV/XML avec le pack « Ecommerce » ou supérieur ; connecteurs marketplace avec le pack « Marketplace » ; le pack B2B n'a pas d'API. Tarifs actuels non affichés | SKU, EAN par variante, prix, stock temps réel, commandes | **Oui en principe** (offre « Dropshipping on Amazon »), **mais** le distributeur doit respecter les restrictions de marque et la distribution sélective (CGV §16) ; BigBuy « n'est pas distributeur officiel des marques » | **Fort** pour la mécanique (API propre, EAN) ; preuve d'autorisation de marque faible pour le dégating |
| 3 | **vidaXL dropshipping** (NL, maison-jardin-meuble, marque propre, Europe) | Flux CSV/XML horaires + API (produit, stock, commande) | Abonnement 30 €/mois par pays de livraison ; accès API sur demande à l'équipe B2B | SKU, prix (mis à jour quotidiennement), stock (horaire), commandes | **Oui** d'après la FAQ (« eBay et Amazon ») — FAQ ancienne | **Moyen** : produits de marque vidaXL, déjà vendus par vidaXL sur Amazon (concurrence directe sur la même fiche) ; utile pour le modèle, pas pour le grossiste multi-marques |
| 4 | **Brandsdistribution** (IT, mode et accessoires de marque) | API REST (authentification Basic, clé API) + bac à sable ; export CSV/XML/XLS | Abonnement dropshipping 99 € HT/mois ou 990 € HT/an ; clé API par le gestionnaire de compte | Prix (EUR, prix public conseillé), stock par modèle (mise à jour toutes les 3 min), code-barres du modèle | **Possible techniquement** (plugins tiers vers Amazon cités) ; **aucune autorisation ou interdiction écrite trouvée** ; mode = catégorie souvent restreinte par marque | **Moyen** : API propre, mais mode de marque = risque de plainte d'authenticité et de restriction de marque |
| 5 | **Alibaba.com** (CN, international, tous produits) | Open API (OAuth, app key) orientée **vendeurs / éditeurs de logiciels (ISV)** ; quelques points d'accès côté acheteur (calcul de fret, commande) sur la plateforme mondiale | Inscription développeur ; accès acheteur au catalogue non documenté clairement | Produit, prix, SKU, fret (côté vendeur) | Rien d'interdit par Alibaba, mais authenticité : produits génériques / marque propre surtout | **Faible pour l'automatisation des prix** (pas d'API catalogue acheteur claire ; collecte automatisée interdite sans accord écrit) ; utile en recherche manuelle pour la marque propre |
| 6 | **Ankorstore** (FR/UE, marques indépendantes, déco, épicerie, beauté) | API **pour les marques** seulement | — | — | **Non** : revendeurs « seulement sur Amazon ou eBay » non éligibles ; dropshipping interdit ; la marque fixe ses conditions de revente | **Nul** pour notre usage ; collecte automatisée interdite |
| 7 | **Faire** (US/UE, marques indépendantes) | API pour marques et partenaires ; **pas de clé API pour les détaillants** | — | — | **Non** : « Prohibited sites include Amazon, eBay, Etsy, and Poshmark » | **Nul** |
| 8 | **Creoate** (UK/UE, marques indépendantes) | Aucune API acheteur trouvée | — | — | **Non** (CGU : interdit d'honorer des commandes sur Amazon pour des articles achetés via Creoate) | **Nul** |
| 9 | **Global Sources** (HK, fabricants Asie) | Aucune API / flux acheteur trouvé | Gratuit (demande de devis) | Prix et MOQ affichés à la main | Pas de clause trouvée | **Faible** : copie / stockage du contenu interdits sans accord écrit |
| 10 | **Made-in-China.com** (CN, fabricants) | Aucune API acheteur trouvée | Gratuit | Prix, MOQ à la main | Pas de clause trouvée | **Faible** : « copier, reproduire, … saisir (grasp) » le contenu interdit sans accord écrit |
| 11 | **1688** (CN, marché intérieur chinois) | Plateforme ouverte (open.1688.com) non lisible ; accès étranger via agents d'achat | — | — | — | **Faible** : NON VÉRIFIÉ, paiement et logistique chinois |
| 12 | **B2B Griffati** (IT, mode) | Applications Shopify / PrestaShop (Sync2Fashion) ; aucune API publique trouvée | — | — | — | **Faible** : NON VÉRIFIÉ |
| 13 | **Wholesale Central** (US, annuaire) | Annuaire seulement, pas d'API | Gratuit pour les acheteurs | Liens vers les sites des grossistes | — | **Faible** : US, annuaire ; aide à trouver des contacts, pas à tirer des prix |
| 14 | **Syncee** (HU, agrégateur dropshipping) | Gestion de flux côté fournisseur (CSV, XML, JSON) ; canaux Shopify, WooCommerce… | Abonnement | — | Amazon non cité | **Faible** : pas de canal Amazon trouvé |

**Lecture** : pour notre usage (prix automatiques + revente Amazon légitime), seuls **Qogita** et **BigBuy** cochent les deux cases, puis vidaXL et Brandsdistribution avec des réserves. Les places de marché « marques indépendantes » (Ankorstore, Faire, Creoate) **interdisent** la revente sur Amazon. Les plateformes asiatiques n'ouvrent pas leur catalogue par API à l'acheteur et interdisent la collecte automatisée.

Conséquence pour l'outil : le cœur doit être un **import de tarif fournisseur** (CSV/Excel avec EAN/GTIN, prix, MOQ, stock) + des connecteurs API pour les sources qui en ont (Qogita, BigBuy). C'est la voie que toutes les sources autorisent : le grossiste envoie son tarif à son client.

---

## 2. Détail par source

### 2.1 Qogita
- Ce que c'est : place de marché de gros européenne, santé-beauté. VÉRIFIÉ (extrait) — https://www.qogita.com/legal/terms-buyer/ (titre : « Europe's wholesale marketplace for health & beauty retailers »).
- Comptes : acheteurs UE avec TVA vérifiable. VÉRIFIÉ (extrait) — https://help.qogita.com/do-i-need-a-vat-and-eori-number : « You must provide a valid VAT number ». Usage réservé aux non-consommateurs. VÉRIFIÉ (extrait) — https://www.qogita.com/legal/terms-buyer/ : « Use of the platform is limited only to parties that do not qualify as a "consumer" ».
- API : existe. VÉRIFIÉ — https://help.qogita.com/developer-hub : « Learn how to connect to our API ». Statut : en développement, sans versionnage, peut changer sans préavis ; contact api@qogita.com. VÉRIFIÉ (extrait) — https://developers.qogita.com.
- Données : VÉRIFIÉ (extrait) — https://help.qogita.com/product-information : « Every product GTIN in our database has multiple offers … Each offer carries its own unique unit price, stock level and MOV ». Prix par paliers aussi via l'API : https://help.qogita.com/are-there-discounts-for-large-orders (« … when you download the catalog or use our API »). Export Excel (noms, GTIN, prix, disponibilité) : https://help.qogita.com/download-our-catalog-in-excel.
- Revente Amazon : VÉRIFIÉ — https://help.qogita.com/proving-chain-of-supply : « We offer proof of supply chain documentation for any marketplace resellers who need it » ; « Qogita invoice: Contains all the information Amazon needs for authorization » ; filtre : « purchase only from suppliers who are happy to share proof of supply documentation with Amazon ». Pas de lettre d'authenticité : VÉRIFIÉ (extrait) — https://help.qogita.com/can-qogita-help-me-challenge-an-authenticity-claim-from-amazon.
- Accès automatisé / stockage des prix : l'API est l'accès prévu. Clause anti-robot des CGU : NON VÉRIFIÉ (CGU non lues en entier).
- Coût de l'API, limites d'appels, frais de port : NON VÉRIFIÉ.

### 2.2 BigBuy
- Ce que c'est : grossiste-dropshipper espagnol, revendeur dans l'EEE. VÉRIFIÉ (extrait) — https://www.bigbuy.eu/en/terms-and-general-conditions.html (§16) : « BigBuy is not an official distributor of the brands and only acts as a reseller within the sales channel in the European Economic Area ».
- API : REST JSON, bac à sable. VÉRIFIÉ (extrait) — https://www.bigbuy.eu/en/api_bigbuy.html. Accès : VÉRIFIÉ (extrait) — https://www.bigbuy.eu/academy/en/?p=620 : « to obtain these accesses you need to have a contract for BigBuy Ecommerce or a higher pack ». Packs : https://www.bigbuy.eu/en/wholesaler-packs.html (pack B2B sans API ni CSV/XML ; pack Marketplace = Ecommerce + connecteurs). Tarifs actuels : NON VÉRIFIÉ (page sans prix ; anciens chiffres de blog non retenus).
- Données : VÉRIFIÉ (extrait) — guide API https://www.bigbuy.eu/public/doc/Guia_API_BigBuy_EN.pdf : « each possible variation of a product has its own SKU, EAN and specific price » ; stock en temps réel (page API).
- Revente Amazon : offre dédiée https://www.bigbuy.eu/en/dropshipping-amazon.html et connecteur https://www.bigbuy.eu/academy/en/synchronise-amazon-multi-channel-integration-platform/ — VÉRIFIÉ (extrait). Restrictions de marque à la charge du revendeur (CGV §16.9-16.11) — VÉRIFIÉ (extrait).
- Authenticité : la FAQ Amazon affirme « All BigBuy products are from top brands with sales and distribution authorisation granted by the brand » — VÉRIFIÉ (extrait), https://www.bigbuy.eu/academy/en/amazon-faq-2/ ; contradiction apparente avec le §16 (« pas distributeur officiel »). Factures acceptées par Amazon : NON VÉRIFIÉ.
- Clause sur l'accès automatisé hors API : NON VÉRIFIÉ.

### 2.3 vidaXL dropshipping
- Flux et API : VÉRIFIÉ (extrait) — https://dropshipping.vidaxl.com/announcement/get-real-time-stock-with-api/ et https://dropshipping.vidaxl.com/announcement/get-product-through-api/ (accès API demandé à l'équipe B2B, jeton).
- Prix : 30 €/mois, un accès par pays de livraison. VÉRIFIÉ (extrait) — https://dropshipping.vidaxl.com/pricing/ et https://dropshipping.vidaxl.com/terms-conditions/.
- Fréquence : prix quotidien, stock horaire. VÉRIFIÉ (extrait) — https://dropshipping.vidaxl.com/dropshipping-faqs/.
- Amazon : VÉRIFIÉ (extrait) — même FAQ : « Can I sell vidaXL products on different marketplaces, like eBay and Amazon? Yes, once you are a vidaXL Drop-shipper … » (FAQ ancienne, à reconfirmer).
- EAN dans le flux : NON VÉRIFIÉ.

### 2.4 Brandsdistribution
- API : VÉRIFIÉ — https://us.brandsdistribution.com/en/cms/developers : « Web Services are available for authenticated Dropshipper users only » ; prix « to be read in EURO » ; champ `barcode` (« the model barcode ») ; mises à jour de stock renouvelées toutes les 3 minutes ; bac à sable, clé par courriel.
- Abonnement : VÉRIFIÉ — https://www.brandsdistribution.com/en/cms/dropshipping-guide : « The monthly rate is €99 + VAT and the annual rate is €990 + VAT ». Export possible vers « Amazon, Ebay » via plugins de tiers (même page).
- Autorisation de revente sur Amazon, restrictions de marque, factures : NON VÉRIFIÉ (rien d'écrit sur la page).

### 2.5 Alibaba.com
- Open API : VÉRIFIÉ — https://developer.alibaba.com/docs/doc.htm?treeId=684&articleId=118416&docType=1 : « Developers are required to register in order to get App key and App security » ; destinée aux ISV « who have been authorized by their end-users » ; gratuite en bêta pour « all paid GGS users » (abonnés vendeurs). Rien pour l'acheteur.
- Collecte automatisée : VÉRIFIÉ (extrait) — conditions d'utilisation (Rules Center, https://rule.alibaba.com/rule/detail/2041.htm) : constituer une collection, compilation, base de données ou répertoire à partir du contenu, par moyen automatisé ou manuel, exige l'accord écrit d'Alibaba.com. Citation exacte non relue (page en JavaScript).

### 2.6 Ankorstore
- Éligibilité : VÉRIFIÉ — https://support.ankorstore.com/articles/3353966746-starting-as-a-retailer : non éligibles ceux qui « Resell only on Amazon or Ebay » ; « Dropshipping companies are not allowed on the platform ».
- CGU détaillants : VÉRIFIÉ — https://support.ankorstore.com/articles/7911860874-terms-of-use-retailers-buyers : §17.5 interdit « Use deep data mining tools, robots or any similar data collection and extraction tools relating to the Platform » ; §3.3 les marques fixent « any restrictions on the resale of the Products ».
- API : VÉRIFIÉ — https://ankorstore.github.io/api-docs/ : « The Ankorstore API enables brands and their partners to programmatically manage their presence ».

### 2.7 Faire
- VÉRIFIÉ (extrait) — CGU détaillants UE https://www.faire.com/support/articles/18524831904667 : « You agree to not fulfil orders on third party websites unless they are approved by Faire. Prohibited sites include Amazon, eBay, Etsy, and Poshmark. »
- VÉRIFIÉ (extrait) — https://www.faire.com/support/articles/31169832450971 : Faire n'accepte pas les détaillants vendant sur Amazon, eBay, Etsy…
- API : VÉRIFIÉ (extrait) — https://www.faire.com/support/articles/37632363832091 : pas de clé API pour les détaillants ; https://developers.faire.com/docs : API pour « brands and integration partners ».

### 2.8 Creoate
- VÉRIFIÉ (extrait) — https://www.creoate.com/terms-and-conditions : interdit de « Fulfill orders on third party websites, including Amazon, eBay, Etsy or any other online marketplace for items purchased through Creoate ». Le centre d'aide (https://helpcenter.creoate.com/can-i-resell-product-on-amazon) dit seulement qu'un fournisseur peut refuser la commande : les deux pages divergent, la CGU prime.

### 2.9 Global Sources
- Pas d'API acheteur trouvée (recherche sur globalsources.com) : NON VÉRIFIÉ qu'il n'en existe aucune.
- VÉRIFIÉ (extrait) — https://www.globalsources.com/help-faq/en/terms-of-use/ (clause 4) : interdit de « download, copy, reproduce … mirror, frame, transmit, store … » tout ou partie du site sans permission, sauf portions « non-substantial », usage interne non commercial.

### 2.10 Made-in-China.com
- VÉRIFIÉ — https://www.made-in-china.com/help/terms/ (V.3) : « no entity or individual shall copy, reproduce, cite, link, grasp or otherwise use » les informations du site sans accord écrit de Focus Technology. Pas d'API acheteur mentionnée.

### 2.11 1688
- Portail https://open.1688.com/ non lisible (page en JavaScript). Accès des acheteurs étrangers par agents d'achat (presse, non officiel). Tout : NON VÉRIFIÉ.

### 2.12 B2B Griffati
- Éditeur de l'application Shopify Sync2Fashion (fiche Shopify, non lue en entier). API, flux, revente Amazon : NON VÉRIFIÉ.

### 2.13 Wholesale Central
- VÉRIFIÉ (extrait) — https://www.wholesalecentral.com/aboutus.htm : annuaire B2B ; « No registration is required to search the site » ; renvoi vers le site du fournisseur pour commander. Marché américain. Pas d'API.

### 2.14 Syncee
- VÉRIFIÉ (extrait) — https://syncee.com/ : fournisseurs US, CA, UE, UK, AU ; gestion de flux CSV/XML/JSON côté fournisseur. Canal Amazon : NON VÉRIFIÉ (non cité).

---

## 3. Amazon : factures acceptées pour l'approbation des catégories restreintes

**NON VÉRIFIÉ.** Les pages d'aide officielles de Seller Central (« Catégories et produits nécessitant une approbation », exigences de facture, politique anti-contrefaçon) exigent une connexion : la page https://sellercentral.amazon.com/help/hub/reference/external/G200333160 ne renvoie que le menu sans le texte.

Ce qui revient dans les forums Seller Central (non officiel, y compris réponses de personnel Amazon, contradictoires) : facture du fabricant ou d'un distributeur, nom et adresse du vendeur identiques au compte, coordonnées du fournisseur (adresse, téléphone, site), datée de moins de 180 jours (parfois 365 jours), souvent au moins 10 unités, prix masquables ; refusés : pro forma, bons de commande, tickets de caisse, factures de places de marché de détail. **À lire dans Seller Central par Sam lui-même** (le formulaire d'approbation affiche les exigences du produit) avant d'en faire une règle du registre.

---

## 4. Liste NON VÉRIFIÉ

1. Exigences officielles d'Amazon pour les factures d'approbation (date, quantité, émetteur) — pages Seller Central derrière connexion.
2. Qogita : coût de l'API, limites d'appels, frais de port dans l'API, clause anti-robot des CGU.
3. BigBuy : tarifs actuels des packs ; clause sur l'accès automatisé hors API ; acceptation de ses factures par Amazon.
4. vidaXL : présence de l'EAN dans le flux ; FAQ « Amazon autorisé » ancienne, à reconfirmer dans les CGU actuelles.
5. Brandsdistribution : autorisation ou interdiction de revente sur Amazon ; restrictions de marques ; authenticité ; factures.
6. Alibaba.com : existence d'une API catalogue pour acheteurs ; texte exact de la clause de collecte (page non chargée).
7. 1688 : tout (portail illisible).
8. Global Sources, Made-in-China : absence d'API acheteur (seulement « non trouvée »).
9. B2B Griffati : API, flux, revente Amazon.
10. Syncee : canal Amazon.
11. Toutes les mentions « VÉRIFIÉ (extrait) » : page complète non chargée (protection anti-robot), à relire dans un navigateur.

## 5. Pistes non explorées (à faire si besoin)
- Grossistes européens qui envoient un tarif CSV/Excel à leurs clients professionnels (modèle classique du « wholesale » Amazon) : pas d'API publique, mais la donnée la plus courante et la plus fiable ; d'où l'import de tarif en priorité.
- Distributeurs agréés par marque (listes de distributeurs officiels sur les sites des marques) : meilleure preuve pour le dégating.
