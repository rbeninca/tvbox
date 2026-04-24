#!/usr/bin/env bash
# ir-listen — exibe eventos IR brutos ao vivo
#
# Funciona com qualquer controle remoto IR suportado pelo Linux.
# Util para descobrir os scancodes de um controle desconhecido.
#
# Instalado em /usr/local/bin/ir-listen pelo install_ir_service.sh
# Tambem pode ser executado diretamente: sudo bash ir_listen.sh
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Execute como root: sudo ir-listen" >&2
  exit 1
fi

if ! command -v ir-keytable >/dev/null 2>&1; then
  echo "Instalando ir-keytable..." >&2
  apt-get update -qq && apt-get install -y -qq ir-keytable
fi

modprobe meson-ir 2>/dev/null || true

RCDEV=""
for rc in /sys/class/rc/rc*; do
  [[ -d "$rc" ]] || continue
  RCDEV=$(basename "$rc")
  break
done

if [[ -z "$RCDEV" ]]; then
  echo "ERRO: nenhum dispositivo RC encontrado em /sys/class/rc/" >&2
  echo "Verifique: overlays=meson-ir em /boot/armbianEnv.txt" >&2
  exit 1
fi

echo "==> Dispositivo: $RCDEV"
ir-keytable -s "$RCDEV" -p nec,necx,rc-5,rc-6,jvc,sony,sanyo 2>/dev/null || \
  ir-keytable -s "$RCDEV" -p all 2>/dev/null || true

echo ""
echo "Aguardando eventos IR (CTRL+C para sair)..."
echo ""
exec ir-keytable -s "$RCDEV" -t
