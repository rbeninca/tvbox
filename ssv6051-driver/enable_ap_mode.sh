#!/usr/bin/env bash
# enable_ap_mode.sh — habilita AP mode no driver SSV6051 e configura hostapd
# Execute no TX9 como root: bash enable_ap_mode.sh
#
# O que este script faz:
#   1. Aplica o patch start_ap/stop_ap no driver
#   2. Liga hw_cap_ap = on no ssv6051-wifi.cfg
#   3. Recompila e reinstala o módulo
#   4. Instala e configura hostapd
#   5. Configura iptables NAT para que os clientes Wi-Fi acessem a rede via Ethernet
set -euo pipefail

[[ $EUID -ne 0 ]] && { echo "Execute como root: sudo bash $0"; exit 1; }

##############################################################################
# Configurações — ajuste conforme necessário
##############################################################################
SSID="TX9-AP"
PASSPHRASE="tx9armbian"          # mínimo 8 caracteres
CHANNEL=6
AP_IP="192.168.99.1"
DHCP_RANGE="192.168.99.10,192.168.99.50,12h"
WAN_IFACE="eth0"                 # interface de saída para internet
AP_IFACE="wlan0"

DRIVER_DIR="/root/ssv6051-driver/6051"
SRC_DIR="$DRIVER_DIR/ssv6xxx"
KVER=$(uname -r)
HDIR="/usr/src/linux-headers-$KVER"
MOD_DEST="/lib/modules/$KVER/kernel/drivers/net/wireless/ssv6051"
FW_DEST="/lib/firmware"

##############################################################################
# 1. Verificar pré-requisitos
##############################################################################
echo "=== [1/6] Verificando pré-requisitos ==="

if [ ! -d "$SRC_DIR" ]; then
    echo "Driver não encontrado em $SRC_DIR"
    echo "Clone primeiro: git clone https://github.com/eloirotava/6051.git $DRIVER_DIR"
    exit 1
fi

if [ ! -d "$HDIR" ]; then
    echo "Headers do kernel não encontrados: $HDIR"
    echo "Instale: apt install linux-headers-current-meson64"
    exit 1
fi

apt-get install -y patch hostapd dnsmasq iptables-persistent 2>/dev/null || \
apt-get install -y patch hostapd dnsmasq iptables

##############################################################################
# 2. Aplicar patch start_ap/stop_ap
##############################################################################
echo "=== [2/6] Aplicando patch start_ap/stop_ap em dev.c ==="

cd "$DRIVER_DIR"

python3 - <<'PYEOF'
import sys

devpath = "ssv6xxx/smac/dev.c"
with open(devpath) as f:
    src = f.read()

if "ssv6200_start_ap" in src:
    print("Patch já presente no dev.c — pulando.")
    sys.exit(0)

