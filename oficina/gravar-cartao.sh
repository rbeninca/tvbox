#!/usr/bin/env bash
# Grava a imagem no cartão SD com verificação.
# Uso: sudo ./gravar-cartao.sh [imagem] [dispositivo]
# Limite de velocidade opcional via variável RATE (ex.: RATE=10M sudo ./gravar-cartao.sh)
set -euo pipefail

IMG="${1:-tx9-pro-armbian-reduzido.img}"
DEV="${2:-/dev/sdb}"
RATE="${RATE:-}"

if [[ $EUID -ne 0 ]]; then
    echo "Rode com sudo: sudo $0 $*" >&2
    exit 1
fi

if [[ ! -f "$IMG" ]]; then
    echo "Imagem não encontrada: $IMG" >&2
    exit 1
fi

if [[ ! -b "$DEV" ]]; then
    echo "Dispositivo de bloco não encontrado: $DEV" >&2
    exit 1
fi

IMG_SIZE=$(stat -c %s "$IMG")

echo "==> Imagem:      $IMG ($((IMG_SIZE / 1024 / 1024)) MiB)"
echo "==> Dispositivo: $DEV"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT "$DEV"
echo
read -rp "Isso vai APAGAR $DEV. Continuar? (digite SIM): " ok
[[ "$ok" == "SIM" ]] || { echo "Abortado."; exit 1; }

echo "==> Desmontando partições de $DEV ..."
for part in "${DEV}"?*; do
    umount "$part" 2>/dev/null && echo "    desmontado: $part" || true
done

if [[ -n "$RATE" ]]; then
    if ! command -v pv >/dev/null; then
        echo "Limite de velocidade pedido (RATE=$RATE) mas 'pv' não está instalado." >&2
        echo "Instale com: sudo dnf install pv" >&2
        exit 1
    fi
    echo "==> Gravando com limite de $RATE/s (oflag=direct) ..."
    pv -L "$RATE" -s "$IMG_SIZE" "$IMG" | dd of="$DEV" bs=4M oflag=direct
else
    echo "==> Gravando (oflag=direct, sem limite) ..."
    dd if="$IMG" of="$DEV" bs=4M status=progress oflag=direct
fi
echo "==> Sincronizando ..."
sync

echo "==> Verificando (cmp) ..."
if cmp -n "$IMG_SIZE" "$DEV" "$IMG"; then
    echo "==> OK: cartão idêntico à imagem. Gravação confiável."
else
    echo "==> FALHA na verificação! O cartão ou o leitor USB está com defeito." >&2
    exit 1
fi
