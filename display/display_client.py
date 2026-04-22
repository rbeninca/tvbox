#!/usr/bin/env python3
"""
Cliente leve para o display_server.
Uso como módulo:
    from display_client import DisplayClient
    DisplayClient().show_text("WIFI", duration=3)

Uso como CLI:
    python3 display_client.py show_text "WIFI" --duration 3
    python3 display_client.py scroll "Temperatura 42 graus"
    python3 display_client.py set_brightness 48
"""
import json, socket, argparse, sys

SOCKET_PATH = "/run/tx9-display.sock"

class DisplayClient:
    def __init__(self, path=SOCKET_PATH, timeout=2.0):
        self.path = path
        self.timeout = timeout

    def _send(self, payload: dict) -> dict:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect(self.path)
            s.sendall((json.dumps(payload) + "\n").encode())
            return json.loads(s.recv(256))
        finally:
            s.close()

    def show_text(self, text, duration=3.0, priority=1):
        return self._send({"cmd": "show_text", "text": text,
                           "duration": duration, "priority": priority})

    def show_number(self, value, duration=3.0, priority=1):
        return self._send({"cmd": "show_number", "value": value,
                           "duration": duration, "priority": priority})

    def scroll(self, text, speed=0.35, priority=1):
        return self._send({"cmd": "scroll", "text": text,
                           "speed": speed, "priority": priority})

    def set_brightness(self, value):
        return self._send({"cmd": "set_brightness", "value": value})

    def clear(self):
        return self._send({"cmd": "clear"})

    def status(self):
        return self._send({"cmd": "status"})


# ── CLI ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Envia comando ao display TX9")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("show_text")
    s.add_argument("text"); s.add_argument("--duration", type=float, default=3.0)
    s.add_argument("--priority", type=int, default=1)

    s = sub.add_parser("show_number")
    s.add_argument("value", type=int); s.add_argument("--duration", type=float, default=3.0)

    s = sub.add_parser("scroll")
    s.add_argument("text"); s.add_argument("--speed", type=float, default=0.35)

    s = sub.add_parser("set_brightness")
    s.add_argument("value", type=int)

    sub.add_parser("clear")
    sub.add_parser("status")

    args = p.parse_args()
    if not args.cmd:
        p.print_help(); sys.exit(1)

    client = DisplayClient()
    result = client._send(vars(args))
    print(json.dumps(result))