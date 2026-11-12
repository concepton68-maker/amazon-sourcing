#!/bin/bash
# Syllig Vente — installation sur un VPS neuf (Debian 13 ; Ubuntu accepté, paquets essayés dans l'ordre) (D-AMZ-023). Lancé par « Installer Syllig Vente.bat ».
# Rejouable : chaque étape vérifie ce qui est déjà fait. Aucun secret ne sort du serveur.
set -euo pipefail
DOMAINE="${1:-vente.concepton.fr}"
DEPOT="git@github.com:concepton68-maker/amazon-sourcing.git"
DOSSIER=/opt/syllig-vente
CLE=/root/.ssh/syllig_vente_depot
etape() { printf '\n==> %s\n' "$1"; }
[ "$(id -u)" = 0 ] || { echo "À lancer avec sudo."; exit 1; }

etape "1/7 Logiciels (Docker, Git, mises à jour de sécurité automatiques)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q git docker.io openssl curl ca-certificates unattended-upgrades
# Compose v2 : paquet « docker-compose » sur Debian 13, « docker-compose-v2 » s'il existe (Ubuntu) ; buildx si disponible
apt-get install -y -q docker-compose-v2 2>/dev/null || apt-get install -y -q docker-compose
apt-get install -y -q docker-buildx 2>/dev/null || true
systemctl enable --now docker
docker compose version >/dev/null

etape "2/7 Clé de lecture du dépôt GitHub (publique, rien de secret à copier)"
install -d -m 700 /root/.ssh
[ -f "$CLE" ] || ssh-keygen -q -t ed25519 -N "" -C "serveur-syllig-vente" -f "$CLE"
grep -q "^Host github.com" /root/.ssh/config 2>/dev/null || printf 'Host github.com\n  IdentityFile %s\n  IdentitiesOnly yes\n' "$CLE" >> /root/.ssh/config
ssh-keyscan -t ed25519 github.com 2>/dev/null >> /root/.ssh/known_hosts
sort -u -o /root/.ssh/known_hosts /root/.ssh/known_hosts
until git ls-remote "$DEPOT" HEAD >/dev/null 2>&1; do
  echo
  echo "GitHub ne connaît pas encore ce serveur. À faire une seule fois :"
  echo "  1. Ouvrez https://github.com/concepton68-maker/amazon-sourcing/settings/keys/new"
  echo "  2. Title : Serveur OVH"
  echo "  3. Key : copiez la ligne ci-dessous (sélection à la souris, puis clic droit)"
  echo
  cat "$CLE.pub"
  echo
  echo "  4. Ne cochez PAS « Allow write access », puis « Add key »."
  read -r -p "Appuyez sur Entrée quand c'est fait… " _
done

etape "3/7 Code de Syllig Vente"
if [ -d "$DOSSIER/.git" ]; then git -C "$DOSSIER" fetch -q origin main; else git clone -q --branch main "$DEPOT" "$DOSSIER"; fi
git -C "$DOSSIER" checkout -q --detach origin/main 2>/dev/null || git -C "$DOSSIER" checkout -q main

etape "4/7 Mots de passe de la base (tirés au sort, restent sur ce serveur)"
ENV="$DOSSIER/deploy/.env"
if [ ! -f "$ENV" ]; then
  umask 077
  { echo "AMZ_PG_ADMIN_PASSWORD=$(openssl rand -hex 24)"
    echo "AMZ_OWNER_PASSWORD=$(openssl rand -hex 24)"
    echo "AMZ_APP_PASSWORD=$(openssl rand -hex 24)"
    echo "AMZ_PORT=8830"
    echo "AMZ_DOMAINE=$DOMAINE"; } > "$ENV"
fi
chmod 600 "$ENV"

etape "5/7 Construction et démarrage (quelques minutes la première fois)"
DC=(docker compose -p syllig-vente -f "$DOSSIER/deploy/docker-compose.prod.yml" --env-file "$ENV")
"${DC[@]}" up -d --build
for i in $(seq 1 60); do curl -fsS http://127.0.0.1:8830/api/sante >/dev/null 2>&1 && break; sleep 3; done
curl -fsS http://127.0.0.1:8830/api/sante >/dev/null || { echo "L'application ne répond pas. Rien n'est perdu : relancez l'installation."; exit 1; }
echo "Application démarrée."

etape "6/7 Mise à jour automatique, sauvegarde et purge de nuit"
bash "$DOSSIER/deploy/serveur/configurer.sh"

etape "7/7 Premier compte"
N=$("${DC[@]}" exec -T postgres psql -U postgres -d amz -tAc "SELECT count(*) FROM amz.utilisateurs" | tr -d '[:space:]')
if [ "$N" = "0" ]; then
  echo "Créez votre compte (le mot de passe ne s'affiche pas quand vous le tapez : c'est normal)."
  read -r -p "Votre adresse électronique : " COURRIEL
  read -r -p "Nom du compte vendeur (ex. Concepton) : " NOM
  "${DC[@]}" run --rm app python -m sourcing creer-utilisateur --courriel "$COURRIEL" --compte "$NOM"
else
  echo "Un compte existe déjà ($N utilisateur(s))."
fi

IP=$(curl -fsS -4 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')
echo
echo "Terminé. Dernière étape chez OVH (zone DNS de concepton.fr) : enregistrement A « ${DOMAINE%%.*} » vers $IP."
echo "Ensuite : https://$DOMAINE (le certificat HTTPS se crée tout seul quelques minutes après)."
