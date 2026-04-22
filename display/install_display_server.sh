#!/usr/bin/env bash
# install_display_server.sh  install|uninstall|restart|status|send
#
# Uso local:
#   sudo bash install_display_server.sh install
#
# Uso remoto (1 sessao SSH):
#   TARGET_HOST=192.168.1.106 TARGET_USER=root bash install_display_server.sh install
#   TARGET_HOST=192.168.1.106 bash install_display_server.sh send '{"cmd":"scroll","text":"OLA"}'
set -euo pipefail

ACTION=${1:-}
SEND_PAYLOAD=${2:-}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

REMOTE_ROOT=/opt/tx9/display
SOCKET_PATH=/run/tx9-display.sock
REMOTE_ENV=/etc/default/tx9-display
REMOTE_LAUNCHER=/usr/local/bin/tx9-display
REMOTE_BOOT_LAUNCHER=/usr/local/bin/tx9-display-boot
SERVICE_NAME=tx9-display.service
BOOT_SERVICE_NAME=tx9-display-boot.service
REMOTE_UNIT=/etc/systemd/system/${SERVICE_NAME}
REMOTE_BOOT_UNIT=/etc/systemd/system/${BOOT_SERVICE_NAME}

TARGET_HOST=${TARGET_HOST:-}
TARGET_USER=${TARGET_USER:-root}

# ---------------------------------------------------------------------------
# Uso
# ---------------------------------------------------------------------------

usage() {
  cat >&2 <<'USAGE'
Uso:
  install_display_server.sh  install
  install_display_server.sh  uninstall
  install_display_server.sh  restart
  install_display_server.sh  status
  install_display_server.sh  send '<json>'

Variaveis de ambiente (execucao remota):
  TARGET_HOST=192.168.1.106
  TARGET_USER=root  (padrao)
USAGE
  exit 1
}

[[ -z "$ACTION" ]] && usage

# ---------------------------------------------------------------------------
# Arquivos necessarios para install
# ---------------------------------------------------------------------------

REQUIRED_FILES=(
  display_driver.py
  display_server.py
  display_client.py
  display_boot.py
  backgrounds/__init__.py
  backgrounds/bg_clock_ip.py
)

check_files() {
  local missing=0
  for f in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$SCRIPT_DIR/$f" ]]; then
      echo "Arquivo nao encontrado: $SCRIPT_DIR/$f" >&2
      missing=1
    fi
  done
  [[ $missing -eq 0 ]] || exit 1
}

# ---------------------------------------------------------------------------
# Helper: executa bloco shell local ou via SSH (1 sessao)
# ---------------------------------------------------------------------------

run_remote() {
  local payload
  payload=$(cat)
  if [[ -z "$TARGET_HOST" ]]; then
    bash -s <<< "$payload"
  else
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        "${TARGET_USER}@${TARGET_HOST}" bash -s <<< "$payload"
  fi
}

# ---------------------------------------------------------------------------
# Acoes simples
# ---------------------------------------------------------------------------

do_status() {
  run_remote <<REMOTE
systemctl status ${SERVICE_NAME} --no-pager || true
echo "---"
systemctl status ${BOOT_SERVICE_NAME} --no-pager || true
REMOTE
}

do_restart() {
  run_remote <<REMOTE
systemctl restart ${SERVICE_NAME}
sleep 1
systemctl status ${SERVICE_NAME} --no-pager
REMOTE
}

do_send() {
  [[ -z "$SEND_PAYLOAD" ]] && { echo "Payload JSON obrigatorio para 'send'" >&2; exit 1; }
  run_remote <<REMOTE
python3 -c "
import socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('${SOCKET_PATH}')
s.sendall(b'${SEND_PAYLOAD}\n')
print(s.recv(256).decode())
s.close()
"
REMOTE
}

do_uninstall() {
  echo "==> Desinstalando servicos TX9 display..."
  run_remote <<REMOTE
set -e
systemctl stop    ${SERVICE_NAME} ${BOOT_SERVICE_NAME} 2>/dev/null || true
systemctl disable ${SERVICE_NAME} ${BOOT_SERVICE_NAME} 2>/dev/null || true
rm -f  "${REMOTE_UNIT}" "${REMOTE_BOOT_UNIT}"
rm -f  "${REMOTE_ENV}" "${REMOTE_LAUNCHER}" "${REMOTE_BOOT_LAUNCHER}"
rm -f  /usr/local/bin/tx9-show
rm -rf "${REMOTE_ROOT}"
systemctl daemon-reload
echo "Desinstalacao concluida."
REMOTE
}

# ---------------------------------------------------------------------------
# INSTALL
# ---------------------------------------------------------------------------

