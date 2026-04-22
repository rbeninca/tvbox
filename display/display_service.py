#!/usr/bin/env python3
"""
Servidor de display TX9. Único processo que acessa o hardware.
Aceita comandos JSON via socket Unix /run/tx9-display.sock.
"""
import json, os, socket, signal, threading, time, queue, sys
from display_driver import DisplayDriver, prepare_display_gpio

SOCKET_PATH = "/run/tx9-display.sock"
BG_REFRESH   = 0.5   # intervalo da tarefa de fundo (s)

class DisplayServer:
    def __init__(self):
        prepare_display_gpio()
        self.hw = DisplayDriver(bit_delay_us=12)
        self.hw.activate()

        # Fila de mensagens prioritárias (priority, deadline, payload)
        self._q = queue.PriorityQueue()
        self._lock = threading.Lock()
        self._stop = threading.Event()

        # Tarefa de fundo plugável — troca sem reiniciar o servidor
        self._bg = None      # callable(hw) chamado a cada tick
        self._bg_lock = threading.Lock()

    # ── API interna ────────────────────────────────────────────────
    def set_background(self, fn):
        """Troca a tarefa de fundo em runtime (thread-safe)."""
        with self._bg_lock:
            self._bg = fn

    def push(self, payload: dict):
        priority  = payload.get("priority", 1)
        duration  = payload.get("duration", 3.0)
        deadline  = time.monotonic() + duration
        self._q.put((priority, deadline, payload))

    # ── Loop principal ─────────────────────────────────────────────
    def run(self):
        threading.Thread(target=self._socket_listener, daemon=True).start()
        while not self._stop.is_set():
            # Consome mensagens prioritárias enquanto dentro do prazo
            try:
                while True:
                    pri, deadline, payload = self._q.get_nowait()
                    remaining = deadline - time.monotonic()
                    if remaining > 0:
                        self._dispatch(payload, remaining)
                    # descarta se expirou
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

    # ── Despacho de comando ────────────────────────────────────────
    def _dispatch(self, p: dict, duration: float):
        cmd = p.get("cmd")
        hw  = self.hw
        end = time.monotonic() + duration

        if cmd == "show_text":
            text = p.get("text", "    ")
            hw.show_text4(text)
            time.sleep(min(duration, end - time.monotonic()))

        elif cmd == "show_number":
            hw.show_number(int(p.get("value", 0)))
            time.sleep(min(duration, end - time.monotonic()))

        elif cmd == "scroll":
            text  = p.get("text", "")
            speed = p.get("speed", 0.35)
            hw.scroll_text(text, step_delay=speed)

        elif cmd == "set_brightness":
            hw.set_brightness(int(p.get("value", 0x10)))

        elif cmd == "clear":
            hw.clear()

    # ── Listener de socket ─────────────────────────────────────────
    def _socket_listener(self):
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(SOCKET_PATH)
        os.chmod(SOCKET_PATH, 0o666)   # qualquer usuário pode enviar
        srv.listen(8)
        srv.settimeout(1.0)

        while not self._stop.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            threading.Thread(target=self._handle_conn,
                             args=(conn,), daemon=True).start()

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
                conn.sendall(json.dumps({"ok": False,
                                         "error": str(e)}).encode() + b"\n")
            except Exception:
                pass
        finally:
            conn.close()


# ── main ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    from backgrounds.bg_clock_ip import make_background

    server = DisplayServer()
    server.set_background(make_background())

    def _exit(sig, frame):
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT,  _exit)
    signal.signal(signal.SIGTERM, _exit)

    print("display_server pronto em", SOCKET_PATH)
    server.run()