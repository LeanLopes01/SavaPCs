#!/bin/bash
exec > /var/log/dietpi_kamikaze.log 2>&1
echo "==============================================="
echo " INICIANDO PROTOCOLO KAMIKAZE (CONECTIVIDADE) "
echo "==============================================="

# Força renovação do IP com os novos parâmetros de DNS injetados
dhclient -r && dhclient

# 1. Garante suporte total a hardware de rede antigo/proprietário antes de instalar os softwares
apt-get update
apt-get install -y firmware-linux-free firmware-realtek network-manager > /dev/null

# 2. Autentica o Tailscale (Se configurado)
echo 'Sem Tailscale'

# 3. Descobre quem é o pendrive atual
USB_DRIVE=$(lsblk -no pkname $(findmnt -n -o SOURCE /) | head -n 1)

# 4. Descobre o HD interno alvo
TARGET_DRIVE=$(lsblk -nd -o NAME,TYPE | awk '$2=="disk" {print $1}' | grep -v "$USB_DRIVE" | head -n 1)

if [ -z "$TARGET_DRIVE" ]; then
    echo "[-] Nenhum HD interno encontrado! Mantendo execução no pendrive."
    exit 0
fi

echo "[+] Clonando sistema para o HD (/dev/$TARGET_DRIVE)..."
dd if=/dev/$USB_DRIVE of=/dev/$TARGET_DRIVE bs=4M status=none

# 5. Corrige tabela de partição e expande para usar 100% do tamanho do HD
apt-get install -y parted gdisk e2fsprogs > /dev/null
sgdisk -e /dev/$TARGET_DRIVE
parted -s /dev/$TARGET_DRIVE resizepart 2 100%

if [[ "$TARGET_DRIVE" == *"nvme"* ]] || [[ "$TARGET_DRIVE" == *"mmcblk"* ]]; then
    TARGET_PART="${TARGET_DRIVE}p2"
else
    TARGET_PART="${TARGET_DRIVE}2"
fi

e2fsck -f -y /dev/$TARGET_PART
resize2fs /dev/$TARGET_PART

echo "[+] PROCESSO CONCLUÍDO COM SUCESSO!"
echo "Desligando a máquina para remoção da mídia USB..."
poweroff
