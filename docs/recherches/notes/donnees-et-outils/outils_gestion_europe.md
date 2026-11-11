# Outils de gestion de compte vendeur Amazon (Europe) : prix vérifiés, add-ons, coûts réels

Date de collecte : 2026-11-11. Méthode : pages tarifs officielles lues directement (HTML brut + données JSON/JS embarquées quand la page est rendue en JS). Tout ce qui n'a pas pu être lu sur une source primaire est marqué **NON VÉRIFIÉ**. Les montants restent dans la devise affichée par l'éditeur (aucune conversion de change inventée).

## Q1. Prix exacts, contenu de chaque palier et add-ons, outil par outil

### Takeaway
Les tarifs d'entrée sont très bas chez sellerboard (19 $), Sellerise (19,99 $) et SellerLogic Business Analytics (gratuit jusqu'à 100 commandes). Ce qui fait monter le coût réel, ce sont les plafonds de commandes et leur mise à niveau automatique (sellerboard, Shopkeeper), les modules facturés à part chez SellerLogic (Repricer au SKU, Lost & Found à 25 %), les services hors abonnement chez Shopkeeper, et l'abonnement PPC lui-même chez Perpetua (695 $/mois minimum).

### Cited Findings

**sellerboard** (éditeur allemand, nextechnology GmbH, Stuttgart). Page tarifs : section #pricing de https://sellerboard.com/en/ (l'URL /en/pricing renvoie un 404).
- Plans (USD) : Standard 19 $/mois en mensuel, ou 15 $/mois en annuel (179 $/an) ; Professional 29 $ (23 $ ; 279 $/an) ; Business 39 $ (31 $ ; 369 $/an) ; Enterprise 79 $ (63 $ ; 759 $/an) ; « Need more? » sur devis. La page ne propose que le mensuel et l'annuel, sans option semestrielle — [sellerboard](https://sellerboard.com/en/)
- Commandes par mois : 3 000 / 6 000 / 15 000 / 50 000. E-mails de suivi ou demandes d'avis par mois : 150 / 6 000 / 15 000 / 30 000 — [sellerboard](https://sellerboard.com/en/)
- Lignes chiffrées du tableau, lues dans le HTML dans l'ordre des lignes : « Additional seller accounts » 4 / 6 / 8 / 16 ; « Additional users » 1 / 2 / 4 / 4 ; « Automated reports » 3 / 6 / 8 / 16 — [sellerboard](https://sellerboard.com/en/)
- « Manage users access rights by account, marketplaces and products » est marqué « Not included » sur Standard, Professional et Business, et inclus seulement sur Enterprise. Inclus dans tous les plans : Real-time profit dashboard, Listing change alerts, PPC optimization, Repricer, Inventory management, Refunds for lost inventory, LTV dashboard — [sellerboard](https://sellerboard.com/en/)
- Conditions : « 1 month free trial », « No credit card required », « Cancel anytime » ; « EU only: All prices are net. Value Added Tax may apply. » ; plafond de 30 000 produits par compte — [sellerboard](https://sellerboard.com/en/)
- CGU, dépassement : « If you exceed the limits of your current plan, you may be automatically upgraded to a higher plan… subject to the pricing of the higher plan. We will notify you per E-Mail ». Les prix peuvent changer « without notice ». Le renouvellement est automatique (« monthly… or on yearly/half yearly basis »). « sellerboard subscription fees are non-refundable » — [sellerboard Terms](https://sellerboard.com/terms)
- Interface disponible en français : hreflang fr, et sélecteur de langue avec Deutsch, Français, Español, Italiano… — [sellerboard](https://sellerboard.com/en/) ; [Terms](https://sellerboard.com/terms)

**Shopkeeper** (positionné comme UK, mais l'adresse publiée est 5645 Coral Ridge Dr., Coral Springs, FL, USA). Page : https://shopkeeper.com/pricing (www.shopkeeper.com ne se résout pas depuis cet environnement ; sans « www », la page charge).
- Mensuel uniquement, en $ : Starter 20 $ (≤ 250 commandes/mois) ; Intermediate 45 $ (≤ 1 000) ; Master 90 $ (≤ 5 000) ; Superseller 250 $ (≤ 10 000) ; Enterprise « Contact Sales » (> 10 000). Tous les plans ont les mêmes fonctions, dont « PPC analysis & campaign management », « VAT configuration & reports », « Automated reimbursement, clawback and adjustment attribution » et « User management control panel ». Free trial sans durée affichée. Pop-up « 50% off » de bienvenue sans conditions — [Shopkeeper pricing](https://shopkeeper.com/pricing)
- Service de remboursement facturé à part : Starter 5 $/mois ; Intermediate 10 $/mois ; Master **15 % du montant remboursé** ; Super Seller **12 %** — [Shopkeeper reimbursement pricing](https://shopkeeper.com/pricing/reimbursement)
- CGU : les services de remboursement, d'appel, PPC, d'alertes, de coaching et d'audit et le support premium « is not included in the monthly subscription ». Si le volume dépasse le palier en cours de période, un ajustement **pro-rata est prélevé automatiquement** et n'est pas remboursable. Renouvellement automatique « at the price you agreed… or in accordance with Shopkeeper's then-current pricing ». « All payments for paid memberships are non-refundable ». Les frais de service sont non remboursables une fois le travail commencé — [Shopkeeper Terms](https://shopkeeper.com/terms)
- Site disponible en Français (sélecteur de langue) — [Shopkeeper Terms](https://shopkeeper.com/terms)

**SELLERLOGIC** (DE). Trois modules réservables séparément.
- **Business Analytics** (EUR, « exclusive of applicable VAT »). Prix basé sur « all orders per month received from all connected Amazon marketplaces ». Durées 3 / 6 / 12 / 24 mois avec remise −0 / −5 / −10 / −15 % ; aucune option mensuelle n'apparaît. Grille par mois, de 3 mois à 24 mois :
  - 0–100 : gratuit
  - 101–500 : 10,00 / 9,50 / 9,00 / 8,50 €
  - 501–1 000 : 15,00 / 14,25 / 13,50 / 12,75 €
  - 1 001–2 500 : 25,00 / 23,75 / 22,50 / 21,25 €
  - 2 501–5 000 : 50,00 / 47,50 / 45,00 / 42,50 €
  - 5 001–10 000 : 75,00 / 71,25 / 67,50 / 63,75 €
  - 10 001–25 000 : 129,00 / 122,55 / 116,10 / 109,65 €
  - 25 001–50 000 : 149,00 / 141,55 / 134,10 / 126,65 €
  - 50 001–100 000 : 199,00 €
  - 100 000–1 000 000 : 249,00 € (prix sur 3 mois)
  - Essai de 14 jours — [SELLERLOGIC Business Analytics](https://www.sellerlogic.com/en/business-analytics-tool-amazon/)
- **Repricer** (EUR). Données JSON de la page (le rendu affiche « 0,00 € » : le calculateur est en JS) :
  - Trial 14 jours. Freemium gratuit, 20 produits optimisés par jour, sans API, sans import ni export. Annuel = « Get 2 months free ».
  - Starter : 100 produits 39 € ; 500 produits 85 € ; 1 000 produits 109 € ; 5 000 produits 399 € ; 10 000 produits 749 € ; 20 000 produits 1 359 €.
  - Advanced (« Recommended », synchro horaire, sync Business Analytics) : 100 produits 49 € ; 500 produits 106 € ; 1 000 produits 136 € ; 5 000 produits 499 € ; 10 000 produits 936 € ; 20 000 produits 1 699 €.
  - Toutes les marketplaces Amazon sont incluses. « automatically renew at the end of each billing cycle ». Paiement par carte uniquement. Gratuit jusqu'à la fin du contrat chez un repricer concurrent (12 mois maximum) — [SELLERLOGIC Repricer](https://www.sellerlogic.com/en/amazon-dynamic-repricing-tool/)
- **Lost & Found Full-Service** : « 25% commission on refunds actually received », « No basic fee », audit sur 18 mois, facturation au début du mois suivant, prix hors TVA, « can be canceled daily. No notice period » — [SELLERLOGIC Lost & Found](https://www.sellerlogic.com/en/amazon-lost-and-found/). Webretailer annonce 20 %, ce qui contredit la page officielle — [Webretailer](https://webretailer.com/reviews/sellerlogic)

**AMALYTIX** (DE, Cologne). Il n'y a pas de page « /pricing » (404). Les prix sont publiés sur https://www.amalytix.com/en/amazon-seller-tool/ ; les valeurs EUR proviennent des données embarquées de la page, qui affiche USD par défaut.
- Essential **69 €/mois** ou 690 €/an (89 $ / 890 $) : jusqu'à 500 produits, dashboards, monitoring de contenu et de stock, alertes, suivi des concurrents, recherche et suivi de mots-clés, « Advertising ».
- Professional **149 €** ou 1 490 €/an (179 $) : jusqu'à 1 500 produits, AI Agent, dashboards personnalisés, mises à jour de fiches poussées vers Amazon, suivi des prix des vendeurs tiers, **3 seats**, onboarding dédié.
- Scale **249 €** ou 2 490 €/an (299 $) : jusqu'à 5 000 produits, Workflows, **jusqu'à 5 seats**.
- Custom sur devis au-delà de 5 000 produits. L'annuel donne 17 % de remise. Essai de 14 jours sans carte.
- « * We count 1 child ASIN on 3 marketplaces as 3 products » — [AMALYTIX Seller Tool](https://www.amalytix.com/en/amazon-seller-tool/)
- CGU : « Remuneration is always net prices plus statutory VAT ». §9.2 : résiliation avec un mois de préavis, sinon « extended by a further year in each case ». La page tarifs dit pourtant « without long-term lock-in ». **Contradiction à faire clarifier** — [AMALYTIX Terms](https://www.amalytix.com/en/about-us/terms-of-services/)

**Sellerise**. La page https://sellerise.com/pricing/ est rendue en JS ; données lues sur l'endpoint JSON officiel https://sellerise.com/pricing/data. Prix stockés en cents et affichés avec « $ » (symbole relevé dans le script de pricing).
- Essai : `trialPeriod: 7` jours, `creditCardRequired: false`. Plans à intervalle « month » ; un bouton annuel existe dans le script, mais aucun prix annuel n'est publié.
- **Starter 19,99 $** : 1 compte vendeur, 1 000 commandes, pas de module remboursement, pas de SQP, 0 collaborateur inclus.
- **Growing 39,99 $** : 2 comptes, 5 000 commandes, remboursements stock/expéditions et frais FBA inclus, SQP inclus.
- **Advanced 99,99 $** : 5 comptes, 50 000 commandes, 2 collaborateurs.
- **Pro-Seller 299,99 $** : 10 comptes, 150 000 commandes, 6 collaborateurs, onboarding personnel.
- **Top-Seller 599,99 $** : 20 comptes, 300 000 commandes, 12 collaborateurs.
- Add-ons :
  - Extra Orders : `price 200`, `min_interval 1000`, soit **2 $ par tranche de 1 000 commandes** (interprétation des champs).
  - Seller Account : 20 $.
  - Collaborator : 10 $.
  - Keyword Tracker : 1 $ par 100 mots-clés.
  - Review Dashboard : 2 $ par 10 produits.
- Un « Seller account » unifié couvre « EU, UK, TR, EG, IN, SA, UAE, ZA ». Inclus dans tous les plans : app iOS & Android, PPC Dashboard, Review Requester, Inventory Tool, P&L — [Sellerise pricing data](https://sellerise.com/pricing/data)
- FAQ : « we do not charge any percentage/extra fees to reimburse you » — [Sellerise pricing](https://sellerise.com/pricing/)

**SellerApp** (USD) — https://www.sellerapp.com/pricing.html
- Freemium 0 $. Pro Plan « starts with $99 per month ». Smart Plan with Automation « starts with $149 $250 * per month », avec « *Discounted pricing is for first 3 months » : **250 $/mois après le 3e mois**. Le Smart Plan inclut Ads Automation et un account manager dédié. Custom sur devis.
- Prix déterminé par questionnaire (ASINs, dépenses pub, CA) ; grille exacte non publiée. Annuel : « save 50% ».
- Marketplaces : DE, ES, FR, IT, NL, PL, SE, UK, etc.
- Agences : 300 $ + 0,5 à 2,5 % des dépenses pub — [SellerApp pricing](https://www.sellerapp.com/pricing.html)

**Perpetua** (PPC uniquement, plan d'entrée) — https://perpetua.io/pricing
- **Essentials 695 $/mois**, jusqu'à 10 k$ de dépenses pub mensuelles.
- **Growth 695 $/mois + % des dépenses pub** au-delà de 10 k$ ; pourcentage non publié.
- Premium sur devis, au-delà de 500 k$ de dépenses pub — [Perpetua pricing](https://perpetua.io/pricing)

**Services de remboursement (commission sur montants récupérés)**
- SELLERLOGIC Lost & Found : 25 %, sans fixe — [SELLERLOGIC](https://www.sellerlogic.com/en/amazon-lost-and-found/)
- Carbon6 Seller Investigators : audit gratuit en 48 h, puis « only pay a 25% commission fee when your money is back » — [Carbon6](https://carbon6.io/seller-investigators/) ; [sellerinvestigators.com](https://sellerinvestigators.com/)
- GETIDA : « performance-based pricing starting at 20% », « No monthly subscription fees », audit sur 18 mois. La page /pricing redirige vers /how-we-help/ — [GETIDA](https://getida.com/how-we-help/)
- Shopkeeper : 5 $/mois ou 10 $/mois forfaitaires, puis 15 % ou 12 % selon le plan — [Shopkeeper](https://shopkeeper.com/pricing/reimbursement)
- Sellerise : 0 % de commission, inclus à partir de Growing — [Sellerise](https://sellerise.com/pricing/)
- Refunds Manager : le site est désormais centré sur la récupération de déductions **vendor** (Walmart Retail Link, Amazon Vendor Central). Il annonce « success-based fee… applicable rate and terms agreed before work begins » ; aucun % publié. https://www.refundsmanager.com/pricing ne répond pas — [Refunds Manager](https://refundsmanager.com/)

### Inferences
- Chez sellerboard, le plan Standard ne convient pas à un vendeur à 1 000 commandes qui veut solliciter des avis systématiquement : il n'offre que 150 demandes d'avis par mois. Il faut alors Professional (29 $).
- Chez sellerboard et Shopkeeper, le dépassement du plafond de commandes déclenche une mise à niveau automatique. Chez Shopkeeper, l'ajustement pro-rata n'est pas remboursable.
- AMALYTIX compte les « produits » par ASIN enfant et par marketplace. Sur 4 marketplaces, 125 ASINs suffisent à atteindre la limite de 500 produits d'Essential.

### Gaps
- sellerboard : commission éventuelle sur « Refunds for lost inventory », prix des utilisateurs ou comptes au-delà des quotas, sens exact de « Additional seller accounts », existence d'une app mobile — **NON VÉRIFIÉ**.
- Shopkeeper : durée de l'essai (non affichée), prix annuels, prix Enterprise au-delà de 10 000 commandes, TVA, prix des services PPC — **NON VÉRIFIÉ**.
- Sellerise : prix annuels, devise confirmée en clair, TVA — **NON VÉRIFIÉ**.
- SellerApp : prix exact par palier ASIN/dépenses pub (questionnaire). La page /terms.html renvoie 404 — **NON VÉRIFIÉ**.
- Perpetua : pourcentage de dépenses pub du plan Growth — **NON VÉRIFIÉ**.
- SELLERLOGIC : liste des langues de l'interface (français ?) — **NON VÉRIFIÉ**.
- AMALYTIX : présence d'un module profit/remboursement pour les vendeurs (le site mentionne « Profitability » sans plan associé ; « shortage claims » concerne les vendors) — **NON VÉRIFIÉ**.

## Q2. Coût mensuel réel pour un vendeur UE (3 à 5 marketplaces, PPC) à 1 000 / 5 000 / 20 000 commandes par mois

### Takeaway
Pour une suite « profit + PPC + stock + remboursements », sellerboard reste de loin le moins cher : 19 à 29 $ à 1 000 commandes, 29 $ à 5 000 et 79 $ à 20 000 en mensuel, hors TVA. Sellerise est proche, avec des remboursements sans commission. Shopkeeper coûte 2 à 3 fois plus cher, et SELLERLOGIC devient coûteux dès qu'on ajoute le Repricer. Perpetua, à 695 $/mois, est un outil PPC et non un outil de gestion de compte.

### Cited Findings (calculs à partir des seuls prix vérifiés ci-dessus)

**sellerboard** (USD, net de TVA). Les commandes sont comptées au niveau du compte, toutes marketplaces confondues — [sellerboard](https://sellerboard.com/en/)
- 1 000 commandes : Standard **19 $** (annuel 179/12 = **14,92 $**). Avec demandes d'avis sur toutes les commandes, il faut Professional (6 000 demandes) : **29 $**, ou 279/12 = **23,25 $** en annuel.
- 5 000 commandes : Professional (plafond 6 000) **29 $**, ou **23,25 $** en annuel.
- 20 000 commandes : Business plafonne à 15 000, donc Enterprise **79 $**, ou 759/12 = **63,25 $** en annuel.
- PPC, repricer, stock et outil de remboursement sont inclus.

**Shopkeeper** (USD). Les deux colonnes ci-dessous sont l'abonnement seul, puis l'abonnement avec le service de remboursement — [pricing](https://shopkeeper.com/pricing) ; [reimbursement](https://shopkeeper.com/pricing/reimbursement)

| Commandes/mois | Plan | Abonnement seul | Avec remboursement |
|---|---|---|---|
| 1 000 | Intermediate | **45 $** | 45 + 10 = **55 $** |
| 5 000 | Master | **90 $** | 90 $ + **15 %** des montants récupérés |
| 20 000 | Enterprise | « Contact Sales », **NON VÉRIFIÉ** | — |

À 20 000 commandes, le plan Superseller (250 $) plafonne à 10 000 et ne suffit donc pas.

**SELLERLOGIC** (EUR, hors TVA). Business Analytics, engagement minimum de 3 mois (une durée de 12 mois donne −10 %) — [BA](https://www.sellerlogic.com/en/business-analytics-tool-amazon/)

| Commandes/mois | Tranche BA | BA sur 3 mois | BA sur 12 mois |
|---|---|---|---|
| 1 000 | 501–1 000 | **15,00 €** | 13,50 € |
| 5 000 | 2 501–5 000 | **50,00 €** | 45,00 € |
| 20 000 | 10 001–25 000 | **129,00 €** | 116,10 € |

Modules à ajouter :
- Repricer, par exemple 500 SKUs en Advanced : **106 €/mois** en mensuel, ou 106 × 10 / 12 = **88,33 €/mois** en annuel — [Repricer](https://www.sellerlogic.com/en/amazon-dynamic-repricing-tool/)
- Lost & Found : 25 % des remboursements.
- Exemple à 5 000 commandes : 50 € + 106 € = **156 €/mois**, plus 25 % des montants récupérés.
- Le PPC n'est pas un module SELLERLOGIC identifié (**NON VÉRIFIÉ**) ; il faudrait un outil PPC à part.

**AMALYTIX** (EUR, hors TVA). Prix indexé sur le catalogue, pas sur les commandes — [AMALYTIX](https://www.amalytix.com/en/amazon-seller-tool/)
- Exemple de 100 ASINs enfants sur 4 marketplaces = 400 « produits » : Essential **69 €**, ou 690/12 = **57,50 €** en annuel. Le volume de commandes est sans effet.
- Exemple de 300 ASINs × 4 = 1 200 produits : Professional **149 €**, ou **124,17 €** en annuel.
- L'outil inclut « Advertising », mais ni module de remboursement vendeur ni repricer n'ont été vérifiés : prévoir en plus un service de remboursement à 20–25 %.

**Sellerise** (USD, mensuel). Tous les marketplaces EU/UK sont dans un seul « seller account » unifié — [data](https://sellerise.com/pricing/data)

| Commandes/mois | Plan | Coût | Remboursements |
|---|---|---|---|
| 1 000 | Starter | **19,99 $** | non inclus |
| 1 000 | Growing | **39,99 $** | inclus, 0 % de commission |
| 5 000 | Growing | **39,99 $** | inclus |
| 20 000 | Growing + 15 000 commandes en add-on | 39,99 + 15 × 2 = **69,99 $** (calcul interprétatif) | inclus |
| 20 000 | Advanced (50 000 commandes) | **99,99 $** | inclus |

Chaque collaborateur ajouté coûte 10 $/mois sur Starter et Growing.

**SellerApp** (USD). Prix minimal publié pour un vendeur qui veut l'automatisation PPC : Smart **149 $** les 3 premiers mois, puis **250 $/mois**. Pro, sans automatisation pub, est à partir de 99 $. Le tarif exact selon le volume d'ASINs et de dépenses pub est **NON VÉRIFIÉ** — [SellerApp](https://www.sellerapp.com/pricing.html)

**Perpetua** (USD). **695 $/mois** jusqu'à 10 k$ de dépenses pub ; au-delà, 695 $ plus un pourcentage non publié — [Perpetua](https://perpetua.io/pricing)

**Coût des remboursements** (exemple : 1 000 € récupérés par mois)
- Sellerise : 0 €
- Shopkeeper Master : 150 €
- GETIDA : à partir de 200 €
- SELLERLOGIC Lost & Found ou Seller Investigators : 250 €
- Sources : [Sellerise](https://sellerise.com/pricing/) ; [Shopkeeper](https://shopkeeper.com/pricing/reimbursement) ; [GETIDA](https://getida.com/how-we-help/) ; [SELLERLOGIC](https://www.sellerlogic.com/en/amazon-lost-and-found/) ; [Seller Investigators](https://sellerinvestigators.com/)

### Inferences
- Les prix d'entrée qui cachent des coûts :
  - Sellerboard Standard : seulement 150 demandes d'avis par mois.
  - Sellerise Starter : pas de remboursements, 0 collaborateur.
  - SellerApp : le prix de 149 $ ne vaut que 3 mois.
  - SELLERLOGIC : Business Analytics est quasi gratuit, mais le Repricer et Lost & Found (25 %) s'ajoutent, et BA impose un engagement de 3 mois minimum.
  - Shopkeeper : remboursements, PPC et support sont hors abonnement, et le palier est relevé automatiquement.
  - AMALYTIX : le comptage par marketplace multiplie la taille du catalogue.
- Pour un vendeur UE à 20 000 commandes, le prix publié va de 63–79 $ (sellerboard) à « sur devis » (Shopkeeper). Chez SELLERLOGIC, on atteint 129 € pour BA seul, puis plus de 1 000 € par mois si l'on reprice 10 000 SKUs ou plus.
- Les commissions de remboursement (20 à 25 %) peuvent dépasser l'abonnement lui-même dès quelques centaines d'euros récupérés par mois.

### Gaps
- Aucun taux de change n'a été appliqué : les comparaisons USD/EUR sont donc approximatives.
- Le traitement exact de la TVA côté vendeur UE n'est publié que pour sellerboard, SELLERLOGIC et AMALYTIX (prix nets, TVA en sus). Shopkeeper, Sellerise, SellerApp et Perpetua : **NON VÉRIFIÉ**.

## Q3. Réputation (lue directement sur Trustpilot, 2026-11-11)

### Takeaway
sellerboard, SELLERLOGIC, Sellerise et SellerApp sont bien notés sur Trustpilot (4,4 à 4,7). Shopkeeper (1,5), Seller Investigators (2,1), Perpetua (2,6) et GETIDA (2,3, sur seulement 7 avis) sont mal notés.

### Cited Findings
| Outil | TrustScore | Nombre d'avis | Source |
|---|---|---|---|
| sellerboard | 4,5 | 164 | [Trustpilot](https://www.trustpilot.com/review/sellerboard.com) |
| SELLERLOGIC | 4,7 | 37 | [Trustpilot](https://www.trustpilot.com/review/sellerlogic.com) |
| Sellerise | 4,4 (les étoiles affichent 4,5) | 132 | [Trustpilot](https://www.trustpilot.com/review/sellerise.com) |
| SellerApp | 4,4 (« Excellent ») | 130 | [Trustpilot](https://www.trustpilot.com/review/sellerapp.com) |
| Shopkeeper | 1,5 | 112 | [Trustpilot](https://www.trustpilot.com/review/shopkeeper.com) |
| Seller Investigators | 2,1 | 122 | [Trustpilot](https://www.trustpilot.com/review/sellerinvestigators.com) |
| Perpetua | 2,6 | 63 | [Trustpilot](https://www.trustpilot.com/review/perpetua.io) |
| GETIDA (domaine getida.com) | 2,3 | 7 | [Trustpilot](https://www.trustpilot.com/review/getida.com) |

- Refunds Manager affiche lui-même « ★ 4.9 / 5 On Trustpilot » : c'est une auto-déclaration, non lue sur Trustpilot — [Refunds Manager](https://refundsmanager.com/)

### Inferences
- La mauvaise note de Shopkeeper est cohérente avec des CGU restrictives : aucun remboursement, et une mise à niveau pro-rata automatique non remboursable.

### Gaps
- Trustpilot bloque les requêtes curl (403) : les scores ont été lus via WebFetch.
- Les profils AMALYTIX, Refunds Manager, et les notes G2/Capterra n'ont pas été lus — **NON VÉRIFIÉ**.
- Les scores peuvent varier selon le domaine Trustpilot retenu.
