#!/usr/bin/env python3
import mmap
import struct
import time
import os
import datetime
import signal
import sys

# ===== Hardware =====
GPIO_BASE = 0xC8834000
GPIO_OEN  = 0x43C
GPIO_OUT  = 0x440
GPIO_IN   = 0x444   # opcional

CLK_BIT  = 27
DIO_BIT  = 29
CLK_MASK = 1 << CLK_BIT
DIO_MASK = 1 << DIO_BIT

# ===== FD6551 - endereços corretos =====
STATUS_ADDR = 0x48
DIG1_ADDR   = 0x66
DIG2_ADDR   = 0x68
DIG3_ADDR   = 0x6A
DIG4_ADDR   = 0x6C
ICONS_ADDR  = 0x6E

# ===== Brilho =====
# Exemplos: 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70
BRIGHTNESS = 0x10
DISPLAY_STATUS = (BRIGHTNESS & 0xF0) | 0x01

# ===== Segmentos =====
SEGMENTS = {
    " ": 0x00,
    "-": 0x40,
    "_": 0x08,
    "0": 0x3F,
    "1": 0x06,
    "2": 0x5B,
    "3": 0x4F,
    "4": 0x66,
    "5": 0x6D,
    "6": 0x7D,
    "7": 0x07,
    "8": 0x7F,
    "9": 0x6F,
}

# ===== Ícones em 0x6E =====
IND_LAN   = 0x01
IND_WIFI  = 0x02
IND_PLAY  = 0x04
IND_PAUSE = 0x08
IND_COLON = 0x10
IND_CLOCK = 0x20
IND_USB   = 0x40

NET_CHECK_INTERVAL = 5.0

def prepare_display_gpio():
    gpio_base = "/sys/class/gpio"
    for gpio in (546, 548):
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

def read_operstate(interface):
    try:
        with open(f"/sys/class/net/{interface}/operstate") as f:
            return f.read().strip() == "up"
    except OSError:
        return False

def wifi_is_up():
    return read_operstate("wlan1") or read_operstate("wlan0")

class DisplayDriver:
    def __init__(self, bit_delay_us=12):
        fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self.mm = mmap.mmap(fd, 0x1000, offset=GPIO_BASE)
        os.close(fd)
        self.delay = bit_delay_us / 1_000_000.0

        self._dio_release()
        self._clk_high()
        time.sleep(0.005)

    def close(self):
        self.mm.close()

    def _sleep(self):
        time.sleep(self.delay)

    def _r(self, off):
        self.mm.seek(off)
        return struct.unpack("<I", self.mm.read(4))[0]

    def _w(self, off, val):
        self.mm.seek(off)
        self.mm.write(struct.pack("<I", val))

    def _clk_high(self):
        self._w(GPIO_OEN, self._r(GPIO_OEN) & ~CLK_MASK)
        self._w(GPIO_OUT, self._r(GPIO_OUT) | CLK_MASK)
        self._sleep()

    def _clk_low(self):
        self._w(GPIO_OEN, self._r(GPIO_OEN) & ~CLK_MASK)
        self._w(GPIO_OUT, self._r(GPIO_OUT) & ~CLK_MASK)
        self._sleep()

    def _dio_release(self):
        self._w(GPIO_OEN, self._r(GPIO_OEN) | DIO_MASK)
        self._sleep()

    def _dio_low(self):
        self._w(GPIO_OUT, self._r(GPIO_OUT) & ~DIO_MASK)
        self._w(GPIO_OEN, self._r(GPIO_OEN) & ~DIO_MASK)
        self._sleep()

    def _bus_idle(self):
        self._dio_release()
        self._clk_high()
        self._sleep()

    def _start(self):
        self._dio_release()
        self._clk_high()
        self._sleep()
        self._dio_low()
        self._sleep()
        self._clk_low()
        self._sleep()

    def _stop(self):
        self._dio_low()
        self._sleep()
        self._clk_high()
        self._sleep()
        self._dio_release()
        self._sleep()

    def _write_byte(self, byte):
        for i in range(8):
            if byte & (0x80 >> i):
                self._dio_release()
            else:
                self._dio_low()
            self._sleep()
            self._clk_high()
            self._sleep()
            self._clk_low()
            self._sleep()

        # ACK ignorado
        self._dio_release()
        self._sleep()
        self._clk_high()
        self._sleep()
        self._clk_low()
        self._sleep()

    def send_cmd(self, addr, data):
        self._start()
        self._write_byte(addr)
        self._write_byte(data)
        self._stop()
        self._bus_idle()

    def clear(self):
        self.send_cmd(DIG1_ADDR, 0x00)
        self.send_cmd(DIG2_ADDR, 0x00)
        self.send_cmd(DIG3_ADDR, 0x00)
        self.send_cmd(DIG4_ADDR, 0x00)
        self.send_cmd(ICONS_ADDR, 0x00)

    def activate(self):
        self._bus_idle()
        time.sleep(0.01)
        self.send_cmd(STATUS_ADDR, DISPLAY_STATUS)
        time.sleep(0.01)
        self.clear()
        time.sleep(0.01)

    def set_brightness(self, brightness):
        status = (brightness & 0xF0) | 0x01
        self.send_cmd(STATUS_ADDR, status)
        time.sleep(0.01)

    def update_time_and_network(self, h, m, colon_on, lan_on, wifi_on):
        d0 = SEGMENTS[str(h // 10)]
        d1 = SEGMENTS[str(h % 10)]
        d2 = SEGMENTS[str(m // 10)]
        d3 = SEGMENTS[str(m % 10)]

        icons = IND_CLOCK
        if colon_on:
            icons |= IND_COLON
        if lan_on:
            icons |= IND_LAN
        if wifi_on:
            icons |= IND_WIFI

        self.send_cmd(DIG1_ADDR, d0)
        self.send_cmd(DIG2_ADDR, d1)
        self.send_cmd(DIG3_ADDR, d2)
        self.send_cmd(DIG4_ADDR, d3)
        self.send_cmd(ICONS_ADDR, icons)

display = None

def cleanup_and_exit(signum=None, frame=None):
    global display
    if display is not None:
        try:
            display.clear()
            display.close()
        except Exception:
            pass
    sys.exit(0)

if __name__ == "__main__":
    prepare_display_gpio()
    display = DisplayDriver(bit_delay_us=12)

    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    try:
        display.activate()
        display.set_brightness(BRIGHTNESS)

        last_net_check = 0.0
        lan_on = False
        wifi_on = False

        print(f"Relógio iniciado | brilho=0x{BRIGHTNESS:02X}")

        while True:
            now = datetime.datetime.now()
            colon_on = (now.second % 2 == 0)

            t = time.monotonic()
            if t - last_net_check >= NET_CHECK_INTERVAL:
                lan_on = read_operstate("eth0")
                wifi_on = wifi_is_up()
                last_net_check = t

            display.update_time_and_network(
                now.hour,
                now.minute,
                colon_on,
                lan_on,
                wifi_on
            )

            time.sleep(0.5)

    except KeyboardInterrupt:
        cleanup_and_exit()
    finally:
        cleanup_and_exit()