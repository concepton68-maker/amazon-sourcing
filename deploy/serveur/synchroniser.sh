#!/bin/bash
# Syllig Vente — synchronisation Amazon de nuit [RM-AMZ-080] ; résultat (sans secret) au journal du serveur.
set -uo pipefail
DOSSIER=/opt/syllig-vente
DC=(docker compose -p syllig-vente -f "$DOSSIER/deploy/docker-compose.prod.yml" --env-file "$DOSSIER/deploy/.env")
R=$("${DC[@]}" --profile taches run --rm -T taches 2>&1); c=$?
echo "$(date -u +%FT%TZ) synchro : $(echo "$R" | tail -5 | tr '\n' ' ')" >> /var/log/syllig-vente-maj.log
exit $c
