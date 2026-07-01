#!/bin/bash
# rebuild_all_wifi.sh - Reconstroi o driver interno (ssv6051) e configura o USB (rtl8188fu)
# Autor: Gemini CLI Agent
set -e

KVER=$(uname -r)
HDIR="/usr/src/linux-headers-$KVER"
SSV_MOD_DEST="/lib/modules/$KVER/kernel/drivers/net/wireless/ssv6051"
FW_DEST="/lib/firmware"
BASE_DIR="/root/ssv6051-driver/6051"
SSV_SRC_DIR="$BASE_DIR/ssv6xxx"
RTL_FW_SRC="$BASE_DIR/rtl8188fu/firmware/rtl8188fufw.bin"

echo -e "\033[0;34m=== Iniciando Manutenção Completa de Wi-Fi (Interno + USB) ===\033[0m"

# --- PARTE 1: Wi-Fi Interno (ssv6051) ---
echo -e "\033[1;33m[1/5] Ajustando cabeçalhos do Kernel para ssv6051...\033[0m"
if [ ! -d "$HDIR" ]; then
    echo "Instalando cabeçalhos do kernel faltantes..."
    apt update && apt install -y linux-headers-current-meson64
fi

cd "$HDIR"
EXTRAVERSION=$(echo $KVER | sed 's/[0-9.]*//')
sed -i "s/^EXTRAVERSION =.*/EXTRAVERSION = $EXTRAVERSION/" Makefile
echo "#define UTS_RELEASE \"$KVER\"" > include/generated/utsrelease.h

echo -e "\033[1;33m[2/5] Recompilando Driver ssv6051...\033[0m"
if [ -d "$SSV_SRC_DIR" ]; then
    cd "$SSV_SRC_DIR"
    make clean || true
    make KBUILD="$HDIR"
    
    echo "Instalando módulo em $SSV_MOD_DEST..."
    mkdir -p "$SSV_MOD_DEST"
    cp ssv6051.ko "$SSV_MOD_DEST/"
    depmod -a
    
    echo "Instalando Firmware ssv6051..."
    cp ssv6051-wifi.cfg "$FW_DEST/"
    cp ssv6051-sw.bin   "$FW_DEST/" 2>/dev/null || true
else
    echo -e "\033[0;31mErro: Código fonte ssv6051 não encontrado em $SSV_SRC_DIR\033[0m"
fi

# --- PARTE 2: Wi-Fi USB (RTL8188FU) ---
echo -e "\033[1;33m[3/5] Configurando Adaptador USB RTL8188FU...\033[0m"
if [ -f "$RTL_FW_SRC" ]; then
    mkdir -p /lib/firmware/rtlwifi
    cp "$RTL_FW_SRC" /lib/firmware/rtlwifi/
    echo "Firmware RTL8188FU instalado em /lib/firmware/rtlwifi/"
else
    echo -e "\033[0;31mAviso: Firmware RTL8188FU não encontrado em $RTL_FW_SRC\033[0m"
fi

# Configuração para o driver nativo rtl8xxxu que gerencia o USB
# Desativa power management que causa quedas em adaptadores USB
echo "options rtl8xxxu dmpm_off=1" > /etc/modprobe.d/rtl8xxxu.conf

# --- PARTE 3: Persistência e Estabilidade ---
echo -e "\033[1;33m[4/5] Configurando persistência e estabilidade...\033[0m"
echo "ssv6051" > /etc/modules-load.d/ssv6051.conf

# Script dispatcher para desativar power save em todas as interfaces wifi ao subir
cat <<EOF > /etc/NetworkManager/dispatcher.d/99-wifi-stability
#!/bin/sh
INTERFACE=\$1
ACTION=\$2
if [ "\$ACTION" = "up" ]; then
    # Desativa economia de energia em qualquer interface wlan
    if echo "\$INTERFACE" | grep -q "wlan"; then
        /usr/sbin/iw dev "\$INTERFACE" set power_save off || true
    fi
fi
EOF
chmod +x /etc/NetworkManager/dispatcher.d/99-wifi-stability

# --- PARTE 4: Ativação ---
echo -e "\033[1;33m[5/5] Ativando drivers e aplicando configurações...\033[0m"
modprobe -r ssv6051 2>/dev/null || true
modprobe -r rtl8xxxu 2>/dev/null || true
sleep 1
modprobe ssv6051
modprobe rtl8xxxu

echo -e "\033[0;32m=== Processo Concluído com Sucesso! ===\033[0m"
echo "Interfaces Wi-Fi detectadas:"
ip -br link show | grep wlan
echo ""
echo "Você pode usar o script em /root/hotspot/manage_hotspot.sh para gerenciar as redes."
