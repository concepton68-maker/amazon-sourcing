# Captures 1.0 — le vrai site, mode production (12/11/2026)

Lancé ici en mode `prod` : base Postgres réelle (migrations 0001 à 0010), connexion obligatoire, **aucune donnée fictive**,
**aucune source branchée** (ni Amazon SP-API ni Keepa : compte vendeur en vérification). Compte de test local.

| Fichier | Ce qu'on voit |
|---|---|
| `01-connexion-*` | Page de connexion (bureau et téléphone) |
| `02-analyse-*` | Analyse d'un vrai ASIN : « Aucune source de données branchée : rien n'a été cherché » (RM-AMZ-071, corrigé grâce à cette capture : le site disait « produit introuvable ») |
| `03` à `09` | Sourcing, Achats & lots, Stock, Fournisseurs, Remboursements, Conformité, Paramètres : écrans vides, prêts à recevoir vos données |

Pages sans débordement (1600 px et 390 px mesurés).
