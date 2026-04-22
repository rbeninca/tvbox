#!/bin/bash
# Script de Reconstrução de Rede TX9 Pro - V2 (Resistente a Upgrades)

set -e

# Detectar Kernel Atual
KVER=$(uname -r)
HDIR="/usr/src/linux-headers-$KVER"
MOD_DEST="/lib/modules/$KVER/kernel/drivers/net/wireless/ssv6051"

echo "=== Iniciando Reparo de Rede TX9 Pro (Kernel $KVER) ==="

# 1. Corrigir Ethernet (Restaurar DTB Mestre se necessário)
echo "[1/3] Verificando integridade do DTB..."
# No seu caso, o p281 genérico do upgrade costuma quebrar a Ethernet do TX9
# Vamos garantir que o DTB correto esteja em uso se tivermos o backup
if [ -f /root/android_tx9.dtb ]; then

# 2. Preparar Cabeçalhos para o novo Kernel
echo "[2/3] Preparando cabeçalhos do Kernel $KVER..."
if [ ! -d "$HDIR" ]; then
    echo "Instalando cabeçalhos faltantes..."
    apt update && apt install -y linux-headers-current-meson64
fi

# Ajustar VERSION MAGIC (Crucial para o Armbian aceitar o driver)
cd "$HDIR"
# Extrair a versão exata que o kernel espera
# O Armbian muitas vezes anexa strings como "-current-meson64"
EXTRAVERSION=$(echo $KVER | sed 's/[0-9.]*//')
echo "Ajustando Makefile com EXTRAVERSION=$EXTRAVERSION"
sed -i "s/^EXTRAVERSION =.*/EXTRAVERSION = $EXTRAVERSION/" Makefile
# Gerar utsrelease.h
echo "#define UTS_RELEASE \"$KVER\"" > include/generated/utsrelease.h

# 3. Recompilar Wi-Fi
echo "[3/3] Recompilando Driver SSV6051..."
if [ -d /root/ssv6051-driver/6051/ssv6xxx ]; then
    cd /root/ssv6051-driver/6051/ssv6xxx
    make clean || true
    make KBUILD="$HDIR"
    
    echo "Instalando módulo..."
    mkdir -p "$MOD_DEST"
    cp ssv6051.ko "$MOD_DEST/"
    depmod -a
    
    # Carregar
    modprobe ssv6051 || echo "Erro ao carregar módulo. Recomenda-se REBOOT."
else
    echo "Erro: Código fonte do driver não encontrado em /root/ssv6051-driver/6051/ssv6xxx"
    exit 1
fi

echo "=== Reparo concluído. Por favor, reinicie a TV Box! ==="
