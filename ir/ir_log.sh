#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME=tx9-ir.service

if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  exec journalctl -u "$SERVICE_NAME" -f
fi

if command -v sudo >/dev/null 2>&1; then
  exec sudo journalctl -u "$SERVICE_NAME" -f
fi

echo "Erro: execute como root ou tenha sudo disponivel para ler o journal do servico." >&2
exit 1