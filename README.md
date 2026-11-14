# Syllig Vente — sourcing et gestion pour vendeurs Amazon

Outil personnel d'abord, conçu pour devenir un SaaS multi-clients (Europe + États-Unis).

## Organisation du dépôt

| Dossier | Contenu |
|---|---|
| `backend/` | Code Python : calcul de rentabilité, clients API Amazon (SP-API) et Keepa, analyse produit, tests |
| `frontend/` | Interface web (à venir) |
| `deploy/` | Déploiement Docker sur le VPS (à venir) |
| `docs/maquettes/` | Maquette cliquable des 11 écrans |
| `docs/regles/` | Registre des règles métier `RM-AMZ-nnn` (règle → source → test) |
| `docs/decisions/` | Registre des décisions `D-AMZ-nnn` |
| `docs/strategie/` | Plan de stratégie et ordre des lots |
| `docs/recherches/` | Études de marché et de données, avec leurs notes sourcées |

## Méthode

1. La règle d'abord (`docs/regles/`), avec sa source ou la mention « non sourcé », puis le test, puis le code.
2. Toute décision structurante va dans `docs/decisions/registre.md`.
3. PR en brouillon ; suite de tests complète sur le dernier commit avant fusion.
4. Aucun secret dans le dépôt : clés dans `.env` (ignoré par git) puis, en production, chiffrées en base.
5. Versions `1.XX` (+1 par mise en ligne).

## Démarrer

```bash
cd backend
python -m sourcing analyse 3700000000017 --mp FR --achat 8.50 --demo
python -m unittest discover -s tests
# avec Postgres (base jetable créée puis supprimée) :
AMZ_TEST_PG="host=localhost port=55432 user=postgres password=…" python -m unittest discover -s tests
```