do_install() {
  check_files

  echo "==> Copiando arquivos para ${TARGET_HOST:-localhost}..."

  # Codifica cada arquivo em base64 para transferencia via heredoc
  local b64_driver b64_server b64_client b64_boot b64_bg_init b64_bg_clock

  b64_driver=$(base64 -w0   < "$SCRIPT_DIR/display_driver.py")
  b64_server=$(base64 -w0   < "$SCRIPT_DIR/display_server.py")
  b64_client=$(base64 -w0   < "$SCRIPT_DIR/display_client.py")
  b64_boot=$(base64 -w0     < "$SCRIPT_DIR/display_boot.py")
  b64_bg_init=$(base64 -w0  < "$SCRIPT_DIR/backgrounds/__init__.py")
  b64_bg_clock=$(base64 -w0 < "$SCRIPT_DIR/backgrounds/bg_clock_ip.py")

  run_remote <<REMOTE_EOF
set -e

mkdir -p "${REMOTE_ROOT}/backgrounds" \
         /etc/default /etc/systemd/system /usr/local/bin

# Copia arquivos Python
printf '%s' "${b64_driver}"    | base64 -d > "${REMOTE_ROOT}/display_driver.py"
printf '%s' "${b64_server}"    | base64 -d > "${REMOTE_ROOT}/display_server.py"
printf '%s' "${b64_client}"    | base64 -d > "${REMOTE_ROOT}/display_client.py"
printf '%s' "${b64_boot}"      | base64 -d > "${REMOTE_ROOT}/display_boot.py"
printf '%s' "${b64_bg_init}"   | base64 -d > "${REMOTE_ROOT}/backgrounds/__init__.py"
printf '%s' "${b64_bg_clock}"  | base64 -d > "${REMOTE_ROOT}/backgrounds/bg_clock_ip.py"

chmod 0755 "${REMOTE_ROOT}"/*.py "${REMOTE_ROOT}/backgrounds"/*.py

# Configuracao (nao sobrescreve se ja existir)
if [[ ! -f "${REMOTE_ENV}" ]]; then
cat > "${REMOTE_ENV}" <<'ENVEOF'
# Brilho: 0x10 (minimo) a 0x70 (maximo)
DISPLAY_BRIGHTNESS=0x10

# Tarefa de fundo: clock_ip | clock | none
DISPLAY_BACKGROUND=clock_ip

# Argumentos do contador de boot
DISPLAY_BOOT_ARGS=--fim 9999 --delay 0.05 --loop --manter-ao-sair
ENVEOF
fi

# Launcher principal
cat > "${REMOTE_LAUNCHER}" <<'LAUNCHEOF'
#!/usr/bin/env bash
source /etc/default/tx9-display 2>/dev/null || true
exec /usr/bin/python3 /opt/tx9/display/display_server.py \
     --brightness "\${DISPLAY_BRIGHTNESS:-0x10}" \
     --background "\${DISPLAY_BACKGROUND:-clock_ip}"
LAUNCHEOF
chmod 0755 "${REMOTE_LAUNCHER}"

# Launcher de boot
cat > "${REMOTE_BOOT_LAUNCHER}" <<'BOOTEOF'
#!/usr/bin/env bash
source /etc/default/tx9-display 2>/dev/null || true
# shellcheck disable=SC2086
exec /usr/bin/python3 /opt/tx9/display/display_boot.py \
     \${DISPLAY_BOOT_ARGS:---fim 9999 --delay 0.05 --loop --manter-ao-sair}
BOOTEOF
chmod 0755 "${REMOTE_BOOT_LAUNCHER}"

# CLI global
ln -sf "${REMOTE_ROOT}/display_client.py" /usr/local/bin/tx9-show

# Servico de boot (fase inicial, sem rede)
cat > "${REMOTE_BOOT_UNIT}" <<'UNITEOF'
[Unit]
Description=TX9 display boot counter
DefaultDependencies=no
After=local-fs.target
Before=basic.target network-pre.target tx9-display.service
Conflicts=shutdown.target tx9-display.service

[Service]
Type=simple
User=root
EnvironmentFile=-/etc/default/tx9-display
WorkingDirectory=/opt/tx9/display
ExecStart=/usr/local/bin/tx9-display-boot
Restart=on-failure
RestartSec=2
TimeoutStopSec=3

[Install]
WantedBy=basic.target
UNITEOF

# Servico principal (servidor IPC)
cat > "${REMOTE_UNIT}" <<'UNITEOF'
[Unit]
Description=TX9 display server
After=network-online.target tx9-display-boot.service
Wants=network-online.target
Conflicts=tx9-display-boot.service

[Service]
Type=simple
User=root
EnvironmentFile=-/etc/default/tx9-display
WorkingDirectory=/opt/tx9/display
ExecStart=/usr/local/bin/tx9-display
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNITEOF

systemctl daemon-reload
systemctl enable "${BOOT_SERVICE_NAME}" "${SERVICE_NAME}"
systemctl stop   "${BOOT_SERVICE_NAME}" 2>/dev/null || true
systemctl restart "${SERVICE_NAME}" 2>/dev/null || systemctl start "${SERVICE_NAME}"
sleep 2

echo ""
echo "Instalado em ${REMOTE_ROOT}/"
echo "Config : /etc/default/tx9-display"
echo "CLI    : tx9-show <comando>"
echo ""
systemctl status "${SERVICE_NAME}" --no-pager
REMOTE_EOF
}

# ---------------------------------------------------------------------------
# Despacho
# ---------------------------------------------------------------------------

case "$ACTION" in
  install)   do_install   ;;
  uninstall) do_uninstall ;;
  restart)   do_restart   ;;
  status)    do_status    ;;
  send)      do_send      ;;
  *)         usage        ;;
esac
