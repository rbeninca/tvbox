#!/usr/bin/env python3
"""ir-map — mapeamento interativo de controle remoto IR

Ouve os botoes do controle, pergunta o nome de cada um (ou sequencia),
e gera um arquivo .conf pronto para o daemon tx9-ir.

Uso:
  sudo ir-map                     # imprime o .conf na tela
  sudo ir-map saida.conf          # salva em arquivo
  sudo ir-map --auto              # lista codigos sem perguntar nomes
  sudo ir-map --auto saida.conf   # lista e salva
"""

import argparse
import glob
import os
import select
import struct
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Constantes de evento Linux
# ---------------------------------------------------------------------------

FMT = "qqHHi" if sys.maxsize > 2**32 else "llHHi"
SZ  = struct.calcsize(FMT)
EV_MSC, MSC_SCAN = 0x04, 0x04

REPEAT_GAP  = 0.22   # segundos — janela para descartar repeats NEC
SEQ_TIMEOUT = 1.5    # segundos — janela para acumular sequencia de botoes

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pr(s="", end="\n", flush=True):
    sys.stdout.write(s + end)
    if flush:
        sys.stdout.flush()


def find_device():
    """Detecta o primeiro dispositivo RC e retorna (rcdev, evdev)."""
    for rc in sorted(glob.glob("/sys/class/rc/rc*")):
        if not os.path.isdir(rc):
            continue
        rcdev = os.path.basename(rc)
        for ev in glob.glob(f"{rc}/input*/event*"):
            evdev = f"/dev/input/{os.path.basename(ev)}"
            return rcdev, evdev
    return None, None


def setup_device():
    """Instala dependencias, carrega driver e configura protocolos."""
    # ir-keytable
    if subprocess.run(["which", "ir-keytable"], capture_output=True).returncode != 0:
        pr("Instalando ir-keytable...")
        subprocess.run(["apt-get", "update", "-qq"], check=False, capture_output=True)
        subprocess.run(["apt-get", "install", "-y", "-qq", "ir-keytable"],
                       check=False, capture_output=True)

    # driver meson-ir
    subprocess.run(["modprobe", "meson-ir"], capture_output=True, check=False)

    rcdev, evdev = find_device()
    if not rcdev:
        pr("ERRO: nenhum dispositivo RC encontrado em /sys/class/rc/")
        pr("Verifique: overlays=meson-ir em /boot/armbianEnv.txt")
        sys.exit(1)

    # protocolos
    ret = subprocess.run(
        ["ir-keytable", "-s", rcdev, "-p", "nec,necx,rc-5,rc-6,jvc,sony,sanyo"],
        capture_output=True,
    )
    if ret.returncode != 0:
        subprocess.run(["ir-keytable", "-s", rcdev, "-p", "all"],
                       capture_output=True, check=False)

    return rcdev, evdev


def drain_ir(fd):
    while select.select([fd], [], [], 0)[0]:
        fd.read(SZ)


def read_ir_event(fd):
    data = fd.read(SZ)
    if not data or len(data) < SZ:
        return None
    _, _, etype, ecode, value = struct.unpack(FMT, data)
    return (value & 0xFFFFFFFF) if etype == EV_MSC and ecode == MSC_SCAN else None


# ---------------------------------------------------------------------------
# Geracao do .conf
# ---------------------------------------------------------------------------

def generate_conf(mappings):
    all_codes = [c for _, codes in mappings for c in codes]
    prefix_str = ""
    if all_codes:
        pcounts = {}
        for c in all_codes:
            p = c >> 8
            pcounts[p] = pcounts.get(p, 0) + 1
        best = max(pcounts, key=lambda k: pcounts[k])
        prefix_str = f"0x{best:04x}" if best > 0xFF else f"0x{best:02x}"

    lines = [
        "[device]",
        "event_device = auto",
        "protocol     = necx",
        "",
        "[filter]",
        (f"# prefix = {prefix_str}  # descomente para filtrar apenas este controle"
         if prefix_str else "# prefix ="),
        "",
        "[settings]",
        "repeat_threshold = 0.22",
        "repeat_delay     = 0.50",
        "repeat_rate      = 0.20",
        "sequence_timeout = 1.50",
        "",
    ]

    singles = [(l, c) for l, c in mappings if len(c) == 1]
    seqs    = [(l, c) for l, c in mappings if len(c) > 1]

    if singles:
        lines.append("[keys]")
        for label, codes in singles:
            lines.append(f"0x{codes[0]:06x} = # {label}")
        lines.append("")

    if seqs:
        lines.append("[sequences]")
        for label, codes in seqs:
            seq_key = ",".join(f"0x{c:06x}" for c in codes)
            lines.append(f"{seq_key} = # {label}")
        lines.append("")

    return "\n".join(lines)


def save_conf(conf, out_file):
    with open(out_file, "w") as f:
        f.write(conf + "\n")
    pr("=" * 58)
    pr(f"  Arquivo salvo em: {out_file}")
    pr("  Edite: substitua '# nome' pelo comando desejado.")
    pr("  Exemplo:")
    pr("    0x40404d = systemctl poweroff")
    pr("    0x404018 = amixer -q set Master 5%+")
    pr("=" * 58)


# ---------------------------------------------------------------------------
# Modo interativo — pergunta o nome de cada botao/sequencia
# ---------------------------------------------------------------------------

