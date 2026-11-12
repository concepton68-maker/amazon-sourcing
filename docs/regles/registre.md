# Registre des règles métier — lot 1 : analyse d'achat et lots

Statut de source : **lu** (texte lu, lien et date) · **non lu** (à lire, jamais bloquant) · **métier** (choix de l'outil, pas une obligation).
État : **codé** · **à coder**. Chaque règle codée est citée par un test `[RM-AMZ-nnn]`.

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-001 | **Prix de vente retenu**, dans cet ordre : prix saisi par l'utilisateur ; sinon Buy Box actuelle (API Amazon) ; sinon offre FBA la plus basse (API Amazon) ; sinon moyenne 90 j (Keepa). Aucun prix disponible : rentabilité non calculée, jamais devinée. | Choix de l'outil | métier | — | `test_prix_retenu` | codé |
| RM-AMZ-002 | **Régime de TVA** par pays de vente : *assujetti* (TVA collectée reversée ; TVA sur achat et sur frais Amazon récupérée), *non assujetti* (aucune TVA collectée ni récupérée ; TVA payée = coût), *hors taxe* (places à prix affichés HT : US, CA). | Directive 2006/112/CE (droit à déduction, art. 168) | non lu | avertissement | `test_assujetti_fr`, `test_non_assujetti`, `test_us_sans_tva` | codé |
| RM-AMZ-003 | **Taux de TVA** : taux standard du pays par défaut, toujours modifiable par produit (taux réduits). | Taux officiels par pays (Commission européenne) | non lu | avertissement | `test_taux_reduit` | codé |
| RM-AMZ-004 | **Frais Amazon** : estimation de l'API Amazon (`getMyFeesEstimate`), supposée hors TVA. Sans API : commission 15 % et FBA à 0, marqués « non confirmés » ; l'analyse ne peut alors pas donner ACHETER. | Référence API Product Fees ; hypothèse HT à vérifier sur un relevé de paiement | lu (API) / non lu (HT) | — | `test_frais`, `test_sans_sources_ne_dit_jamais_acheter` | codé |
| RM-AMZ-005 | **Profit net** = prix de vente HT − coût d'achat net − frais Amazon − TVA non récupérable sur frais − autres coûts (envoi, préparation, stockage, provision retours). **ROI** = profit / coût d'achat net. **Marge** = profit / prix de vente affiché. | Choix de l'outil | métier | — | `test_assujetti_fr`, `test_autres_couts_et_retours` | codé |
| RM-AMZ-006 | **Prix d'achat maximum** pour atteindre le ROI cible, exprimé dans la même base (HT ou TTC) que la saisie. | Choix de l'outil | métier | — | `test_assujetti_fr`, `test_assujetti_achat_ttc` | codé |
| RM-AMZ-007 | **Scénario prudent** : si la moyenne 90 j est inférieure de plus de 2 % au prix retenu, la rentabilité est recalculée à ce prix et affichée à côté. | Choix de l'outil | métier | — | `test_scenario_prudent` | codé |
| RM-AMZ-008 | **Verdict** : PASSER si vente non autorisée sur le compte ou profit ≤ 0 ; ACHETER seulement si toutes les données sont vérifiées, les seuils atteints et aucune alerte ; sinon À VÉRIFIER. Une donnée manquante n'est jamais remplacée par une supposition. | Choix de l'outil | métier | — | `test_bon_produit`, `test_produit_restreint`, `test_sans_sources_ne_dit_jamais_acheter` | codé |
| RM-AMZ-009 | **Alertes** : Amazon détient la Buy Box ; Amazon en stock > 50 % du temps sur 90 j ; prix actuel > moyenne 90 j + 20 % ; listing en lot (> 1 unité) ; écart min/max sur 90 j > 40 %. Seuils réglables. | Choix de l'outil | métier | avertissement | `test_alertes` | codé |
| RM-AMZ-010 | **Ventes** : « achetés le mois dernier » (Keepa `monthlySold`) = relevé du badge Amazon, affiché comme observé ; la part « pour vous » (partage égal entre vendeurs FBA) est affichée comme **estimation**. | Doc Keepa : « It is not an estimate » (lu le 11/11/2026) | lu | — | `test_historique` | codé |
| RM-AMZ-011 | **Lot** : à la création d'un achat, la prévision est figée (prix, frais, coût, ROI prévus, date, sources des données). Une prévision ne se modifie jamais ; une correction crée une nouvelle version. | Choix de l'outil | métier | — | `test_lot_fige`, `test_prevision_depuis_analyse`, `test_base_refuse_modification_de_lot` | codé |
| RM-AMZ-012 | **Rattachement des ventes** aux lots par produit et place de marché, premier entré premier sorti. Profit réel du lot = ventes encaissées − frais réellement prélevés − coût du lot. | Choix de l'outil (méthode du premier entré premier sorti). Source des ventes réelles : API financière Amazon, **à étudier** | métier / non lu | — | `test_fifo`, `test_fifo_ignore_versions_remplacees` | codé |
| RM-AMZ-013 | **Écart prévu / réel** décomposé en causes : prix de vente, frais Amazon, retours, stockage, autres. La somme des causes égale l'écart total. | Choix de l'outil | métier | — | `test_decomposition_ecart` | codé |
| RM-AMZ-014 | **Isolation des données** : toute donnée appartient à un compte ; aucune donnée d'un vendeur n'est utilisée pour un autre ; suppression sous 30 jours après retrait de l'autorisation Amazon. | Politique d'usage SP-API 4.4, 4.6 ; politique de protection des données (lues le 11/11/2026) | lu | bloquant | `test_isolation_comptes`, `test_isolation_lecture_ecriture`, `test_purge_apres_revocation`, `test_base_refuse_acces_croise_meme_sans_le_code` | codé |
| RM-AMZ-015 | **Devises** : chaque montant est stocké avec sa devise ; aucune conversion implicite ; une conversion utilise un taux daté dont la source est enregistrée. | Choix de l'outil ; source de taux à choisir | métier | — | `test_conversion_datee` | codé |

## Lot 2 : ventes et frais réels (API financière Amazon)

Source commune : notes `docs/recherches/notes/api-financiere/finances_spapi.md` (documentation SP-API lue le 12/11/2026).

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-016 | **Source des ventes et frais réels** : API Finances v2024-06-19, opération `listTransactions` (la v0 est dépréciée et supprimée le 27/08/2027). Aucune autre source ne remplace un montant Amazon. | Notes § 1 (« Current » / « Legacy ») | lu | — | `test_normalisation_transaction` | codé |
| RM-AMZ-017 | **Synchronisation rejouable** : clé unique = identifiant de transaction Amazon + rang de l'article. Rejouer la même transaction met à jour la ligne, ne la double jamais. | `transactionId` « The unique identifier of the transaction » ; stabilité du rang **non vérifiée** | lu / non lu | — | `test_sync_rejouable`, `test_aller_retour_lot_et_fifo` | codé |
| RM-AMZ-018 | **Fenêtre de synchronisation** : chaque nuit, de (dernière synchro − 7 jours) à (maintenant − 5 minutes), jamais plus de 180 jours d'un coup ; toutes les pages lues jusqu'à la fin, même après une page vide. | Délai de 48 h, borne > 2 min, 180 jours, pages vides possibles (notes § 3) | lu | — | `test_fenetre_sync` | codé |
| RM-AMZ-019 | **Ajustements tardifs** (remboursement client, rétrofacturation, ajustement) : ajoutés comme nouvelles lignes, jamais en écrasant la vente ; rattachés au(x) lot(s) qui ont reçu la vente de la même commande, au prorata des unités. Sans vente d'origine connue : signalés « non rattachés ». | Remboursements « days, weeks, or even months later » (notes § 3) ; rattachement : métier | lu / métier | — | `test_ajustement_rattache_a_la_commande` | codé |
| RM-AMZ-020 | **TVA dans les montants Amazon (UE)** : la doc ne dit pas si les montants sont TTC. Si une ventilation de taxe est présente, elle est retirée du chiffre d'affaires ; sinon le montant est pris tel quel et la ligne est marquée « TVA non séparée » (avertissement). À confirmer sur le premier relevé réel. | Non précisé par la doc Finances (notes § 9) | non lu | avertissement | `test_tva_separee_ou_signalee` | codé |
| RM-AMZ-021 | **Types de frais** : la liste des `breakdownType` n'est pas publiée. Classement par une table modifiable (vente, taxe, frais Amazon, retours, stockage, autres) ; un type inconnu est compté en « autres » **et** signalé, jamais ignoré. Seules les ventilations finales (sans sous-ventilation) sont additionnées. | « open-ended string… handle unknown values » (notes § 2) ; noms des types **non vérifiés** | lu / non lu | avertissement | `test_types_inconnus_signales`, `test_pas_de_double_comptage` | codé |
| RM-AMZ-022 | **Aucune donnée personnelle d'acheteur** : ni rôle restreint, ni `BUYER`/`RECIPIENT`, ni rapport contenant des données d'acheteurs. Seuls les identifiants de commande sont conservés. | Notes § 5–6 | lu | bloquant | `test_aucune_donnee_acheteur` | codé |
| RM-AMZ-023 | **Montants différés** (`DEFERRED`) : comptés dans le profit du lot mais affichés à part comme « à encaisser » jusqu'à leur libération. | Statuts `DEFERRED`, `RELEASED`, `DEFERRED_RELEASED` (notes § 2) ; affichage : métier | lu / métier | — | `test_montant_differe` | codé |

## Lot 3 : écran « Achats & lots »

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-024 | **Statut d'un lot** : *en vente* tant que des unités restent ; *écoulé* quand toutes les unités sont rattachées à des ventes. Aucun autre statut n'est déduit. | Choix de l'outil | métier | — | `test_api_statut_lot` | codé |
| RM-AMZ-025 | **Base de comparaison** : prévu et réel sont comparés sur les **unités vendues** (même quantité des deux côtés) ; le profit prévu du lot entier est affiché à part. | Choix de l'outil | métier | — | `test_api_detail_lot`, `test_api_lot_autre_compte_introuvable` | codé |
| RM-AMZ-026 | **Écran sans texte en dur** : l'API renvoie des codes (`statut`, `cause`) et des montants avec leur devise ; l'interface les traduit (fichier `fr.json`) et formate selon la langue. | D-AMZ-010 | métier | — | `test_api_codes_sans_texte` | codé |

## Lot 4 : écran « Analyse produit »

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-027 | **Messages codés** : raisons, alertes, données non vérifiées et hypothèses de calcul sont des codes avec paramètres (ex. `ROI_SOUS_SEUIL {roi, seuil}`), jamais des phrases ; le verdict se décide sur ces codes. | D-AMZ-010 | métier | — | `test_messages_codes`, `test_verdict_sur_codes` | codé |
| RM-AMZ-028 | **Analyse par l'interface** : code produit (ASIN, EAN, UPC, ISBN), place de marché, prix d'achat (HT ou TTC), régime de TVA, taux réduit éventuel ; seuils et coûts par défaut du compte. Un code qui donne plusieurs ASIN renvoie une analyse par ASIN. Code introuvable : réponse « introuvable », jamais une analyse inventée. | RM-AMZ-001 à 010 | métier | — | `test_api_analyse`, `test_api_analyse_introuvable` | codé |
| RM-AMZ-029 | **Créer un lot depuis une analyse** : la prévision du lot est celle de l'analyse au moment du clic (prix, frais, coûts, ROI, sources), figée ; quantité > 0 obligatoire ; analyse sans rentabilité calculée : création refusée ; **une analyse crée un seul lot** (un double clic ne crée pas de doublon). | RM-AMZ-011 | métier | — | `test_api_creer_lot_depuis_analyse` | codé |

## Lot 5 : écran « Sourcing fichier fournisseur »

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-030 | **Import** : fichier CSV (séparateur `;`, `,` ou tabulation ; UTF-8 ou Windows-1252) ou Excel `.xlsx`, première ligne = en-têtes, 20 000 lignes au plus, 10 Mo au plus. Le fichier reste sur le serveur du compte ; il n'est jamais envoyé à un moteur IA. | Choix de l'outil ; D-AMZ-008 | métier | bloquant (format) | `test_lecture_csv_et_xlsx`, `test_limites_fichier` | codé |
| RM-AMZ-031 | **Colonnes** : proposées d'après les en-têtes (liste de synonymes : EAN, GTIN, code-barres, UPC, ASIN ; prix, PU HT, tarif, cost ; désignation ; colisage ; minimum de commande). Code et prix obligatoires ; la proposition est toujours modifiable ; rien n'est deviné quand deux colonnes concourent : la colonne reste à choisir. | Choix de l'outil | métier | — | `test_proposition_colonnes` | codé |
| RM-AMZ-032 | **Lignes** : prix lu au format français ou anglais (`1 234,56 €`, `1,234.56`) ; prix absent, nul ou négatif → ligne rejetée avec son motif ; code EAN/UPC dont la clé de contrôle est fausse → **avertissement**, la ligne est quand même cherchée ; code en double → première ligne gardée, doublons signalés. | Clé de contrôle : spécifications générales GS1 (**non lu**) | métier / non lu | avertissement | `test_lignes_prix_et_cles` | codé |
| RM-AMZ-033 | **Prix par carton** : option explicite ; si cochée, prix unitaire = prix ÷ colisage (colisage absent ou nul → ligne rejetée). **Listing Amazon en lot de k unités** : coût d'achat = k × prix unitaire, signalé sur la ligne. | Choix de l'outil | métier | — | `test_prix_carton_et_lot_amazon` | codé |
| RM-AMZ-034 | **Mémoire des appariements** : code fournisseur → ASIN mémorisé par compte et place de marché, réutilisé au fichier suivant ; rafraîchi s'il date de plus de 30 jours ; jamais partagé entre comptes. | Choix de l'outil ; RM-AMZ-014 | métier | — | `test_memoire_appariements`, `test_appariements_par_compte` | codé |
| RM-AMZ-035 | **Traitement** : en tâche de fond, ligne par ligne, avec progression ; résultats triés par verdict (ACHETER, À VÉRIFIER, PASSER) puis ROI décroissant ; produits introuvables et lignes rejetées listés à part ; export CSV des résultats. | Choix de l'outil | métier | — | `test_traitement_complet`, `test_export_csv` | codé |

## Lot 6 : connexion des utilisateurs

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-036 | **Mot de passe** : 12 caractères au moins ; stocké uniquement sous forme d'empreinte Argon2id (bibliothèque `argon2-cffi`, réglages par défaut) ; jamais journalisé ni renvoyé. | RFC 9106 (Argon2) ; recommandations OWASP sur le stockage des mots de passe — **non lus dans cette session**, réglages à vérifier | non lu | bloquant (sécurité) | `test_mot_de_passe_empreinte`, `test_authentification_postgres` | codé |
| RM-AMZ-037 | **Connexion** : courriel + mot de passe ; même réponse « identifiants invalides » que le courriel existe ou non ; après 5 échecs, connexion refusée 15 minutes pour ce courriel. | Choix de l'outil (seuils réglables) | métier | bloquant | `test_connexion_et_blocage` | codé |
| RM-AMZ-038 | **Session** : jeton aléatoire de 256 bits dans un cookie `HttpOnly`, `SameSite=Lax`, `Secure` hors développement, **sans attribut Domain** (jamais partagé avec `syllig.com`) ; seule son empreinte SHA-256 est conservée ; expire après 12 h d'inactivité et 30 jours au plus ; déconnexion = suppression. | Choix de l'outil ; D-AMZ-015 | métier | bloquant | `test_session_cookie_et_expiration` | codé |
| RM-AMZ-039 | **Accès aux données** : hors mode démo, toute route `/api/*` (sauf connexion) exige une session ; le compte vendeur vient **de la session**, jamais de la requête ; une analyse ou un traitement d'un autre compte répond « introuvable ». | RM-AMZ-014 | métier | bloquant | `test_routes_protegees`, `test_jetons_par_compte` | codé |
| RM-AMZ-040 | **Requêtes qui modifient** (POST, DELETE), hors mode démo : refusées sans l'en-tête `X-Syllig-Vente` (protection contre les requêtes intersites). | Choix de l'outil | métier | bloquant | `test_entete_anti_csrf` | codé |
| RM-AMZ-041 | **Création d'utilisateur** : par la ligne de commande seulement, sur le serveur (pas d'inscription publique tant que l'outil n'est pas commercialisé). | D-AMZ-001 | métier | — | `test_creer_utilisateur_cli` | codé |

