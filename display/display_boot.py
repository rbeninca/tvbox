#!/usr/bin/env python3
"""
display_boot.py — Contador de boot para o display TX9.

Roda como serviço de fase inicial (antes da rede), exibindo um contador
crescente no display enquanto o sistema inicializa.

Uso (via systemd / tx9-display-boot):
  python3 display_boot.py [--inicio 0] [--fim 9999] [--delay 0.05]
                          [--loop] [--manter-ao-sair]

Parâmetros padrão configuráveis em /etc/default/tx9-display:
  DISPLAY_BOOT_ARGS=--fim 9999 --delay 0.05 --loop --manter-ao-sair
"""

import argparse
import signal
import sys
import time

from display_driver import DisplayDriver, prepare_display_gpio


def _parse_args():
    p = argparse.ArgumentParser(description="Contador de boot TX9")
    p.add_argument("--inicio",  type=int,   default=0,     help="Valor inicial (padrão: 0)")
    p.add_argument("--fim",     type=int,   default=9999,  help="Valor final (padrão: 9999)")
    p.add_argument("--delay",   type=float, default=0.05,  help="Delay entre incrementos em segundos (padrão: 0.05)")
    p.add_argument("--loop",    action="store_true",       help="Reinicia a contagem ao atingir --fim")
    p.add_argument(
        "--manter-ao-sair",
        action="store_true",
        dest="manter",
        help="Mantém o último valor no display ao encerrar (não limpa)",
    )
    return p.parse_args()


def main():
    args = _parse_args()

    prepare_display_gpio()
    hw = DisplayDriver(bit_delay_us=12)
    hw.activate()

    _stop = [False]

    def _on_signal(sig, frame):
        _stop[0] = True

    signal.signal(signal.SIGINT,  _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    last_value = args.inicio

    try:
        while not _stop[0]:
            for n in range(args.inicio, args.fim + 1):
                if _stop[0]:
                    break
                hw.show_number(n, leading_zeros=True)
                last_value = n
                time.sleep(args.delay)

            if not args.loop:
                break

    finally:
        if not args.manter:
            hw.clear()
        hw.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
