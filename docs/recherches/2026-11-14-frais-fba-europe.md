# Frais FBA Europe (amazon.fr) — vérification aux sources officielles

Lu le 14/11/2026 (heure de Paris). Sources officielles uniquement, téléchargées avec `curl`. Rien de mémoire, aucun blog.

Sources lues :

- **S1** — https://sell.amazon.fr/tarifs (FR) et https://sell.amazon.fr/en/tarifs (EN), HTML statique lisible.
- **S2** — Grille tarifaire officielle « Rate Card Europe Fees, Effective as of 2 November, 2026 », liée depuis S1 :
  https://m.media-amazon.com/images/G/02/sell/images/261014-FBA-Rate-Card-EN.pdf (33 p.) et `…-FR.pdf`.
- **S3** — https://developer-docs.amazon/sp-api/reference/getmyfeesestimateforasin.md (updatedAt 2026-09-10) et `…/getmyfeesestimates.md` ;
  modèle officiel https://raw.githubusercontent.com/amzn/selling-partner-api-models/main/models/product-fees-api-model/productFeesV0.json.
- **S4** — https://developer-docs.amazon/sp-api/reference/listplacementoptions.md (updatedAt 2026-09-10) et
  https://developer-docs.amazon/sp-api/docs/create-an-inbound-shipment.md.
- **S5** — https://developer-docs.amazon/sp-api/reference/getcatalogitem.md (Catalog Items 2022-04-01, updatedAt 2026-09-10).
- **Non lisible** — pages d'aide Seller Central (ex. https://sellercentral.amazon.fr/gp/help/external/201074400 et les liens
  `sellercentral-europe.amazon.com/help/hub/reference/external/…` cités par S2) : la page renvoyée contient seulement
  « You need to enable JavaScript to run this app. » → contenu non lu.

## Tableau

