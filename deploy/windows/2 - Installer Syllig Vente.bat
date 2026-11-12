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
set UTIL=
for %%U in (debian ubuntu root) do (
  if not defined UTIL ssh %OPT% %%U@%IP% "true" >nul 2>&1 && set UTIL=%%U
)
if not defined UTIL (
  echo.
  echo Le serveur refuse la cle. Il a ete installe sans elle.
  echo Chez OVH : Reinstaller mon VPS, Debian 13, Ctrl+V de la cle dans le cadre, Confirmer. Puis relancez ce fichier 5 minutes apres.
  pause
  exit /b 1
)
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
