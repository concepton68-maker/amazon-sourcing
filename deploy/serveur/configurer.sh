#!/bin/bash
# Syllig Vente — réglages du serveur, rejoués après chaque mise à jour réussie [RM-AMZ-068 à 070]. Idempotent.
set -euo pipefail
DOSSIER=/opt/syllig-vente
S="$DOSSIER/deploy/serveur"
install -m 755 "$S/mettre-a-jour.sh" /usr/local/bin/syllig-vente-mettre-a-jour
install -m 755 "$S/sauvegarder.sh" /usr/local/bin/syllig-vente-sauvegarder
install -m 755 "$S/purger.sh" /usr/local/bin/syllig-vente-purger
install -m 755 "$S/synchroniser.sh" /usr/local/bin/syllig-vente-synchroniser
install -d -m 755 "$DOSSIER/deploy/etat"
[ -f "$DOSSIER/deploy/etat/version.txt" ] || git -C "$DOSSIER" rev-parse HEAD > "$DOSSIER/deploy/etat/version.txt"
install -d -m 700 /var/backups/syllig-vente

# [RM-AMZ-074] clé de chiffrement des identifiants saisis sur le site : tirée au sort une fois, reste sur le serveur
ENV="$DOSSIER/deploy/.env"
if ! grep -q '^AMZ_CLE_CHIFFREMENT=.\{64\}$' "$ENV"; then
  sed -i '/^AMZ_CLE_CHIFFREMENT=/d' "$ENV"
  echo "AMZ_CLE_CHIFFREMENT=$(openssl rand -hex 32)" >> "$ENV"
  chmod 600 "$ENV"
  docker compose -p syllig-vente -f "$DOSSIER/deploy/docker-compose.prod.yml" --env-file "$ENV" up -d app >/dev/null 2>&1 || true
fi

unite() {  # nom, description, commande, planification du minuteur
  printf '[Unit]\nDescription=%s\n[Service]\nType=oneshot\nExecStart=%s\n' "$2" "$3" > "/etc/systemd/system/$1.service"
  printf '[Unit]\nDescription=%s\n[Timer]\n%s\nPersistent=true\n[Install]\nWantedBy=timers.target\n' "$2" "$4" > "/etc/systemd/system/$1.timer"
}
unite syllig-vente-maj "Syllig Vente - mise a jour depuis GitHub" /usr/local/bin/syllig-vente-mettre-a-jour \
  "$(printf 'OnBootSec=2min\nOnUnitActiveSec=5min')"
unite syllig-vente-sauvegarde "Syllig Vente - sauvegarde de la base" /usr/local/bin/syllig-vente-sauvegarder "OnCalendar=*-*-* 02:15:00 UTC"
unite syllig-vente-purge "Syllig Vente - purge des comptes revoques" /usr/local/bin/syllig-vente-purger "OnCalendar=*-*-* 02:45:00 UTC"
unite syllig-vente-synchro "Syllig Vente - synchronisation Amazon de nuit" /usr/local/bin/syllig-vente-synchroniser "OnCalendar=*-*-* 03:15:00 UTC"
systemctl daemon-reload
for t in syllig-vente-maj syllig-vente-sauvegarde syllig-vente-purge syllig-vente-synchro; do systemctl enable --now "$t.timer" >/dev/null 2>&1; done

# [RM-AMZ-077] sécurité du serveur (pare-feu, fail2ban, SSH par clé, antivirus)
bash "$S/securite.sh" || echo "$(date -u +%FT%TZ) sécurité : ÉCHEC de securite.sh" >> /var/log/syllig-vente-maj.log
