#!/usr/bin/env python3
"""
ir_daemon.py — Daemon de controle remoto IR flexível para TX9 / Armbian.

Lê scancodes brutos de /dev/input/eventX (EV_MSC/MSC_SCAN), mapeia para
comandos shell via arquivo de configuração INI. Suporta:
  - teclas simples → comando
  - sequências de teclas → comando
  - hold/repeat por tecla
  - hot-reload da configuração (SIGHUP)
  - auto-detecção do dispositivo IR

Uso:
  python3 ir_daemon.py [--config /etc/tx9-ir/ir_daemon.conf]

Sinais:
  SIGHUP  → recarrega configuração em tempo real (sem perder o estado)
  SIGTERM → encerra com limpeza
"""

import argparse
import configparser
import glob
import os
import select
import signal
import struct
import subprocess
import sys
import time

# ── Constantes ─────────────────────────────────────────────────────────────────

CONFIG_DEFAULT = "/etc/tx9-ir/ir_daemon.conf"

# Linux input_event struct (linux/input.h)
# 64-bit kernel: { int64 tv_sec; int64 tv_usec; uint16 type; uint16 code; int32 value; }
# 32-bit kernel: { int32 tv_sec; int32 tv_usec; uint16 type; uint16 code; int32 value; }
_FMT_64 = "qqHHi"   # 24 bytes
_FMT_32 = "llHHi"   # 16 bytes

EV_MSC   = 0x04
MSC_SCAN = 0x04


def _native_fmt() -> tuple[str, int]:
    """Retorna (format_string, size) para o kernel atual (64 vs 32 bit)."""
    fmt = _FMT_64 if sys.maxsize > 2**32 else _FMT_32
    return fmt, struct.calcsize(fmt)


# ── Configuração ───────────────────────────────────────────────────────────────

class Config:
    """Carrega e expõe a configuração do daemon IR a partir de um arquivo INI."""

    def __init__(self, path: str):
        self.path = path
        self.load()

    def load(self):
        # Disable interpolation so '%' in shell commands is treated literally.
        p = configparser.ConfigParser(
            inline_comment_prefixes=('#', ';'),
            interpolation=None,
        )
        p.read(self.path)

        # ── [keys] teclas simples: scancode (hex/dec) = comando shell ─────────
        self.keys: dict[int, str] = {}
        for raw_k, v in (p.items('keys') if p.has_section('keys') else []):
            v = v.strip()
            if not v:
                continue
            try:
                self.keys[int(raw_k, 0)] = v
            except ValueError:
                print(f"[config] tecla inválida ignorada: {raw_k!r}", file=sys.stderr)

        # ── [sequences] sequências: sc1,sc2,... = comando shell ───────────────
        self.sequences: dict[tuple, str] = {}
        for raw_k, v in (p.items('sequences') if p.has_section('sequences') else []):
            v = v.strip()
            if not v:
                continue
            try:
                seq = tuple(int(x.strip(), 0) for x in raw_k.split(',') if x.strip())
                if len(seq) >= 2:
                    self.sequences[seq] = v
            except ValueError:
                print(f"[config] sequência inválida ignorada: {raw_k!r}", file=sys.stderr)

        # ── [device] ──────────────────────────────────────────────────────────
        self.event_device = p.get('device', 'event_device', fallback='auto').strip()
        self.protocol     = p.get('device', 'protocol',      fallback='necx').strip()

        # ── [filter] prefixo para ignorar outros controles ────────────────────
        # O prefixo é comparado com (scancode >> 8) — adequado para NEC extended
        # onde os 16 bits superiores são o código customizado do fabricante.
        prefix_raw = p.get('filter', 'prefix', fallback='').strip()
        self.filter_prefix: int | None = int(prefix_raw, 0) if prefix_raw else None

        # ── [settings] ────────────────────────────────────────────────────────
        # Limiar de tempo (s) entre dois eventos do MESMO código para ser
        # considerado "repeat" (NEC envia repeats a cada ~110ms)
        self.repeat_threshold = p.getfloat('settings', 'repeat_threshold', fallback=0.22)
        # Tempo de hold antes de começar a disparar ações em repetição
        self.repeat_delay     = p.getfloat('settings', 'repeat_delay',     fallback=0.50)
        # Intervalo mínimo entre disparos durante hold
        self.repeat_rate      = p.getfloat('settings', 'repeat_rate',      fallback=0.20)
        # Tempo máximo entre teclas de uma sequência
        self.seq_timeout      = p.getfloat('settings', 'sequence_timeout', fallback=1.50)

        self.max_seq_len = max((len(k) for k in self.sequences), default=0)

        print(
            f"[config] {len(self.keys)} tecla(s), {len(self.sequences)} sequência(s)"
            f" | device={self.event_device} proto={self.protocol}",
            flush=True,
        )


