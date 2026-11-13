@echo off
chcp 65001 >nul
title Test Amazon SP-API
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0test-amazon.ps1"
