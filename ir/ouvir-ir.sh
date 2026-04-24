#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Execute como root: sudo bash ouvir-ir.sh"
  exit 1
fi

echo "==> Verificando pacote ir-keytable"
if ! command -v ir-keytable >/dev/null 2>&1; then
  echo "Instalando ir-keytable..."
  apt update
  apt install -y ir-keytable
fi

echo "==> Verificando se o driver meson-ir está carregado"
if ! lsmod | grep -q '^meson_ir'; then
  modprobe meson-ir 2>/dev/null || true
fi

echo "==> Verificando /boot/armbianEnv.txt"
if [[ -f /boot/armbianEnv.txt ]]; then
  if grep -q '^overlays=' /boot/armbianEnv.txt; then
    if ! grep -Eq '^overlays=.*\bmeson-ir\b' /boot/armbianEnv.txt; then
      echo "Aviso: meson-ir não aparece em overlays= no /boot/armbianEnv.txt"
      echo "Sugestão: edite o arquivo e deixe algo como:"
      echo "  overlays=meson-ir"
    fi
  else
    echo "Aviso: não encontrei linha overlays= em /boot/armbianEnv.txt"
    echo "Sugestão: adicione:"
    echo "  overlays=meson-ir"
  fi
else
  echo "Aviso: /boot/armbianEnv.txt não encontrado"
fi

echo "==> Dispositivos RC encontrados:"
ls -l /sys/class/rc || true
echo

RCDEV=""
if [[ -d /sys/class/rc/rc0 ]]; then
  RCDEV="rc0"
else
  RCDEV="$(basename "$(find /sys/class/rc -maxdepth 1 -type l | head -n1)" 2>/dev/null || true)"
fi

if [[ -z "${RCDEV}" ]]; then
  echo "Nenhum dispositivo RC encontrado em /sys/class/rc"
  echo "Verifique se o overlay meson-ir está ativo e reinicie."
  exit 1
fi

echo "==> Usando dispositivo: ${RCDEV}"
ir-keytable -s "${RCDEV}" || true
echo

echo "==> Tentando habilitar protocolos comuns"
ir-keytable -s "${RCDEV}" -p nec,rc-5,rc-6,jvc,sony,sanyo,sharp,mce_kbd,xmp 2>/dev/null || \
ir-keytable -s "${RCDEV}" -p all

echo
echo "==> Ouvindo o controle remoto..."
echo "Pressione CTRL+C para sair."
echo

exec ir-keytable -s "${RCDEV}" -t