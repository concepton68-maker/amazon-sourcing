@echo off
chcp 65001 >nul
title Cle de connexion au serveur
set CLE=%USERPROFILE%\.ssh\syllig_vente
if not exist "%USERPROFILE%\.ssh" mkdir "%USERPROFILE%\.ssh"
if not exist "%CLE%" ssh-keygen -q -t ed25519 -N "" -C "pc-syllig-vente" -f "%CLE%"
if not exist "%CLE%.pub" goto erreur
type "%CLE%.pub" | clip
echo.
echo  La cle PUBLIQUE est copiee. Dans OVH (Reinstaller mon VPS), cliquez dans le cadre "Votre cle SSH Publique" puis Ctrl+V.
echo  Elle commence par ssh-ed25519. Rien de secret : la partie secrete reste sur ce PC.
echo.
type "%CLE%.pub"
echo.
pause
exit /b 0
:erreur
echo La cle n a pas pu etre creee. Faites une capture de cette fenetre et envoyez-la a Claude.
pause
exit /b 1
