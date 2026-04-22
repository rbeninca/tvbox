#!/usr/bin/env python3
"""
display_driver.py — Driver de baixo nível para o display FD6551 do TX9 Pro.

Hardware:
  - Display: 4 dígitos 7-segmentos + indicadores (FD6551 ou compatível)
  - Comunicação: GPIO Amlogic via /dev/mem (bit-bang serial síncrono 2 fios)
  - SoC: Amlogic S905W/X (GXL)

Referência de hardware (DISPLAY.MD):
  GPIO_BASE = 0xC8834000
  OEN @ +0x43C, OUT @ +0x440, IN @ +0x444
  CLK_BIT = 27, DIO_BIT = 29

Registradores FD6551:
  0x48 → Controle (brilho bits[7:4] + enable bit[0])
  0x66, 0x68, 0x6A, 0x6C → Dígitos 0-3
  0x6E → Indicadores (bit0=LAN, bit1=WiFi, bit2=Play, bit3=Pause,
                       bit4=Colon, bit5=Clock, bit6=USB)
"""

import mmap
import os
import struct
import time

# ── Constantes de hardware ─────────────────────────────────────────────────────

GPIO_BASE  = 0xC8834000
PAGE_SIZE  = 0x1000        # 4 KB, suficiente para cobrir todos os offsets

OEN_OFF    = 0x43C         # Output Enable register  (1=input/HiZ, 0=output)
OUT_OFF    = 0x440         # Output Data register
IN_OFF     = 0x444         # Input Data register

CLK_BIT    = 27
DIO_BIT    = 29

# Registradores FD6551
REG_CTRL   = 0x48
REG_DIGIT  = (0x66, 0x68, 0x6A, 0x6C)
REG_IND    = 0x6E

# Bits do registrador de indicadores
IND_LAN    = 1 << 0
IND_WIFI   = 1 << 1
IND_PLAY   = 1 << 2
IND_PAUSE  = 1 << 3
IND_COLON  = 1 << 4
IND_CLOCK  = 1 << 5
IND_USB    = 1 << 6

# ── Tabela de segmentos 7-seg (DP G F E D C B A) ──────────────────────────────

_SEG: dict[str, int] = {
    '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F,
    '4': 0x66, '5': 0x6D, '6': 0x7D, '7': 0x07,
    '8': 0x7F, '9': 0x6F,
    'A': 0x77, 'B': 0x7C, 'C': 0x39, 'D': 0x5E,
    'E': 0x79, 'F': 0x71, 'G': 0x3D, 'H': 0x76,
    'I': 0x06, 'J': 0x1E, 'L': 0x38, 'N': 0x37,
    'O': 0x3F, 'P': 0x73, 'Q': 0x67, 'R': 0x50,
    'S': 0x6D, 'T': 0x78, 'U': 0x3E, 'Y': 0x6E,
    '-': 0x40, '_': 0x08, ' ': 0x00, '.': 0x80,
}


def _seg(ch: str) -> int:
    """Converte caractere para padrão de segmentos."""
    return _SEG.get(ch.upper(), 0x00)


# ── Funções de estado de rede ──────────────────────────────────────────────────

def read_operstate(iface: str) -> bool:
    """Retorna True se a interface de rede está 'up'."""
    try:
        with open(f"/sys/class/net/{iface}/operstate") as f:
            return f.read().strip() == "up"
    except OSError:
        return False


def wifi_is_up() -> bool:
    """Retorna True se wlan0 está up."""
    return read_operstate("wlan0")


def get_network_state() -> dict:
    """Retorna dict com estado de LAN e WiFi."""
    return {"lan": read_operstate("eth0"), "wifi": wifi_is_up()}


def usb_storage_is_connected() -> bool:
    """Retorna True se há algum dispositivo de armazenamento USB conectado.
    Verifica /sys/block/sd* cujo symlink de device contém 'usb'.
    """
    import glob
    for dev in glob.glob("/sys/block/sd*"):
        try:
            link = os.readlink(dev)
            if "usb" in link:
                return True
        except OSError:
            pass
    return False