def ask_name(codes):
    pr()
    if len(codes) == 1:
        pr(f"  Tecla ouvida    : 0x{codes[0]:06x}")
    else:
        pr("  Sequencia ouvida: " + " -> ".join(f"0x{c:06x}" for c in codes))
    pr("  Nome do botao   : (Enter = pular) ", end="")
    try:
        name = sys.stdin.readline().strip()
        return name if name else None
    except EOFError:
        return None


def run_interactive(evdev):
    mappings    = []
    last_code   = None
    last_code_t = 0.0
    seq_buf     = []
    seq_last_t  = 0.0
    state       = "idle"

    pr("=" * 58)
    pr("  MAPEAMENTO IR - MODO INTERATIVO")
    pr("=" * 58)
    pr("  Pressione cada botao do controle, um a um.")
    pr("  Sequencia: varios botoes pressionados em < 1.5 s.")
    pr("  CTRL+C encerra e gera o arquivo .conf.")
    pr("=" * 58)
    pr()
    pr("Aguardando primeira tecla...")

    try:
        with open(evdev, "rb") as ir_fd:
            while True:
                now     = time.monotonic()
                timeout = max(0.0, SEQ_TIMEOUT - (now - seq_last_t)) if state == "collect" else None
                ready   = select.select([ir_fd], [], [], timeout)[0]

                if not ready:
                    # timeout: finaliza sequencia acumulada
                    if state == "collect" and seq_buf:
                        codes = list(seq_buf)
                        seq_buf.clear()
                        state = "idle"
                        name = ask_name(codes)
                        if name:
                            mappings.append((name, codes))
                            pr(f"  -> Salvo como '{name}'")
                        else:
                            pr("  -> Pulado.")
                        drain_ir(ir_fd)
                        pr()
                        pr("Aguardando proxima tecla...")
                    continue

                code = read_ir_event(ir_fd)
                if code is None:
                    continue

                now = time.monotonic()
                # descartar repeats NEC
                if code == last_code and (now - last_code_t) < REPEAT_GAP:
                    last_code_t = now
                    continue
                last_code, last_code_t = code, now

                if state == "idle":
                    seq_buf.clear()
                    seq_buf.append(code)
                    seq_last_t = now
                    state = "collect"
                else:
                    seq_buf.append(code)
                    seq_last_t = now

                seq_str = " -> ".join(f"0x{c:06x}" for c in seq_buf)
                pr(f"\r  [{seq_str}]  aguardando...", end="      ")

    except KeyboardInterrupt:
        pass

    # flush ultima sequencia incompleta (interrompida por CTRL+C)
    if state == "collect" and seq_buf:
        pr()
        name = ask_name(list(seq_buf))
        if name:
            mappings.append((name, list(seq_buf)))

    return mappings


# ---------------------------------------------------------------------------
# Modo automatico — lista codigos unicos sem perguntar nomes
# ---------------------------------------------------------------------------

def run_auto(evdev):
    seen     = {}
    mappings = []

    pr("=" * 58)
    pr("  MODO AUTO - lista codigos unicos (CTRL+C para sair)")
    pr("=" * 58)
    pr()
    pr("  [keys]")

    try:
        with open(evdev, "rb") as ir_fd:
            while True:
                if not select.select([ir_fd], [], [], 0.5)[0]:
                    continue
                code = read_ir_event(ir_fd)
                if code is None:
                    continue
                now  = time.monotonic()
                last = seen.get(code, 0)
                if now - last < REPEAT_GAP:
                    continue
                is_new = code not in seen
                seen[code] = now
                tag = "  # NOVO" if is_new else ""
                pr(f"  0x{code:06x} = {tag}")
                if is_new:
                    mappings.append((f"botao_{len(mappings) + 1}", [code]))
    except KeyboardInterrupt:
        pass

    pr()
    pr(f"  Total de botoes distintos: {len(seen)}")
    return mappings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if os.geteuid() != 0:
        pr("Execute como root: sudo ir-map")
        sys.exit(1)

    ap = argparse.ArgumentParser(
        description="Mapeamento interativo de controle remoto IR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  sudo ir-map                        # interativo, imprime na tela
  sudo ir-map controle.conf          # interativo, salva no arquivo
  sudo ir-map --auto                 # lista codigos sem perguntar nomes
  sudo ir-map --auto controle.conf   # lista e salva
        """,
    )
    ap.add_argument("output", nargs="?", default="",
                    help="Arquivo .conf de saida (opcional)")
    ap.add_argument("--auto", action="store_true",
                    help="Modo automatico: lista codigos sem perguntar nomes")
    args = ap.parse_args()

    rcdev, evdev = setup_device()
    pr(f"==> Dispositivo: {rcdev} ({evdev})")
    pr()

    if args.auto:
        mappings = run_auto(evdev)
    else:
        mappings = run_interactive(evdev)

    pr()
    pr()
    pr("=" * 58)
    pr(f"  {len(mappings)} botao(s) / sequencia(s) mapeado(s)")
    pr("=" * 58)

    if not mappings:
        pr("Nenhum botao mapeado.")
        return

    conf = generate_conf(mappings)
    pr()
    pr(conf)

    if args.output:
        save_conf(conf, args.output)
    else:
        pr("=" * 58)
        pr("  Dica: passe um nome de arquivo para salvar:")
        pr("    ir-map meu_controle.conf")
        pr("=" * 58)


if __name__ == "__main__":
    main()
