# 📟 FD6551 / TX9 Front Display — Documentação Técnica Completa

## 🧠 Visão Geral

O display frontal presente em diversos TV Box (como TX9 com placa P281) é baseado em um driver de LED multiplexado compatível com o **FD6551** (ou variantes equivalentes não documentadas publicamente).

Este sistema consiste em:

* 4 dígitos de 7 segmentos
* LEDs indicadores (LAN, Wi-Fi, clock, etc)
* Interface serial síncrona de 2 fios
* Controle de brilho via registrador

---

## ⚙️ Arquitetura do Sistema

```
SoC (Amlogic S905/S912/...)
    │
    ├── GPIO (bit-bang)
    │       ├── CLK (clock)
    │       └── DIO (data open-drain)
    │
    └── FD6551 (driver)
            │
            ├── matriz multiplexada
            └── display LED (7 segmentos + ícones)
```

---

## 🔌 Interface Elétrica

### Sinais

| Sinal | Tipo         | Descrição          |
| ----- | ------------ | ------------------ |
| CLK   | saída        | Clock serial       |
| DIO   | bidirecional | Dados (open-drain) |
| VCC   | alimentação  | 3.3V ou 5V         |
| GND   | terra        | referência         |

### ⚠️ Open-drain

O pino DIO não deve ser forçado em nível alto.

* HIGH → configurar como entrada (alta impedância)
* LOW → forçar nível 0

---

## 🔁 Protocolo de Comunicação

### Características

* Serial síncrono proprietário
* MSB first
* Sem endereço de dispositivo
* Sem framing complexo

---

## 📡 Sequência de Comunicação

### START

```
CLK = 1
DIO: 1 → 0
CLK = 0
```

### STOP

```
CLK = 1
DIO: 0 → 1
```

---

## 📤 Escrita de Byte

Para cada bit:

```
1. Define DIO
2. CLK ↑
3. CLK ↓
```

Após 8 bits:

```
Release DIO
CLK ↑
CLK ↓
```

---

## 🧠 Mapa de Registradores

| Endereço | Função                     |
| -------- | -------------------------- |
| 0x48     | Controle (enable + brilho) |
| 0x66     | Dígito 0                   |
| 0x68     | Dígito 1                   |
| 0x6A     | Dígito 2                   |
| 0x6C     | Dígito 3                   |
| 0x6E     | Indicadores                |

---

## 💡 Registrador de Controle (0x48)

### Estrutura de Bits

```
bit: 7 6 5 4 3 2 1 0
     B B B B x x x E
```

### Descrição

| Bits | Função       |
| ---- | ------------ |
| 7-4  | brilho (PWM) |
| 3-1  | reservado    |
| 0    | enable       |

---

## 🔢 Registradores de Dígitos

### Estrutura

```
bit: 7 6 5 4 3 2 1 0
     DP G F E D C B A
```

---

## 🔔 Registrador de Indicadores (0x6E)

### Estrutura

```
bit: 7 6 5 4 3 2 1 0
     x U C : P L W E
```

| Bit | Função |
| --- | ------ |
| 0   | LAN    |
| 1   | Wi-Fi  |
| 2   | Play   |
| 3   | Pause  |
| 4   | Colon  |
| 5   | Clock  |
| 6   | USB    |

---

## 🔧 GPIO (Amlogic)

### Base

```
GPIO_BASE = 0xC8834000
```

### Offsets

| Registrador | Offset |
| ----------- | ------ |
| OEN         | 0x43C  |
| OUT         | 0x440  |
| IN          | 0x444  |

---

## 🧮 Controle de Bits

```
CLK_BIT = 27
DIO_BIT = 29
```

---

## 🚀 Inicialização

### Sequência robusta

```
for val in [0x01,0x11,0x21,0x31,0x41,0x51,0x61,0x71]:
    send_cmd(0x48,val)
    clear()
```

---

## ⏱️ Timing

```
delay ≈ 10us a 100us
```

---

## 🧠 Conclusão

O FD6551 é um driver simples porém sensível, exigindo:

* inicialização correta
* controle preciso de timing
* manipulação correta de open-drain

Ele permite controle total de display via GPIO, sem necessidade de periféricos dedicados.

