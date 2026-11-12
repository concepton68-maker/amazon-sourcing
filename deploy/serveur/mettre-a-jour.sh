#!/bin/bash
# Syllig Vente — mise à jour automatique depuis main (minuteur systemd, toutes les 5 min). D-AMZ-023.
# Nouvelle version : construction, migrations, redémarrage ; si l'application ne répond plus, retour à la version précédente.
set -uo pipefail
DOSSIER=/opt/syllig-vente
JOURNAL=/var/log/syllig-vente-maj.log
exec 9>/run/syllig-vente-maj.lock; flock -n 9 || exit 0
log() { echo "$(date -u +%FT%TZ) $*" >> "$JOURNAL"; }
DC=(docker compose -p syllig-vente -f "$DOSSIER/deploy/docker-compose.prod.yml" --env-file "$DOSSIER/deploy/.env")
cd "$DOSSIER" || exit 1
git fetch -q origin main || { log "fetch impossible"; exit 1; }
AVANT=$(git rev-parse HEAD); APRES=$(git rev-parse origin/main)
[ "$AVANT" = "$APRES" ] && exit 0
repond() { for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8830/api/sante >/dev/null 2>&1 && return 0; sleep 3; done; return 1; }
log "nouvelle version $APRES (était $AVANT)"
git checkout -q --detach "$APRES"
if "${DC[@]}" up -d --build >> "$JOURNAL" 2>&1 && repond; then
  log "version $APRES en ligne"
  docker image prune -f >/dev/null 2>&1
else
  log "ÉCHEC de $APRES : retour à $AVANT (les migrations déjà appliquées restent)"
  git checkout -q --detach "$AVANT"
  "${DC[@]}" up -d --build >> "$JOURNAL" 2>&1 && repond && log "retour à $AVANT réussi" || log "RETOUR IMPOSSIBLE : intervention nécessaire"
fi
