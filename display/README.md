# TX9 Display Service

Serviço de controle do display frontal 7-segmentos do TV Box **TX9 Pro** (SoC Amlogic S905W/X).

---

## Hardware

| Item | Detalhe |
|---|---|
| Driver IC | FD6551 (ou compatível não documentado) |
| Interface | Serial síncrono 2 fios via GPIO Amlogic (bit-bang) |
| SoC | Amlogic S905W/X (GXL) — acesso via `/dev/mem` |
| Dígitos | 4 × 7-segmentos |
| Indicadores | LAN, Wi-Fi, Relógio, Dois-pontos (:), Play, Pause, USB |

### GPIO

| Sinal | Bit | Tipo |
|---|---|---|
| CLK | 27 | Saída |
| DIO | 29 | Open-drain (bidirecional) |

`GPIO_BASE = 0xC8834000` — registradores `OEN` (+0x43C), `OUT` (+0x440), `IN` (+0x444).

### Registradores FD6551

| Endereço | Função |
|---|---|
| `0x48` | Controle: brilho `[7:4]` + enable `[0]` |
| `0x66` | Dígito 0 (mais à esquerda) |
| `0x68` | Dígito 1 |
| `0x6A` | Dígito 2 |
| `0x6C` | Dígito 3 (mais à direita) |
| `0x6E` | Indicadores |

---

## Arquitetura

```
                     ┌──────────────────────────────────┐
  qualquer processo  │  display_client.py               │
  (Python ou CLI)    │  socket Unix /run/tx9-display.sock│
                     └────────────────┬─────────────────┘
                                      │ JSON over Unix socket
                     ┌────────────────▼─────────────────┐
                     │  display_server.py               │
                     │  (único processo com acesso hw)  │
                     │  fila de prioridade + background │
                     └────────────────┬─────────────────┘
                                      │
                     ┌────────────────▼─────────────────┐
                     │  display_driver.py               │
                     │  GPIO bit-bang → FD6551          │
                     └──────────────────────────────────┘

  Fase de boot (antes da rede):
  ┌────────────────────────────┐
  │  display_boot.py           │
  │  contador crescente no hw  │
  │  (acesso direto ao driver) │
  └────────────────────────────┘
```

### Arquivos

| Arquivo | Função |
|---|---|
| `display_driver.py` | Driver de baixo nível — GPIO/mmap, protocolo FD6551, tabela 7-seg |
| `display_server.py` | Servidor IPC — fila de prioridade, socket Unix, background plugável |
| `display_client.py` | Cliente — módulo Python e CLI (`tx9-show`) |
| `display_boot.py` | Contador de boot — roda antes do servidor, acesso direto ao driver |
| `backgrounds/bg_clock_ip.py` | Tarefa de fundo — relógio HH:MM com indicadores LAN/Wi-Fi |
| `install_display_server.sh` | Script de instalação/desinstalação local ou remota (via SSH) |

---

## Instalação

Requer **Python 3** e acesso root (necessário para `/dev/mem`).

```bash
# Instalação local
sudo bash install_display_server.sh install

# Instalação remota (1 sessão SSH)
TARGET_HOST=192.168.1.106 TARGET_USER=root bash install_display_server.sh install
```

O script instala:

- Arquivos Python em `/opt/tx9/display/`
- Configuração em `/etc/default/tx9-display`
- CLI global `/usr/local/bin/tx9-show` → `display_client.py`
- Dois serviços systemd:

| Serviço | Quando | Função |
|---|---|---|
| `tx9-display-boot.service` | Fase inicial (`basic.target`) | Contador de boot, sem rede |
| `tx9-display.service` | Após rede (`network-online.target`) | Servidor IPC + relógio |

---

## Configuração

`/etc/default/tx9-display`:

