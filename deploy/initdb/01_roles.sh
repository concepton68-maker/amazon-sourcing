#!/bin/sh
# Exécuté une seule fois par l'image Postgres à la création de la base (docker-entrypoint-initdb.d).
# Crée les rôles (bootstrap_roles.sql), leur pose un mot de passe lu dans l'environnement, crée la base.
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -f /bootstrap_roles.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" \
  -v owner_mdp="$AMZ_OWNER_PASSWORD" -v app_mdp="$AMZ_APP_PASSWORD" <<'SQL'
ALTER ROLE amz_owner PASSWORD :'owner_mdp';
ALTER ROLE amz_app PASSWORD :'app_mdp';
CREATE DATABASE amz OWNER amz_owner;
REVOKE ALL ON DATABASE amz FROM PUBLIC;
GRANT CONNECT ON DATABASE amz TO amz_app;
SQL
