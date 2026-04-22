#!/usr/bin/env python3
"""
display_server.py — Servidor de display TX9.

Único processo que acessa o hardware FD6551 via GPIO.
Aceita comandos JSON via socket Unix /run/tx9-display.sock.

Uso:
  python3 display_server.py [--brightness 0x10] [--background clock_ip|clock|none]
"""

import argparse
import json
import os
import queue
import signal
import socket
import sys
import threading
import time

from display_driver import DisplayDriver, prepare_display_gpio

SOCKET_PATH = "/run/tx9-display.sock"
BG_REFRESH  = 0.5   # intervalo da tarefa de fundo (s)


class DisplayServer:
    def __init__(self):
        prepare_display_gpio()
        self.hw = DisplayDriver(bit_delay_us=12)
        self.hw.activate()

        self._q        = queue.PriorityQueue()
        self._lock     = threading.Lock()
        self._stop     = threading.Event()
        self._bg       = None
        self._bg_lock  = threading.Lock()

    # ── API interna ────────────────────────────────────────────────────────────

    def set_background(self, fn):
        """Troca a tarefa de fundo em runtime (thread-safe)."""
        with self._bg_lock:
            self._bg = fn

    def push(self, payload: dict):
        priority = payload.get("priority", 1)
        duration = payload.get("duration", 3.0)
        deadline = time.monotonic() + duration
        self._q.put((priority, deadline, payload))

    # ── Loop principal ─────────────────────────────────────────────────────────

    def run(self):
        threading.Thread(target=self._socket_listener, daemon=True).start()

        while not self._stop.is_set():
            # Consome mensagens prioritárias dentro do prazo
            try:
                while True:
                    pri, deadline, payload = self._q.get_nowait()
                    remaining = deadline - time.monotonic()
                    if remaining > 0:
                        self._dispatch(payload, remaining)
            except queue.Empty:
                pass

            # Tarefa de fundo
            with self._bg_lock:
                bg = self._bg
            if bg:
                try:
                    bg(self.hw)
                except Exception as e:
                    print(f"[bg] erro: {e}", file=sys.stderr)

            time.sleep(BG_REFRESH)

    def stop(self):
        self._stop.set()
        self.hw.clear()
        self.hw.close()

    # ── Despacho de comando ────────────────────────────────────────────────────

    def _dispatch(self, p: dict, duration: float):
        cmd = p.get("cmd")
        hw  = self.hw
        end = time.monotonic() + duration

        if cmd == "show_text":
            text = p.get("text", "    ")
            if len(text) > 4:
                hw.scroll_text(text, step_delay=p.get("speed", 0.35))
            else:
                hw.show_text4(text)
                time.sleep(min(duration, end - time.monotonic()))

        elif cmd == "show_number":
            hw.show_number(int(p.get("value", 0)))
            time.sleep(min(duration, end - time.monotonic()))

        elif cmd == "scroll":
            hw.scroll_text(p.get("text", ""), step_delay=p.get("speed", 0.35))

        elif cmd == "set_brightness":
            hw.set_brightness(int(p.get("value", 0x10)))

        elif cmd == "clear":
            hw.clear()

    # ── Listener de socket Unix ────────────────────────────────────────────────

    def _socket_listener(self):
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(SOCKET_PATH)
        os.chmod(SOCKET_PATH, 0o666)
        srv.listen(8)
        srv.settimeout(1.0)

        while not self._stop.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            threading.Thread(
                target=self._handle_conn, args=(conn,), daemon=True
            ).start()

        srv.close()
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

    def _handle_conn(self, conn):
        try:
            data = b""
            conn.settimeout(2.0)
            while b"\n" not in data:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                data += chunk
            payload = json.loads(data.strip())

            if payload.get("cmd") == "status":
                conn.sendall(b'{"ok":true}\n')
            else:
                self.push(payload)
                conn.sendall(b'{"ok":true}\n')

        except Exception as e:
            try:
                conn.sendall(
                    json.dumps({"ok": False, "error": str(e)}).encode() + b"\n"
                )
            except Exception:
                pass
        finally:
            conn.close()


# ── Seleção de background ──────────────────────────────────────────────────────

def _load_background(name: str):
    """Retorna callable(hw) ou None para 'none'."""
    if name == "none":
        return None
    if name in ("clock_ip", "clock"):
        from backgrounds.bg_clock_ip import make_background
        return make_background()
    print(f"[warn] background '{name}' desconhecido, usando clock_ip.", file=sys.stderr)
    from backgrounds.bg_clock_ip import make_background
    return make_background()


# ── Ponto de entrada ───────────────────────────────────────────────────────────

def _parse_args():
    p = argparse.ArgumentParser(description="Servidor de display TX9")
    p.add_argument(
        "--brightness",
        type=lambda x: int(x, 0),
        default=0x10,
        help="Brilho: 0x10 (mínimo) a 0x70 (máximo). Padrão: 0x10",
    )
    p.add_argument(
        "--background",
        default="clock_ip",
        choices=["clock_ip", "clock", "none"],
        help="Tarefa de fundo. Padrão: clock_ip",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    server = DisplayServer()
    server.hw.set_brightness(args.brightness)
    server.set_background(_load_background(args.background))

    def _exit(sig, frame):
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT,  _exit)
    signal.signal(signal.SIGTERM, _exit)

    print(f"display_server pronto em {SOCKET_PATH} "
          f"(brightness=0x{args.brightness:02X}, background={args.background})",
          flush=True)
    server.run()