# ── Helpers de sistema ─────────────────────────────────────────────────────────

def find_ir_device() -> str | None:
    """
    Localiza o primeiro dispositivo de input IR via /sys/class/rc/.
    Retorna o caminho em /dev/input/eventX ou None.
    """
    for rc in sorted(glob.glob('/sys/class/rc/rc*')):
        for evpath in sorted(glob.glob(f'{rc}/input*/event*')):
            dev = f'/dev/input/{os.path.basename(evpath)}'
            if os.path.exists(dev):
                return dev
    return None


def set_protocol(protocol: str) -> bool:
    """
    Configura o protocolo IR via ir-keytable no primeiro dispositivo rc* encontrado.
    Retorna True se bem-sucedido.
    """
    if not protocol:
        return True
    for rc in sorted(glob.glob('/sys/class/rc/rc*')):
        rc_name = os.path.basename(rc)
        r = subprocess.run(
            ['ir-keytable', '-s', rc_name, '-p', protocol],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            print(f"[ir] protocolo '{protocol}' ativo em {rc_name}", flush=True)
        else:
            print(
                f"[ir] aviso ir-keytable ({rc_name}): {r.stderr.strip()}",
                file=sys.stderr, flush=True,
            )
        return r.returncode == 0
    print("[ir] nenhum dispositivo rc* encontrado para configurar protocolo",
          file=sys.stderr, flush=True)
    return False


def run_action(cmd: str):
    """Executa um comando shell em background (não-bloqueante)."""
    try:
        subprocess.Popen(
            cmd, shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[ir] erro ao executar {cmd!r}: {e}", file=sys.stderr, flush=True)


# ── Daemon principal ───────────────────────────────────────────────────────────

class IrDaemon:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._stop   = False
        self._reload = False

    def run(self):
        signal.signal(signal.SIGHUP,  lambda *_: setattr(self, '_reload', True))
        signal.signal(signal.SIGTERM, lambda *_: setattr(self, '_stop', True))
        signal.signal(signal.SIGINT,  lambda *_: setattr(self, '_stop', True))

        fmt, sz = _native_fmt()
        print(f"[ir] input_event={sz}B ({'64' if sz == 24 else '32'}-bit kernel)",
              flush=True)

        while not self._stop:
            if self._reload:
                self._reload = False
                self.cfg.load()

            dev = self.cfg.event_device
            if dev == 'auto':
                dev = find_ir_device()

            if not dev:
                print("[ir] dispositivo IR não encontrado — aguardando 5s...",
                      flush=True)
                time.sleep(5)
                continue

            print(f"[ir] usando dispositivo: {dev}", flush=True)
            set_protocol(self.cfg.protocol)

            try:
                self._read_loop(dev, fmt, sz)
            except OSError as e:
                print(f"[ir] erro no dispositivo: {e} — re-tentando em 3s...",
                      flush=True)
                time.sleep(3)

    # ── Loop de leitura de eventos ─────────────────────────────────────────────

    def _read_loop(self, dev: str, fmt: str, sz: int):
        cfg = self.cfg

        # Estado de sequência
        seq_buf:  list[int] = []
        seq_last: float     = 0.0

        # Estado de repeat/hold
        last_code:     int | None = None
        first_press_t: float      = 0.0
        last_action_t: float      = 0.0
        in_hold:       bool       = False

        with open(dev, 'rb') as fd:
            while not self._stop and not self._reload:
                ready, _, _ = select.select([fd], [], [], 1.0)
                now = time.monotonic()

                # Timeout de sequência sem evento
                if not ready:
                    if seq_buf and now - seq_last > cfg.seq_timeout:
                        seq_buf.clear()
                    continue

                data = fd.read(sz)
                if len(data) < sz:
                    return  # dispositivo fechado ou removido

                _, _, etype, ecode, value = struct.unpack(fmt, data)

                # Só nos interessa EV_MSC / MSC_SCAN (scancode bruto)
                if etype != EV_MSC or ecode != MSC_SCAN:
                    continue

                scancode = value & 0xFFFFFFFF  # garante unsigned 32-bit
                now = time.monotonic()

                # ── Filtro de prefixo ──────────────────────────────────────────
                # Compara bits [23:8] com o prefixo configurado.
                # Para NEC extended (24-bit): custom code = bits [23:8]
                # Para NEC standard (16-bit): address = bits [15:8]
                if cfg.filter_prefix is not None:
                    if (scancode >> 8) != cfg.filter_prefix:
                        continue

                # ── Detecção de repeat/hold ────────────────────────────────────
                # NEC protocol envia frames de repeat a cada ~110ms quando o botão
                # é mantido pressionado. Dois eventos do mesmo código em menos de
                # repeat_threshold segundos são tratados como hold.
                if scancode == last_code and (now - first_press_t) < cfg.repeat_threshold:
                    is_repeat = True
                else:
                    is_repeat     = False
                    last_code     = scancode
                    first_press_t = now
                    in_hold       = False

                if is_repeat:
                    if not in_hold:
                        # Aguarda repeat_delay antes de disparar ações em hold
                        if (now - first_press_t) < cfg.repeat_delay:
                            continue
                        in_hold = True
                    if (now - last_action_t) < cfg.repeat_rate:
                        continue  # respeita o intervalo entre repetições

                print(
                    f"[ir] 0x{scancode:06x}{' (hold)' if is_repeat else ''}",
                    flush=True,
                )

                # ── Matching de sequências (apenas no press inicial) ───────────
                if cfg.max_seq_len >= 2 and not is_repeat:
                    # Limpa buffer se expirou
                    if seq_buf and now - seq_last > cfg.seq_timeout:
                        seq_buf.clear()

                    seq_buf.append(scancode)
                    seq_last = now

                    # Verifica sequências do maior comprimento para o menor
                    seq_matched = False
                    for length in range(min(len(seq_buf), cfg.max_seq_len), 1, -1):
                        candidate = tuple(seq_buf[-length:])
                        if candidate in cfg.sequences:
                            cmd = cfg.sequences[candidate]
                            codes_str = ', '.join(f'0x{c:06x}' for c in candidate)
                            print(f"[ir] seq [{codes_str}] → {cmd!r}", flush=True)
                            run_action(cmd)
                            seq_buf.clear()
                            last_action_t = now
                            seq_matched = True
                            break

                    if seq_matched:
                        continue

                    # Limita o buffer ao tamanho máximo de sequência conhecida
                    if len(seq_buf) > cfg.max_seq_len:
                        seq_buf = seq_buf[-cfg.max_seq_len:]

                # ── Ação de tecla simples ──────────────────────────────────────
                if scancode in cfg.keys:
                    cmd = cfg.keys[scancode]
                    print(f"[ir] 0x{scancode:06x} → {cmd!r}", flush=True)
                    run_action(cmd)
                    last_action_t = now


# ── Ponto de entrada ───────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Daemon IR flexível para TX9 / Armbian",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument(
        '--config', default=CONFIG_DEFAULT,
        help="Arquivo de configuração INI",
    )
    args = ap.parse_args()

    if not os.path.exists(args.config):
        print(f"ERRO: arquivo de configuração não encontrado: {args.config}",
              file=sys.stderr)
        sys.exit(1)

    IrDaemon(Config(args.config)).run()


if __name__ == '__main__':
    main()
