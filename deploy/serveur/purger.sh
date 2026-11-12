#!/bin/bash
# Syllig Vente — purge de nuit des comptes révoqués [RM-AMZ-068, RM-AMZ-014].
set -uo pipefail
DOSSIER=/opt/syllig-vente
DC=(docker compose -p syllig-vente -f "$DOSSIER/deploy/docker-compose.prod.yml" --env-file "$DOSSIER/deploy/.env")
R=$("${DC[@]}" run --rm -T migrer python -m sourcing purger 2>&1); c=$?
echo "$(date -u +%FT%TZ) purge : $R" >> /var/log/syllig-vente-maj.log
exit $c
