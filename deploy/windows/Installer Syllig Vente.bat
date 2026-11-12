@echo off
chcp 65001 >nul
title Installation de Syllig Vente
cd /d "%~dp0"
echo.
echo  Installation de Syllig Vente sur le serveur OVH
echo  Les mots de passe se tapent ici, jamais dans le chat. Ils ne s affichent pas quand vous tapez : c est normal.
echo.
set /p IP=Adresse IP du serveur (courriel d OVH) : 
set UTIL=debian
set /p UTIL=Utilisateur du serveur [debian] : 
set DOMAINE=vente.concepton.fr
echo.
echo Premiere connexion. Si le serveur demande de changer le mot de passe :
echo   "Current password" = mot de passe du courriel d OVH, puis deux fois votre nouveau mot de passe (a garder pour vous).
ssh -t -o StrictHostKeyChecking=accept-new %UTIL%@%IP% "echo Connexion au serveur reussie."
echo.
echo Envoi du programme d installation (mot de passe du serveur : le nouveau s il a ete change)...
scp -o StrictHostKeyChecking=accept-new installer.sh %UTIL%@%IP%:/tmp/installer-syllig-vente.sh
if errorlevel 1 goto erreur
ssh -t -o StrictHostKeyChecking=accept-new %UTIL%@%IP% "if command -v sudo >/dev/null; then sudo bash /tmp/installer-syllig-vente.sh %DOMAINE%; else bash /tmp/installer-syllig-vente.sh %DOMAINE%; fi"
if errorlevel 1 goto erreur
echo.
echo Installation terminee.
pause
exit /b 0
:erreur
echo.
echo Une etape a echoue. Faites une capture de cette fenetre et envoyez-la a Claude.
pause
exit /b 1