new_funcs = """\

/*
 * start_ap / stop_ap — callbacks requeridos pelo mac80211 em kernels >= 6.1.
 *
 * O mac80211 ainda chama bss_info_changed() com BSS_CHANGED_BEACON_ENABLED
 * após start_ap retornar, então o handler existente de bss_info_changed faz o
 * trabalho real do beacon. Esses callbacks apenas inicializam beacon_interval
 * para que bss_info_changed encontre estado consistente.
 */
#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 1, 0)
static int ssv6200_start_ap(struct ieee80211_hw *hw,
\t\t\t    struct ieee80211_vif *vif,
\t\t\t    struct ieee80211_bss_conf *link_conf)
{
\tstruct ssv_softc *sc = hw->priv;
\tdev_dbg(sc->dev, "[AP] start_ap: beacon_int=%u dtim=%u\\n",
\t\tlink_conf->beacon_int, link_conf->dtim_period);
\tmutex_lock(&sc->mutex);
\tsc->beacon_interval = link_conf->beacon_int ? link_conf->beacon_int : 100;
\tsc->beacon_dtim_cnt = (link_conf->dtim_period > 0)
\t\t\t      ? link_conf->dtim_period - 1 : 0;
\tssv6xxx_beacon_set_info(sc, sc->beacon_interval, sc->beacon_dtim_cnt);
\tmutex_unlock(&sc->mutex);
\treturn 0;
}

static void ssv6200_stop_ap(struct ieee80211_hw *hw,
\t\t\t    struct ieee80211_vif *vif,
\t\t\t    struct ieee80211_bss_conf *link_conf)
{
\tstruct ssv_softc *sc = hw->priv;
\tdev_dbg(sc->dev, "[AP] stop_ap\\n");
\tmutex_lock(&sc->mutex);
\tssv6xxx_beacon_enable(sc, false);
\tmutex_unlock(&sc->mutex);
}
#else
static int ssv6200_start_ap(struct ieee80211_hw *hw, struct ieee80211_vif *vif)
{
\tstruct ssv_softc *sc = hw->priv;
\tmutex_lock(&sc->mutex);
\tsc->beacon_interval = vif->bss_conf.beacon_int ? vif->bss_conf.beacon_int : 100;
\tsc->beacon_dtim_cnt = (vif->bss_conf.dtim_period > 0)
\t\t\t      ? vif->bss_conf.dtim_period - 1 : 0;
\tssv6xxx_beacon_set_info(sc, sc->beacon_interval, sc->beacon_dtim_cnt);
\tmutex_unlock(&sc->mutex);
\treturn 0;
}

static void ssv6200_stop_ap(struct ieee80211_hw *hw, struct ieee80211_vif *vif)
{
\tstruct ssv_softc *sc = hw->priv;
\tmutex_lock(&sc->mutex);
\tssv6xxx_beacon_enable(sc, false);
\tmutex_unlock(&sc->mutex);
}
#endif

"""

# Inserir as funções antes de ssv6200_ops
marker = "struct ieee80211_ops ssv6200_ops = {"
if marker not in src:
    print("ERRO: marcador 'ssv6200_ops' não encontrado em dev.c", file=sys.stderr)
    sys.exit(1)
src = src.replace(marker, new_funcs + marker, 1)

# Adicionar .start_ap e .stop_ap após .bss_info_changed na struct de ops
old_ops = "\t.bss_info_changed = ssv6200_bss_info_changed,\n\t.sta_add"
new_ops = ("\t.bss_info_changed = ssv6200_bss_info_changed,\n"
           "\t.start_ap = ssv6200_start_ap,\n"
           "\t.stop_ap  = ssv6200_stop_ap,\n"
           "\t.sta_add")
if old_ops not in src:
    print("ERRO: padrão '.bss_info_changed...sta_add' não encontrado em dev.c", file=sys.stderr)
    sys.exit(1)
src = src.replace(old_ops, new_ops, 1)

with open(devpath, "w") as f:
    f.write(src)
print("dev.c modificado com sucesso.")
PYEOF

##############################################################################
# 3. Habilitar hw_cap_ap no arquivo de configuração
##############################################################################
echo "=== [3/6] Habilitando hw_cap_ap no ssv6051-wifi.cfg ==="

CFG_SRC="$SRC_DIR/ssv6051-wifi.cfg"
sed -i 's/^hw_cap_ap = off/hw_cap_ap = on/' "$CFG_SRC"
grep hw_cap_ap "$CFG_SRC"

# Também atualizar o que já está em /lib/firmware
sed -i 's/^hw_cap_ap = off/hw_cap_ap = on/' "$FW_DEST/ssv6051-wifi.cfg" 2>/dev/null || true

##############################################################################
# 4. Recompilar e reinstalar o módulo
##############################################################################
echo "=== [4/6] Compilando módulo ssv6051 ==="

# Corrigir version magic (mesmo procedimento do rebuild_wifi_v3.sh)
EXTRAVERSION=$(echo "$KVER" | sed 's/[0-9.]*//')
sed -i "s/^EXTRAVERSION =.*/EXTRAVERSION = $EXTRAVERSION/" "$HDIR/Makefile"
echo "#define UTS_RELEASE \"$KVER\"" > "$HDIR/include/generated/utsrelease.h"

cd "$SRC_DIR"
make clean || true
make KBUILD="$HDIR"

mkdir -p "$MOD_DEST"
cp ssv6051.ko "$MOD_DEST/"
cp ssv6051-wifi.cfg "$FW_DEST/"
cp ssv6051-sw.bin   "$FW_DEST/" 2>/dev/null || true
depmod -a

