# Syllig Vente — état courant (à lire EN PREMIER à chaque reprise)

Mis à jour le 14/11/2026, 14 h 30 (heure de Paris). **À mettre à jour dans la même livraison que chaque changement**
(D-AMZ-029). Aucun secret ici.

## 1. Où en est le site

- En ligne : **https://vente.concepton.fr** (VPS OVH, D-AMZ-023). Mise à jour automatique depuis `main` toutes les
  5 minutes, avec retour arrière si la vérification de santé échoue.
- Page de contrôle publique : `/version.json` (version, mise à jour, sauvegarde, purge, tâches de nuit).
- Amazon : connexion SP-API du compte de Sam opérationnelle (développeur privé, région EU, jeton de marchand saisi
  sur le site). Compte vendeur neuf : la plupart des rayons demandent une approbation ; Vêtements est le plus ouvert
  (13/20 au sondage du 14/11).
- Nuit (UTC) : 02:15 sauvegarde · 02:45 purge · 03:15 tâches de nuit dans l'ordre : ventes, stock, remboursements, contrôle des prix (plancher),
  sondage des rayons (chaque nuit), historique de marché, correspondance fournisseurs. Elles peuvent aussi être
  lancées à la main (Paramètres › Connexions et synchronisation).
- **Remboursements lancés à la main le 14/11 à 12 h 24** : coupés à 12 h 25 par la mise à jour automatique (fusion de la PR #47), donc sans résultat ; à relancer. Corrigé le 14/11 (RM-AMZ-135) : la mise à jour attend la fin d'un travail.
- **À vérifier le 15/11 au matin** : la première nuit complète sur le vrai compte (sondage, historique,
  correspondance) ; et les remboursements, qui ont échoué la nuit du 14/11 avant la correction « CANCELLED = vide ».

## 2. Livraisons du 14/11/2026 (fusionnées dans `main`, PR du dépôt concepton68-maker/amazon-sourcing)

| PR | Lot | Règles | Captures |
|---|---|---|---|
| #28 | Plan de stratégie, sources fournisseurs, D-AMZ-027, D-AMZ-028 | — | — |
| #29 | Historique maison et suivi de marché (relevé de nuit, familles, liste de suivi) | RM-AMZ-086 à 090 | 1.5 |
| #30 | Nouveau design, tableau de bord calculé | RM-AMZ-091 à 094 | 1.6 |
| #31 | Filtre des familles (tout cocher), suivi depuis « Je peux vendre » | — | — |
| #32 | Coût complet par unité (stockage grille Amazon, carburant, port, placement) | RM-AMZ-095 à 099 | 1.7 |
| #33 | Paramètres en rubriques, supplément carburant réglable | RM-AMZ-097 révisée | — |
| #34 | Base de fournisseurs (annuaire, fiche, catalogue par fichier, analyse) | RM-AMZ-100 à 104 | 1.8 |
| #35 | Liste des produits rentables (tri, filtres, vendabilité) | RM-AMZ-105 à 108 | 1.9 |
| #36 | Annuaire élargi (20 fournisseurs) | — | — |
| #37, #38 | Annuaire compact, sélection groupée, lignes cliquables | — | 1.10 |
| #39 | D'Amazon vers les fournisseurs (codes-barres, « Où l'acheter ») | RM-AMZ-109 à 112 | 1.11 |
| #40 | Travail autonome de nuit, déblocages annoncés | RM-AMZ-085 révisée, 113, 114 | 1.12 |
| #41 | Travaux de nuit lancés à la main | RM-AMZ-115 | 1.13 |
| #42 | Résultats en temps réel, sans doublon | RM-AMZ-116 | 1.14 |
| #43, #44 | Traçabilité (ce fichier), audit de cohérence face à la concurrence | — | — |
| #45 | Chantier concurrence 1/5 : comparaison entre pays européens dans l'analyse | RM-AMZ-117 | 1.15 |
| #46 | Chantier concurrence 2/5 : détenteur de la Buy Box relevé, demande et Buy Box dans l'analyse | RM-AMZ-118, 119 | 1.16 |
| #47 | Chantier concurrence 3/5 : vérification d'autorisation en masse, lien « Demander l'autorisation » d'Amazon | RM-AMZ-120, 121 | 1.17 |
| #48 | Chantier concurrence 4/5 : prix plancher (analyse), repricer gratuit d'Amazon depuis Stock (validation obligatoire), tâche de nuit PRIX et alerte sous plancher | RM-AMZ-122 à 124 | — (pas d'offre en ligne pour l'essayer) |

| (lot plan-achat) | Chantier concurrence 5/5, partie 1 : plan d'achat depuis les produits rentables (sélection groupée → bon brouillon par fournisseur), quantité proposée et modifiable, Paramètres › Société, bon en PDF et Excel. **Correctif** : l'ajout des produits rentables au fil de l'eau était refusé par la base depuis la PR #42 (droit manquant), corrigé par la migration 0020 | RM-AMZ-125 à 128 | 1.18 |

| (lot messagerie) | Chantier 5/5, partie 2 : envoi du bon depuis la messagerie Microsoft du vendeur (connexion par code + PKCE, envoi seul, aperçu puis envoi, traces en ajout seul, incertain jamais repris) ; bascule jour / nuit en icônes seules | RM-AMZ-129 à 131 | 1.20 |

| (lot analyse-catalogues) | « Analyser tous mes catalogues » (l'un après l'autre, résultats au fil de l'eau), textes clairs de la recherche Amazon → fournisseurs et de la liste vide. Cause du « rien » de Sam : ses analyses lancées avant 13 h le 14/11 n'avaient rien rangé (droit manquant, corrigé par la PR #49) ; à relancer | RM-AMZ-132 | — |

| (lot remboursements-rapides) | Remboursements seulement sur les places actives (avant : 3 rapports × chaque pays ouvert, des heures), avancement en direct (« FR · rapport 2 sur 3 · Amazon prépare le rapport (4 min) », depuis, dernière nouvelle, lien « voir »), mise à jour automatique reportée tant qu'un travail tourne (3 h au plus) | RM-AMZ-133 à 135 | — |

| (lot arreter) | Bouton « Arrêter » (travaux lancés à la main, analyses de catalogues, recherche chez les fournisseurs), à la prochaine étape sûre, déjà obtenu gardé ; pas de pause (arrêter puis relancer suffit) | RM-AMZ-136 | — |

| (lot envoi-fba-1) | Envoi FBA par l'API, partie 1 : brouillon depuis le stock, plan chez Amazon, options d'emballage, confirmation (définitive, sur un clic), cartons, annulation ; adresse d'expédition dans Paramètres › Société ; réglages du sourcing repliés après lancement ; verdicts « À acheter / À vérifier / Ne pas acheter » | RM-AMZ-137 à 139 | 1.21 |

| (lot double-clic) | Produits rentables : clic sur la ligne = cocher, double-clic = analyser (le titre n'est plus un lien) | — | — |

| (lot donnees) | Écran « Données » (produits analysés, marché, relevés jour par jour, autorisations, catalogues : recherche, filtres par colonne, tri, colonnes, export, clic/double-clic, ajout au plan) ; « Relever maintenant » dans Marché avec arrêt | RM-AMZ-140, 141 | 1.22 |

| (lot arret-effectif) | L'arrêt agit aussi au milieu d'une tâche (à chaque pause entre deux appels à Amazon) ; l'historique de marché donne des nouvelles (fiches, offres et Buy Box n sur N) | RM-AMZ-134, 136 précisées | — |

| (lot envoi-fba-2) | Envoi FBA partie 2 : répartition (frais tels que rendus), transport colis (toutes les pages, même transporteur), fenêtres, deux confirmations payantes séparées, étiquettes (PDF téléchargé aussitôt), suivi ; « Relever maintenant » limité à 500 produits suivis et analysés | RM-AMZ-142 à 147 | — |

Registres : règles `docs/regles/registre.md` (RM-AMZ-001 à 147) · décisions `docs/decisions/registre.md`
(D-AMZ-001 à 035).

## 3. Études (sources officielles, statut VÉRIFIÉ / extrait / NON VÉRIFIÉ dans chaque fichier)

Index : `docs/recherches/README.md`.

## 4. Consignes permanentes de Sam (à respecter sans qu'il les répète)

- **Vérité** : n'avancer que des informations vérifiées, sinon le dire. Aucune valeur réglementaire de mémoire.
- **Réponses courtes et précises**, en français simple. Sam ne tape aucune commande. Ne jamais lui demander de mot
  de passe, de clé ou de jeton, ni dans le chat ni ailleurs : il les colle lui-même dans le site.
- **Stratégie d'abord, puis règles, puis code.** Mandat de fusion permanent (D-AMZ-024) : fusionner quand la
  suite complète et la construction sont vertes, vérifier la mise en ligne, le dire.
- **Ordinateur d'abord** (D-AMZ-025) ; **téléphone = mode nomade** (D-AMZ-033) : suivi, actions urgentes, scan, rien d'autre ; **reporté** jusqu'à ce que la partie ordinateur soit à peu près figée.
- **Ergonomie** :
  - tout ce qui se coche a « tout cocher / tout décocher » et une sélection groupée ;
  - **un clic sur la ligne coche ou décoche la case, un double-clic ouvre le détail ou l'analyse** (Sam, 14/11) ;
  - affichage dense et professionnel, sans grosses pastilles ni phrases d'explication inutiles (infobulle ⓘ) ;
  - réglages rangés par rubriques logiques ;
  - pluriels corrects.
- **Le manuel d'abord** (D-AMZ-035) : tout ce qui est automatique se lance, s'arrête et se consulte aussi à la main ; chaque donnée se trie, se cherche, se filtre, s'exporte, s'importe.
- **Résultats en temps réel** : tout ce qui est long tourne en arrière-plan, de façon autonome (nuit + à la
  demande), les résultats tombent au fil de l'eau et sont exploitables tout de suite ; avancement réel visible.
- **Réglages pilotés par l'utilisateur, toujours rappelés quand ils sont actifs** (ex. supplément carburant :
  taux + case active, taux gardé quand on décoche).
- **Fournisseurs** : la recherche doit être la plus large possible, sur toutes les familles (Amazon peut
  débloquer une famille à tout moment) ; branchements API prioritaires ; l'utilisateur écarte lui-même ce qu'il
  ne peut pas vendre, avec une indication claire (vendable sûr / probable / improbable / non vendable sûr / inconnu).
- **Pas d'aspiration de pages** (D-AMZ-027), **pas de Keepa pour Sam** (D-AMZ-026), **pas de revente de données
  Amazon** (règlement SP-API 4.3 et 4.4).
- **Indices de déboîtage** (D-AMZ-030, pour Sam seul, hors application) : https://claude.ai/artifact/UjiGRcjK2FnL99xcVUFbL8 ,
  source `docs/indices/indices-deboitage.html`. **À mettre à jour et republier à la même adresse à CHAQUE livraison** (consigne répétée par Sam le 14/11) :
  bloc `donnees` ; chaque livraison = une nouvelle strate (`strates`), les notes qui bougent dans `notes`, une ligne dans `historique` ; la dernière strate s'affiche en orange.
- **Traçabilité** : chaque recherche est enregistrée dans `docs/recherches/`, chaque livraison dans ce fichier.

## 5. Vision (plan `docs/strategie/plan-action.md`, section 7 bis « copilote »)

L'outil dit quoi vendre, à quel prix, avec quel ROI et quelle rotation ; il propose un plan d'achat que Sam valide,
puis suit commande, réception, envoi à Amazon et encaissement. Courriels depuis la messagerie du vendeur connectée
(comme la suite Syllig). Paiement intégré plus tard, après étude réglementaire.

## 6. En attente

- **Messagerie : action de Sam** (guide `docs/guides/microsoft-messagerie.md`) : ajouter l'adresse de retour à l'application « Syllig » chez Microsoft, créer une clé, la coller dans Paramètres › Connexions, connecter sa boîte, faire un premier envoi vers sa propre adresse.
- **Vision « pilote automatique »** (Sam, 14/11) : objectifs + garde-fous + niveaux d'autonomie 0 à 3 par étape, validation humaine aux étapes qui engagent de l'argent ; mode téléphone « nomade » décidé (D-AMZ-033 : suivi, actions urgentes, scan code-barres ; le reste sur ordinateur) ; recherche faite (`docs/recherches/2026-11-14-passerelle-amazon-sp-api.md`) ; **feuille de route proposée** `docs/strategie/pilote-automatique.md`, en attente de validation de Sam (cadre, ordre des 7 étapes).
- **Envoi FBA** : chaîne complète codée (PR #60, #64), à essayer sur le vrai compte jusqu'au transport, puis annuler, avant tout envoi réel. **Chantier 5 (suite)** : partie 3 = envoi FBA par l'API (étude `2026-11-14-envoi-fba-api-inbound.md` : transporteur partenaire en France incertain, deux confirmations payantes à valider à la main).
- **Nom : Syllig Pilot** (D-AMZ-031, 14/11). Marques à vérifier à la main (TMview, INPI, classes 9, 35, 42). **Logo posé** (piste 1, D-AMZ-032) : mot-symbole « syllig pilot » à repère orange, favicon, mode Jour · Nuit · Auto (captures 1.19). L'adresse reste vente.concepton.fr (changement d'adresse : décision à part).
- **Chantier « réponse à la concurrence » lancé par Sam le 14/11** (ordre) : 1 multi-pays (fait), 2 demande et Buy Box tirées de nos relevés (fait), 3 éligibilité en masse + lien de demande d'autorisation (fait), 4 prix plancher + repricer gratuit d'Amazon + alerte (fait, non essayé sur une vraie offre), 5 bon de commande envoyé au fournisseur puis envoi FBA par l'API.
- (Ancien) choix parmi les 7 pistes d'efficacité proposées le 14/11 : ajustement automatique des
  prix, arbitrage entre pays européens, assistant de demande d'autorisation, négociation fournisseur, alertes de
  risque sur le stock, plan de trésorerie, saisonnalité.
- **Audit de cohérence face à la concurrence** fait (`docs/recherches/2026-11-14-audit-coherence-concurrence.md`). Résultat : devant sur fournisseurs UE, coût complet, éligibilité de nuit, prévu/réel ; derrière sur ventes/historique, rotation de Buy Box, repricing, multi-pays UE, envoi FBA, recherche par marque, éligibilité en masse, alertes stock. Priorités recommandées en attente de choix de Sam : (1) demande et Buy Box tirées de nos relevés, (2) prix plancher + repricer gratuit d'Amazon + alerte, (3) vue multi-pays UE, (4) éligibilité en masse + guide d'approbation, (5) bon de commande envoyé au fournisseur puis envoi FBA par l'API.
- **Actions de Sam** : ouvrir ses comptes fournisseurs (Qogita, puis Puckator, BigBuy…), charger leurs fichiers de
  prix ; Qogita : demander la « Public API (Buyers) » à api@qogita.com (l'API actuelle s'arrête fin janvier 2027).
- Lot « Annuaire » : remplacer le formulaire manuel « Nom, Délai, Ajouter » par un vrai formulaire de création.
- Sélection groupée à ajouter dans Produits rentables et Marché (suivre ou retirer plusieurs produits).
- Supplément carburant : vérifier sur un vrai relevé Amazon s'il est déjà inclus dans les frais de l'API.
- Serveur au Canada : à déplacer en Europe avant le premier client.
