#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import mmap
import os
import signal
import struct
import sys
import time

# Endereço base GPIO Amlogic
GPIO_BASE = 0xC8834000
GPIO_OEN = 0x43C
GPIO_OUT = 0x440

# Bits do barramento do display
CLK_BIT = 27
DIO_BIT = 29
CLK_MASK = 1 << CLK_BIT
DIO_MASK = 1 << DIO_BIT

# GPIOs Linux exportados no sysfs
SYSFS_GPIO_CLK = 546
SYSFS_GPIO_DIO = 548

# Endereços do FD6551
STATUS_ADDR = 0x48
DIG0_ADDR = 0x66
DIG1_ADDR = 0x68
DIG2_ADDR = 0x6A
DIG3_ADDR = 0x6C
IND_ADDR = 0x6E

# Brilho
BRIGHTNESS = 0x10
DISPLAY_STATUS = (BRIGHTNESS & 0xF0) | 0x01

SEGMENTS = {
    " ": 0x00,
    "-": 0x40,
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

display_driver_instance = None
clear_display_on_exit = True


def prepare_display_gpio():
    gpio_base = "/sys/class/gpio"

    for gpio in (SYSFS_GPIO_CLK, SYSFS_GPIO_DIO):
        gpath = f"{gpio_base}/gpio{gpio}"

        try:
            with open(f"{gpio_base}/unexport", "w", encoding="utf-8") as f:
                f.write(str(gpio))
        except OSError:
            pass

        time.sleep(0.02)

        if not os.path.exists(gpath):
            try:
                with open(f"{gpio_base}/export", "w", encoding="utf-8") as f:
                    f.write(str(gpio))
            except OSError:
                pass

        time.sleep(0.02)

        try:
            with open(f"{gpath}/direction", "w", encoding="utf-8") as f:
                f.write("out")
            with open(f"{gpath}/value", "w", encoding="utf-8") as f:
                f.write("1")
        except OSError:
            pass


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

    def activate(self):
        self._bus_idle()
        time.sleep(0.01)
        self.send_cmd(STATUS_ADDR, DISPLAY_STATUS)
        time.sleep(0.01)
        self.clear()
        time.sleep(0.01)

    def clear(self):
        for addr in (DIG0_ADDR, DIG1_ADDR, DIG2_ADDR, DIG3_ADDR, IND_ADDR):
            self.send_cmd(addr, 0x00)

    def set_brightness(self, brightness):
        status = (brightness & 0xF0) | 0x01
        self.send_cmd(STATUS_ADDR, status)
        time.sleep(0.01)

    def show_number(self, value, leading_zeroes=True):
        if not 0 <= value <= 9999:
            raise ValueError("O display suporta somente valores entre 0 e 9999.")

        if leading_zeroes:
            text = f"{value:04d}"
        else:
            text = str(value).rjust(4)

        digits = [SEGMENTS[ch] for ch in text]
        self.send_cmd(DIG0_ADDR, digits[0])
        self.send_cmd(DIG1_ADDR, digits[1])
        self.send_cmd(DIG2_ADDR, digits[2])
        self.send_cmd(DIG3_ADDR, digits[3])
        self.send_cmd(IND_ADDR, 0x00)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Faz uma contagem simples no display frontal FD6551 do TX9."
    )
    parser.add_argument("--inicio", type=int, default=0, help="Valor inicial da contagem.")
    parser.add_argument("--fim", type=int, default=9999, help="Valor final da contagem.")
    parser.add_argument("--passo", type=int, default=1, help="Incremento da contagem.")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Tempo em segundos entre cada atualização.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Reinicia a contagem automaticamente ao chegar no final.",
    )
    parser.add_argument(
        "--sem-zeros",
        action="store_true",
        help="Mostra a contagem alinhada à direita, sem zeros à esquerda.",
    )
    parser.add_argument(
        "--manter-ao-sair",
        action="store_true",
        help="Nao limpa o display ao encerrar; util para handoff entre servicos.",
    )
    args = parser.parse_args()

    if args.passo == 0:
        parser.error("--passo não pode ser zero.")
    if args.delay < 0:
        parser.error("--delay não pode ser negativo.")
    if not 0 <= args.inicio <= 9999:
        parser.error("--inicio deve estar entre 0 e 9999.")
    if not 0 <= args.fim <= 9999:
        parser.error("--fim deve estar entre 0 e 9999.")
    if args.inicio < args.fim and args.passo < 0:
        parser.error("Use um --passo positivo para contagem crescente.")
    if args.inicio > args.fim and args.passo > 0:
        parser.error("Use um --passo negativo para contagem decrescente.")

    return args


def iter_values(start, end, step):
    if step > 0:
        return range(start, end + 1, step)
    return range(start, end - 1, step)


def cleanup_and_exit(signum=None, frame=None):
    del signum, frame

    global clear_display_on_exit, display_driver_instance
    try:
        if display_driver_instance is not None:
            if clear_display_on_exit:
                display_driver_instance.clear()
            display_driver_instance.close()
    finally:
        raise SystemExit(0)


def main():
    global clear_display_on_exit, display_driver_instance

    args = parse_args()
    clear_display_on_exit = not args.manter_ao_sair

    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    prepare_display_gpio()

    display_driver_instance = DisplayDriver(bit_delay_us=12)
    display_driver_instance.activate()
    display_driver_instance.set_brightness(BRIGHTNESS)

    print(
        "Contador iniciado "
        f"| inicio={args.inicio} fim={args.fim} passo={args.passo} "
        f"delay={args.delay:.3f}s loop={args.loop}"
    )

    try:
        while True:
            for value in iter_values(args.inicio, args.fim, args.passo):
                display_driver_instance.show_number(
                    value,
                    leading_zeroes=not args.sem_zeros,
                )
                time.sleep(args.delay)

            if not args.loop:
                break
    except KeyboardInterrupt:
        cleanup_and_exit()
    finally:
        cleanup_and_exit()


if __name__ == "__main__":
    main()
