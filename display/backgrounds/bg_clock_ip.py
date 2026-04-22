import datetime
import fcntl
import glob
import os
import socket
import struct
import time

from display_driver import (
    usb_storage_is_connected,
    IND_LAN, IND_WIFI, IND_USB,
)

SIOCGIFADDR = 0x8915


def _get_ip(iface: str) -> str:
    """Retorna o IPv4 da interface ou string vazia."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            res = fcntl.ioctl(
                s.fileno(), SIOCGIFADDR,
                struct.pack("256s", iface[:15].encode()),
            )
            return socket.inet_ntoa(res[20:24])
        finally:
            s.close()
    except OSError:
        return ""


def _iface_type(iface: str) -> str:
    """Retorna 'wifi', 'eth' ou '' para interfaces ignoradas (lo, virtual)."""
    if iface == "lo":
        return ""
    if os.path.isdir(f"/sys/class/net/{iface}/wireless"):
        return "wifi"
    # Descarta interfaces virtuais sem MAC físico (docker, bridge, tun…)
    try:
        with open(f"/sys/class/net/{iface}/address") as f:
            mac = f.read().strip()
        if mac in ("", "00:00:00:00:00:00"):
            return ""
    except OSError:
        return ""
    return "eth"


def _scan_ifaces() -> dict:
    """
    Varre /sys/class/net e retorna {iface: {"type": "eth"/"wifi", "ip": str}}
    para todas as interfaces up que possuam endereço IPv4.
    """
    result = {}
    for path in glob.glob("/sys/class/net/*"):
        iface = os.path.basename(path)
        itype = _iface_type(iface)
        if not itype:
            continue
        try:
            with open(f"/sys/class/net/{iface}/operstate") as f:
                op = f.read().strip()
        except OSError:
            continue
        if op not in ("up", "unknown"):
            continue
        ip = _get_ip(iface)
        if ip:
            result[iface] = {"type": itype, "ip": ip}
    return result


def make_background(
    clock_duration: float = 4.0,
    ip_step_delay: float = 0.35,
    net_interval: float = 5.0,
):
    """
    Retorna um callable(hw) para o servidor.
    Ciclo: relógio HH:MM (clock_duration s) → scroll com IPs das interfaces → repete.
    O ícone USB acende enquanto pendrive estiver conectado.
    """
    state = {
        "phase": "clock",
        "phase_start": time.monotonic(),
        "colon": True,
        # rede: {iface: {"type": "eth"/"wifi", "ip": str}}
        "last_net": 0.0,
        "ifaces": {},
        "usb": False,
        # scroll não-bloqueante
        "scroll_buf": "",
        "scroll_pos": 0,
        "scroll_last": 0.0,
    }

    def _has_type(itype: str) -> bool:
        return any(v["type"] == itype for v in state["ifaces"].values())

    def _build_scroll() -> str:
        # Ethernet primeiro (por nome), depois wifi (por nome)
        parts = []
        for iface, info in sorted(
            state["ifaces"].items(),
            key=lambda x: (0 if x[1]["type"] == "eth" else 1, x[0]),
        ):
            prefix = "LAN " if info["type"] == "eth" else "WIFI"
            parts.append(f"{prefix} {info['ip']}")
        return "      ".join(parts)

    def tick(hw):
        t = time.monotonic()
        now = datetime.datetime.now()

        # Atualiza estado de rede e USB periodicamente
        if t - state["last_net"] > net_interval:
            state["ifaces"]   = _scan_ifaces()
            state["usb"]      = usb_storage_is_connected()
            state["last_net"] = t

        state["colon"] = (now.second % 2 == 0)

        lan_on  = _has_type("eth")
        wifi_on = _has_type("wifi")

        # ── Fase: relógio ──────────────────────────────────────────────────
        if state["phase"] == "clock":
            hw.show_clock(
                hour=now.hour, minute=now.minute,
                colon_on=state["colon"],
                lan_on=lan_on, wifi_on=wifi_on,
                usb_on=state["usb"],
            )
            if t - state["phase_start"] >= clock_duration:
                text = _build_scroll()
                if text:
                    state["phase"]       = "scroll"
                    state["phase_start"] = t
                    state["scroll_buf"]  = "    " + text + "    "
                    state["scroll_pos"]  = 0
                    state["scroll_last"] = t

        # ── Fase: scroll de IPs ────────────────────────────────────────────
        else:
            buf = state["scroll_buf"]
            pos = state["scroll_pos"]

            # Monta máscara de indicadores ativos durante o scroll
            ind = 0x00
            if lan_on:
                ind |= IND_LAN
            if wifi_on:
                ind |= IND_WIFI
            if state["usb"]:
                ind |= IND_USB

            if t - state["scroll_last"] >= ip_step_delay:
                hw.show_text4(buf[pos: pos + 4], indicators=ind)
                state["scroll_pos"] += 1
                state["scroll_last"] = t

                if pos + 4 >= len(buf):
                    state["phase"]       = "clock"
                    state["phase_start"] = t

    return tick