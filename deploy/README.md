# Déploiement de Syllig Vente sur le VPS

Projet Docker **isolé** de Syllig (D-AMZ-007, D-AMZ-021) : sa propre base, son propre réseau, mémoire plafonnée
(Postgres 512 Mo, application 512 Mo, migration 256 Mo). La base n'a aucun accès à Internet.

| Fichier | Rôle |
|---|---|
| `../Dockerfile` | Image unique : interface construite + API Python, utilisateur non privilégié, contrôle de santé |
| `docker-compose.prod.yml` | Services `postgres`, `migrer` (une fois par déploiement), `app` (port 8830 en local seulement) |
| `initdb/01_roles.sh` + `bootstrap_roles.sql` | À la création de la base : rôles `amz_owner` / `amz_app`, mots de passe lus dans `.env` |
| `env.exemple` | Modèle de `deploy/.env` (secrets, jamais versionné) |
| `Caddy.exemple` | Bloc Caddy : HTTPS, en-têtes de sécurité, domaine à part de `syllig.com` |
| `docker-compose.dev.yml` | Postgres de développement |

## Première installation (sur le serveur)

1. Copier `env.exemple` en `deploy/.env`, droits `600`, y mettre trois mots de passe tirés au sort.
2. `docker compose -p syllig-vente -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build`
3. Créer le premier utilisateur (mot de passe saisi sur le serveur) :
   `docker compose -p syllig-vente -f deploy/docker-compose.prod.yml --env-file deploy/.env run --rm app python -m sourcing creer-utilisateur --courriel … --compte …`
4. Ajouter le bloc `Caddy.exemple` (avec le vrai domaine) au Caddyfile, recharger Caddy.
5. Pointer le domaine (Cloudflare) vers le VPS.

## Mise à jour

`git pull` puis la commande de l'étape 2 : l'image est reconstruite, `migrer` applique les migrations manquantes
(une migration déjà appliquée puis modifiée est refusée), puis `app` redémarre.

## Vérifié le 12/11/2026 (sans Docker, absent de l'environnement de développement)

- Fichier compose : syntaxe validée (`docker compose config`), plafonds de mémoire, réseau interne isolé, port local seulement.
- Mode production lancé sur un Postgres 16 local : 5 migrations appliquées, `/api/sante` 200, routes protégées 401,
  documentation de l'API fermée, requête sans en-tête 403, connexion 200 avec cookie `Secure`, données servies.
- **Non vérifié** : construction de l'image Docker elle-même et démarrage par `docker compose` (à faire au premier déploiement).

## À prévoir

- Sauvegarde chiffrée de la base (sur le modèle de Syllig, D223) et essai de restauration.
- Tâches de nuit : synchronisation Amazon (quand le compte vendeur est validé) et purge des comptes révoqués.
