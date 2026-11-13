# Déploiement de Syllig Vente

## Serveur dédié OVH (D-AMZ-023) — sans commande pour Sam

Serveur : VPS OVH (Debian 13), domaine `vente.concepton.fr` (zone DNS chez OVH). Rien n'est partagé avec Syllig.

| Fichier | Rôle |
|---|---|
| `windows/1 - Creer ma cle.bat` puis `windows/2 - Installer Syllig Vente.bat` + `serveur/installer.sh` | Double-clic sur le PC : envoie et lance l'installation ; clé de connexion créée sur le PC (partie secrète jamais transmise), collée dans la réinstallation OVH ; aucun mot de passe |
| `serveur/installer.sh` | Docker (paquets Debian), clé de lecture du dépôt (à coller une fois dans GitHub), mots de passe de la base tirés au sort sur le serveur, démarrage, minuteur de mise à jour, premier compte |
| `serveur/mettre-a-jour.sh` | Toutes les 5 min : nouvelle version de `main` → construction, migrations, redémarrage ; retour à la version précédente si `/api/sante` ne répond plus. Journal : `/var/log/syllig-vente-maj.log`. Aucun workflow GitHub (D-AMZ-009) |
| `serveur/configurer.sh` | Scripts et minuteurs (mise à jour 5 min, sauvegarde 02:15 UTC, purge 02:45 UTC), rejoués après chaque mise à jour réussie |
| `serveur/sauvegarder.sh` | `pg_dump` quotidien dans `/var/backups/syllig-vente`, 14 jours, jamais remplacé par une sauvegarde vide (RM-AMZ-069) |
| `serveur/synchroniser.sh` | Synchronisation Amazon de nuit (03:15 UTC) par le service `taches` du compose (RM-AMZ-080) |
| `etat/` (sur le serveur, non versionné) | Dates et statuts lus par la page publique `/version.json` (RM-AMZ-081) |
| `serveur/purger.sh` | Purge de nuit des comptes révoqués (RM-AMZ-068) |
| `serveur/Caddyfile` | HTTPS automatique et en-têtes de sécurité, dans le projet Docker |

Après l'installation : enregistrement A `vente` → IP du serveur dans la zone DNS `concepton.fr` (OVH).
**Non vérifié ici** (ni Docker ni Debian 13 dans l'environnement de développement) : la première installation réelle le dira.
Paquets Debian 13 lus sur packages.debian.org le 12/11/2026 : `docker.io` 26.1.5, `docker-compose` 2.26.1, `docker-buildx` 0.13.1.

---

## Ancien plan : VPS de Syllig (D-AMZ-007, remplacé par D-AMZ-023)

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