```bash
# Brilho: 0x10 (mínimo) a 0x70 (máximo)
DISPLAY_BRIGHTNESS=0x10

# Tarefa de fundo: clock_ip | clock | none
DISPLAY_BACKGROUND=clock_ip

# Argumentos do contador de boot
DISPLAY_BOOT_ARGS=--fim 9999 --delay 0.05 --loop --manter-ao-sair
```

---

## Uso via CLI

```bash
# Exibe texto fixo por 5 segundos (até 4 caracteres)
# O indicador ":" é apagado automaticamente durante a exibição
tx9-show show_text "UPDT" --duration 5

# Texto com mais de 4 caracteres rola automaticamente no display
tx9-show show_text "NETFLIX" --duration 5
tx9-show show_text "Sistema iniciado"

# Exibe número (indicador ":" também é apagado)
tx9-show show_number 42

# Rola texto explicitamente (controle de velocidade)
tx9-show scroll "Sistema atualizado com sucesso" --speed 0.3

# Ajusta brilho (0x10 mínimo, 0x70 máximo)
tx9-show set_brightness 0x40

# Limpa o display
tx9-show clear

# Verifica se o servidor está respondendo
tx9-show status
```

---

## Uso como módulo Python

```python
from display_client import DisplayClient

c = DisplayClient()

# Texto curto: exibição fixa, indicador ":" apagado
c.show_text("BOOT", duration=3)

# Texto longo: rola automaticamente (> 4 caracteres)
c.show_text("NETFLIX", duration=5)
c.show_text("Atualizando sistema", speed=0.3)

# Número: indicador ":" também apagado
c.show_number(42, duration=2)

c.scroll("Temperatura 38 graus Celsius", speed=0.3)
c.set_brightness(0x40)
c.clear()
print(c.status())   # {"ok": true}
```

---

## Protocolo do socket

Comandos enviados como JSON com `\n` terminador para `/run/tx9-display.sock`.

| Campo | Tipo | Descrição |
|---|---|---|
| `cmd` | string | `show_text`, `show_number`, `scroll`, `set_brightness`, `clear`, `status` |
| `priority` | int | Prioridade da fila (menor = mais urgente). Padrão: `1` |
| `duration` | float | Tempo de exibição em segundos. Padrão: `3.0` |
| `speed` | float | Velocidade do scroll em segundos por passo. Padrão: `0.35` |

### Comportamento de `show_text`

| Comprimento do texto | Comportamento |
|---|---|
| ≤ 4 caracteres | Exibição fixa pelo tempo de `duration`; indicador `:` apagado |
| > 4 caracteres | Rola automaticamente da direita para a esquerda; velocidade controlada por `speed` |

### Exemplos diretos

```bash
# Via Python
python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/run/tx9-display.sock')
s.sendall(json.dumps({'cmd':'show_text','text':'OLA','duration':5}).encode() + b'\n')
print(s.recv(256))
s.close()
"

# Via install script (remoto)
TARGET_HOST=192.168.1.106 bash install_display_server.sh send '{"cmd":"scroll","text":"TX9 online"}'
```

---

## Gerenciamento do serviço

```bash
# Status
sudo bash install_display_server.sh status

# Reiniciar
sudo bash install_display_server.sh restart

# Desinstalar
sudo bash install_display_server.sh uninstall

# Via systemctl diretamente
systemctl status tx9-display.service
systemctl restart tx9-display.service
journalctl -u tx9-display.service -f
```

---

## Extensão: novos backgrounds

Crie um módulo em `backgrounds/` expondo `make_background()`:

```python
# backgrounds/bg_temperatura.py

def make_background():
    def tick(hw):
        # lê sensor, exibe no hw
        hw.show_number(get_cpu_temp())
    return tick
```

Registre em `DISPLAY_BACKGROUND` (via `/etc/default/tx9-display`) e adicione o carregamento em `display_server.py` na função `_load_background()`.

---

## Requisitos

- Python 3.8+
- Root (acesso a `/dev/mem`)
- Linux com systemd
- Hardware: TX9 Pro (Amlogic S905W/X) ou compatível com FD6551
