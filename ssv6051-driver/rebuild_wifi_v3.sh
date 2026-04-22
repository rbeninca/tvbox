#!/bin/bash
# Script de Reconstrução e Estabilização de Wi-Fi TX9 Pro - V4
set -e

KVER=$(uname -r)
HDIR="/usr/src/linux-headers-$KVER"
MOD_DEST="/lib/modules/$KVER/kernel/drivers/net/wireless/ssv6051"
FW_DEST="/lib/firmware"
SRC_DIR="/root/ssv6051-driver/6051/ssv6xxx"

echo "=== Iniciando Manutenção Completa de Wi-Fi TX9 Pro (Kernel $KVER) ==="

# 1. Preparar Cabeçalhos do Kernel
echo "[1/4] Ajustando cabeçalhos do Kernel para Version Magic..."
if [ ! -d "$HDIR" ]; then
    echo "Erro: Cabeçalhos do kernel não encontrados em $HDIR"
    echo "Execute: apt install -y linux-headers-current-meson64"
    exit 1
fi

cd "$HDIR"
# Força o EXTRAVERSION para bater com o uname -r (ex: -current-meson64)
EXTRAVERSION=$(echo $KVER | sed 's/[0-9.]*//')
sed -i "s/^EXTRAVERSION =.*/EXTRAVERSION = $EXTRAVERSION/" Makefile
echo "#define UTS_RELEASE \"$KVER\"" > include/generated/utsrelease.h

# 2. Recompilar Driver
echo "[2/4] Recompilando Driver SSV6051..."
if [ -d "$SRC_DIR" ]; then
    cd "$SRC_DIR"
    make clean || true
    make KBUILD="$HDIR"
    
    echo "Instalando módulo em $MOD_DEST..."
    mkdir -p "$MOD_DEST"
    cp ssv6051.ko "$MOD_DEST/"
    depmod -a
else
    echo "Erro: Código fonte não encontrado em $SRC_DIR"
    exit 1
fi

# 3. Instalar Firmware e Configurações de Hardware
echo "[3/4] Instalando Firmware e Configurações em $FW_DEST..."
cp "$SRC_DIR/ssv6051-wifi.cfg" "$FW_DEST/"
cp "$SRC_DIR/ssv6051-sw.bin" "$FW_DEST/"

# Garantir carregamento no boot
echo "ssv6051" > /etc/modules-load.d/ssv6051.conf

# 4. Aplicar Correções de Estabilidade (Power Management)
echo "[4/4] Configurando Dispatcher para estabilidade (Power Save Off)..."
cat <<EOF > /etc/NetworkManager/dispatcher.d/99-ssv6051-fix
#!/bin/sh
INTERFACE=\$1
ACTION=\$2
if [ "\$INTERFACE" = "wlan0" ] && [ "\$ACTION" = "up" ]; then
    /usr/sbin/iw dev wlan0 set power_save off
fi
EOF
chmod +x /etc/NetworkManager/dispatcher.d/99-ssv6051-fix

# Carregar agora
echo "Ativando módulo e aplicando configurações..."
modprobe ssv6051 || true
if [ -d /sys/class/net/wlan0 ]; then
    /usr/sbin/iw dev wlan0 set power_save off || true
    echo "Wi-Fi wlan0 detectado e Power Save desativado."
fi

echo "=== Processo Concluído! Wi-Fi pronto e persistente. ==="