# ── Preparação ─────────────────────────────────────────────────────────────────

def prepare_display_gpio():
    """Valida pré-requisitos de acesso ao hardware (deve rodar como root)."""
    if not os.access("/dev/mem", os.R_OK | os.W_OK):
        raise PermissionError(
            "Sem acesso a /dev/mem. Execute o servidor como root."
        )


# ── Driver principal ───────────────────────────────────────────────────────────

class DisplayDriver:
    """
    Driver bit-bang para o display FD6551 do TX9 Pro.

    Parâmetros:
        bit_delay_us: tempo de setup por bit (us). Padrão 12us.
                      Intervalo recomendado: 10–100 us.
    """

    def __init__(self, bit_delay_us: int = 12):
        self._delay = bit_delay_us * 1e-6
        self._brightness = 0x10   # padrão: brilho mínimo

        fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        try:
            self._mm = mmap.mmap(
                fd, PAGE_SIZE,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
                offset=GPIO_BASE,
            )
        finally:
            os.close(fd)

        # CLK: saída permanente, começa em LOW
        self._clr_oen(CLK_BIT)
        self._clr_out(CLK_BIT)

        # DIO: open-drain — OUT mantém sempre 0; HIGH = input (HiZ)
        self._clr_out(DIO_BIT)
        self._set_oen(DIO_BIT)   # começa em HiZ (idle HIGH)

    # ── Ciclo de vida ──────────────────────────────────────────────────────────

    def activate(self):
        """Inicializa o FD6551 com a sequência robusta de rampa de brilho."""
        for val in (0x01, 0x11, 0x21, 0x31, 0x41, 0x51, 0x61, 0x71):
            self._send_cmd(REG_CTRL, val)
            self._clear_hw()
        # Aplica brilho configurado
        self._send_cmd(REG_CTRL, (self._brightness & 0xF0) | 0x01)

    def close(self):
        """Limpa o display e libera o mmap."""
        self.clear()
        self._mm.close()

    # ── API pública ────────────────────────────────────────────────────────────

    def clear(self):
        """Apaga todos os dígitos e indicadores."""
        self._clear_hw()

    def set_brightness(self, value: int):
        """
        Define o brilho.
        value: nibble alto = brilho (0x10 mínimo … 0x70 máximo), bit 0 = enable.
        """
        self._brightness = value & 0xF0
        self._send_cmd(REG_CTRL, self._brightness | 0x01)

    def show_text4(self, text: str, indicators: int = 0x00):
        """Exibe até 4 caracteres no display (completado com espaços).
        indicators: máscara de bits IND_* a manter acesos (padrão: apaga todos)."""
        text = (str(text) + "    ")[:4]
        self._write_digits([_seg(c) for c in text])
        self._send_cmd(REG_IND, indicators)

    def show_number(self, value: int, leading_zeros: bool = True):
        """Exibe número de 0 a 9999.
        Apaga todos os indicadores (incluindo os dois-pontos)."""
        value = max(0, min(9999, value))
        digits = [
            value // 1000,
            (value // 100) % 10,
            (value // 10) % 10,
            value % 10,
        ]
        segs = []
        blanking = not leading_zeros
        for i, d in enumerate(digits):
            if i == 3:
                blanking = False   # último dígito sempre visível
            if blanking and d == 0:
                segs.append(0x00)
            else:
                blanking = False
                segs.append(_seg(str(d)))
        self._write_digits(segs)
        self._send_cmd(REG_IND, 0x00)

    def scroll_text(self, text: str, step_delay: float = 0.35):
        """Rola texto da direita para a esquerda."""
        padded = "    " + str(text) + "    "
        for i in range(len(padded) - 3):
            self.show_text4(padded[i:i + 4])
            time.sleep(step_delay)

    def show_clock(
        self,
        hour: int,
        minute: int,
        colon_on: bool = True,
        lan_on: bool = False,
        wifi_on: bool = False,
        usb_on: bool = False,
    ):
        """Exibe HH:MM com indicadores de rede e USB."""
        segs = [
            _seg(str(hour // 10)),
            _seg(str(hour % 10)),
            _seg(str(minute // 10)),
            _seg(str(minute % 10)),
        ]
        self._write_digits(segs)
        ind = 0x00
        if colon_on:
            ind |= IND_COLON
        if lan_on:
            ind |= IND_LAN
        if wifi_on:
            ind |= IND_WIFI
        if usb_on:
            ind |= IND_USB
        self._send_cmd(REG_IND, ind)

    # ── Internos de display ────────────────────────────────────────────────────

    def _clear_hw(self):
        for reg in REG_DIGIT:
            self._send_cmd(reg, 0x00)
        self._send_cmd(REG_IND, 0x00)

    def _write_digits(self, segs: list):
        for reg, val in zip(REG_DIGIT, segs):
            self._send_cmd(reg, val)

    # ── Protocolo serial síncrono FD6551 ──────────────────────────────────────

    def _send_cmd(self, addr: int, data: int):
        self._start()
        self._write_byte(addr)
        self._write_byte(data)
        self._stop()

    def _start(self):
        """START: CLK=H, DIO 1→0, CLK=L"""
        self._dio_high()
        self._clk_high()
        self._wait()
        self._dio_low()
        self._wait()
        self._clk_low()
        self._wait()

    def _stop(self):
        """STOP: CLK=L, DIO=L, CLK=H, DIO=H"""
        self._clk_low()
        self._dio_low()
        self._wait()
        self._clk_high()
        self._wait()
        self._dio_high()
        self._wait()

    def _write_byte(self, byte: int):
        """Envia 1 byte MSB primeiro; consome ACK no 9º ciclo."""
        for bit in range(7, -1, -1):
            if (byte >> bit) & 1:
                self._dio_high()
            else:
                self._dio_low()
            self._wait()
            self._clk_high()
            self._wait()
            self._clk_low()
            self._wait()
        # Pulso de ACK — libera DIO e pulsa CLK
        self._dio_high()
        self._wait()
        self._clk_high()
        self._wait()
        self._clk_low()
        self._wait()

    # ── Controle de pinos ──────────────────────────────────────────────────────

    def _clk_high(self):
        self._set_out(CLK_BIT)

    def _clk_low(self):
        self._clr_out(CLK_BIT)

    def _dio_high(self):
        # Open-drain HIGH = colocar como entrada (HiZ)
        self._set_oen(DIO_BIT)

    def _dio_low(self):
        # Open-drain LOW = colocar como saída (OUT já está em 0)
        self._clr_oen(DIO_BIT)

    def _wait(self):
        if self._delay > 0:
            time.sleep(self._delay)

    # ── Acesso ao mmap de GPIO ─────────────────────────────────────────────────

    def _rd32(self, off: int) -> int:
        self._mm.seek(off)
        return struct.unpack("<I", self._mm.read(4))[0]

    def _wr32(self, off: int, val: int):
        self._mm.seek(off)
        self._mm.write(struct.pack("<I", val & 0xFFFFFFFF))

    def _set_oen(self, bit: int):
        self._wr32(OEN_OFF, self._rd32(OEN_OFF) | (1 << bit))

    def _clr_oen(self, bit: int):
        self._wr32(OEN_OFF, self._rd32(OEN_OFF) & ~(1 << bit))

    def _set_out(self, bit: int):
        self._wr32(OUT_OFF, self._rd32(OUT_OFF) | (1 << bit))

    def _clr_out(self, bit: int):
        self._wr32(OUT_OFF, self._rd32(OUT_OFF) & ~(1 << bit))
