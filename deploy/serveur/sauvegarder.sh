#!/bin/bash
# Syllig Vente — sauvegarde quotidienne de la base, gardée 14 jours [RM-AMZ-069].
set -uo pipefail
DOSSIER=/opt/syllig-vente
CIBLE=/var/backups/syllig-vente
JOURNAL=/var/log/syllig-vente-maj.log
etat() { install -d -m 755 /opt/syllig-vente/deploy/etat; echo "$(date -u +%FT%TZ) $2" > "/opt/syllig-vente/deploy/etat/$1.txt"; }  # [RM-AMZ-081]
log() { echo "$(date -u +%FT%TZ) sauvegarde : $*" >> "$JOURNAL"; }
DC=(docker compose -p syllig-vente -f "$DOSSIER/deploy/docker-compose.prod.yml" --env-file "$DOSSIER/deploy/.env")
install -d -m 700 "$CIBLE"
F="$CIBLE/amz-$(date -u +%Y%m%d-%H%M).dump"
if "${DC[@]}" exec -T postgres pg_dump -U postgres -Fc amz > "$F.part" 2>>"$JOURNAL" && [ -s "$F.part" ]; then
  mv "$F.part" "$F"; chmod 600 "$F"
  find "$CIBLE" -name 'amz-*.dump' -mtime +13 -delete
  log "ok $(basename "$F") $(du -h "$F" | cut -f1)"; etat sauvegarde OK
else
  rm -f "$F.part"; log "ÉCHEC (les sauvegardes précédentes sont gardées)"; etat sauvegarde ECHEC; exit 1
fi
