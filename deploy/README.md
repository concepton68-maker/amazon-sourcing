# Déploiement

- `bootstrap_roles.sql` : rôles Postgres `amz_owner` (propriétaire, migrations, purge) et `amz_app` (application, cloisonnée par compte). Mots de passe posés hors dépôt.
- `docker-compose.dev.yml` : Postgres de développement, mémoire plafonnée à 512 Mo.
- Production (à venir) : projet Docker isolé sur le VPS, domaine à part (D-AMZ-007).