# Recarregar módulo
modprobe -r ssv6051 2>/dev/null || true
sleep 1
modprobe ssv6051

sleep 2
echo "Interfaces suportadas pelo driver:"
iw phy phy0 info 2>/dev/null | grep -A10 "Supported interface modes" || \
    iw list 2>/dev/null | grep -A10 "Supported interface modes"

##############################################################################
# 5. Configurar hostapd
##############################################################################
echo "=== [5/6] Configurando hostapd ==="

systemctl stop hostapd 2>/dev/null || true

# Desvincular APENAS wlan0 do NetworkManager — NÃO parar o serviço (evita perder eth0)
NM_CONF=/etc/NetworkManager/NetworkManager.conf
if [ -f "$NM_CONF" ]; then
    if ! grep -q "unmanaged-devices" "$NM_CONF"; then
        cat >> "$NM_CONF" << EOF

[keyfile]
unmanaged-devices=interface-name:$AP_IFACE
EOF
    fi
    # Recarregar NM para aplicar a exclusão do wlan0 sem derrubar eth0
    systemctl reload NetworkManager 2>/dev/null || true
fi

cat > /etc/hostapd/hostapd.conf << EOF
interface=$AP_IFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CHANNEL
ieee80211n=0
wmm_enabled=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSPHRASE
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

# Garantir DAEMON_CONF no /etc/default/hostapd (sem duplicar)
if ! grep -q '^DAEMON_CONF=' /etc/default/hostapd 2>/dev/null; then
    echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd
fi

##############################################################################
# 6. Configurar IP, dnsmasq (DHCP) e NAT
##############################################################################
echo "=== [6/6] Configurando rede AP (IP + DHCP + NAT) ==="

# IP estático na interface AP
ip link set "$AP_IFACE" up || true
ip addr flush dev "$AP_IFACE" 2>/dev/null || true
ip addr add "$AP_IP/24" dev "$AP_IFACE"

# dnsmasq para DHCP apenas (port=0 desativa DNS para não colidir com systemd-resolved)
cat > /etc/dnsmasq.d/tx9-ap.conf << EOF
port=0
bind-interfaces
interface=$AP_IFACE
dhcp-range=$DHCP_RANGE
dhcp-option=3,$AP_IP
dhcp-option=6,8.8.8.8,8.8.4.4
EOF

# IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
sed -i 's/^#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf 2>/dev/null || \
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# NAT
iptables -t nat -A POSTROUTING -o "$WAN_IFACE" -j MASQUERADE 2>/dev/null || true
iptables -A FORWARD -i "$AP_IFACE" -o "$WAN_IFACE" -j ACCEPT 2>/dev/null || true
iptables -A FORWARD -i "$WAN_IFACE" -o "$AP_IFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
netfilter-persistent save 2>/dev/null || true

# Persistir o IP no boot
cat > /etc/systemd/system/tx9-ap-setup.service << EOF
[Unit]
Description=TX9 AP mode network setup
After=network.target
Before=hostapd.service dnsmasq.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'ip addr add $AP_IP/24 dev $AP_IFACE 2>/dev/null || true; echo 1 > /proc/sys/net/ipv4/ip_forward'

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable tx9-ap-setup.service

# Iniciar serviços
systemctl unmask hostapd 2>/dev/null || true
systemctl enable hostapd dnsmasq
systemctl restart dnsmasq
systemctl restart hostapd

echo ""
echo "================================================================="
echo "AP mode configurado!"
echo "  SSID     : $SSID"
echo "  Senha    : $PASSPHRASE"
echo "  Canal    : $CHANNEL"
echo "  IP AP    : $AP_IP"
echo "  DHCP     : ${DHCP_RANGE%%,*} .. $(echo $DHCP_RANGE | cut -d, -f2)"
echo "================================================================="
echo ""
echo "Verificar status:"
echo "  systemctl status hostapd"
echo "  iw dev $AP_IFACE info"
echo "  journalctl -u hostapd -f"
echo ""
echo "Se hostapd falhar, verifique:"
echo "  iw phy phy0 info | grep -A10 'Supported interface modes'"
echo "  # 'AP' deve aparecer na lista"