## Lot 8 : paramètres du compte

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-042 | **Paramètres du compte** : seuils d'achat (ROI minimum 0 à 1 000 %, profit minimum 0 à 1 000, ventes minimales 0 à 100 000/mois, part de ventes minimale, écart maximal prix/moyenne 0 à 500 %), coûts par défaut par unité (envoi, préparation, stockage : 0 à 1 000 ; provision retours 0 à 100 %), régime de TVA par place de marché (assujetti / non assujetti ; places à prix HT toujours « hors taxe »). Valeur hors bornes : refusée avec son champ. Sans réglage : valeurs par défaut de l'outil. | Choix de l'outil | métier | bloquant (bornes) | `test_parametres_bornes_et_defauts` | codé |
| RM-AMZ-043 | **Historique** : chaque enregistrement crée une nouvelle version (date, contenu) ; aucune version n'est modifiée ni effacée (hors purge du compte). | Choix de l'outil | métier | — | `test_parametres_versions`, `test_parametres_par_compte_et_versions` | codé |
| RM-AMZ-044 | **Application** : l'analyse et le sourcing utilisent les paramètres en vigueur au lancement (seuils, coûts par défaut, régime de TVA de la place choisie) ; une valeur saisie dans le formulaire prime pour cette analyse seulement. | Choix de l'outil | métier | — | `test_parametres_appliques_a_l_analyse` | codé |

