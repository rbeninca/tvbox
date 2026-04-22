#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mmap
import struct
import time
import os
import datetime
import signal
import socket
import fcntl
import sys

# =========================================================
# CONFIGURAÇÃO
# =========================================================

# Endereço base GPIO Amlogic
GPIO_BASE = 0xC8834000
GPIO_OEN  = 0x43C
GPIO_OUT  = 0x440

# Bits do barramento do display
CLK_BIT  = 27
DIO_BIT  = 29
CLK_MASK = 1 << CLK_BIT
DIO_MASK = 1 << DIO_BIT

# GPIOs Linux exportados no sysfs
SYSFS_GPIO_CLK = 546
SYSFS_GPIO_DIO = 548

# Temporização do bit-bang
BIT_DELAY = 0.00008

# Endereços do FD6551
STATUS_ADDR = 0x48
DIG0_ADDR   = 0x66
DIG1_ADDR   = 0x68
DIG2_ADDR   = 0x6A
DIG3_ADDR   = 0x6C
IND_ADDR    = 0x6E

# Brilho
# Exemplos: 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70
BRIGHTNESS = 0x10
DISPLAY_STATUS = (BRIGHTNESS & 0xF0) | 0x01

# Duração das fases
CLOCK_PHASE_SECONDS = 3.0
CLOCK_REFRESH_DELAY = 0.2
SCROLL_STEP_DELAY   = 0.35
TYPE_STEP_DELAY     = 0.28
IFACE_STEP_DELAY    = 0.24
OCTET_DURATION      = 1.0

# =========================================================
# INDICADORES
# =========================================================

IND_LAN   = 0x01
IND_WIFI  = 0x02
IND_PLAY  = 0x04
IND_PAUSE = 0x08
IND_COLON = 0x10
IND_CLOCK = 0x20
IND_USB   = 0x40

# =========================================================
# TABELA 7 SEGMENTOS
# =========================================================

SEGMENTS = {
    '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F,
    '4': 0x66, '5': 0x6D, '6': 0x7D, '7': 0x07,
    '8': 0x7F, '9': 0x6F,

    ' ': 0x00, '-': 0x40, '_': 0x08,

    'A': 0x77, 'B': 0x7C, 'C': 0x39, 'D': 0x5E,
    'E': 0x79, 'F': 0x71, 'G': 0x3D, 'H': 0x76,
    'I': 0x06, 'J': 0x1E, 'L': 0x38, 'N': 0x54,
    'O': 0x3F, 'P': 0x73, 'R': 0x50, 'T': 0x78,
    'U': 0x3E, 'W': 0x3E, 'Y': 0x6E,

    'b': 0x7C, 'c': 0x58, 'd': 0x5E, 'h': 0x74,
    'i': 0x04, 'n': 0x54, 'o': 0x5C, 'r': 0x50,
    't': 0x78, 'u': 0x1C,
}

display_driver_instance = None

# =========================================================
# GPIO SYSFS
# =========================================================

def prepare_display_gpio():
    gpio_base = "/sys/class/gpio"

    for gpio in (SYSFS_GPIO_CLK, SYSFS_GPIO_DIO):
        gpath = f"{gpio_base}/gpio{gpio}"

        try:
            with open(f"{gpio_base}/unexport", "w") as f:
                f.write(str(gpio))
        except OSError:
            pass

        time.sleep(0.02)

        if not os.path.exists(gpath):
            try:
                with open(f"{gpio_base}/export", "w") as f:
                    f.write(str(gpio))
            except OSError:
                pass

        time.sleep(0.02)

        try:
            with open(f"{gpath}/direction", "w") as f:
                f.write("out")
            with open(f"{gpath}/value", "w") as f:
                f.write("1")
        except OSError:
            pass

# =========================================================
# REDE
# =========================================================

def interface_exists(interface):
    return os.path.exists(f"/sys/class/net/{interface}")

def list_network_interfaces():
    base = "/sys/class/net"
    try:
        names = sorted(os.listdir(base))
    except OSError:
        return []

    result = []
    for name in names:
        if name == "lo":
            continue
        if interface_exists(name):
            result.append(name)
    return result

def is_wireless(interface):
    return os.path.exists(f"/sys/class/net/{interface}/wireless")

def read_operstate(interface):
    try:
        with open(f"/sys/class/net/{interface}/operstate", "r") as f:
            return f.read().strip() == "up"
    except OSError:
        return False

def get_ipv4_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ifreq = struct.pack("256s", ifname[:15].encode("utf-8"))
        res = fcntl.ioctl(s.fileno(), 0x8915, ifreq)  # SIOCGIFADDR
        return socket.inet_ntoa(res[20:24])
    except OSError:
        return None

