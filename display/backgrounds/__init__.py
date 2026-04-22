"""
backgrounds — Tarefas de fundo plugáveis para o display_server TX9.

Cada módulo neste pacote expõe uma função `make_background()` que retorna
um callable `tick(hw)` chamado periodicamente pelo DisplayServer.

Disponíveis:
  bg_clock_ip   — Relógio HH:MM com indicadores de LAN/WiFi (padrão)
"""

from .bg_clock_ip import make_background

__all__ = ["make_background"]