> Limite connue (lot 8) : les taxes du Brésil ne sont pas modélisées ; la place y est traitée comme « hors taxe » — **non sourcé**, à corriger avant toute vente sur amazon.com.br.

## Lot 9 : stock et réapprovisionnement

Source : notes `docs/recherches/notes/stock/stock_spapi.md` (documentation SP-API lue le 12/11/2026).

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-045 | **Stock** : photo complète chaque nuit par place de marché via `getInventorySummaries` (`details=true`, sans `startDateTime`) : disponible = `fulfillableQuantity` ; en route = préparation + expédié + réception ; réservé ; invendable. Une photo par compte, place, SKU et jour ; relancer la même nuit remplace la photo. Les places UE ne sont **jamais additionnées** (stock Pan-UE possiblement compté plusieurs fois : non vérifié). | Notes § 1 ; Pan-UE : **non vérifié** | lu / non lu | — | `test_inventaire_parse_et_photo`, `test_synchro_stock_pages`, `test_photo_stock_par_compte` | codé |
| RM-AMZ-046 | **Vitesse de vente** = unités vendues sur les 30 derniers jours (ventes réelles synchronisées, par ASIN et place) ÷ 30. **Couverture** = (disponible + en route) ÷ vitesse, en jours ; vitesse nulle : couverture illimitée, pas de rupture prévue. | Choix de l'outil | métier | — | `test_vitesse_et_couverture` | codé |
| RM-AMZ-047 | **Quantité à commander** = max(0, arrondi supérieur de vitesse × (délai fournisseur + délai de réception Amazon + marge de sécurité) − disponible − en route). Délais réglables dans les paramètres (défauts : 7, 10 et 14 jours, choix de l'outil). | Choix de l'outil | métier | — | `test_quantite_a_commander` | codé |
| RM-AMZ-048 | **Alertes** : rupture si couverture < seuil (défaut 15 jours) ; surstock si couverture > seuil (défaut 180 jours). Commandes suggérées regroupées par fournisseur (fournisseur et coût du dernier lot du produit). | Choix de l'outil | métier | avertissement | `test_alertes_stock_et_commandes` | codé |

## Lot 10 : fournisseurs et bons de commande

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-049 | **Fournisseur** : nom obligatoire et unique dans le compte (sans tenir compte des majuscules), devise d'achat, délai habituel en jours (0 à 365), courriel de commande facultatif. Rien d'autre n'est demandé (minimisation : RGPD art. 5 §1 c, **non lu dans cette session**). | Choix de l'outil ; RGPD non lu | métier / non lu | bloquant (nom) | `test_fournisseur_regles` | codé |
| RM-AMZ-050 | **Bon de commande** : numéro `BC-0001`, `BC-0002`… par compte ; statuts BROUILLON → ENVOYÉ → REÇU, ou ANNULÉ depuis BROUILLON ou ENVOYÉ ; lignes modifiables seulement en BROUILLON ; pas d'envoi sans ligne ; toute autre transition refusée. Ligne : produit, place, quantité > 0, prix unitaire HT > 0 dans la devise du fournisseur, prévision figée à l'ajout de la ligne (celle d'une analyse, ou celle du dernier lot du produit au nouveau prix). | Choix de l'outil | métier | bloquant | `test_bon_cycle_de_vie`, `test_bon_lignes` | codé |
| RM-AMZ-051 | **Réception** : une seule fois ; quantité reçue par ligne de 0 à la quantité commandée ; chaque ligne reçue (> 0) devient un **lot** (RM-AMZ-011) : quantité reçue, date de réception, fournisseur et prévision de la ligne, lien vers le bon. | RM-AMZ-011 | métier | bloquant | `test_reception_cree_les_lots`, `test_parcours_api`, `test_achats_par_compte` | codé |
| RM-AMZ-052 | **Bilan fournisseur** : nombre de lots, montant acheté sur 12 mois, ROI prévu et ROI réel pondérés par le coût (lots ayant des ventes), délai réel moyen (envoi → réception). Sans données : « — », jamais une valeur supposée. | Choix de l'outil | métier | — | `test_bilan_fournisseur` | codé |
| RM-AMZ-053 | **Depuis le stock** : une commande suggérée (RM-AMZ-048) crée un bon BROUILLON pour ce fournisseur, une ligne par produit à commander, au coût et avec la prévision du dernier lot. | RM-AMZ-048 | métier | — | `test_bon_depuis_stock` | codé |

## Lot 11 : remboursements FBA (vérification de ce qu'Amazon a versé)

Source : notes `docs/recherches/notes/remboursements/remboursements_spapi.md` (SP-API lue le 12/11/2026 ; annonces officielles « News_Amazon » des 09/01/2025, 10/03/2025 et 15/10/2025 ; la page de politique de Seller Central n'a **pas** pu être lue).

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-054 | **Rôle de l'outil** : Amazon rembourse désormais d'office la plupart des pertes en entrepôt et des retours (annonce du 09/01/2025) ; l'outil **vérifie** ce qui a été versé et signale les écarts. Il ne dépose jamais de réclamation (aucune API ne le permet : Support API en lecture seule) ; il prépare un dossier que le vendeur dépose lui-même. Aucune commission. | Annonce 09/01/2025 ; référence Support API v2025-02-01 | lu | — | `test_aucune_reclamation_automatique` | codé |
| RM-AMZ-055 | **Pertes et dommages en entrepôt** : par FNSKU et place, Lost + Damaged − Found (rapport Ledger synthèse) − unités déjà remboursées sans numéro de commande (rapport Remboursements) ; écart > 0 → cas « à vérifier ». Les codes de motif du Ledger ne sont **pas** utilisés (non documentés). | Colonnes : référence des rapports FBA | lu | avertissement | `test_detection_pertes_entrepot` | codé |
| RM-AMZ-056 | **Remboursé au client sans retour** : commande + produit remboursés (Finances), sans ligne de retour (rapport Retours) ni remboursement portant ce numéro de commande, **45 jours** au moins après le remboursement → cas. | Fenêtre « between 45-105 days » : annonce du 15/10/2025 (pas la page de politique) | lu (annonce) | avertissement | `test_detection_retour_non_restitue` | codé |
| RM-AMZ-057 | **Envoi entrant incomplet** : envoi `CLOSED`, quantité expédiée − reçue (API Inbound v0) − déjà remboursé > 0 → cas. Délai de réclamation : **non vérifié** pour aujourd'hui (seule une annonce UE de 2024 le chiffre) : aucune échéance affichée. | Champs : référence Inbound v0 ; délai : non vérifié | lu / non lu | avertissement | `test_detection_envoi_incomplet` | codé |
| RM-AMZ-058 | **Échéances et montants** : échéance affichée seulement quand une annonce officielle la chiffre (pertes : 60 jours après la perte ; retours : 105 jours après le remboursement), avec la mention « selon annonce Amazon, à confirmer dans Seller Central ». Aucun montant « dû » n'est calculé : l'outil montre la valeur d'achat des unités (vos lots) et ce qu'Amazon a réellement versé (`amount-total`). | Annonce 15/10/2025 ; montants : choix de prudence | lu (annonce) / métier | avertissement | `test_echeances_et_montants` | codé |
| RM-AMZ-059 | **Suivi d'un cas** : DÉTECTÉ → DOSSIER ENVOYÉ (numéro de cas saisi) → REMBOURSÉ / REFUSÉ / CLOS ; un cas redétecté garde son suivi (clé : type + référence) ; un remboursement arrivé ensuite (même FNSKU ou même commande) passe le cas à REMBOURSÉ. | Choix de l'outil | métier | — | `test_suivi_des_cas`, `test_api_remboursements_demo`, `test_remboursements_par_compte` | codé |

> Limites connues (lot 11) : signe des colonnes `Lost` / `Damaged` / `Found` non documenté (valeurs absolues retenues) ;
> remboursements sans numéro de commande imputés d'abord aux envois entrants puis aux pertes (choix de l'outil) ;
> téléchargement des rapports et lecture des envois (`rapport`, `envois_fermes`) écrits d'après la documentation,
> **non testés sur un vrai compte** ; page de politique de remboursement de Seller Central **non lue**.

## Lot 12 : conformité Europe (RSGP, REP, emballages, appareils électriques, piles)

Source : note `docs/recherches/notes/conformite/conformite_ue.md` (textes lus le 12/11/2026 : règlements UE dans leur **version
initiale au JO** — versions consolidées non lues ; code de l'environnement via Légifrance, citations partielles ; VerpackDG,
ElektroG, BattDG sur gesetze-im-internet.de ; pages Amazon sell.amazon.fr / sell.amazon.de). **Rien ici n'est un avis juridique.**
Le vendeur décide lui-même s'il est producteur et de quelles filières relève chaque produit : l'outil ne le devine jamais.
Toutes les alertes sont des **avertissements**, jamais un blocage.

| N° | Règle | Source | Statut | Blocage | Test | État |
|---|---|---|---|---|---|---|
| RM-AMZ-060 | **Champ** : places de l'Union européenne seulement (DE, FR, IT, ES, NL, BE, IE, SE, PL). Les autres places (dont UK, US) n'ont aucune vérification dans ce lot : « non couvert », jamais « conforme ». Produits vérifiés : ceux qui ont un lot ou du stock sur une place de l'UE. | Champ du lot (note §§1-8) | lu / choix | — | `test_champ_ue` | à coder |
| RM-AMZ-061 | **Enregistrements du compte** : par pays et par filière (`EMBALLAGES`, `EEE`, `PILES`, `AUTRE` avec intitulé saisi par le vendeur), un numéro (1 à 64 caractères) et un mandataire facultatif. France : un IDU par filière (L541-10-13 ; ADEME « as many UINs as there are schemes »). Allemagne : emballages = n° LUCID (VerpackDG §6), électrique = n° ElektroG (§6 al. 1), piles = n° BattDG (§4). Numéro LUCID qui n'a pas 13 chiffres → avertissement (page Amazon DE « 13-digit registration number », pas la loi). | L541-10-13 ; VerpackDG §6 ; ElektroG §6 ; BattDG §4 ; page sell.amazon.de | lu | bloquant (format de saisie) / avertissement (LUCID) | `test_enregistrements` | à coder |
| RM-AMZ-062 | **Fiche produit RSGP** (par ASIN) : fabricant (nom, adresse postale, adresse électronique), « fabricant établi hors UE » oui/non, personne responsable dans l'UE (nom, adresse postale, électronique), avertissements de sécurité dans la langue du pays confirmés par le vendeur. Adresse électronique au format `x@y.z`. | Règl. 2023/988 art. 19 a, b, d ; art. 16 §1, §3 | lu (version JO) | avertissement | `test_fiche_rsgp` | à coder |
| RM-AMZ-063 | **Alertes RSGP** : fabricant incomplet → `C_FABRICANT_INCOMPLET` ; fabricant hors UE et personne responsable incomplète → `C_RESPONSABLE_MANQUANT` ; avertissements non confirmés → `C_AVERTISSEMENTS_A_CONFIRMER`. Chaque alerte cite son article. | Règl. 2023/988 art. 19, art. 16 | lu (version JO) | avertissement | `test_alertes_rsgp` | à coder |
| RM-AMZ-064 | **Rôle et filières, déclarés par le vendeur** : « producteur » OUI / NON / À DÉTERMINER et la liste des filières du produit (aucune = « non déclaré »). À DÉTERMINER ou filières non déclarées → `C_ROLE_A_DETERMINER` / `C_FILIERES_A_DECLARER`, sans aucune supposition. | Note « À trancher par le vendeur » | métier | avertissement | `test_role_et_filieres` | à coder |
| RM-AMZ-065 | **Numéro attendu** pour chaque (place UE où le produit est, filière déclarée) : producteur OUI → enregistrement du compte pour (pays, filière) ; producteur NON → numéro du producteur noté sur la fiche (en France l'IDU du fournisseur vaut preuve : L541-10-9). Manquant → `C_ENREGISTREMENT_MANQUANT` avec le texte : FR = L541-10-13 ; DE = VerpackDG §6 / ElektroG §6 / BattDG §4 ; autre pays UE = emballages règl. 2025/40 art. 44, piles règl. 2023/1542 art. 55 ; EEE et AUTRE hors FR/DE = `C_OBLIGATION_NON_VERIFIEE` (pays non recherché), jamais « conforme ». | L541-10-13, L541-10-9 ; VerpackDG §6 ; ElektroG §6 ; BattDG §4 ; règl. 2025/40 art. 44 ; règl. 2023/1542 art. 55 | lu | avertissement | `test_numero_attendu` | à coder |
| RM-AMZ-066 | **France, Triman** : produit sur FR avec au moins une filière déclarée → le vendeur confirme la signalétique Triman / info-tri, sinon `C_TRIMAN_A_CONFIRMER` (L541-9-3 ; modèle graphique non lu). **Marquage CE** : OUI / NON CONCERNÉ / À DÉTERMINER, saisi par le vendeur ; À DÉTERMINER → `C_CE_A_DETERMINER` (règl. 765/2008 art. 30 : seulement si une législation d'harmonisation le prévoit). | L541-9-3 ; règl. 765/2008 art. 30 | lu / non lu (annexe) | avertissement | `test_triman_et_ce` | à coder |
| RM-AMZ-067 | **Bibliothèque des textes** : chaque obligation affichée porte son texte, son article, son lien et son état « vérifié » ou « non vérifié » (date de lecture 12/11/2026) ; aucune amende ni délai affiché sans source lue. Statut d'un produit : « à compléter » s'il a au moins une alerte, sinon « rien de signalé » (jamais « conforme »). | Note conformite_ue.md | lu | — | `test_bibliotheque`, `test_api_conformite_demo`, `test_conformite_par_compte` | à coder |

> Limites connues (lot 12) : textes UE lus dans leur version initiale (modifications non vérifiées) ; citations françaises
> partielles ; autres pays UE que FR/DE non recherchés ; articulation PPWR / filière française des emballages non recherchée ;
> les numéros ne sont pas contrôlés auprès des registres (aucun accès) ; l'outil ne lit pas encore ce qui est saisi chez Amazon.
