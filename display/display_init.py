#!/usr/bin/env python3
import mmap
import struct
import time
import os

# ===== Hardware =====
GPIO_BASE = 0xC8834000
GPIO_OEN  = 0x43C
GPIO_OUT  = 0x440
GPIO_IN   = 0x444   # se existir nesse bloco; usado só para ACK opcional

CLK_BIT  = 27
DIO_BIT  = 29
CLK_MASK = 1 << CLK_BIT
DIO_MASK = 1 << DIO_BIT

# Comandos/endereço no fio (datasheet "x2")
STATUS_ADDR = 0x48   # 0x24 << 1
ICONS_ADDR  = 0x66   # 0x33 << 1
DIG1_ADDR   = 0x68   # 0x34 << 1
DIG2_ADDR   = 0x6A   # 0x35 << 1
DIG3_ADDR   = 0x6C   # 0x36 << 1
DIG4_ADDR   = 0x6E   # 0x37 << 1

SEGMENTS = {
    0: 0x3F, 1: 0x06, 2: 0x5B, 3: 0x4F,
    4: 0x66, 5: 0x6D, 6: 0x7D, 7: 0x07,
    8: 0x7F, 9: 0x6F,
    " ": 0x00,
    "-": 0x40,
    "_": 0x08,
    "A": 0x77,
    "b": 0x7C,
    "C": 0x39,
    "d": 0x5E,
    "E": 0x79,
    "F": 0x71,
}

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

