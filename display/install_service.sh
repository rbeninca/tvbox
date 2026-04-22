#!/usr/bin/env bash
# install_service.sh  install|uninstall  [script.py]
#
# Instala ou desinstala os servicos systemd do display TX9 no Armbian.
# Instala um contador de boot cedo e o servico principal depois.
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
BOOT_SERVICE_NAME=tx9-display-boot.service
REMOTE_ROOT=/opt/tx9/display
REMOTE_LAUNCHER=/usr/local/bin/tx9-display-launcher
REMOTE_BOOT_LAUNCHER=/usr/local/bin/tx9-display-boot-launcher
REMOTE_ENV=/etc/default/tx9-display
REMOTE_UNIT=/etc/systemd/system/${SERVICE_NAME}
REMOTE_BOOT_UNIT=/etc/systemd/system/${BOOT_SERVICE_NAME}

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
  for py in display_init.py display_relogio.py display_relogio_ip.py display_contador.py; do
    if [[ ! -f "$SCRIPT_DIR/$py" ]]; then
      echo "Arquivo nao encontrado: $SCRIPT_DIR/$py" >&2
      exit 1
    fi
  done

  case "$SELECTED_SCRIPT" in
    display_init.py|display_relogio.py|display_relogio_ip.py|display_contador.py)
      ;;
    *)
      echo "Script principal nao suportado: ${SELECTED_SCRIPT}" >&2
      exit 1
      ;;
  esac
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
  echo "==> Desinstalando ${SERVICE_NAME} e ${BOOT_SERVICE_NAME} ..."
  run_remote <<REMOTE_EOF
set -e
systemctl stop ${SERVICE_NAME} ${BOOT_SERVICE_NAME}    2>/dev/null || true
systemctl disable ${SERVICE_NAME} ${BOOT_SERVICE_NAME} 2>/dev/null || true
rm -f  "${REMOTE_UNIT}" "${REMOTE_BOOT_UNIT}" "${REMOTE_ENV}" "${REMOTE_LAUNCHER}" "${REMOTE_BOOT_LAUNCHER}"
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

  local b64_init b64_relogio b64_relogio_ip b64_contador
  b64_init=$(base64 -w0     < "$SCRIPT_DIR/display_init.py")
  b64_relogio=$(base64 -w0  < "$SCRIPT_DIR/display_relogio.py")
  b64_relogio_ip=$(base64 -w0 < "$SCRIPT_DIR/display_relogio_ip.py")
  b64_contador=$(base64 -w0 < "$SCRIPT_DIR/display_contador.py")

  echo "==> Instalando em ${TARGET_HOST:-localhost} (1 sessao SSH)..."

  run_remote <<REMOTE_EOF
set -e

# ----- Diretorios -----
mkdir -p "${REMOTE_ROOT}" /etc/default /etc/systemd/system /usr/local/bin

# ----- Scripts Python -----
printf '%s' "${b64_init}"       | base64 -d > "${REMOTE_ROOT}/display_init.py"
printf '%s' "${b64_relogio}"    | base64 -d > "${REMOTE_ROOT}/display_relogio.py"
printf '%s' "${b64_relogio_ip}" | base64 -d > "${REMOTE_ROOT}/display_relogio_ip.py"
printf '%s' "${b64_contador}"   | base64 -d > "${REMOTE_ROOT}/display_contador.py"
chmod 0755 "${REMOTE_ROOT}"/*.py

# ----- Arquivo de configuracao -----
cat > "${REMOTE_ENV}" <<'ENVEOF'
# Script principal do display TX9.
# Opcoes: display_init.py  display_relogio.py  display_relogio_ip.py  display_contador.py
DISPLAY_SCRIPT=${SELECTED_SCRIPT}

# Script usado na fase inicial do boot.
DISPLAY_BOOT_SCRIPT=display_contador.py

# Argumentos do contador de boot.
DISPLAY_BOOT_ARGS="--inicio 0 --fim 9999 --delay 0.05 --loop --manter-ao-sair"
ENVEOF

# ----- Launcher principal -----
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

# ----- Launcher de boot -----
cat > "${REMOTE_BOOT_LAUNCHER}" <<'BOOTLAUNCHEOF'
#!/usr/bin/env bash
set -euo pipefail
ENV_FILE=/etc/default/tx9-display
DISPLAY_BOOT_SCRIPT=display_contador.py
DISPLAY_BOOT_ARGS="--inicio 0 --fim 9999 --delay 0.05 --loop --manter-ao-sair"
[[ -f "\${ENV_FILE}" ]] && source "\${ENV_FILE}"
SCRIPT_PATH=/opt/tx9/display/\${DISPLAY_BOOT_SCRIPT}
if [[ ! -f "\${SCRIPT_PATH}" ]]; then
  echo "Script nao encontrado: \${SCRIPT_PATH}" >&2
  exit 1
fi
BOOT_ARGS=()
if [[ -n "\${DISPLAY_BOOT_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  BOOT_ARGS=(\${DISPLAY_BOOT_ARGS})
fi
exec /usr/bin/env python3 "\${SCRIPT_PATH}" "\${BOOT_ARGS[@]}"
BOOTLAUNCHEOF
chmod 0755 "${REMOTE_BOOT_LAUNCHER}"

# ----- Unidade systemd de boot -----
cat > "${REMOTE_BOOT_UNIT}" <<'BOOTUNITEOF'
[Unit]
Description=TX9 early boot display service (contador)
DefaultDependencies=no
After=local-fs.target
Wants=local-fs.target
Before=basic.target network-pre.target tx9-display.service
Conflicts=shutdown.target tx9-display.service

[Service]
Type=simple
User=root
Group=root
EnvironmentFile=-/etc/default/tx9-display
WorkingDirectory=/opt/tx9/display
ExecStart=/usr/local/bin/tx9-display-boot-launcher
Restart=always
RestartSec=0
StartLimitIntervalSec=0

[Install]
WantedBy=basic.target
BOOTUNITEOF

# ----- Unidade systemd principal -----
cat > "${REMOTE_UNIT}" <<'UNITEOF'
[Unit]
Description=TX9 display service (relogio + IP + icones de rede)
After=network-online.target tx9-display-boot.service
Wants=network-online.target
Conflicts=tx9-display-boot.service

[Service]
Type=simple
User=root
Group=root
EnvironmentFile=-/etc/default/tx9-display
WorkingDirectory=/opt/tx9/display
ExecStart=/usr/local/bin/tx9-display-launcher
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNITEOF

# ----- Ativar servico -----
systemctl daemon-reload
systemctl enable "${BOOT_SERVICE_NAME}" "${SERVICE_NAME}"
systemctl stop "${BOOT_SERVICE_NAME}" 2>/dev/null || true
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
