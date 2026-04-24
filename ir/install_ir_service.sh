#!/usr/bin/env bash
# install_ir_service.sh — Instala/gerencia o servico daemon IR do TX9
#
# Todos os arquivos necessarios devem estar no mesmo diretorio deste script:
#   ir_daemon.py      daemon principal
#   ir_listen.sh      utilitario: mostra eventos IR brutos
#   ir_map.py         utilitario: mapeamento interativo de controle
#   tx9_remote.conf   configuracao padrao do TX9
#
# Apos instalar, os comandos ir-listen, ir-map, ir-log, ir-reload e ir-help
# ficam disponiveis no PATH.
#
# Uso (como root):
#   sudo bash install_ir_service.sh install
#   sudo bash install_ir_service.sh uninstall | restart | status | reload
set -euo pipefail

ACTION=${1:-}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

INSTALL_DIR=/opt/tx9/ir
CONF_DIR=/etc/tx9-ir
CONF_FILE=${CONF_DIR}/ir_daemon.conf
SERVICE_NAME=tx9-ir.service
UNIT=/etc/systemd/system/${SERVICE_NAME}
BIN_DIR=/usr/local/bin

REQUIRED_FILES=(
  ir_daemon.py
  ir_listen.sh
  ir_map.py
  ir_log.sh
  ir_reload.sh
  ir_help.sh
  tx9_remote.conf
)

# ---------------------------------------------------------------------------
# Uso
# ---------------------------------------------------------------------------

usage() {
  cat >&2 <<'USAGE'
Uso (como root):
  install_ir_service.sh  install    instala servico, daemon e utilitarios
  install_ir_service.sh  uninstall  remove tudo (preserva config em /etc/tx9-ir)
  install_ir_service.sh  restart    reinicia o servico
  install_ir_service.sh  status     mostra status e configuracao ativa
  install_ir_service.sh  reload     recarrega config sem reiniciar (SIGHUP)

Apos instalar, os seguintes comandos ficam disponiveis:
  ir-listen              exibe eventos IR brutos de qualquer controle
  ir-map [saida.conf]    mapeamento interativo -- gera .conf pronto
  ir-map --auto          lista codigos sem perguntar nomes
  ir-log                 acompanha o journal do daemon IR ao vivo
  ir-reload              recarrega o .conf sem reiniciar o servico
  ir-help                mostra um manual rapido dos comandos IR

Fluxo para configurar um novo controle:
  sudo ir-map /etc/tx9-ir/ir_daemon.conf
  # edite o arquivo: substitua os comentarios pelos comandos desejados
  sudo install_ir_service.sh reload
USAGE
  exit 1
}

[[ -z "$ACTION" ]] && usage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

require_root() {
  [[ $EUID -eq 0 ]] || {
    echo "Erro: execute como root (sudo bash $0 $ACTION)" >&2
    exit 1
  }
}

check_files() {
  local missing=0
  for f in "${REQUIRED_FILES[@]}"; do
    [[ -f "$SCRIPT_DIR/$f" ]] || {
      echo "Arquivo nao encontrado: $SCRIPT_DIR/$f" >&2
      missing=1
    }
  done
  [[ $missing -eq 0 ]] || exit 1
}

# ---------------------------------------------------------------------------
# Acoes
# ---------------------------------------------------------------------------

