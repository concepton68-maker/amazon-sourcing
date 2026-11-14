# Audit de cohérence — Syllig Vente face à la concurrence (parcours complet du revendeur)

*Recherche documentaire du 14/11/2026 (heure de Paris). Sources : sites officiels des éditeurs (pages tarifs, fonctions, centres d'aide), pages officielles Amazon (sell.amazon.*, aboutamazon.com, sellingpartners.aboutamazon.com). Complète, sans les répéter, `2026-11-14-benchmark-fonctions.md` (prix Helium 10, Jungle Scout, SellerAmp, SmartScout, Tactical Arbitrage, frais Amazon 2026) et `2026-11-11-donnees-et-outils-verifies.md`.*

**Règle de lecture**
- **VÉRIFIÉ** : page officielle lue, URL + court extrait.
- **VÉRIFIÉ (extrait)** : vu dans un extrait de résultat de recherche pointant vers une page officielle, page non relue en entier.
- **NON VÉRIFIÉ** : source non officielle, ambiguë ou absente de la page lue. Jamais base d'une conclusion ferme.
- **Analyse** : avis de l'auteur.
- Une fonction « non trouvée » chez un concurrent veut dire « non trouvée sur les pages lues », pas « prouvée absente ».
- Contraintes Syllig prises en compte : sans Keepa pour Sam (D-AMZ-026), aucune aspiration de pages (D-AMZ-027), pas de mise en commun entre comptes et branchement Keepa suspendu (D-AMZ-028).

---

## (a) Tableau étape × concurrents × Syllig Vente

Légende : ● fait (VÉRIFIÉ) · ◐ partiel ou limité (VÉRIFIÉ) · ○ vu seulement en extrait / NON VÉRIFIÉ · — non trouvé sur les pages lues · US = États-Unis seulement (VÉRIFIÉ).

| Étape | H10 | JS | SAS | Keepa | SmartScout | TA / Seller 365 | sellerboard | BuyBotPro | Aura / BQool | InventoryLab | Boxem | Seller Assistant | Amazon gratuit | **Syllig Vente** | **Niveau** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. Éligibilité / ungating | — | — | ● (alerte) | — | — | ● (vérif. CSV) | — | ● (+ ○ « Auto Ungate ») | — | — | ● « Automated Ungating » (US) | ● (20 000 ASIN d'un coup) | ◐ (au cas par cas) | Scan nocturne 16 catégories + alerte « nouvellement autorisé » ; pas d'assistant ungating | **au niveau** (veille : devant ; ungating, vrac : derrière) |
| 2. Trouver des produits (marché, base produits, vitrines, marques) | ● Black Box | ● Product Database | ● Storefront Search | ● Product Finder | ● 500K+ marques | ● 1 400+ sites, Amazon Flips | — | ○ | — | ◐ (Scoutify) | — | ● Seller Spy, Brand Analyzer | ● POE (FR, DE, IT, ES, NL, PL, SE…) | Suivi de marché par catégorie (nos relevés), liste « produits rentables » | **derrière** |
| 3. Fournisseurs & prix fournisseurs | ◐ (commandes fournisseurs) | ● Supplier Database (usines) | — (via ArbiSource) | — | — | ● Wholesale Search 50k–100k lignes | — | — | — | — | ◐ (suivi fournisseurs) | ● Price List Analyzer 150k/mois, base fournisseurs, AI Supplier Finder | — | Fichier fournisseur (mappage mémorisé, lots, contrôle titre), annuaire 20 fournisseurs UE, catalogues, « où acheter », rapprochement nocturne | **devant** (UE) / au niveau (fichier) |
| 4. Analyse du profit (frais, TVA, stockage, prix max, ventes, Buy Box, historique) | ◐ | ○ | ● Max Cost, TVA, UE | ● historique | ● ventes/rang, Buy Box Map | ● TVA par catégorie 5 pays | — (après coup) | ● TVA, PAN-EU, ventes estimées | — | — | — | ● Keepa + calculateur | ● Revenue Calculator, POE | Coût complet (stockage barème UE, carburant, placement, TVA), prix max, verdict ; historique seulement depuis nos relevés, rotation en proxy | **devant** (coût) / **derrière** (ventes, historique, Buy Box) |
| 5. Acheter (bons de commande, échanges fournisseur) | ● « complete supplier orders » | — | — | — | — | — | ● plan des commandes | — | — | — | — | ● PO en un clic, export PDF/XLSX | — | Bons de commande et lots, prévu/réel par lot | **au niveau** |
| 6. Envoyer chez Amazon (FBA, prep, étiquettes) | ● « send inventory to Amazon » | — | — | — | — | ● (InventoryLab, US) | — | — | — | ● étiquettes de cartons (US) | ● (US) | ● FBA Shipments, centres de prep | ● Send to Amazon | Absent | **absent** |
| 7. Vendre (repricing, fiches, multi-pays) | ● Listing Builder | — | ◐ (lien BQool) | — | — | ● SmartRepricer | ◐ PPC | — | ● repricers | ● création fiches FBA/FBM (US) | ◐ (lien repricers) | ● Repricer | ● Automate Pricing gratuit | Absent (repricer, fiches, comparaison UE à l'écran) | **absent** |
| 8. Après-vente (P&L, remboursements, stock, alertes, conformité UE) | ● Refunds 10–15 %, P&L | ◐ | — | ◐ suivi | — | ● remboursements 5–15 %, P&L | ● remboursements, FIFO, alertes | — | — | ● P&L (US) | ◐ | ● P&L, unités manquantes | ● Seller Assistant (US), Profit Analytics, conformité | Tableau de bord, profit réel, FIFO, réassort, cas de remboursement, fiches EPR/GPSR | **au niveau** (P&L, remb.) / **derrière** (alertes Buy Box) |

### Preuves principales par étape (complément des preuves du benchmark du 14/11)

**1. Éligibilité**
- Seller Assistant : « check product and brand restrictions and verify selling eligibility for up to 20,000 products at once » — VÉRIFIÉ ([aide](https://help.sellerassistant.app/en/articles/7050085-what-is-seller-assistant)) ; Pro 29,99 $/mois : « 4k ASINs checks/mo » — VÉRIFIÉ ([tarifs](https://www.sellerassistant.app/pricing)).
- Tactical Arbitrage : « Check whether your Amazon account is eligible to sell specific products or brands, individually or by uploading a CSV » — VÉRIFIÉ ([page](https://www.threecolts.com/seller-365/tactical-arbitrage)).
- Boxem : « Automated Ungating » dans Standard et plus — VÉRIFIÉ ([tarifs](https://www.boxem.com/pricing)) ; « focused on serving the US market » — VÉRIFIÉ ([accueil](https://www.boxem.com/)). Fonctionnement réel de l'« ungating automatique » : NON VÉRIFIÉ.
- BuyBotPro : « Can you sell the item or are you restricted (gated)… » — VÉRIFIÉ ([accueil](https://www.buybotpro.com/)) ; bouton « Auto Ungate » — VÉRIFIÉ (extrait, centre d'aide intercom, page 404 à la relecture).
- SellerAmp : « Eligibility to sell the product » — VÉRIFIÉ ([features](https://selleramp.com/features/)).
- **Alerte « vous êtes désormais autorisé » sur une catégorie, relancée chaque nuit** : non trouvée chez les 14 outils lus. Un outil hors liste (Ecom Circles) annonce un contrôle de marques en arrière-plan — NON VÉRIFIÉ (extrait non officiel).

**2. Trouver des produits**
- SmartScout : « Filter 500K+ brands by criteria » ; « Filter out brands where Amazon is a first-party seller » — VÉRIFIÉ ([wholesale](https://www.smartscout.com/amazon-wholesale-brands-suppliers-fba)). Couverture UK/UE : non mentionnée.
- Seller Assistant : Seller Spy « Track any storefront over time » ; Brand Analyzer « revenue, Buy Box ownership, and Amazon's share across the full brand catalog » — VÉRIFIÉ ([accueil](https://www.sellerassistant.app/)).
- SellerAmp : « see SAS analysis for the products in any seller's storefront » — VÉRIFIÉ ([features](https://selleramp.com/features/)).
- Tactical Arbitrage : « 1,400+ supported retail sites built in » ; Amazon Flips « priced lower than their typical value » — VÉRIFIÉ ([page](https://www.threecolts.com/seller-365/tactical-arbitrage)). Repose sur la lecture de sites tiers : non reproductible chez nous (D-AMZ-027).
- Amazon Product Opportunity Explorer : pays listés dont France, Allemagne, Italie, Espagne, Pays-Bas, Pologne, Suède, Royaume-Uni — VÉRIFIÉ (extrait, [page POE](https://sell.amazon.com/tools/product-opportunity-explorer)).
- **Analyse** : les vitrines et marques chez les concurrents viennent de Keepa ou de bases propres. Chez nous, l'API Amazon ne liste pas le catalogue d'un autre vendeur (benchmark 14/11, déduction NON VÉRIFIÉE par une phrase d'Amazon). L'écart est en partie structurel.

**3. Fournisseurs**
- Tactical Arbitrage Wholesale Search : « up to 50,000 products via CSV or Google Sheets » ; « Wholesale limits are 50k, 50k, and 100k » — VÉRIFIÉ ([page](https://www.threecolts.com/seller-365/tactical-arbitrage)). Le guide : fichier « csv, xls, or xlsx », mappage des colonnes Title/UPC/Price/ASIN — VÉRIFIÉ (extrait, [blog Threecolts](https://www.threecolts.com/blog/tactical-arbitrage-wholesale-search-guide/)).
- Seller Assistant Price List Analyzer : « Upload, ASIN-match, filter by margin and competition » — VÉRIFIÉ ([accueil](https://www.sellerassistant.app/)) ; signale « bundled listings » et « ASIN mismatches » — VÉRIFIÉ ([blog officiel](https://www.sellerassistant.app/blog/from-price-list-to-purchase-order-with-seller-assistant/)) ; Business 79,99 $/mois : « 150k Product scans/mo » — VÉRIFIÉ ([tarifs](https://www.sellerassistant.app/pricing)) ; AI Supplier Finder « find reliable wholesale suppliers by brand name » — VÉRIFIÉ ([aide](https://help.sellerassistant.app/en/articles/7050085-what-is-seller-assistant)).
- Jungle Scout : Supplier Database dès Growth Accelerator (79 $/mois) — VÉRIFIÉ ([tarifs](https://www.junglescout.com/pricing/catalyst-plans/)) ; orientée fabricants (private label) — Analyse.
- SellerAmp : import de liste non trouvé ; passe par ArbiSource — VÉRIFIÉ (extrait, [page intégration](https://selleramp.com/integrations/new-sas-integration-with-arbisource/)).
- **Rapprochement d'un même produit avec TOUS les catalogues fournisseurs importés (« où acheter », profit par fournisseur) relancé chaque nuit** : non trouvé. Le plus proche : Seller Assistant (P&L « by product, brand, and supplier », VÉRIFIÉ) et Tactical Arbitrage Reverse Search (ASIN → sites marchands, lecture de sites tiers).

**4. Analyse du profit**
- SellerAmp : « Maximum Cost (Max Cost) » ; « SAS uses your selected VAT Scheme in all calculations » ; vue « European marketplaces » ; « inbound FBA shipping rates » — VÉRIFIÉ ([features](https://selleramp.com/features/)).
- Tactical Arbitrage : « Localized fees across 13 Amazon marketplaces » ; « Category VAT across 5 European markets » (« 7% vs 19% in Germany ») — VÉRIFIÉ ([page](https://www.threecolts.com/seller-365/tactical-arbitrage)).
- BuyBotPro : « Accounts for VAT not only on Amazon fees but on your buy and sell decisions! » ; « Amazon UK, US, CA, DE, FR, ES & IT Compatible » ; « PAN-EU Fee Calculator » ; « Estimated Sales - now, previously and predicted » ; lit les courbes Keepa — VÉRIFIÉ ([accueil](https://www.buybotpro.com/)). Prix : Basic 24,95 £, Pro 34,95 £, Enterprise 99,95 £ HT/mois — VÉRIFIÉ (même page, qui affiche aussi une ancienne grille : ambigu).
- Seller Assistant : « Keepa and profit calculator in the same panel » — VÉRIFIÉ ([accueil](https://www.sellerassistant.app/)).
- Amazon : Revenue Calculator gratuit ; Revenue Calculator, « Profit Analytics dashboard and Fee and Economics Preview reports have been updated » (surcharge carburant) ; stockage « €27.54 per cubic metre per month » (janv.–sept.), « €52.20 » (oct.–déc.) — VÉRIFIÉ ([sell.amazon.de](https://sell.amazon.de/en/preisgestaltung)).
- **Analyse** : sur le coût complet (stockage au barème UE à partir des dimensions, supplément carburant, placement, prep, transport fournisseur, régimes de TVA), Syllig Vente est au moins au niveau de SellerAmp / BuyBotPro. Aucune page concurrente lue ne détaille stockage + placement dans le prix d'achat max. Sur l'historique, les ventes/mois et la part de Buy Box, tous les outils d'analyse s'appuient sur Keepa ; nous non (D-AMZ-026/028) : écart réel.

**5. Acheter**
- Seller Assistant : « Generate POs in one click directly from your Price List Analyzer shortlist » ; « Export finalized POs in PDF or XLSX format » — VÉRIFIÉ ([blog officiel](https://www.sellerassistant.app/blog/from-price-list-to-purchase-order-with-seller-assistant/)).
- sellerboard : « plan your Purchase Orders in one easy-to-use dashboard » — VÉRIFIÉ ([accueil](https://sellerboard.com/)).
- Helium 10 : « Keep track of inventory, complete supplier orders, and send inventory to Amazon » (40 SKU en Platinum, 500 en Diamond) — VÉRIFIÉ ([tarifs](https://www.helium10.com/pricing/)).
- Envoi du bon au fournisseur par courriel depuis l'outil : non trouvé chez les concurrents.

**6. Envoyer chez Amazon**
- Seller Assistant : « FBA Shipments helps you plan and manage sending inventory to Amazon » ; « Add prep centers and send products to prep from any purchase order » ; « Catch missing units on closed shipments » — VÉRIFIÉ ([aide](https://help.sellerassistant.app/en/articles/7050085-what-is-seller-assistant), [accueil](https://www.sellerassistant.app/)).
- InventoryLab : « Box content labels generated automatically » ; « InventoryLab is currently available for US Amazon sellers » — VÉRIFIÉ ([page](https://www.threecolts.com/seller-365/inventorylab)).
- Boxem : « Follow every shipment from creation to check-in » ; US seulement — VÉRIFIÉ ([accueil](https://www.boxem.com/)).
- Amazon Send to Amazon : flux standard, gratuit hors étiquetage par Amazon (« per-item fee ») — VÉRIFIÉ (extrait, [blog Amazon](https://sell.amazon.com/blog/send-to-amazon-shipment-creation), page ancienne).
- **Analyse** : en Europe, l'offre est mince (InventoryLab et Boxem US seulement). Seller Assistant est le seul vérifié à relier bon de commande → prep → envoi, sans confirmation sur les pays UE.

**7. Vendre**
- Amazon Automate Pricing : « included for free in the Professional selling plan » ; « Compare against the Featured Offer, lowest price, or lowest external price » ; prix minimum et maximum ; règles liées entre pays — VÉRIFIÉ ([page](https://sell.amazon.com/tools/automate-pricing)).
- Aura : de 37 $ (Starter, 2 marketplaces, CA ≤ 15 K$) à 237 $/mois (Pro) ; « Includes Amazon & Walmart » ; pays UE non mentionnés — VÉRIFIÉ ([tarifs](https://goaura.com/pricing)).
- BQool : AI Repricing dès 25 $/mois ; UK/UE non mentionnés — VÉRIFIÉ ([accueil](https://www.bqool.com/)).
- Seller Assistant : « Automated repricing with strategies, rules, and safety limits » ; 250 produits en Business — VÉRIFIÉ.
- Threecolts SmartRepricer : « keep the Buy Box » ; inclus dans Seller 365 (69–199 $) — VÉRIFIÉ ([Seller 365](https://www.threecolts.com/seller-365)).
- **Analyse** : le repricer gratuit d'Amazon couvre l'essentiel d'un revendeur. Notre manque n'est pas le moteur mais le **prix plancher calculé** (coût complet) à y reporter.

**8. Après-vente**
- sellerboard : « Get reimbursed for lost and damaged inventory » ; « identify cases where Amazon reimbursed less than your product's cost of goods sold (COGS) » ; « Stay informed about listing changes, new sellers and loss of Buy Box, fees modifications » ; 19 / 29 / 39 / 79 $ par mois — VÉRIFIÉ ([accueil](https://sellerboard.com/)).
- Seller 365 Reimbursements : « audited and filed automatically », commission 15 % (5 % en Pro) — VÉRIFIÉ ([Seller 365](https://www.threecolts.com/seller-365)).
- Helium 10 : remboursements gérés, commission de 10 à 15 % selon le plan — VÉRIFIÉ ([tarifs](https://www.helium10.com/pricing/)).
- Amazon Seller Assistant (IA, gratuit) : « currently available to all sellers in the U.S. store » ; surveille stock, réassort, conformité (« missing certifications ») — VÉRIFIÉ ([aboutamazon.com, 17/09/2025](https://www.aboutamazon.com/news/innovation-at-amazon/seller-assistant-agentic-ai)). Accelerate 2026 : « pricing adjustments that run in the background » ; plugin vers « Anthropic's Claude and Amazon's own Quick in the U.S. » — VÉRIFIÉ ([récapitulatif](https://sellingpartners.aboutamazon.com/accelerate-2026-recap)). Disponibilité en France à ce jour : NON VÉRIFIÉ.
- Conformité UE chez Amazon : numéro EPR à saisir sur la page « Compliance Information for Extended Producer Responsibility » ; France « 19 different categories » — VÉRIFIÉ ([sell.amazon.fr](https://sell.amazon.fr/en/conformite-a-la-responsabilite-elargie-des-producteurs)) ; tableau « Manage your compliance » pour GPSR — VÉRIFIÉ (extrait, forums officiels Seller Central Europe).
- Conformité GPSR/EPR chez les 13 concurrents tiers : non trouvée sur leurs pages. Helium 10 en parle dans un podcast (nov. 2025) — NON VÉRIFIÉ.

---

## (b) Écarts classés par impact pour un revendeur grossiste / arbitrage UE

Classement = **Analyse** (impact sur « acheter juste ce qui se vend, au bon prix »).

| # | Écart | Impact | Qui le fait le mieux (preuve) | Faisable chez nous sans Keepa ni aspiration ? |
|---|---|---|---|---|
| 1 | **Ventes/mois et historique (prix, BSR, nombre d'offres)** : nous n'avons que nos relevés depuis le démarrage + rotation en proxy | Très fort : risque d'acheter sur un prix gonflé ou un produit lent | Keepa (`monthlySold`, `salesRankDrops`, VÉRIFIÉ benchmark) ; SellerAmp, BuyBotPro, Seller Assistant s'y adossent (VÉRIFIÉ ci-dessus) | Partiellement : nos relevés nocturnes (baisses de BSR comptées, stabilité de prix) sur les ASIN suivis ; ventes réelles du vendeur. Écart structurel sur l'historique ancien |
| 2 | **Buy Box : part, rotation, présence d'Amazon dans le temps** | Très fort | Keepa (`buyBoxStats`), SmartScout Buy Box Map, Seller Assistant Brand Analyzer (VÉRIFIÉ) | Partiellement : instantanés SP-API relevés chaque nuit (Amazon présent / absent, nombre d'offres éligibles) → taux sur 30 j à partir de nos relevés |
| 3 | **Repricing** (absent) | Fort : marge perdue après l'achat | SmartRepricer, Aura, BQool, Seller Assistant ; **Amazon Automate Pricing gratuit** (VÉRIFIÉ) | Oui, à moindre coût : calculer et pousser le prix plancher (coût complet + marge mini) vers les règles Amazon, plutôt qu'écrire un moteur |
| 4 | **Comparaison multi-pays UE à l'écran** (calcul déjà par pays) | Fort pour un vendeur Pan-EU / EFN | Tactical Arbitrage (13 marketplaces, TVA par catégorie dans 5 pays), SellerAmp (vue « European marketplaces »), BuyBotPro (PAN-EU) — VÉRIFIÉ | Oui (SP-API par marketplace) ; nous pouvons couvrir NL, BE, PL, SE, IE |
| 5 | **Création d'envoi FBA + étiquettes + prep** | Fort en temps passé, faible sur la décision d'achat | Seller Assistant (PO → prep → FBA, VÉRIFIÉ) ; InventoryLab et Boxem US seulement | Oui (API Inbound 2024-03-20, VÉRIFIÉE dans le benchmark) ; lot important |
| 6 | **Découverte par marque / vitrine** (pistes grossiste) | Moyen à fort | SmartScout (500K+ marques), Seller Assistant (Seller Spy, Brand Analyzer), SellerAmp Storefront — VÉRIFIÉ | Faiblement : pas de liste du catalogue d'un autre vendeur en SP-API (déduction) ; possible : explorer les marques des produits les mieux classés de nos relevés par catégorie |
| 7 | **Vérification d'éligibilité en masse sur une liste d'ASIN** (fichier) + aide à l'ungating | Moyen | Seller Assistant (20 000 ASIN), Tactical Arbitrage (CSV), Boxem « Automated Ungating » (US) — VÉRIFIÉ | Oui pour la vérification (Listings Restrictions) ; ungating = guide + lien Amazon, pas d'automatisme sourcé |
| 8 | **Alertes sur produits en stock** : perte de Buy Box, nouveau vendeur, Amazon revient, prix sous le plancher | Moyen | sellerboard, Helium 10 (VÉRIFIÉ) | Oui (relevés nocturnes ; notifications SP-API à vérifier) |
| 9 | **Extension navigateur / scanner mobile** | Moyen (arbitrage), faible (grossiste) | SellerAmp (extension + mobile Android/iOS), Seller Assistant, BuyBotPro, Scoutify — VÉRIFIÉ | Oui, extension affichant notre analyse API (prévue par D-AMZ-027) |
| 10 | **Bon de commande exporté / envoyé au fournisseur** | Faible à moyen | Seller Assistant (PDF/XLSX, VÉRIFIÉ) | Oui ; envoi par courriel possible dans l'esprit de D315 (Syllig) |
| 11 | Assistant IA | Faible pour l'instant | Amazon Seller Assistant (US, gratuit), Helium 10 (Helium Agent, MCP), Seller Assistant (MCP) — VÉRIFIÉ | Hors priorité ; minimisation D-AMZ-008 |
| 12 | Création de fiches, PPC | Faible pour un revendeur | Helium 10, InventoryLab (US), sellerboard (PPC) | Non prioritaire |

---

## (c) Ce que nous faisons et que personne ne montre (absence vérifiée au mieux)

| Point Syllig Vente | Recherche d'absence | Statut |
|---|---|---|
| **Veille nocturne d'éligibilité sur 16 catégories avec alerte « nouvellement autorisé »** | Non trouvée chez les 14 outils (pages tarifs, fonctions, aide lues). Les concurrents vérifient à la demande (SellerAmp, BuyBotPro) ou en masse sur une liste (Seller Assistant, TA). Outil hors liste (Ecom Circles) : contrôle de marques en arrière-plan, NON VÉRIFIÉ | Probable exclusivité dans le panel, **non prouvable** (absence ≠ preuve) |
| **« Où acheter » : un ASIN rapproché de tous les catalogues fournisseurs importés, profit par fournisseur, relancé chaque nuit** | Seller Assistant analyse une liste à la fois et ventile le P&L par fournisseur ; TA Reverse Search cherche chez des détaillants (sites tiers). Aucune page lue ne décrit la comparaison de plusieurs catalogues fournisseurs pour un même ASIN | Non trouvé ailleurs ; **non vérifiable** pour Seller Assistant (fonctions internes non documentées publiquement) |
| **Profit prévu vs réel par lot d'achat (FIFO)** | sellerboard : COGS par lot et FIFO (après coup) ; Seller Assistant : coût des bons dans le P&L. La comparaison « prévu à l'achat / réalisé » n'est décrite nulle part | Non trouvé (confirme l'étude du 11/11) |
| **Coût complet avant achat : stockage calculé sur les dimensions × barème UE officiel, supplément carburant réglable, placement, prep, transport fournisseur, régimes de TVA → prix d'achat max** | SellerAmp : TVA, transport entrant, Max Cost ; BuyBotPro : TVA, PAN-EU ; TA : TVA par catégorie. Stockage au barème et placement dans le prix max : non décrits | Plus complet que ce qui est publié ; **non vérifiable** pour SellerAmp/BuyBotPro (calcul interne) |
| **Annuaire de fournisseurs UE étudiés pour la revente Amazon (conditions de revente)** | Jungle Scout : base d'usines ; Seller Assistant : AI Supplier Finder (contacts par marque). Aucune ne publie des conditions de revente Amazon étudiées | Différent par nature (sélection manuelle, 20 entrées) ; pas une exclusivité technique |
| **Fiches de conformité UE (numéros EPR, fiche GPSR) dans l'outil de sourcing** | Non trouvé chez les 13 tiers ; Amazon le gère dans Seller Central et son Seller Assistant signale les certificats manquants (US) | Non trouvé chez les tiers ; Amazon couvre une partie |
| **Fichier fournisseur : détection des lots et contrôle de correspondance des titres** | Seller Assistant signale « bundled listings » et « ASIN mismatches » (VÉRIFIÉ) | **Pas une exclusivité** |
| Sans Keepa, sans aspiration, sans mise en commun | Tous les outils d'analyse lus s'appuient sur Keepa ou des bases propres | Choix de conformité, pas une fonction ; argument de confiance (Analyse) |

---

## (d) Cinq priorités recommandées (Analyse)

Respectent D-AMZ-026/027/028 (sans Keepa, sans aspiration, sans mise en commun). Chaque fonction commence par sa ligne dans `docs/regles/registre.md`.

1. **Demande et Buy Box à partir de nos relevés** (écarts 1 et 2) : compter les baisses de BSR et la stabilité du prix sur 30/90 j, taux de présence d'Amazon et nombre d'offres éligibles relevés chaque nuit, affichés avec leur profondeur réelle (« 23 jours de relevés ») ; verdict prudent quand l'historique est court. C'est le plus gros risque d'achat restant.
2. **Prix plancher vers le repricer gratuit d'Amazon** (écart 3) : à partir du coût complet déjà calculé, exporter ou pousser le prix minimum (et maximum) par SKU vers Automate Pricing ; alerte quand le prix de vente passe sous le plancher (écart 8). Coût faible, gain de marge direct ; pas de moteur à écrire.
3. **Vue multi-pays UE dans l'écran d'analyse et la liste rentable** (écart 4) : même EAN sur FR, DE, IT, ES, NL, BE, PL, SE, IE ; meilleur pays, frais et TVA du pays, Pan-EU ou EFN. Le calcul existe déjà ; c'est surtout de l'affichage. Dépasse SellerAmp et TA sur le nombre de pays (Analyse).
4. **Vérification d'éligibilité en masse sur un fichier d'ASIN/EAN, et aide à l'ungating** (écart 7) : prolonge le scan nocturne (notre avance) aux marques et aux listes fournisseurs ; l'aide à l'ungating reste un guide + lien vers la demande Amazon tant qu'aucun automatisme n'est sourcé.
5. **Bon de commande → envoi FBA** (écarts 5 et 10) : export PDF/XLSX ou envoi par courriel du bon au fournisseur, puis création de l'envoi via l'API Inbound 2024-03-20 (placement réel repris dans le profit prévu du lot). Peu d'offres sur ce point en Europe (InventoryLab, Boxem : US seulement).

Ensuite : extension navigateur affichant notre analyse (D-AMZ-027), découverte par marque à partir des relevés par catégorie.

---

## Annexe — Non vérifié ou ambigu

- Keepa Pro 29 €/mois : vu en extrait d'une page communautaire keepa.com, page tarifs illisible — VÉRIFIÉ (extrait).
- SmartScout : prix contradictoires sur la page wholesale (« Plans start at $25/month (billed annually) » contre « starting at $29/mo »).
- BuyBotPro : deux grilles de prix affichées ; « Auto Ungate » vu en extrait seulement.
- Boxem : FAQ « starts at $42/mo » contre 23 $ affiché sur la grille.
- InventoryLab : prix doubles (58 $ / 69 $) dans la page, ancien et nouveau non libellés.
- Tactical Arbitrage : prix doubles affichés (ancien / nouveau) ; nombre de marketplaces 12 ou 13 selon la page.
- Seller Assistant : pays UE pris en charge non listés ; création d'envoi FBA détaillée non décrite.
- Aura, BQool, SmartScout : prise en charge des marketplaces UE non mentionnée sur les pages lues.
- Amazon Seller Assistant (IA) : disponibilité en France / UE en novembre 2026 non confirmée.
- Amazon Revenue Calculator : inclut-il le stockage mensuel ? non relu sur la page de l'outil (page FR en 404).
- Conformité GPSR/EPR chez les concurrents : absence seulement constatée sur les pages lues.