| Frais | Valeur (amazon.fr / UE) | Source et citation exacte | Statut |
|---|---|---|---|
| Supplément carburant et logistique | 1,5 % → **2 %** à compter du **2 novembre 2026** ; s'applique aux **frais d'expédition FBA** ; pays : Royaume-Uni, France, Allemagne, Italie, Espagne, Pologne, Suède, Pays-Bas, Irlande, Belgique | S1 FR : « À compter du 2 novembre 2026, le supplément lié au carburant et à la logistique passera de 1,5 % à 2 % et s'appliquera aux frais d'expédition de l'ensemble de nos sites Expédié par Amazon situés au Royaume-Uni, en France, […] et en Belgique. » S2 EN p. 5-6 : « will apply to fulfillment fees across Fulfillment by Amazon (FBA) in our UK, France, […] and Belgium stores. » | VÉRIFIÉ (14/11/2026) |
| — outils Amazon à jour du supplément | Calculatrice des recettes FBA, tableau Analyse des bénéfices, rapports d'aperçu des frais | S1 FR : « La calculatrice des recettes Expédié par Amazon, le tableau de bord Analyse des bénéfices et les rapports d'aperçu des frais […] ont tous été mis à jour pour répercuter le supplément carburant et logistique ». | VÉRIFIÉ — **l'API n'est pas citée** |
| — inclus dans getMyFeesEstimate(ForASIN) ? | Inconnu | S3 : aucune mention de « surcharge » ni « fuel ». `FeeType` est une chaîne libre, sans liste de valeurs : « "FeeType": { "description": "The type of fee charged to a seller.", "type": "string" } ». Les exemples ont `"FeeDetailList": []`. Les noms FBAFees, ReferralFee, VariableClosingFee, PerItemFee **n'apparaissent pas** dans la doc ni dans le modèle JSON. | **NON VÉRIFIÉ** (doc muette) |
| — inclus dans les montants de la grille S2 ? | Inconnu | S2 donne la note du supplément au-dessus des tableaux, sans dire si les montants l'incluent. | **NON VÉRIFIÉ** |
| Stockage mensuel, standard, Vêtements/Lunettes/Chaussures/Sacs (non dangereux) | **19,99 €/m³/mois** janv.–sept. ; **29,23 €** oct.–déc. | S1 + S2 p. 21 : « DE/FR/IT/ES/NL/PL/BE/IE (€/m3/month) 19.99 29.23 27.54 52.20 21.78 34.49 30.00 50.51 27.50 43.89 » | VÉRIFIÉ |
| Stockage mensuel, standard, autres catégories (non dangereux) | **27,54 €/m³/mois** janv.–sept. ; **52,20 €** oct.–déc. | S1 FR : « le tarif est de 27,54 € par mètre cube de janvier à septembre, et de 52,20 € d'octobre à décembre. » | VÉRIFIÉ |
| Stockage mensuel, hors gabarit (non dangereux) | **21,78 €** ; **34,49 €** | S1 EN : « Oversized products (Non-hazardous products) €21.78 per cubic metre per month €34.49 per cubic metre per month » | VÉRIFIÉ |
| Stockage, produits dangereux standard / hors gabarit | 30,00 € / 50,51 € ; 27,50 € / 43,89 € | S1 + S2 p. 21 (même ligne ci-dessus) | VÉRIFIÉ |
| Base du volume stocké | volume journalier moyen, unité emballée prête à expédier | S1 FR/EN : « The volume measurement is based on unit size when properly packaged and ready to ship. » | VÉRIFIÉ |
| Supplément d'utilisation du stockage (DE/FR/IT/ES) | ratio > 22 sem. : de 14,85 à 76,87 €/m³/mois (standard), 4,29 à 23,10 € (hors gabarit) ; exclu : nouveaux vendeurs < 52 sem., comptes Individuels, < 25 pi³ de volume journalier | S2 p. 21 : « The storage utilisation surcharge does not apply to new sellers, sellers with Individual selling accounts and sellers with less than 25 cubic feet of daily volume. » | VÉRIFIÉ |
| Supplément stock ancien (> 241 jours) | DE/FR/IT/ES/IE : 47,99 €/m³/mois (241-270 j) … 261,97 €/m³ ou 0,25 €/unité (455 j +) | S2 p. 21 : « DE/FR/IT/ES/IE (€/m3/month) 47.99 125.16 129.92 135.98 » | VÉRIFIÉ |
| Frais de placement à l'envoi (« inbound placement fee ») en UE | **Aucun dans la grille UE 2026** | S2 (33 p.) : le mot « placement » n'apparaît que pour Pan-EU (« In the countries enabled for placement, Selling Partners will benefit from local FBA fulfilment fees »). La seule page « 2025 FBA inbound placement service fee » citée par S4 est sur `sellercentral.amazon.com` (US) et n'est pas lisible (JavaScript). | VÉRIFIÉ pour l'absence dans la grille UE ; NON VÉRIFIÉ sur Seller Central |
| — champ API listPlacementOptions (2024-03-20) | `placementOptions[].fees[]` et `discounts[]` de type `Incentive` {description, target, type, value: Currency} | S4 : « "fees": { "description": "The fee for the offered option.", "items": { "$ref": "#/components/schemas/Incentive" } } » ; Incentive : « "target": "Possible values: 'Placement Services', 'Fulfillment Fee Discount'." », « "type": "Possible values: `FEE`, `DISCOUNT`." ». Guide : « Each option can include fees or discounts determined by an algorithm during shipment creation, not calculated using set rates. » Opération disponible « Regions NA, EU, FE ». | VÉRIFIÉ |
| Frais de faible stock (Pan-EU Low-Inventory Cost Coverage Fee) | Existe : **FR/DE/IT/ES**, produits taille standard **en Pan-EU** ; si les jours de stock historiques à 90 j **et** à 30 j sont < 28 j. Ex. petit colis ≤ 3,9 kg : 0,46 € (< 14 j), 0,27 € (14-21 j), 0,18 € (21-28 j) ; colis standard ≤ 11,9 kg : 0,67 / 0,35 / 0,21 € ; enveloppe légère ≤ 100 g : 0,27 / 0,18 / 0,16 €. Ne s'applique pas à NL, PL, SE, BE, IE. | S2 p. 10 : « applies to standard-size products fulfilled through the Pan-European FBA (Pan-EU) programme when inventory units are less than 28 days relative to shipped units across Germany, France, Italy and Spain. […] when both the long-term historical days of supply (last 90 days) and short-term historical days of supply (last 30 days) are below 28 days (4 weeks). » Pas de montant lisible pour la ligne « Oversize / Heavy bulky ». | VÉRIFIÉ (Pan-EU seulement ; vendeur FBA local FR non concerné d'après ce texte) |
| Frais de traitement des retours | Existe : produits à **fort taux de retour** (seuil propre à chaque catégorie), toutes catégories **sauf** vêtements, accessoires, chaussures ; FR ex. enveloppe légère ≤ 20 g : 2,60 € ; petit colis ≤ 900 g : 4,11 € ; colis standard ≤ 1,9 kg : 4,42 €. Vêtements/chaussures : **50 % des frais d'expédition** du produit. | S2 p. 25 : « This is for high-return-rate products in all categories, excluding clothing, accessories and footwear. The fee will only apply to products that have return rates above a threshold specific to each category. » ; note 1 : « The Returns Processing Fee is equal to 50% of the total fulfilment fee for a given product in the clothing, accessories and footwear categories. » Seuils par catégorie : sur Seller Central (illisible). | VÉRIFIÉ (tarifs) ; seuils NON VÉRIFIÉS |
| Dimensions et poids, Catalog Items 2022-04-01 | `includedData=dimensions` → `dimensions[]` par `marketplaceId`, avec `item` et `package` {height, length, width, weight : {unit, value}} ; aussi `includedData=attributes` → `item_package_dimensions`, `item_package_weight` (exemples de la doc) | S5 : « "value": "dimensions", "description": "Dimensions of an item in the Amazon catalog." » ; « "Dimensions": { "description": "Dimensions of an Amazon catalog item or item in its packaging." » ; ItemDimensionsByMarketplace : `"item"`, `"package"`. Exemple : « "item_package_weight": [ { "unit": "kilograms", "value": 62.142, … } ] ». | VÉRIFIÉ |
| getMyFeesEstimate : dimensions en entrée ? | **Non** : la requête n'a que MarketplaceId, IsAmazonFulfilled, PriceToEstimateFees (ListingPrice, Shipping, Points), Identifier, OptionalFulfillmentProgram (FBA_CORE, FBA_SNL, FBA_EFN) ; l'API utilise la taille du catalogue | S3 : « these estimates use the item's catalog size, which might not always match the actual size of the item sent to Amazon. » ; « The estimated fees returned by this API are not guaranteed. Actual fees can vary. » (guide Product Fees) | VÉRIFIÉ |

Autres points lus dans S2, utiles au calcul :

- **Haute saison** : des frais d'expédition « peak » s'appliquent du **15/10/2026 au 14/01/2027** (S2 p. 7 : « 2026 Peak fees (October 15, 2026 - Jan 14, 2027) »), retour aux tarifs normaux le 15/01/2027.
- **Poids facturé** : colis et hors gabarit = le plus grand du poids unitaire et du poids volumétrique « (length x width x height cm³) divided by 5000 » (S2 p. 4) ; enveloppes, Low-Price FBA et hors gabarit spécial = poids unitaire.
- **Supplément batteries lithium / dangereux** : « An additional per-unit fee of £0.10, €0.10 […] » (S2 p. 6, note 1).
- **Supplément hors gabarit Pan-EU** (p. 9) : seulement si le pays d'envoi diffère du pays de vente.

## Conséquences pour le calcul

**Calculable de façon fiable (valeurs sourcées, à dater) :**

1. Stockage mensuel : volume emballé (m³) × taux selon taille (standard / hors gabarit), catégorie (vêtements…), dangereux ou non, et mois (janv.–sept. / oct.–déc.). Les 10 taux € de S2 p. 21.
2. Poids facturé (poids volumétrique /5000) et tranche de taille, à partir des dimensions `package` de Catalog Items (`includedData=dimensions`).
3. Frais de retour pour les vêtements/chaussures : 50 % des frais d'expédition.
4. Commission (referral) : S2 p. 27-30 (non détaillée ici).

**Reprendre de l'API plutôt que recalculer :**

5. Frais d'expédition FBA et commission : `getMyFeesEstimateForASIN` (`IsAmazonFulfilled=true`, MarketplaceId `A13V1IB3VIYZZH`). Attention : basé sur la taille du catalogue, pas sur la taille réelle mesurée, et « not guaranteed ».

**À garder en paramètre saisi par l'utilisateur (ou à vérifier) :**

6. **Supplément carburant 2 %** : la doc SP-API ne dit pas s'il est inclus dans l'estimation, et la grille ne dit pas si ses montants l'incluent. Paramètre « supplément carburant inclus dans l'estimation : oui / non / inconnu » (défaut : inconnu, on affiche les deux). Test à faire avec un vrai compte : comparer le `FeeDetail` FBA d'un ASIN connu avec la grille S2 et avec la calculatrice des recettes Amazon.
7. Supplément d'utilisation du stockage (dépend du ratio du compte entier) ; supplément stock ancien (âge du stock).
8. Frais de faible stock : seulement si l'utilisateur est en Pan-EU ; dépend de ses jours de stock → paramètre « Pan-EU oui/non » + jours de stock prévus.
9. Frais de retour hors vêtements : seulement au-delà d'un seuil par catégorie (seuils sur Seller Central, illisibles) → paramètre « taux de retour prévu » et « produit à fort taux de retour oui/non ».
10. Frais de placement à l'envoi : absents de la grille UE ; si l'API `listPlacementOptions` renvoie des `fees`, prendre la valeur réelle de l'envoi (algorithmique, pas de barème) → coût d'envoi saisi ou lu par expédition, jamais calculé.
11. Haute saison (15/10 – 14/01) : appliquer la grille « peak » selon la date de vente prévue.
12. Coûts d'envoi vers l'entrepôt (transporteur partenaire) : saisis.
