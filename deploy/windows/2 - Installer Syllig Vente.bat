@echo off
chcp 65001 >nul
title Installation de Syllig Vente
cd /d "%~dp0"
set CLE=%USERPROFILE%\.ssh\syllig_vente
if not exist "%CLE%" (
  echo Cle absente : lancez d abord "1 - Creer ma cle.bat", puis reinstallez le VPS chez OVH avec cette cle.
  pause
  exit /b 1
)
set /p IP=Adresse IP du serveur : 
set DOMAINE=vente.concepton.fr
ssh-keygen -R %IP% >nul 2>&1
set OPT=-i "%CLE%" -o IdentitiesOnly=yes -o PreferredAuthentications=publickey -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15
set UTIL=debian
echo.
echo Connexion au serveur. S il demande de changer le mot de passe :
echo   Current password = mot de passe du dernier courriel d OVH (collage : clic droit), puis 2 fois un nouveau mot de passe.
echo   Si la connexion se ferme juste apres, relancez ce fichier : c est normal.
ssh -t %OPT% %UTIL%@%IP% "echo Connexion reussie." || goto erreur
echo Connexion reussie avec l utilisateur %UTIL%.
scp %OPT% installer.sh %UTIL%@%IP%:/tmp/installer-syllig-vente.sh || goto erreur
ssh -t %OPT% %UTIL%@%IP% "if [ $(id -u) = 0 ]; then bash /tmp/installer-syllig-vente.sh %DOMAINE%; else sudo bash /tmp/installer-syllig-vente.sh %DOMAINE%; fi" || goto erreur
echo.
echo Installation terminee.
pause
exit /b 0
:erreur
echo.
echo Une etape a echoue. Capture de cette fenetre pour Claude.
pause
exit /b 1
