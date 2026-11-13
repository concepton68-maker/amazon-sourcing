# amazon-sourcing — à lire au démarrage de chaque session

Outil de sourcing et de gestion pour vendeurs Amazon. Usage personnel d'abord, architecture multi-comptes (D-AMZ-001).
Façon de travailler : celle de Syllig (`concepton68-maker/syllig-suite`, `BONNES-MANIERES.md`), en particulier :

- Français simple, réponses courtes ; heures de Paris ; ne jamais demander de mot de passe, clé ou jeton ; aucun secret dans le dépôt.
- **La règle d'abord** : toute fonction métier commence par sa ligne dans `docs/regles/registre.md` (règle, source ou « non sourcé », test), puis le test, puis le code. Un commit « règles » avant le commit de code.
- Jamais une valeur réglementaire de mémoire : source lue et citée, sinon « non sourcé », jamais bloquant.
- Décisions structurantes : `docs/decisions/registre.md` (numéro suivant le dernier sur `main`).
- Une branche par lot (`lot/<sujet>`), PR en brouillon ; fusion seulement avec la suite complète verte sur le dernier commit. **Mandat de fusion permanent de Sam (D-AMZ-024)** : fusionner sans redemander une fois la suite et le build verts, puis vérifier la mise en ligne et le dire.
- Pas de workflow GitHub automatique (D-AMZ-009) : les tests tournent en local.
- Écrans sobres : données et une action, pas de phrases d'explication (BONNES-MANIERES 1.11).
- Rien d'identifiant vers un moteur IA sans minimisation (D-AMZ-008).
- Textes d'interface jamais en dur : codes de message traduits (D-AMZ-010).

## Tests

```bash
cd backend
python -m unittest discover -s tests                     # sans Postgres : tests Postgres sautés
AMZ_TEST_PG="host=<socket ou hôte> port=55432 user=postgres" python -m unittest discover -s tests
```

Postgres local de test (conteneur cloud) : données dans `/var/lib/postgresql/amz-test` (le dossier temporaire de session perd ses droits), démarré par
`su postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/amz-test/data -o '-p 55432 -k /var/lib/postgresql/amz-test' -l /var/lib/postgresql/amz-test/log.txt start"`.

## Interface

`cd frontend && npm install && npm run build`, puis `cd backend && AMZ_MODE=dev python -m sourcing serveur` (http://127.0.0.1:8820, données fictives, sans connexion). `AMZ_MODE=prod` exige `AMZ_DATABASE_URL` et la connexion (D-AMZ-019) ; premier utilisateur : `python -m sourcing creer-utilisateur --courriel … --compte …` (mot de passe demandé sur le serveur, jamais dans le chat). Captures de preuve : `docs/captures/<version>/` avec `LISEZ-MOI.md`.

## Repères

- Règles : `docs/regles/registre.md` · Décisions : `docs/decisions/registre.md` · Maquette : `docs/maquettes/README.md`
- Études : `docs/recherches/`
