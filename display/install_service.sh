#!/usr/bin/env bash
# install_service.sh  install|uninstall  [script.py]
#
# Instala ou desinstala o servico systemd tx9-display no Armbian do TX9.
# Usa UMA unica sessao SSH — pede senha apenas uma vez.
#
# Uso local (precisa de sudo):
#   sudo bash display/install_service.sh install
#   sudo bash display/install_service.sh uninstall
#
# Uso remoto:
#   TARGET_HOST=192.168.1.106 TARGET_USER=root bash display/install_service.sh install
#   TARGET_HOST=192.168.1.106 TARGET_USER=root bash display/install_service.sh uninstall
set -euo pipefail

ACTION=${1:-}
SELECTED_SCRIPT=${2:-display_relogio_ip.py}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

SERVICE_NAME=tx9-display.service
REMOTE_ROOT=/opt/tx9/display
REMOTE_LAUNCHER=/usr/local/bin/tx9-display-launcher
REMOTE_ENV=/etc/default/tx9-display
REMOTE_UNIT=/etc/systemd/system/${SERVICE_NAME}

TARGET_HOST=${TARGET_HOST:-}
TARGET_USER=${TARGET_USER:-root}

# ---------------------------------------------------------------------------
# Validacoes iniciais
# ---------------------------------------------------------------------------

if [[ "$ACTION" != "install" && "$ACTION" != "uninstall" ]]; then
  cat >&2 <<'USAGE'
Uso:
  install_service.sh install   [script.py]
  install_service.sh uninstall

Exemplos:
  sudo bash display/install_service.sh install
  TARGET_HOST=192.168.1.106 TARGET_USER=root bash display/install_service.sh install
  TARGET_HOST=192.168.1.106 TARGET_USER=root bash display/install_service.sh uninstall
USAGE
  exit 1
fi

if [[ "$ACTION" == "install" ]]; then
  for py in display_init.py display_relogio.py display_relogio_ip.py; do
    if [[ ! -f "$SCRIPT_DIR/$py" ]]; then
      echo "Arquivo nao encontrado: $SCRIPT_DIR/$py" >&2
      exit 1
    fi
  done
fi

# ---------------------------------------------------------------------------
# Funcao auxiliar: envia bloco de shell para execucao no destino (1 sessao)
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
# UNINSTALL
# ---------------------------------------------------------------------------

do_uninstall() {
  echo "==> Desinstalando ${SERVICE_NAME} ..."
  run_remote <<REMOTE_EOF
set -e
systemctl stop ${SERVICE_NAME}    2>/dev/null || true
systemctl disable ${SERVICE_NAME} 2>/dev/null || true
rm -f  "${REMOTE_UNIT}" "${REMOTE_ENV}" "${REMOTE_LAUNCHER}"
rm -rf "${REMOTE_ROOT}"
systemctl daemon-reload
echo "Desinstalacao concluida."
REMOTE_EOF
}

# ---------------------------------------------------------------------------
# INSTALL — tudo em uma unica sessao SSH via heredoc + base64
# ---------------------------------------------------------------------------

do_install() {
  echo "==> Codificando arquivos Python localmente..."

  local b64_init b64_relogio b64_relogio_ip
  b64_init=$(base64 -w0    < "$SCRIPT_DIR/display_init.py")
  b64_relogio=$(base64 -w0 < "$SCRIPT_DIR/display_relogio.py")
  b64_relogio_ip=$(base64 -w0 < "$SCRIPT_DIR/display_relogio_ip.py")

  echo "==> Instalando em ${TARGET_HOST:-localhost} (1 sessao SSH)..."

  run_remote <<REMOTE_EOF
set -e

# ----- Diretorios -----
mkdir -p "${REMOTE_ROOT}" /etc/default /etc/systemd/system /usr/local/bin

# ----- Scripts Python -----
printf '%s' "${b64_init}"       | base64 -d > "${REMOTE_ROOT}/display_init.py"
printf '%s' "${b64_relogio}"    | base64 -d > "${REMOTE_ROOT}/display_relogio.py"
printf '%s' "${b64_relogio_ip}" | base64 -d > "${REMOTE_ROOT}/display_relogio_ip.py"
chmod 0755 "${REMOTE_ROOT}"/*.py

# ----- Arquivo de configuracao -----
cat > "${REMOTE_ENV}" <<'ENVEOF'
# Script padrao do display TX9.
# Opcoes: display_init.py  display_relogio.py  display_relogio_ip.py
DISPLAY_SCRIPT=${SELECTED_SCRIPT}
ENVEOF

# ----- Launcher -----
cat > "${REMOTE_LAUNCHER}" <<'LAUNCHEOF'
#!/usr/bin/env bash
set -euo pipefail
ENV_FILE=/etc/default/tx9-display
DISPLAY_SCRIPT=display_relogio_ip.py
[[ -f "\${ENV_FILE}" ]] && source "\${ENV_FILE}"
SCRIPT_PATH=/opt/tx9/display/\${DISPLAY_SCRIPT}
if [[ ! -f "\${SCRIPT_PATH}" ]]; then
  echo "Script nao encontrado: \${SCRIPT_PATH}" >&2
  exit 1
fi
exec /usr/bin/env python3 "\${SCRIPT_PATH}"
LAUNCHEOF
chmod 0755 "${REMOTE_LAUNCHER}"

# ----- Unidade systemd -----
cat > "${REMOTE_UNIT}" <<'UNITEOF'
[Unit]
Description=TX9 display service (relogio + IP + icones de rede)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
EnvironmentFile=/etc/default/tx9-display
WorkingDirectory=/opt/tx9/display
ExecStart=/usr/local/bin/tx9-display-launcher
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNITEOF

# ----- Ativar servico -----
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}" 2>/dev/null || systemctl start "${SERVICE_NAME}"
sleep 2
systemctl status "${SERVICE_NAME}" --no-pager
REMOTE_EOF
}

# ---------------------------------------------------------------------------
# Execucao
# ---------------------------------------------------------------------------

if [[ "$ACTION" == "install" ]]; then
  do_install
else
  do_uninstall
fi