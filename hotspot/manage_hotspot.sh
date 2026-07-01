#!/usr/bin/env bash
# manage_hotspot.sh - Ferramenta para gerenciar Hotspot e Conexão Wi-Fi no TX9
# Autor: Gemini CLI Agent

set -e

# Cores para o terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE}          Gerenciador de Wi-Fi/Hotspot TX9           ${NC}"
echo -e "${BLUE}=====================================================${NC}"

# Verificar se é root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Este script deve ser executado como root (sudo).${NC}"
   exit 1
fi

# Funções Utilitárias
list_interfaces() {
    echo -e "${YELLOW}Buscando interfaces Wi-Fi...${NC}"
    # Busca interfaces que o iw reconhece como wireless ou que o nmcli identifica
    WIFI_INTERFACES=($(nmcli -t -f DEVICE,TYPE device | grep wifi | cut -d: -f1))
    
    if [ ${#WIFI_INTERFACES[@]} -eq 0 ]; then
        echo -e "${RED}Nenhuma interface Wi-Fi encontrada!${NC}"
        return 1
    fi

    echo -e "Interfaces encontradas:"
    for i in "${!WIFI_INTERFACES[@]}"; do
        echo -e "  [$i] ${WIFI_INTERFACES[$i]}"
    done
    return 0
}

speed_test() {
    local iface=$1
    echo -e "${YELLOW}Preparando interface $iface para teste...${NC}"
    ip link set "$iface" up 2>/dev/null || true
    
    echo -e "${YELLOW}Realizando teste de velocidade na interface $iface...${NC}"
    echo -e "Isso pode levar alguns segundos (baixando 10MB de teste)..."
    
    # Tenta usar curl para um teste rápido se speedtest-cli não existir
    # Usando um arquivo de teste do Fast.com ou similar se possível, ou apenas um download genérico
    # Nota: O teste de velocidade precisa de internet. Se estiver criando um hotspot, o teste deve ser feito ANTES ou via Ethernet.
    
    local start_time=$(date +%s)
    # Download de 10MB do DigitalOcean (exemplo)
    local test_url="http://speedtest.tele2.net/10MB.zip"
    
    if curl --interface "$iface" -s -o /dev/null "$test_url"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        if [ $duration -eq 0 ]; then duration=1; fi
        local speed=$(( 80 / duration )) # 80 Mbits / duration
        echo -e "${GREEN}Velocidade aproximada de download: ~${speed} Mbps${NC}"
    else
        echo -e "${RED}Falha no teste de velocidade. Verifique se a interface $iface tem acesso à internet.${NC}"
    fi
}

setup_hotspot() {
    local iface=$1
    read -p "Digite o nome da rede (SSID) [TX9_Hotspot]: " ssid
    ssid=${ssid:-TX9_Hotspot}
    read -p "Digite a senha (mínimo 8 caracteres): " password
    
    if [ ${#password} -lt 8 ]; then
        echo -e "${RED}Senha muito curta! Mínimo de 8 caracteres.${NC}"
        return 1
    fi

    echo -e "${YELLOW}Configurando Hotspot na interface $iface...${NC}"
    
    # Remover conexões anteriores de hotspot na mesma interface para evitar conflitos
    nmcli connection delete "Hotspot-$iface" 2>/dev/null || true
    
    if nmcli device wifi hotspot ssid "$ssid" password "$password" ifname "$iface" name "Hotspot-$iface"; then
        echo -e "${GREEN}Hotspot '$ssid' criado com sucesso!${NC}"
        echo -e "IP do dispositivo: $(ip addr show $iface | grep 'inet ' | awk '{print $2}')"
    else
        echo -e "${RED}Erro ao criar hotspot. Verifique se o driver suporta modo AP.${NC}"
    fi
}

connect_wifi() {
    local iface=$1
    echo -e "${YELLOW}Escaneando redes disponíveis...${NC}"
    nmcli device wifi rescan ifname "$iface" 2>/dev/null || true
    nmcli device wifi list ifname "$iface"
    
    read -p "Digite o SSID da rede que deseja conectar: " ssid
    read -s -p "Digite a senha da rede: " password
    echo ""

    echo -e "${YELLOW}Conectando a '$ssid'...${NC}"
    if nmcli device wifi connect "$ssid" password "$password" ifname "$iface"; then
        echo -e "${GREEN}Conectado com sucesso!${NC}"
    else
        echo -e "${RED}Erro ao conectar a '$ssid'.${NC}"
    fi
}

# Menu Principal
main_menu() {
    while true; do
        echo -e "\n${BLUE}--- Menu Principal ---${NC}"
        echo "1) Listar Interfaces e Status"
        echo "2) Teste de Velocidade"
        echo "3) Criar Hotspot (Ponto de Acesso)"
        echo "4) Conectar a uma rede Wi-Fi (Cliente)"
        echo "5) Desconectar/Parar Hotspot"
        echo "0) Sair"
        read -p "Escolha uma opção: " opt

        case $opt in
            1)
                nmcli device status | grep wifi || echo "Nenhuma interface wifi ativa."
                ;;
            2)
                if list_interfaces; then
                    read -p "Escolha o índice da interface para o teste: " idx
                    speed_test "${WIFI_INTERFACES[$idx]}"
                fi
                ;;
            3)
                if list_interfaces; then
                    read -p "Escolha o índice da interface: " idx
                    setup_hotspot "${WIFI_INTERFACES[$idx]}"
                fi
                ;;
            4)
                if list_interfaces; then
                    read -p "Escolha o índice da interface: " idx
                    connect_wifi "${WIFI_INTERFACES[$idx]}"
                fi
                ;;
            5)
                if list_interfaces; then
                    read -p "Escolha o índice da interface: " idx
                    iface="${WIFI_INTERFACES[$idx]}"
                    echo -e "${YELLOW}Desconectando $iface...${NC}"
                    nmcli device disconnect "$iface"
                    nmcli connection delete "Hotspot-$iface" 2>/dev/null || true
                fi
                ;;
            0)
                echo "Saindo..."
                break
                ;;
            *)
                echo -e "${RED}Opção inválida.${NC}"
                ;;
        esac
    done
}

main_menu
