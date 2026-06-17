@echo off
title Procurando Servidor
color 0A
echo Tentando conectar com meuservidor.local...
ping -n 1 -w 2000 meuservidor.local >nul
if %errorlevel% equ 0 (
    echo [SUCESSO] O servidor respondeu!
    timeout /t 3 >nul
    start http://meuservidor.local/nextcloud
) else (
    color 0C
    echo [AGUARDE] Ainda instalando. Tente de novo daqui a pouco!
    pause
)