def get_network_state():
    interfaces = []

    for name in list_network_interfaces():
        wireless = is_wireless(name)
        up = read_operstate(name)
        ip = get_ipv4_address(name)

        interfaces.append({
            "name": name,
            "type": "wireless" if wireless else "ethernet",
            "up": up,
            "ip": ip,
        })

    lan_icon = any(i["type"] == "ethernet" and (i["up"] or i["ip"]) for i in interfaces)
    wifi_icon = any(i["type"] == "wireless" and (i["up"] or i["ip"]) for i in interfaces)

    return {
        "interfaces": interfaces,
        "lan_icon": lan_icon,
        "wifi_icon": wifi_icon,
    }

def build_ip_sequence(state):
    wireless = []
    ethernet = []

    for item in state["interfaces"]:
        if not item["ip"]:
            continue

        entry = {
            "ifname": item["name"],
            "label": "WIFI" if item["type"] == "wireless" else "ETHERNET",
            "type": item["type"],
            "ip": item["ip"],
        }

        if item["type"] == "wireless":
            wireless.append(entry)
        else:
            ethernet.append(entry)

    wireless.sort(key=lambda x: x["ifname"])
    ethernet.sort(key=lambda x: x["ifname"])

    return wireless + ethernet

def short_ifname(ifname):
    name = ifname.upper()

    if name.startswith("WLAN") and len(name) >= 5:
        return "WLN" + name[-1]

    if name.startswith("WLX"):
        return "WLX" + name[-1]

    if name.startswith("ETH") and len(name) >= 4:
        return name[:4]

    if name.startswith("ENX"):
        return "ENX" + name[-1]

    if name.startswith("USB") and len(name) >= 4:
        return name[:4]

    return name[:4].ljust(4)

# =========================================================
# DRIVER DISPLAY
# =========================================================

