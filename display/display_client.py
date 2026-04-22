#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
display_client.py — Cliente para o display_server TX9.

Como modulo Python:
    from display_client import DisplayClient
    c = DisplayClient()
    c.show_text("UPDT", duration=5)
    c.scroll("Sistema atualizado")

Como CLI:
    python3 display_client.py show_text "UPDT" --duration 5
    python3 display_client.py scroll "Temperatura 42 graus"
    python3 display_client.py show_number 42
    python3 display_client.py set_brightness 0x40
    python3 display_client.py status
    python3 display_client.py clear
"""
import argparse
import json
import socket
import sys

SOCKET_PATH = "/run/tx9-display.sock"


class DisplayClient:
    def __init__(self, path=SOCKET_PATH, timeout=3.0):
        self.path    = path
        self.timeout = timeout

    def _send(self, payload: dict) -> dict:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect(self.path)
            s.sendall((json.dumps(payload) + "\n").encode())
            raw = b""
            while b"\n" not in raw:
                chunk = s.recv(256)
                if not chunk:
                    break
                raw += chunk
            return json.loads(raw.strip())
        finally:
            s.close()

    def show_text(self, text, duration=3.0, priority=1):
        return self._send({"cmd": "show_text", "text": str(text),
                           "duration": float(duration), "priority": int(priority)})

    def show_number(self, value, duration=3.0, leading_zeros=True, priority=1):
        return self._send({"cmd": "show_number", "value": int(value),
                           "duration": float(duration),
                           "leading_zeros": leading_zeros,
                           "priority": int(priority)})

    def scroll(self, text, speed=0.35, priority=1):
        return self._send({"cmd": "scroll", "text": str(text),
                           "speed": float(speed), "priority": int(priority)})

    def set_brightness(self, value):
        return self._send({"cmd": "set_brightness", "value": int(value)})

    def clear(self):
        return self._send({"cmd": "clear"})

    def status(self):
        return self._send({"cmd": "status"})


# -----------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Envia comandos ao display TX9")
    p.add_argument("--socket", default=SOCKET_PATH)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("show_text")
    s.add_argument("text")
    s.add_argument("--duration", type=float, default=3.0)
    s.add_argument("--priority", type=int,   default=1)

    s = sub.add_parser("show_number")
    s.add_argument("value", type=int)
    s.add_argument("--duration",         type=float, default=3.0)
    s.add_argument("--no-leading-zeros", action="store_true")
    s.add_argument("--priority",         type=int,   default=1)

    s = sub.add_parser("scroll")
    s.add_argument("text")
    s.add_argument("--speed",    type=float, default=0.35)
    s.add_argument("--priority", type=int,   default=1)

    s = sub.add_parser("set_brightness")
    s.add_argument("value", type=lambda x: int(x, 0))

    sub.add_parser("clear")
    sub.add_parser("status")

    args = p.parse_args()
    c = DisplayClient(path=args.socket)

    try:
        if args.cmd == "show_text":
            result = c.show_text(args.text, args.duration, args.priority)
        elif args.cmd == "show_number":
            result = c.show_number(args.value, args.duration,
                                   not args.no_leading_zeros, args.priority)
        elif args.cmd == "scroll":
            result = c.scroll(args.text, args.speed, args.priority)
        elif args.cmd == "set_brightness":
            result = c.set_brightness(args.value)
        elif args.cmd == "clear":
            result = c.clear()
        elif args.cmd == "status":
            result = c.status()

        print(json.dumps(result))
        sys.exit(0 if result.get("ok") else 1)

    except (FileNotFoundError, ConnectionRefusedError):
        print("Erro: servidor nao encontrado. O servico esta rodando?", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()