do_install() {
  require_root
  check_files

  echo "==> Instalando servico IR..."

  # Dependencias
  if ! command -v ir-keytable >/dev/null 2>&1; then
    echo "==> Instalando ir-keytable..."
    apt-get update -qq && apt-get install -y -qq ir-keytable
  fi

  # Copia arquivos
  mkdir -p "$INSTALL_DIR" "$CONF_DIR"
  install -m 0755 "$SCRIPT_DIR/ir_daemon.py"  "$INSTALL_DIR/ir_daemon.py"
  install -m 0755 "$SCRIPT_DIR/ir_listen.sh"  "$INSTALL_DIR/ir_listen.sh"
  install -m 0755 "$SCRIPT_DIR/ir_map.py"     "$INSTALL_DIR/ir_map.py"
  install -m 0755 "$SCRIPT_DIR/ir_log.sh"     "$INSTALL_DIR/ir_log.sh"
  install -m 0755 "$SCRIPT_DIR/ir_reload.sh"  "$INSTALL_DIR/ir_reload.sh"
  install -m 0755 "$SCRIPT_DIR/ir_help.sh"    "$INSTALL_DIR/ir_help.sh"

  # Symlinks nos binarios do sistema
  ln -sf "$INSTALL_DIR/ir_listen.sh" "$BIN_DIR/ir-listen"
  ln -sf "$INSTALL_DIR/ir_map.py"    "$BIN_DIR/ir-map"
  ln -sf "$INSTALL_DIR/ir_log.sh"    "$BIN_DIR/ir-log"
  ln -sf "$INSTALL_DIR/ir_reload.sh" "$BIN_DIR/ir-reload"
  ln -sf "$INSTALL_DIR/ir_help.sh"   "$BIN_DIR/ir-help"

  # Configuracao: nao sobrescreve se ja existir
  if [[ ! -f "$CONF_FILE" ]]; then
    install -m 0640 "$SCRIPT_DIR/tx9_remote.conf" "$CONF_FILE"
    echo "==> Configuracao criada em $CONF_FILE"
  else
    echo "==> Configuracao existente preservada: $CONF_FILE"
  fi

  # Overlay meson-ir no armbianEnv.txt
  if [[ -f /boot/armbianEnv.txt ]] && ! grep -Eq '^overlays=.*\bmeson-ir\b' /boot/armbianEnv.txt; then
    if grep -q '^overlays=' /boot/armbianEnv.txt; then
      sed -i 's/^overlays=\(.*\)/overlays=\1 meson-ir/' /boot/armbianEnv.txt
    else
      echo "overlays=meson-ir" >> /boot/armbianEnv.txt
    fi
    echo "==> Overlay meson-ir adicionado em /boot/armbianEnv.txt (requer reboot)"
  fi

  # Carrega driver imediatamente (sem reboot)
  modprobe meson-ir 2>/dev/null || true

  # Unidade systemd
  cat > "$UNIT" <<'UNITEOF'
[Unit]
Description=TX9 IR remote daemon
After=basic.target
Wants=basic.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /opt/tx9/ir/ir_daemon.py --config /etc/tx9-ir/ir_daemon.conf
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNITEOF

  systemctl daemon-reload
  systemctl enable  "$SERVICE_NAME"
  systemctl restart "$SERVICE_NAME" 2>/dev/null || systemctl start "$SERVICE_NAME"
  sleep 1

  echo ""
  echo "==> Instalacao concluida."
  echo "    Daemon   : $INSTALL_DIR/ir_daemon.py"
  echo "    Config   : $CONF_FILE"
  echo "    Comandos : ir-listen | ir-map | ir-log | ir-reload | ir-help"
  echo ""
  echo "  sudo ir-listen                        # veja os codigos do controle"
  echo "  sudo ir-map /etc/tx9-ir/ir_daemon.conf # mapeie e salve direto"
  echo "  sudo ir-log                           # logs ao vivo"
  echo "  sudo ir-reload                        # recarrega o .conf"
  echo "  ir-help                               # manual rapido"
  echo ""
  systemctl status "$SERVICE_NAME" --no-pager || true
}

do_uninstall() {
  require_root
  echo "==> Desinstalando..."
  systemctl stop    "$SERVICE_NAME" 2>/dev/null || true
  systemctl disable "$SERVICE_NAME" 2>/dev/null || true
  rm -f "$UNIT"
  rm -rf "$INSTALL_DIR"
  rm -f "$BIN_DIR/ir-listen" "$BIN_DIR/ir-map" "$BIN_DIR/ir-log" "$BIN_DIR/ir-reload" "$BIN_DIR/ir-help"
  systemctl daemon-reload
  echo "==> Pronto. Configuracoes preservadas em $CONF_DIR"
}

do_restart() {
  require_root
  systemctl restart "$SERVICE_NAME"
  sleep 1
  systemctl status "$SERVICE_NAME" --no-pager
}

do_status() {
  systemctl status "$SERVICE_NAME" --no-pager || true
  echo ""
  echo "--- Configuracao ativa: $CONF_FILE ---"
  cat "$CONF_FILE" 2>/dev/null || echo "(arquivo nao encontrado)"
}

do_reload() {
  require_root
  PID=$(systemctl show -p MainPID --value "$SERVICE_NAME" 2>/dev/null || echo "")
  if [[ -n "$PID" && "$PID" != "0" ]]; then
    kill -HUP "$PID"
    echo "==> SIGHUP enviado para PID $PID -- configuracao recarregada."
  else
    echo "==> Servico nao esta rodando." >&2
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Despacho
# ---------------------------------------------------------------------------

case "$ACTION" in
  install)   do_install   ;;
  uninstall) do_uninstall ;;
  restart)   do_restart   ;;
  status)    do_status    ;;
  reload)    do_reload    ;;
  *)         usage        ;;
esac