class DisplayDriver:
    def __init__(self, dt=BIT_DELAY):
        self.dt = dt
        fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self.mm = mmap.mmap(fd, 0x1000, offset=GPIO_BASE)
        os.close(fd)

        self._dio_high()
        self._clk_high()
        time.sleep(0.005)

    def close(self):
        self.mm.close()

    def _r(self, off):
        self.mm.seek(off)
        return struct.unpack("<I", self.mm.read(4))[0]

    def _w(self, off, val):
        self.mm.seek(off)
        self.mm.write(struct.pack("<I", val))

    def _clk_high(self):
        self._w(GPIO_OEN, self._r(GPIO_OEN) & ~CLK_MASK)
        self._w(GPIO_OUT, self._r(GPIO_OUT) | CLK_MASK)

    def _clk_low(self):
        self._w(GPIO_OEN, self._r(GPIO_OEN) & ~CLK_MASK)
        self._w(GPIO_OUT, self._r(GPIO_OUT) & ~CLK_MASK)

    def _dio_high(self):
        self._w(GPIO_OEN, self._r(GPIO_OEN) | DIO_MASK)

    def _dio_low(self):
        self._w(GPIO_OUT, self._r(GPIO_OUT) & ~DIO_MASK)
        self._w(GPIO_OEN, self._r(GPIO_OEN) & ~DIO_MASK)

    def _start(self):
        self._dio_high()
        self._clk_high()
        time.sleep(self.dt)

        self._dio_low()
        time.sleep(self.dt)

        self._clk_low()
        time.sleep(self.dt)

    def _stop(self):
        self._dio_low()
        time.sleep(self.dt)

        self._clk_high()
        time.sleep(self.dt)

        self._dio_high()
        time.sleep(self.dt)

        self._clk_low()
        time.sleep(self.dt)

    def _write_byte(self, byte):
        for i in range(8):
            if byte & (0x80 >> i):
                self._dio_high()
            else:
                self._dio_low()

            time.sleep(self.dt)
            self._clk_high()
            time.sleep(self.dt)
            self._clk_low()
            time.sleep(self.dt)

        # ACK ignorado
        self._dio_high()
        time.sleep(self.dt)
        self._clk_high()
        time.sleep(self.dt)
        self._clk_low()
        time.sleep(self.dt)

    def send_cmd(self, addr, data):
        self._start()
        self._write_byte(addr)
        self._write_byte(data)
        self._stop()

    def init(self):
        self.send_cmd(STATUS_ADDR, DISPLAY_STATUS)
        time.sleep(0.01)
        self.clear()

    def clear(self):
        for addr in (DIG0_ADDR, DIG1_ADDR, DIG2_ADDR, DIG3_ADDR, IND_ADDR):
            self.send_cmd(addr, 0x00)

    def set_brightness(self, brightness):
        status = (brightness & 0xF0) | 0x01
        self.send_cmd(STATUS_ADDR, status)

    def _build_indicators(self, colon=False, clock=False, lan=False, wifi=False):
        ind = 0
        if colon:
            ind |= IND_COLON
        if clock:
            ind |= IND_CLOCK
        if lan:
            ind |= IND_LAN
        if wifi:
            ind |= IND_WIFI
        return ind

    def set_raw(self, d0, d1, d2, d3, indicators=0):
        self.send_cmd(DIG0_ADDR, d0)
        self.send_cmd(DIG1_ADDR, d1)
        self.send_cmd(DIG2_ADDR, d2)
        self.send_cmd(DIG3_ADDR, d3)
        self.send_cmd(IND_ADDR, indicators)

    def set_text4(self, text, indicators=0):
        text = (text[:4]).ljust(4)
        vals = [SEGMENTS.get(ch, 0x00) for ch in text]
        self.set_raw(vals[0], vals[1], vals[2], vals[3], indicators)

    def show_clock(self, hour, minute, colon_on, lan_on, wifi_on):
        d0 = SEGMENTS[str(hour // 10)]
        d1 = SEGMENTS[str(hour % 10)]
        d2 = SEGMENTS[str(minute // 10)]
        d3 = SEGMENTS[str(minute % 10)]

        ind = self._build_indicators(
            colon=colon_on,
            clock=True,
            lan=lan_on,
            wifi=wifi_on,
        )
        self.set_raw(d0, d1, d2, d3, ind)

    def scroll_text(self, text, step_delay=SCROLL_STEP_DELAY, lan=False, wifi=False, clock=False):
        ind = self._build_indicators(lan=lan, wifi=wifi, clock=clock)
        padded = "    " + text + "    "
        for i in range(len(padded) - 3):
            self.set_text4(padded[i:i+4], ind)
            time.sleep(step_delay)

    def show_octet(self, octet, duration=OCTET_DURATION, lan=False, wifi=False):
        ind = self._build_indicators(lan=lan, wifi=wifi)
        self.set_text4(str(int(octet)).rjust(4), ind)
        time.sleep(duration)

# =========================================================
# FLUXO DE EXIBIÇÃO
# =========================================================

def show_clock_phase(display, seconds=CLOCK_PHASE_SECONDS):
    start = time.monotonic()

    while time.monotonic() - start < seconds:
        state = get_network_state()
        now = datetime.datetime.now()

        display.show_clock(
            hour=now.hour,
            minute=now.minute,
            colon_on=(now.second % 2 == 0),
            lan_on=state["lan_icon"],
            wifi_on=state["wifi_icon"],
        )
        time.sleep(CLOCK_REFRESH_DELAY)

def show_ip_info_phase(display):
    state = get_network_state()
    seq = build_ip_sequence(state)

    if not seq:
        display.scroll_text(
            "NOIP",
            step_delay=SCROLL_STEP_DELAY,
            lan=state["lan_icon"],
            wifi=state["wifi_icon"]
        )
        return

    for item in seq:
        fresh = get_network_state()

        current = None
        for iface in fresh["interfaces"]:
            if iface["name"] == item["ifname"]:
                current = iface
                break

        if not current or not current["ip"]:
            continue

        lan_on = fresh["lan_icon"]
        wifi_on = fresh["wifi_icon"]

        display.scroll_text(
            "IP",
            step_delay=0.30,
            lan=lan_on,
            wifi=wifi_on
        )

        display.scroll_text(
            item["label"],
            step_delay=TYPE_STEP_DELAY,
            lan=lan_on,
            wifi=wifi_on
        )

        display.scroll_text(
            short_ifname(current["name"]),
            step_delay=IFACE_STEP_DELAY,
            lan=lan_on,
            wifi=wifi_on
        )

        for octet in current["ip"].split("."):
            fresh2 = get_network_state()
            display.show_octet(
                octet,
                duration=OCTET_DURATION,
                lan=fresh2["lan_icon"],
                wifi=fresh2["wifi_icon"]
            )

# =========================================================
# ENCERRAMENTO
# =========================================================

def cleanup_and_exit(signum=None, frame=None):
    global display_driver_instance
    try:
        if display_driver_instance is not None:
            display_driver_instance.clear()
            display_driver_instance.close()
    finally:
        raise SystemExit(0)

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    prepare_display_gpio()

    display_driver_instance = DisplayDriver(dt=BIT_DELAY)
    display_driver_instance.init()
    display_driver_instance.set_brightness(BRIGHTNESS)
    display_driver_instance.clear()

    try:
        print(f"Display iniciado | brilho=0x{BRIGHTNESS:02X}")
        while True:
            show_clock_phase(display_driver_instance, seconds=CLOCK_PHASE_SECONDS)
            show_ip_info_phase(display_driver_instance)
    except KeyboardInterrupt:
        cleanup_and_exit()
    except Exception as e:
        print(f"Erro: {e}")
        cleanup_and_exit()