class DisplayDriver:
    def __init__(self, bit_delay_us=8):
        fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self.mm = mmap.mmap(fd, 0x1000, offset=GPIO_BASE)
        os.close(fd)
        self.delay = bit_delay_us / 1_000_000.0

        # Barramento em idle alto
        self._dio_release()
        self._clk_high()
        time.sleep(0.005)

    def close(self):
        self.mm.close()

    def _sleep(self):
        time.sleep(self.delay)

    def _r(self, off):
        self.mm.seek(off)
        return struct.unpack('<I', self.mm.read(4))[0]

    def _w(self, off, val):
        self.mm.seek(off)
        self.mm.write(struct.pack('<I', val))

    # ===== Clock =====
    def _clk_high(self):
        # saída habilitada + nível alto
        self._w(GPIO_OEN, self._r(GPIO_OEN) & ~CLK_MASK)
        self._w(GPIO_OUT, self._r(GPIO_OUT) | CLK_MASK)
        self._sleep()

    def _clk_low(self):
        self._w(GPIO_OEN, self._r(GPIO_OEN) & ~CLK_MASK)
        self._w(GPIO_OUT, self._r(GPIO_OUT) & ~CLK_MASK)
        self._sleep()

    # ===== Data (open-drain style) =====
    def _dio_release(self):
        # libera linha => pull-up externo/interno mantém alto
        self._w(GPIO_OEN, self._r(GPIO_OEN) | DIO_MASK)
        self._sleep()

    def _dio_low(self):
        self._w(GPIO_OUT, self._r(GPIO_OUT) & ~DIO_MASK)
        self._w(GPIO_OEN, self._r(GPIO_OEN) & ~DIO_MASK)
        self._sleep()

    def _dio_read(self):
        # se GPIO_IN não for válido no seu SoC, remova ACK real e deixe ACK "cego"
        try:
            return 1 if (self._r(GPIO_IN) & DIO_MASK) else 0
        except Exception:
            return 1

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

    def _write_byte(self, byte, check_ack=False):
        # MSB first
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

        # ACK bit
        self._dio_release()
        self._sleep()
        self._clk_high()
        self._sleep()

        ack = True
        if check_ack:
            ack = (self._dio_read() == 0)

        self._clk_low()
        self._sleep()
        return ack

    def send_cmd(self, addr, data, check_ack=False):
        self._start()
        ack1 = self._write_byte(addr, check_ack=check_ack)
        ack2 = self._write_byte(data, check_ack=check_ack)
        self._stop()
        self._bus_idle()
        return ack1 and ack2

    def clear(self):
        self.send_cmd(DIG1_ADDR, 0x00)
        self.send_cmd(DIG2_ADDR, 0x00)
        self.send_cmd(DIG3_ADDR, 0x00)
        self.send_cmd(DIG4_ADDR, 0x00)
        self.send_cmd(ICONS_ADDR, 0x00)

    def raw_test_pattern(self):
        # 8.8.8.8 + ícones apagados
        self.send_cmd(DIG1_ADDR, 0x7F)
        self.send_cmd(DIG2_ADDR, 0x7F)
        self.send_cmd(DIG3_ADDR, 0x7F)
        self.send_cmd(DIG4_ADDR, 0x7F)
        self.send_cmd(ICONS_ADDR, 0x00)

    def show_text4(self, text):
        text = (text[:4]).ljust(4)
        vals = [SEGMENTS.get(ch, 0x00) for ch in text]
        self.send_cmd(DIG1_ADDR, vals[0])
        self.send_cmd(DIG2_ADDR, vals[1])
        self.send_cmd(DIG3_ADDR, vals[2])
        self.send_cmd(DIG4_ADDR, vals[3])

    def show_number(self, n, icons=0x00):
        s_num = f"{n:04d}"
        self.send_cmd(DIG1_ADDR, SEGMENTS[int(s_num[0])])
        self.send_cmd(DIG2_ADDR, SEGMENTS[int(s_num[1])])
        self.send_cmd(DIG3_ADDR, SEGMENTS[int(s_num[2])])
        self.send_cmd(DIG4_ADDR, SEGMENTS[int(s_num[3])])
        self.send_cmd(ICONS_ADDR, icons)

    def _try_status_value(self, value):
        # sequência conservadora
        self._bus_idle()
        time.sleep(0.002)

        # status/brightness
        self.send_cmd(STATUS_ADDR, value)
        time.sleep(0.003)

        # limpa tudo após ativar
        self.clear()
        time.sleep(0.003)

        # escreve padrão de teste
        self.raw_test_pattern()
        time.sleep(0.02)

    def activate(self, verbose=True):
        """
        Tenta ativar o display com uma sequência mais robusta.

        0x48 é o endereço de status no fio.
        O byte exato de brilho/enable varia entre implementações;
        0x71 é um candidato comum no seu contexto, mas alguns painéis
        aceitam outros valores.
        """
        # candidatos: seu 0x71 + varredura de valores baixos e alguns nibbles altos
        candidates = [
            0x01, 0x03, 0x07,
            0x11, 0x21, 0x31, 0x41, 0x51, 0x61, 0x71,
            0x09, 0x19, 0x29, 0x39, 0x49, 0x59, 0x69, 0x79,
            0x0F, 0x1F, 0x7F
        ]

        # primeiro: estado limpo
        self._bus_idle()
        time.sleep(0.01)

        for val in candidates:
            if verbose:
                print(f"[activate] testando STATUS=0x{val:02X}")
            self._try_status_value(val)
            time.sleep(0.05)

        # deixa por padrão o valor que você já usava
        self.send_cmd(STATUS_ADDR, 0x71)
        time.sleep(0.01)
        self.clear()
        time.sleep(0.01)

    def activate_with_probe(self):
        """
        Faz um teste visual automático para você descobrir qual byte 'acende' de fato.
        """
        tests = [
            ("----", 0x00),
            ("8888", 0x00),
            ("1111", 0x00),
            ("2222", 0x00),
            ("8888", 0x20),
            ("8888", 0x10),
            ("8888", 0x30),
        ]

        candidates = [0x71, 0x61, 0x51, 0x41, 0x31, 0x21, 0x11, 0x01, 0x79, 0x19, 0x09]

        for val in candidates:
            print(f"\n[probe] STATUS=0x{val:02X}")
            self.send_cmd(STATUS_ADDR, val)
            time.sleep(0.01)

            for txt, icon in tests:
                if txt == "----":
                    self.show_text4("----")
                else:
                    self.show_text4(txt)
                self.send_cmd(ICONS_ADDR, icon)
                time.sleep(0.7)

            self.clear()
            time.sleep(0.15)

if __name__ == "__main__":
    prepare_display_gpio()
    display = DisplayDriver(bit_delay_us=12)   # comece com 8~15 us

    try:
        # Ativação robusta
        display.activate(verbose=True)

        # Opcional: faça uma varredura visual para descobrir qual STATUS realmente acende
        # display.activate_with_probe()

        contador = 0
        while True:
            icons = 0x20 | (0x10 if contador % 2 == 0 else 0x00)
            display.show_number(contador, icons=icons)
            contador = (contador + 1) % 10000
            time.sleep(1)

    except KeyboardInterrupt:
        display.clear()
    finally:
        display.close()