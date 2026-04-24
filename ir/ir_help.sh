#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
TX9 IR - Manual rapido

Comandos:
  ir-listen               mostra scancodes IR brutos em tempo real
  ir-map [saida.conf]     mapeia botoes e gera um arquivo .conf
  ir-log                  acompanha os logs do daemon IR ao vivo
  ir-reload               recarrega o arquivo de configuracao sem reiniciar
  ir-help                 mostra este manual

Arquivos principais:
  Configuracao ativa : /etc/tx9-ir/ir_daemon.conf
  Daemon instalado   : /opt/tx9/ir/ir_daemon.py
  Servico systemd    : tx9-ir.service

Fluxo comum:
  1. sudo ir-map /etc/tx9-ir/ir_daemon.conf
  2. edite os comandos no .conf
  3. sudo ir-reload
  4. sudo ir-log

Comandos equivalentes:
  ir-log      -> journalctl -u tx9-ir.service -f
  ir-reload   -> systemctl kill -s HUP tx9-ir.service

Se alterar codigo Python ou a unidade systemd, use restart:
  sudo systemctl restart tx9-ir.service
EOF