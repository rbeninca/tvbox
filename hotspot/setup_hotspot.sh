#!/bin/bash

# Script para configurar Hotspot Wi-Fi com compartilhamento de Internet
# e configurar os serviços de inicialização e display.
# Uso: sudo ./setup_hotspot.sh

set -e

SSID="balancaGFIG"
PASSWORD="aabbccddee"
CON_NAME="balancaGFIG"

# 1. Detectar interfaces
if ip link show wlan1 > /dev/null 2>&1; then
    WIFI_INT="wlan1"
else
    WIFI_INT="wlan0"
fi

echo "--- Configurando Hotspot Wi-Fi ---"
echo "Usando interface: $WIFI_INT"

# 2. Instalar dependências se necessário
if ! dpkg -l | grep -q dnsmasq-base; then
    echo "Instalando dnsmasq-base..."
    sudo apt-get update -qq
    sudo apt-get install -y dnsmasq-base
fi

# 3. Habilitar IP Forwarding
echo "Habilitando IP Forwarding..."
sudo sysctl -w net.ipv4.ip_forward=1 | sudo tee /dev/null
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
fi

# 4. Configurar a conexão no NetworkManager
echo "Configurando conexão '$CON_NAME'..."
sudo nmcli connection delete "$CON_NAME" > /dev/null 2>&1 || true
sudo nmcli connection add \
    type wifi \
    ifname "$WIFI_INT" \
    con-name "$CON_NAME" \
    autoconnect yes \
    ssid "$SSID" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    ipv4.method shared \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.proto rsn \
    wifi-sec.group ccmp \
    wifi-sec.pairwise ccmp \
    wifi-sec.psk "$PASSWORD"

# 5. Criar o serviço de inicialização do Hotspot
echo "Criando serviço systemd tx9-hotspot.service..."
sudo tee /etc/systemd/system/tx9-hotspot.service <<EOF
[Unit]
Description=TX9 Hotspot Activation
After=network.target NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=oneshot
ExecStart=/usr/bin/nmcli connection up id $CON_NAME
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# 6. Configurar o script e serviço do Display
echo "Configurando loop de informações no display..."
sudo mkdir -p /opt/tx9/hotspot
sudo cp /root/display_hotspot.sh /opt/tx9/hotspot/display_hotspot.sh
sudo chmod +x /opt/tx9/hotspot/display_hotspot.sh

sudo tee /etc/systemd/system/tx9-hotspot-display.service <<EOF
[Unit]
Description=TX9 Hotspot Info Display Loop
After=tx9-display.service tx9-hotspot.service
Wants=tx9-display.service tx9-hotspot.service

[Service]
Type=simple
ExecStart=/bin/bash /opt/tx9/hotspot/display_hotspot.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 7. Ativar e Iniciar os serviços
echo "Ativando serviços..."
sudo systemctl daemon-reload
sudo systemctl enable tx9-hotspot.service
sudo systemctl enable tx9-hotspot-display.service

echo "Iniciando Hotspot e Display..."
sudo systemctl start tx9-hotspot.service
sudo systemctl start tx9-hotspot-display.service

echo "--- Configuração Concluída com Sucesso ---"
echo "O Hotspot iniciará automaticamente no boot."
echo "As informações (SSID/Senha/IP) serão exibidas no display frontal."
echo "----------------------------------------"
