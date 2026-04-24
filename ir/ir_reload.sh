#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME=tx9-ir.service

reload_service() {
  local pid
  pid=$(systemctl show -p MainPID --value "$SERVICE_NAME" 2>/dev/null || echo "")
  if [[ -n "$pid" && "$pid" != "0" ]]; then
    kill -HUP "$pid"
    echo "==> Configuracao do $SERVICE_NAME recarregada (SIGHUP em PID $pid)."
  else
    echo "Erro: servico $SERVICE_NAME nao esta rodando." >&2
    exit 1
  fi
}

if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  reload_service
  exit 0
fi

if command -v sudo >/dev/null 2>&1; then
  exec sudo "$0"
fi

echo "Erro: execute como root ou tenha sudo disponivel para recarregar o servico." >&2
exit 1