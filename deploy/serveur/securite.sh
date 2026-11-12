#!/bin/bash
# Syllig Vente — sécurité du serveur [RM-AMZ-077], appelée par configurer.sh. Idempotent.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
manque=""
for p in nftables fail2ban clamav clamav-freshclam; do dpkg -s "$p" >/dev/null 2>&1 || manque="$manque $p"; done
[ -z "$manque" ] || { apt-get update -q; apt-get install -y -q $manque; }

# 1. Pare-feu : table propre (les règles de Docker ne sont pas touchées ; les ports publiés passent par le transfert).
install -d -m 755 /etc/syllig-vente
cat > /etc/syllig-vente/pare-feu.nft <<'NFT'
table inet syllig_pare_feu
delete table inet syllig_pare_feu
table inet syllig_pare_feu {
  chain entree {
    type filter hook input priority 0; policy drop;
    iif lo accept
    ct state established,related accept
    ct state invalid drop
    iifname { "docker0", "br-*" } accept
    meta l4proto { icmp, ipv6-icmp } accept
    udp dport { 68, 546 } accept
    tcp dport { 22, 80, 443 } accept
  }
}
NFT
cat > /etc/systemd/system/syllig-vente-pare-feu.service <<'UNIT'
[Unit]
Description=Syllig Vente - pare-feu
After=network-pre.target
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/nft -f /etc/syllig-vente/pare-feu.nft
ExecStop=/usr/sbin/nft delete table inet syllig_pare_feu
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable syllig-vente-pare-feu.service >/dev/null 2>&1
systemctl restart syllig-vente-pare-feu.service

# 2. Détection et blocage des intrusions sur SSH (fail2ban).
cat > /etc/fail2ban/jail.d/syllig-vente.local <<'F2B'
[sshd]
enabled = true
backend = systemd
banaction = nftables-multiport
maxretry = 5
findtime = 10m
bantime = 1h
F2B
systemctl enable --now fail2ban >/dev/null 2>&1
systemctl restart fail2ban

# 3. SSH par clé seulement — appliqué uniquement si une clé est installée (jamais de verrouillage).
if cat /root/.ssh/authorized_keys /home/*/.ssh/authorized_keys 2>/dev/null | grep -q '^ssh-'; then
  printf 'PasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin prohibit-password\n' \
    > /etc/ssh/sshd_config.d/00-syllig-vente.conf
  if sshd -t; then systemctl reload ssh 2>/dev/null || systemctl reload sshd; else rm -f /etc/ssh/sshd_config.d/00-syllig-vente.conf; fi
fi

# 4. Antivirus : bases tenues à jour par clamav-freshclam ; analyse chaque dimanche, résultat au journal.
systemctl enable --now clamav-freshclam >/dev/null 2>&1 || true
cat > /usr/local/bin/syllig-vente-antivirus <<'AV'
#!/bin/bash
R=$(nice -n 19 clamscan -r -i --no-summary --exclude-dir='^/opt/syllig-vente/.git' \
    /opt/syllig-vente /var/backups/syllig-vente /tmp /var/tmp 2>&1); c=$?
case $c in 0) m="aucun fichier infecté";; 1) m="FICHIER INFECTÉ : $R";; *) m="erreur d'analyse : $R";; esac
echo "$(date -u +%FT%TZ) antivirus : $m" >> /var/log/syllig-vente-maj.log
exit $c
AV
chmod 755 /usr/local/bin/syllig-vente-antivirus
printf '[Unit]\nDescription=Syllig Vente - analyse antivirus\n[Service]\nType=oneshot\nExecStart=/usr/local/bin/syllig-vente-antivirus\n' \
  > /etc/systemd/system/syllig-vente-antivirus.service
printf '[Unit]\nDescription=Syllig Vente - analyse antivirus hebdomadaire\n[Timer]\nOnCalendar=Sun *-*-* 03:30:00 UTC\nPersistent=true\n[Install]\nWantedBy=timers.target\n' \
  > /etc/systemd/system/syllig-vente-antivirus.timer
systemctl daemon-reload
systemctl enable --now syllig-vente-antivirus.timer >/dev/null 2>&1
echo "$(date -u +%FT%TZ) sécurité : pare-feu, fail2ban, SSH par clé, antivirus appliqués" >> /var/log/syllig-vente-maj.log
