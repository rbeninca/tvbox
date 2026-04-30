# Relatório Técnico: Descaracterização de TV Box TX9 Pro para Armbian Linux

> **Projeto:** Transformação de TV Boxes apreendidos pela Receita Federal do Brasil em minicomputadores Linux  para fins educacionais e projetos de tecnologia. como microservidores, automação residencial, e ambientes de desenvolvimento.  
> **Hardware:** TX9 Pro — SoC Amlogic S905W (GXL), 1 GB RAM, 8 GB eMMC  mascarado com 32GB
> **SO original:** Android 7.1.2 (mascarado como Android 10)  
> **SO final:** Armbian Linux — Ubuntu Noble, kernel 6.18.23-current-meson64

---

Palavras chave: armbian
tvbox ,tx9 ,amlogic, rk3328 ,wifi ,linux, embedded-linux , device-tree
# Armbian TX9 with Working WiFi

## 🔧 Problem
Most TX9 devices have no WiFi support on Armbian.

## ✅ Solution
This repo provides:
- Correct DTB
- Working WiFi driver
- Firmware included

## 📦 Supported devices
- TX9 (RK3328)
- TX9 (S905X?) [se aplicável]

## 🚀 Installation
(passos claros)

## 📶 WiFi details
(chip, driver, etc)

## 🧪 Technical details
- DTB changes
- kernel version
- modules


## Índice

1. [Introdução e Contexto](#1-introdução-e-contexto)
2. [Fase 1 — Análise e Engenharia Reversa do Hardware](#2-fase-1--análise-e-engenharia-reversa-do-hardware)
   - 2.1 [Análise inicial do Android](#21-análise-inicial-do-android)
   - 2.2 [Identificação de plataforma e versão real](#22-identificação-de-plataforma-e-versão-real)
   - 2.3 [Identificação dos componentes de hardware](#23-identificação-dos-componentes-de-hardware)
   - 2.4 [Localização e extração do DTB](#24-localização-e-extração-do-dtb)
   - 2.5 [Análise do DTS e mapeamento de hardware](#25-análise-do-dts-e-mapeamento-de-hardware)
   - 2.6 [Mapeamento de partições da eMMC](#26-mapeamento-de-partições-da-emmc)
3. [Fase 2 — Instalação do Armbian](#3-fase-2--instalação-do-armbian)
   - 3.1 [Seleção da imagem](#31-seleção-da-imagem)
   - 3.2 [Boot via cartão SD](#32-boot-via-cartão-sd)
   - 3.3 [Atualização do kernel](#33-atualização-do-kernel)
   - 3.4 [Migração para eMMC](#34-migração-para-emmc)
4. [Fase 3 — Drivers e Serviços de Hardware](#4-fase-3--drivers-e-serviços-de-hardware)
   - 4.1 [Driver Wi-Fi SSV6051](#41-driver-wi-fi-ssv6051)
   - 4.2 [Driver do Display Frontal FD6551](#42-driver-do-display-frontal-fd6551)
   - 4.3 [Receptor Infravermelho (IR)](#43-receptor-infravermelho-ir)
   - 4.4 [Instalação do Docker Engine](#44-instalação-do-docker-engine)
5. [Análise de Desempenho de Rede](#5-análise-de-desempenho-de-rede)
6. [Limitações e Problemas Encontrados](#6-limitações-e-problemas-encontrados)
7. [Conclusão](#7-conclusão)
8. [Referências](#8-referências)

---

## 1. Introdução e Contexto

### Origem dos dispositivos

Os dispositivos TX9 Pro foram disponibilizados pela **Receita Federal do Brasil** por meio de processos de apreensão e destinação de bens. Esses equipamentos eram majoritariamente utilizados para reprodução de conteúdo multimídia sem autorização dos detentores de direitos (IPTV "pirata") e apresentavam riscos de segurança que inviabilizavam o reuso institucional direto.

### Riscos identificados no firmware original

Durante a análise inicial do Android embarcado, foram identificados:

- **Processos com privilégios de root** sem justificativa documentada, incluindo serviços de terceiros de origem desconhecida.
- **Sistema de arquivos montado em leitura/escrita** (`rw`) — configuração insegura em ambiente de produção; qualquer processo com permissão adequada pode modificar arquivos do sistema.
- **Kernel Linux 3.14.29**, sem recebimento de atualizações de segurança desde 2015 — mais de uma década de vulnerabilidades acumuladas.
- **Ausência de mecanismo de atualização** do firmware pelo fabricante.
- Possibilidade de **backdoors ou software de monitoramento** embutidos no firmware de origem desconhecida.

### Por que não manter o Android?

A simples instalação de aplicativos sobre o Android original não mitigaria esses riscos: as camadas inferiores do sistema (kernel, init, daemons de root) permaneceriam intactas e fora do controle institucional. A solução adotada foi a **remoção completa do ecossistema Android** e a instalação de um sistema Linux controlável.

### Objetivo

Descaracterizar completamente os dispositivos TX9 Pro, instalando Armbian Linux com manutenção das funcionalidades de hardware específicas:

- **Display frontal** de 4 dígitos de 7 segmentos (chip FD6551)
- **Receptor infravermelho** (pino GPIOAO_7, protocolo NECx)
- **Conectividade Wi-Fi** (chipset SSV6051/6200)
- **Docker Engine** para execução de serviços em contêineres

> **Nota:** O acesso root disponível no Android original — embora seja uma falha de segurança — facilitou significativamente a fase de engenharia reversa, permitindo extrair o Device Tree Blob e analisar os processos em execução.

---

## 2. Fase 1 — Análise e Engenharia Reversa do Hardware

### Ferramentas utilizadas

- **ADB** (Android Debug Bridge) — comunicação com o dispositivo via USB
- **dtc** (Device Tree Compiler) — descompilação do DTB binário para DTS legível
- **dd** — extração de partições e imagens de bloco

### Pré-requisito: habilitar ADB no Android

1. Configurações → Sobre o dispositivo → Toque 7 vezes em "Número da versão"
2. Configurações → Opções do desenvolvedor → Depuração USB: **Ativar**
3. Conectar o cabo USB ao computador

---

### 2.1 Análise inicial do Android

#### Verificar conexão ADB

```bash
adb devices
# Saída esperada:
# List of devices attached
# XXXXXXXX    device
```

#### Identificar processos em execução com privilégios de root

```bash
adb shell ps -A | grep root
```

**Observações importantes identificadas:**
- `init` (PID 1) — normal
- `surfaceflinger` — servidor gráfico com root
- `hwservicemanager` — gerenciador de serviços de hardware
- `ir_remote` — daemon de controle remoto IR
- `vfd_display` — daemon de controle do display frontal
- Processos de terceiros sem documentação pública

#### Verificar montagem do sistema de arquivos

```bash
adb shell mount | grep -E "system|data|/"
```

**Resultado:** sistema de arquivos raiz e `/system` montados como `rw` (leitura e escrita) — vulnerabilidade de segurança confirmada.

#### Informações do hardware

```bash
adb shell cat /proc/cpuinfo
# Hardware: Amlogic
# model name: ARMv8 Processor rev 4 (v8l)
# CPU implementer: 0x41 (ARM)
# CPU part: 0xD03 (Cortex-A53)

adb shell cat /proc/meminfo | head -5
# MemTotal: ~1 GB

adb shell df -h
# Mostra partições e uso da eMMC
```

---

### 2.2 Identificação de plataforma e versão real

#### Identificar o chipset

```bash
adb shell getprop | grep -iE 'product.model|board.platform|hardware'
# [ro.board.platform]: [gxl]       ← CONFIRMADO: família Amlogic GXL (S905W/X)
# [ro.hardware]: [amlogic]
# [ro.product.model]: [TX9 Pro]
```

#### Detectar a versão real do Android (sistema mentia)

```bash
# O sistema reportava Android 10:
adb shell getprop ro.build.version.release
# 10     ← FALSO

# Mas o kernel entrega a verdade:
adb shell uname -a
# Linux localhost 3.14.29 ... aarch64
# Kernel 3.14 é INCOMPATÍVEL com Android 10

# Fingerprint confirma a versão real:
adb shell getprop ro.build.fingerprint
# generic/gxl_p281_1g/gxl_p281_1g:7.1.2/NHG47L/...
# REAL: Android 7.1.2 (Nougat) disfarçado como Android 10
```

> **Conclusão:** O fabricante alterou a propriedade `ro.build.version.release` para reportar Android 10, mas o kernel 3.14 e o fingerprint expõem a versão real como **Android 7.1.2 (Nougat)**.

---

### 2.3 Identificação dos componentes de hardware

#### GPU

```bash
# Método 1: módulos carregados
adb shell su -c "lsmod | grep mali"
# mali    XXXXXXX  35 [utilizado por 35 processos]

# Método 2: logs do kernel
adb shell su -c "dmesg | grep -i mali"
# mali: [GPU] Mali-450 MP initialised

# Correlação: plataforma gxl (S905W) → GPU integrada: ARM Mali-450 MP (Penta-core)
```

#### Chipset Wi-Fi

```bash
# Busca no kernel por referências ao módulo de Wi-Fi
adb shell su -c "dmesg | grep -iE 'wifi|wlan0|ssv|rtl'"
# ssv6200_sw_scan_start()  ← identifica o chipset
# ssv6051: ...

adb shell su -c "lsmod | grep ssv"
# ssv6051    XXXXXXX  0

# Conclusão: chipset South Silicon Valley SSV6051/6200
```

> **Por que isso é crítico:** O SSV6051 não tem driver no kernel mainline. Sem identificação prévia, o Wi-Fi seria permanentemente perdido após a migração.

#### Identificar controlador do display

```bash
adb shell su -c "lsmod | grep -iE 'fd6|vfd|display'"
# fd655_dev ou similar

adb shell su -c "dmesg | grep -iE 'fd6|vfd|display'"
# fd655: device initialized
```

---

### 2.4 Localização e extração do DTB

O DTB (Device Tree Blob) é o arquivo binário que descreve ao kernel Linux onde cada componente de hardware está localizado, quais endereços de memória ocupa e quais interrupções utiliza. Em plataformas ARM sem BIOS/UEFI, é o único mecanismo que o kernel tem para localizar periféricos soldados na placa.

#### Tentativa 1: buscar DTB no boot.img (fracasso)

```bash
# Extrair boot.img
adb shell su -c "dd if=/dev/block/boot of=/sdcard/boot.img"
adb pull /sdcard/boot.img .

# Buscar assinatura do DTB (magic bytes: d00dfeed)
hexdump -C boot.img | grep "d0 0d fe ed"
# Nenhum resultado — DTB não está concatenado ao kernel
```

#### Tentativa 2: ler /sys/firmware/fdt (fracasso)

```bash
adb shell su -c "cat /sys/firmware/fdt > /sdcard/fdt.dtb"
# Permission denied — kernel 3.14 bloqueia acesso
```

#### Tentativa 3: extração direta do dispositivo de bloco (sucesso)

```bash
# O bootloader mantém o DTB em um dispositivo de bloco dedicado
adb shell su -c "dd if=/dev/dtb of=/sdcard/dtb.img"
adb pull /sdcard/dtb.img .

# Verificar integridade
hexdump -C dtb.img | head -2
# 00000000  d0 0d fe ed ...   ← magic bytes do DTB confirmados

# Tamanho esperado: ~256 KB
ls -lh dtb.img
```

> **Por que funciona:** `/dev/dtb` é o dispositivo de bloco que contém exatamente o binário que o bootloader U-Boot entrega ao kernel durante o boot. É a cópia mais fidedigna do DTB em uso.

#### Descompilação do DTB para análise

```bash
# Instalar dtc (Device Tree Compiler)
sudo apt install device-tree-compiler

# Descompilar binário → texto legível
dtc -I dtb -O dts dtb.img -o extracted.dts

# Verificar tamanho do arquivo gerado
wc -l extracted.dts
# ~2000 linhas de código DTS
```

#### Extração completa de partições para backup

```bash
# Criar diretório de backup
mkdir -p analises/tx9_pro_dump_android/
cd analises/tx9_pro_dump_android/

# DTB (já extraído acima)
cp ~/dtb.img .

# Kernel + ramdisk
adb shell su -c "dd if=/dev/block/boot of=/sdcard/boot.img"
adb pull /sdcard/boot.img .

# Imagens de boot
adb shell su -c "dd if=/dev/block/logo of=/sdcard/logo.img"
adb pull /sdcard/logo.img .

# Partição de recovery
adb shell su -c "dd if=/dev/block/recovery of=/sdcard/recovery.img"
adb pull /sdcard/recovery.img .
```

**Arquivos obtidos:**

| Arquivo | Tamanho aprox. | Conteúdo |
|---------|---------------|---------|
| `dtb.img` | ~256 KB | Device Tree Blob — mapeamento completo do hardware |
| `boot.img` | ~8 MB | Kernel 3.14.29 + ramdisk Android 7.1.2 |
| `logo.img` | ~1 MB | Splash screens do fabricante |
| `recovery.img` | ~16 MB | Partição de recuperação original |
| `extracted.dts` | ~150 KB | DTB descompilado — arquivo mais importante para análise |

---

### 2.5 Análise do DTS e mapeamento de hardware

O arquivo `extracted.dts` contém toda a descrição de hardware. Os trechos abaixo foram localizados por busca de palavras-chave.

#### Display FD6551 — nó fd655_dev

```bash
grep -n "fd655\|fd650\|fd6" extracted.dts
# linha ~1247: fd655_dev
```

Trecho relevante do DTS:

```dts
fd655_dev {
    compatible = "amlogic,fd655_dev";
    dev_name = "fd655_dev";
    status = "okay";
    clk_pin = <0x27 0x17 0x00>;  /* banco 0x27, pino 0x17 (23 dec) */
    dat_pin = <0x27 0x19 0x00>;  /* banco 0x27, pino 0x19 (25 dec) */
};
```

> **Atenção:** Os valores `0x17` (23) e `0x19` (25) do DTS são **índices relativos ao banco GPIO**, não os bits absolutos do registrador. Após testes empíricos, os bits absolutos no registrador `0xC8834000` foram confirmados como **bit 27** e **bit 29**.

#### Receptor IR — nó rc@c8100580

```bash
grep -n "remote\|rc@\|gpioao_7\|GPIOAO_7" extracted.dts -i
# linha ~364:  remote_pin
# linha ~915:  rc@c8100580
```

```dts
remote_pin {
    amlogic,setmask = <0x10 0x01>;
    amlogic,clrmask = <0x10 0x200000>;
    amlogic,pins = "GPIOAO_7";
    linux,phandle = <0x17>;
    phandle = <0x17>;
};

rc@c8100580 {
    compatible = "amlogic, aml_remote";
    dev_name = "meson-remote";
    reg = <0x00 0xc8100580 0x00 0x44 0x00 0xc8100480 0x00 0x20>;
    status = "okay";
    protocol = <0x01>;
    interrupts = <0x00 0xc4 0x01>;
    pinctrl-names = "default";
    pinctrl-0 = <0x17>;   /* aponta para GPIOAO_7 */
    map = <0x18>;
    max_frame_time = <0xc8>;
};
```

#### Wi-Fi SSV6051

```bash
grep -n "ssv\|wifi\|wlan" extracted.dts -i | head -20
```

```dts
wifi {
    compatible = "amlogic, aml_wifi";
    status = "okay";
    interrupt_pin = <0x27 0x56 0x00>;
    power_on_pin  = <0x27 0x55 0x00>;
    pinctrl-0 = <0x31>;   /* wifi_32k_pins: GPIOX_16 */
};

wifi_pwm_conf {
    pwm_channel1_conf = <0x774d 0x3ba6 0x06>;
    pwm_channel2_conf = <0x7736 0x3b9b 0x09>;
};
```

#### LED de status do sistema

```bash
grep -n "sysled\|led_gpio" extracted.dts
```

```dts
sysled {
    compatible = "amlogic, sysled";
    status = "okay";
    led_gpio = <0x27 0x49 0x00>;   /* banco 0x27, pino 73 */
    led_active_low = <0x01>;
    me_gpio = <0x27 0x4b 0x01>;    /* banco 0x27, pino 75 */
};
```

#### Mapas de teclas do controle remoto (custom_maps)

```dts
custom_maps {
    mapnum = <0x03>;

    map_0 {
        mapname = "amlogic-remote-1";
        customcode = <0x4040>;         /* ← controle original do TX9 */
        release_delay = <0x50>;
        size = <0x0d>;
        keymap = <0x180073 0x170072 0x1a0066 0x11006a 0x100069
                  0xb0067 0xe006c 0xd00e8 0x45008b 0x430071
                  0x42009e 0x4d0074 0x470057>;
    };

    map_1 {
        mapname = "amlogic-remote-2";
        customcode = <0xfb04>;
    };

    map_2 {
        mapname = "amlogic-remote-3";
        customcode = <0x7f80>;
    };
};
```

> **Observação:** O DTS declara 3 mapas de teclas para 3 modelos de controle remoto diferentes. Não havia indicação de qual corresponderia ao controle físico incluído no kit — isso precisou ser determinado empiricamente.

#### Resumo do mapeamento de hardware

| Componente | Endereço/Pino | Driver Linux | Observação |
|-----------|---------------|-------------|-----------|
| Display FD6551 (CLK) | GPIOX bit **27** \| `0xC8834000` | bit-bang Python via `/dev/mem` | Bit absoluto no registrador; DTS usa índice relativo |
| Display FD6551 (DIO) | GPIOX bit **29** \| `0xC8834000` | bit-bang Python via `/dev/mem` | Open-drain bidirecional |
| Receptor IR | **GPIOAO_7** \| `0xC8100580` | `meson-ir` (IRQ `0xc4`) | Domínio Always-On |
| Wi-Fi SSV6051 | GPIOX_28 (ctrl) \| `0xC8100000` | `ssv6051.ko` (out-of-tree) | IRQ `0x2c` |
| Ethernet | GPIOZ_14, GPIOZ_15 | Driver interno Amlogic | RMII, PHY interno |
| LED sistema | GPIOX pino 73 | GPIO sysfs | active_low |

---

### 2.6 Mapeamento de partições da eMMC

```bash
# Listar dispositivos de bloco
adb shell su -c "ls -la /dev/block/platform/d0074000.emmc/"
# d0074000.emmc é o controlador eMMC do S905W

# Ver partições
adb shell su -c "ls -la /dev/block/platform/d0074000.emmc/by-name/"
# boot      → /dev/block/mmcblk0boot0
# recovery  → /dev/block/mmcblk0p1
# logo      → /dev/block/mmcblk0p2
# dtb       → /dev/block/mmcblk0p3   ← DTB está aqui!
# system    → /dev/block/mmcblk0p7   (2 GB)
# data      → /dev/block/mmcblk0p10  (restante)
```

**Estrutura de partições do firmware Android (extraída do DTS):**

| Partição | Tamanho | Função |
|----------|---------|--------|
| `logo` | 32 MB | Splash screen de boot |
| `recovery` | 32 MB | Recovery do fabricante |
| `rsv` | 8 MB | Reservada |
| `tee` | 8 MB | TrustZone / Secure OS |
| `crypt` | 32 MB | Chaves de criptografia |
| `misc` | 32 MB | Dados de recovery |
| `boot` | 32 MB | Kernel + ramdisk |
| `system` | 2 GB | Sistema Android |
| `cache` | 512 MB | Cache do sistema |
| `data` | restante | Dados do usuário |

---

## 3. Fase 2 — Instalação do Armbian

### Por que Armbian?

- Distribuição Linux especializada em plataformas ARM de baixo custo
- Suporte ativo à família **Amlogic S905W (GXL)** com kernel mainline série 6.x
- DTBs atualizados pela comunidade, incluindo variantes do TX9 Pro
- Baseado em Ubuntu (Noble) — ecossistema de pacotes amplo
- Contraste com o kernel vendor 3.14 do Android: sem suporte de segurança há mais de 10 anos

---

### 3.1 Seleção da imagem

**Imagem utilizada:**

```
Armbian_community_26.2.0-trunk.703_Aml-s9xx-box_noble_current_6.18.21_xfce_desktop.img.xz
```

**Fontes para download:**

```
https://fi.mirror.armbian.de/cache/artifacts/aml-s9xx-box/archive/
https://github.com/armbian/community/releases
https://armbian.com/boards/aml-s9xx-box
```

> **Atenção:** Imagens genéricas para S905W encontradas em fóruns geralmente não incluem o mapeamento completo do hardware TX9 Pro. Sempre usar a imagem oficial da comunidade Armbian para `aml-s9xx-box`.

**DTB selecionado:** `meson-gxl-s905w-tx9.dtb` — o mais próximo do hardware identificado na fase de engenharia reversa.

---

### 3.2 Boot via cartão SD

#### Gravação da imagem no cartão SD

```bash
# No computador — descomprimir e gravar
xz -d Armbian_community_26.2.0-trunk.703_Aml-s9xx-box_noble_current_6.18.21_xfce_desktop.img.xz

# Linux/macOS
sudo dd if=Armbian_*.img of=/dev/sdX bs=4M status=progress conv=fsync
# Substituir /dev/sdX pelo dispositivo correto (verificar com lsblk)

# Windows: usar balenaEtcher ou Rufus
```

#### Configurar o bootloader para usar o DTB correto

Após gravar a imagem, montar a partição boot do SD e editar o arquivo de configuração:

```bash
# Montar a partição boot (geralmente a primeira partição FAT32)
# Editar /boot/uEnv.txt
```

Conteúdo do `uEnv.txt`:

```text
# /boot/uEnv.txt — configuração de boot para TX9 Pro
dtb_name=/dtb/amlogic/meson-gxl-s905w-tx9.dtb
bootargs=console=ttyAML0,115200n8 root=/dev/mmcblk0p1 rootwait rw no_console_suspend
```

#### Forçar boot pelo SD no TX9 Pro

O TX9 Pro tenta bootar da eMMC por padrão. Para forçar o boot pelo SD:

1. Inserir o cartão SD com o Armbian
2. Ligar o dispositivo com o cartão inserido
3. **Método 1:** Pressionar o botão reset interno (pequeno buraco na lateral) por 5 segundos após ligar
4. **Método 2:** Via ADB com Android ainda funcionando:
   ```bash
   adb shell su -c "reboot update"
   # Isso força o bootloader a verificar o SD antes da eMMC
   ```

#### Primeiro boot e configuração inicial

No primeiro boot pelo SD, o Armbian executa um assistente de configuração:

```
[ Network access required for initial setup ]
1. Definir senha do root
2. Criar usuário padrão
3. Configurar localização e timezone
   → America/Sao_Paulo
4. Configurar idioma do sistema
   → pt_BR.UTF-8
```

#### Verificar hardware reconhecido

```bash
# Kernel em execução
uname -a
# Linux armbian 6.18.21-current-meson64 #1 SMP ... aarch64 GNU/Linux

# CPU e memória
cat /proc/cpuinfo | grep -E "Hardware|processor|model name" | head -6
free -h

# Dispositivos de bloco
lsblk
# mmcblk0      → eMMC interna (8 GB)
# mmcblk1      → Cartão SD (boot atual)
# mmcblk1p1    → partição raiz do Armbian

# Interfaces de rede disponíveis
ip link show
# eth0: Ethernet (deve aparecer)
# wlan0: Wi-Fi (pode não aparecer ainda sem o driver)
```

---

### 3.3 Atualização do kernel

```bash
# Atualizar lista de pacotes
sudo apt update

# Ver kernel atual
uname -r
# 6.18.21-current-meson64

# Atualizar kernel para versão mais recente disponível
sudo apt install linux-image-current-meson64 linux-headers-current-meson64

# Reiniciar para aplicar
sudo reboot

# Verificar após reiniciar
uname -r
# 6.18.23-current-meson64
```

---

### 3.4 Migração para eMMC

> **Pré-requisito:** Validar completamente o sistema rodando do SD antes de instalar na eMMC. Testar SSH, Ethernet e todos os serviços necessários.

#### Usando o script de migração do Armbian

```bash
# O Armbian inclui ferramenta nativa de instalação na eMMC
sudo armbian-install
```

Menu interativo:
```
[ Armbian install to internal media ]
1 - Boot from eMMC - system on eMMC
2 - Boot from eMMC - system on SD/USB
...
Selecionar: 1 (sistema completo na eMMC)

[ Select filesystem type ]
1 - ext4
2 - btrfs
Selecionar: 1 (ext4 - mais estável)
```

O script realiza automaticamente:
1. Formatação da eMMC
2. Cópia do sistema do SD para a eMMC
3. Ajuste do bootloader
4. Configuração do dtb na eMMC

```bash
# Após conclusão, remover o SD e reiniciar
sudo reboot
# O sistema agora inicia diretamente da eMMC
```

#### Verificar boot da eMMC

```bash
# Confirmar dispositivo raiz
df -h /
# /dev/mmcblk0p1  (eMMC, não mais mmcblk1)

lsblk
# mmcblk0   → eMMC (dispositivo raiz agora)
```

---

## 4. Fase 3 — Drivers e Serviços de Hardware

Esta fase concentrou a maior complexidade técnica do projeto. Os três componentes proprietários do TX9 Pro — Wi-Fi, display frontal e receptor IR — exigiram abordagens distintas.

---

### 4.1 Driver Wi-Fi SSV6051

#### Contexto do problema

O chipset **South Silicon Valley SSV6051/6200** não possui suporte nativo estável nos kernels Linux mainline. Os drivers foram desenvolvidos originalmente para a série 3.x do kernel e há anos sem manutenção ativa. Esta provavelmente é a razão pela qual a maioria dos projetos de migração para TX9 Pro perde o Wi-Fi: sem compilar um módulo out-of-tree, a interface simplesmente não é reconhecida.

#### 4.1.1 Instalar dependências de compilação

```bash
sudo apt update
sudo apt install -y \
    build-essential \
    linux-headers-current-meson64 \
    git \
    dkms \
    bc \
    bison \
    flex \
    libssl-dev
```

#### 4.1.2 Obter o código-fonte do driver

```bash
# Repositório com versão parcialmente atualizada para kernels modernos
git clone https://github.com/eloi-rotava/ssv6051.git /root/ssv6051-driver
cd /root/ssv6051-driver
ls
# 6051/  rebuild_wifi_v3.sh  ...
```

#### 4.1.3 Corrigir o problema de version magic

Este é o passo mais crítico. O kernel rejeita módulos cujo campo de versão não corresponde exatamente à string do kernel ativo. Os headers instalados pelo Armbian nem sempre geram essa string corretamente.

**Diagnóstico do problema:**

```bash
# Sem a correção, ao tentar carregar o módulo:
modprobe ssv6051
# ERROR: could not insert 'ssv6051': Exec format error

# Verificar a discrepância
modinfo ssv6051.ko | grep vermagic
# vermagic: 6.18.23 SMP ...

uname -r
# 6.18.23-current-meson64   ← "current-meson64" faltando no módulo!
```

**Aplicar a correção:**

```bash
KVER=$(uname -r)
HDIR="/usr/src/linux-headers-${KVER}"

echo "Kernel ativo: $KVER"
echo "Diretório de headers: $HDIR"

# Verificar se os headers existem
ls $HDIR
# Se não existir: sudo apt install linux-headers-$(uname -r)

# Corrigir EXTRAVERSION no Makefile dos headers
sudo sed -i "s/^EXTRAVERSION =.*/EXTRAVERSION = -current-meson64/" \
    ${HDIR}/Makefile

# Verificar a correção
grep "^EXTRAVERSION" ${HDIR}/Makefile
# EXTRAVERSION = -current-meson64

# Recriar o arquivo utsrelease.h com a versão correta
sudo bash -c "echo '#define UTS_RELEASE \"${KVER}\"' \
    > ${HDIR}/include/generated/utsrelease.h"

# Verificar
cat ${HDIR}/include/generated/utsrelease.h
# #define UTS_RELEASE "6.18.23-current-meson64"
```

#### 4.1.4 Compilar o módulo ssv6051.ko

```bash
cd /root/ssv6051-driver

# Dar permissão de execução ao script
chmod +x rebuild_wifi_v3.sh

# Executar — o script realiza todo o processo
bash rebuild_wifi_v3.sh
```

**O que o script `rebuild_wifi_v3.sh` faz:**

```bash
# Conteúdo simplificado do script:

KVER=$(uname -r)
KDIR="/lib/modules/${KVER}/build"
INSTALL_DIR="/lib/modules/${KVER}/kernel/drivers/net/wireless/ssv6051"

# 1. Validar headers
if [ ! -d "$KDIR" ]; then
    echo "ERRO: Headers não encontrados em $KDIR"
    exit 1
fi

# 2. Limpar compilação anterior
cd /root/ssv6051-driver/6051/ssv6xxx
make clean

# 3. Compilar
make -C "$KDIR" M=$(pwd) modules

# 4. Instalar o módulo
sudo mkdir -p "$INSTALL_DIR"
sudo cp ssv6051.ko "$INSTALL_DIR/"

# 5. Atualizar dependências de módulos
sudo depmod -a

# 6. Carregar o driver
sudo modprobe ssv6051

echo "Wi-Fi SSV6051 carregado com sucesso"
```

**Verificar compilação bem-sucedida:**

```bash
ls -la /root/ssv6051-driver/6051/ssv6xxx/ssv6051.ko
# -rw-r--r-- 1 root root ~2.5MB ssv6051.ko

# Verificar version magic corrigida
modinfo ssv6051.ko | grep vermagic
# vermagic: 6.18.23-current-meson64 SMP ...   ← CORRETO agora
```

#### 4.1.5 Instalar arquivos de firmware

O chipset exige arquivos de firmware e configuração em `/lib/firmware/`. Sem eles, o módulo carrega mas a interface não inicializa.

```bash
# Localizar os arquivos no repositório
ls /root/ssv6051-driver/6051/ssv6xxx/
# ssv6051-wifi.cfg    ← configurações do chipset
# ssv6051-sw.bin      ← firmware binário

# Copiar para o diretório de firmware do sistema
sudo cp /root/ssv6051-driver/6051/ssv6xxx/ssv6051-wifi.cfg \
        /lib/firmware/ssv6051-wifi.cfg

sudo cp /root/ssv6051-driver/6051/ssv6xxx/ssv6051-sw.bin \
        /lib/firmware/ssv6051-sw.bin

# Verificar
ls -la /lib/firmware/ssv6051*
```

#### 4.1.6 Configurar carregamento automático no boot

```bash
# Criar arquivo de configuração para carregamento automático
echo 'ssv6051' | sudo tee /etc/modules-load.d/ssv6051.conf

# Verificar
cat /etc/modules-load.d/ssv6051.conf
# ssv6051
```

#### 4.1.7 Corrigir instabilidade — desativar power management

Durante os testes, o Wi-Fi apresentava quedas frequentes. A causa foi identificada como o gerenciamento de energia do chipset, que colocava a interface em estado de baixo consumo, causando timeouts de conexão.

```bash
# Criar dispatcher do NetworkManager para desativar power_save automaticamente
sudo tee /etc/NetworkManager/dispatcher.d/99-ssv6051-fix << 'EOF'
#!/bin/sh
# Desativa power saving do SSV6051 quando wlan0 fica ativa
INTERFACE=$1
ACTION=$2

if [ "$INTERFACE" = "wlan0" ] && [ "$ACTION" = "up" ]; then
    logger "SSV6051: desativando power_save em wlan0"
    /usr/sbin/iw dev wlan0 set power_save off
fi
EOF

sudo chmod +x /etc/NetworkManager/dispatcher.d/99-ssv6051-fix

# Verificar
cat /etc/NetworkManager/dispatcher.d/99-ssv6051-fix
```

#### 4.1.8 Reiniciar e validar

```bash
sudo reboot
```

Após reiniciar:

```bash
# 1. Verificar kernel ativo
uname -r
# 6.18.23-current-meson64

# 2. Verificar módulo carregado
lsmod | grep ssv6051
# ssv6051  XXXXXXX  0

# 3. Verificar interface
ip link show wlan0
# 3: wlan0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN

# 4. Verificar firmware carregado no kernel
dmesg | grep -i ssv
# ssv6051: firmware loaded
# ssv6051: MAC address: XX:XX:XX:XX:XX:XX

# 5. Verificar power save desativado após conectar
iw dev wlan0 get power_save
# Power save: off
```

#### 4.1.9 Configurar e conectar à rede Wi-Fi

```bash
# Escanear redes disponíveis
nmcli device wifi rescan
nmcli device wifi list

# Conectar (substituir com credenciais reais)
nmcli device wifi connect 'NOME_DA_REDE' password 'SENHA_AQUI'

# Configurar conexão automática no boot
nmcli connection modify 'NOME_DA_REDE' connection.autoconnect yes

# Verificar conexão
ip addr show wlan0
# inet 192.168.X.X/24 brd ...

ping -c 4 8.8.8.8
```

#### 4.1.10 Script completo de instalação do Wi-Fi

Para facilitar a replicação em outras unidades, o processo foi encapsulado em um script:

```bash
#!/usr/bin/env bash
# instalar_wifi_ssv6051.sh
set -euo pipefail

KVER=$(uname -r)
HDIR="/usr/src/linux-headers-${KVER}"
DRIVER_DIR="/root/ssv6051-driver"

echo "==> Instalando dependências..."
apt update -qq
apt install -y build-essential linux-headers-${KVER} git bc libssl-dev

echo "==> Clonando driver..."
if [ ! -d "$DRIVER_DIR" ]; then
    git clone https://github.com/eloi-rotava/ssv6051.git "$DRIVER_DIR"
fi

echo "==> Corrigindo version magic para kernel $KVER..."
sed -i "s/^EXTRAVERSION =.*/EXTRAVERSION = -current-meson64/" ${HDIR}/Makefile
echo "#define UTS_RELEASE \"${KVER}\"" > ${HDIR}/include/generated/utsrelease.h

echo "==> Compilando módulo..."
bash ${DRIVER_DIR}/rebuild_wifi_v3.sh

echo "==> Instalando firmware..."
cp ${DRIVER_DIR}/6051/ssv6xxx/ssv6051-wifi.cfg /lib/firmware/
cp ${DRIVER_DIR}/6051/ssv6xxx/ssv6051-sw.bin   /lib/firmware/

echo "==> Configurando autoload..."
echo 'ssv6051' > /etc/modules-load.d/ssv6051.conf

echo "==> Configurando correção de power_save..."
tee /etc/NetworkManager/dispatcher.d/99-ssv6051-fix << 'DISPATCHER_EOF'
#!/bin/sh
if [ "$1" = "wlan0" ] && [ "$2" = "up" ]; then
    iw dev wlan0 set power_save off
fi
DISPATCHER_EOF
chmod +x /etc/NetworkManager/dispatcher.d/99-ssv6051-fix

echo "==> Wi-Fi SSV6051 instalado com sucesso!"
echo "==> Reinicie o sistema para aplicar todas as configurações."
```

---

### 4.2 Driver do Display Frontal FD6551

#### Contexto técnico

O display de 4 dígitos de 7 segmentos é controlado pelo chip **FD6551** (ou variante compatível sem documentação pública) usando um **protocolo serial síncrono proprietário de 2 fios**:

- **CLK** — clock de saída permanente
- **DIO** — dados, bidirecional **open-drain** (nunca deve ser forçado em HIGH; HIGH = colocar em alta impedância / HiZ)

**Diferenças em relação ao I²C padrão:**
- Sem endereçamento de dispositivo no barramento
- Sem framing complexo (Start, Addr, ACK, Data, Stop — sem 7-bit device address)
- MSB first (bit 7 transmitido primeiro)
- Sem leitura de registradores (write-only na prática)

**Mapa de registradores FD6551:**

| Endereço | Registrador | Função |
|----------|------------|--------|
| `0x48` | CTRL | Controle: brilho `[7:4]` + enable `[0]` |
| `0x66` | DIG0 | Dígito 0 (mais à esquerda) |
| `0x68` | DIG1 | Dígito 1 |
| `0x6A` | DIG2 | Dígito 2 |
| `0x6C` | DIG3 | Dígito 3 (mais à direita) |
| `0x6E` | IND | Indicadores |

**Registrador de indicadores (0x6E):**

| Bit | Função |
|-----|--------|
| 0 | LAN |
| 1 | Wi-Fi |
| 2 | Play |
| 3 | Pause |
| 4 | Dois-pontos (:) |
| 5 | Relógio |
| 6 | USB |

**Padrão de segmentos (0x66–0x6C):**
```
bit:  7  6  5  4  3  2  1  0
      DP G  F  E  D  C  B  A

Segmento físico:
       _
      |A|
    F| |B
       -G
    E| |C
      |_|D   .DP
```

#### 4.2.1 Acesso ao GPIO via mmap

O driver acessa o hardware diretamente mapeando o registrador GPIO na memória:

```python
import mmap, os, struct, time

GPIO_BASE = 0xC8834000
PAGE_SIZE = 0x1000
OEN_OFF   = 0x43C   # Output Enable (1=HiZ/entrada, 0=saída)
OUT_OFF   = 0x440   # Output Data
IN_OFF    = 0x444   # Input Data

CLK_BIT = 27
DIO_BIT = 29

# Abrir /dev/mem (requer root)
fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
mm = mmap.mmap(fd, PAGE_SIZE, mmap.MAP_SHARED,
               mmap.PROT_READ | mmap.PROT_WRITE, offset=GPIO_BASE)
os.close(fd)

def rd32(off):
    mm.seek(off)
    return struct.unpack("<I", mm.read(4))[0]

def wr32(off, val):
    mm.seek(off)
    mm.write(struct.pack("<I", val & 0xFFFFFFFF))

# CLK: saída permanente, inicia em LOW
wr32(OEN_OFF, rd32(OEN_OFF) & ~(1 << CLK_BIT))  # CLR OEN → saída
wr32(OUT_OFF, rd32(OUT_OFF) & ~(1 << CLK_BIT))  # CLR OUT → nível 0

# DIO: open-drain (OUT mantém sempre 0; HIGH = input/HiZ)
wr32(OUT_OFF, rd32(OUT_OFF) & ~(1 << DIO_BIT))  # OUT = 0 permanente
wr32(OEN_OFF, rd32(OEN_OFF) |  (1 << DIO_BIT))  # OEN = 1 → HiZ (idle HIGH)
```

#### 4.2.2 Identificação dos pinos — processo de engenharia reversa

**Problema:** o DTS declarava pinos com índices relativos ao banco GPIO (`clk_pin = <0x27 0x17 0x00>`), mas não indicava diretamente os bits absolutos do registrador de controle em `0xC8834000`.

**Método de identificação empírica via sysfs:**

```bash
# O sysfs permite controlar GPIOs sem escrever código

# 1. Encontrar o número base do banco GPIO do TX9
cat /sys/kernel/debug/gpio | grep -i "gpiochip\|bank"

# 2. Para cada bit candidato (variando sistematicamente):
for bit in 23 24 25 26 27 28 29 30; do
    echo "Testando bit $bit como CLK..."
    echo $((480 + bit)) > /sys/class/gpio/export 2>/dev/null || true
    echo "out" > /sys/class/gpio/gpio$((480 + bit))/direction
    # Pulsar e observar display
    for i in $(seq 1 10); do
        echo "1" > /sys/class/gpio/gpio$((480 + bit))/value
        sleep 0.001
        echo "0" > /sys/class/gpio/gpio$((480 + bit))/value
        sleep 0.001
    done
done
```

**Resultado dos testes:**
- Bits 27 (CLK) e 29 (DIO) produziram resposta visual no display ✓
- Confirmação: bits absolutos no registrador `0xC8834000` são 27 e 29

#### 4.2.3 Protocolo de comunicação — implementação

```python
BIT_DELAY = 12e-6  # 12 microsegundos (intervalo recomendado: 10-100 µs)

def clk_high(): wr32(OUT_OFF, rd32(OUT_OFF) |  (1 << CLK_BIT))
def clk_low():  wr32(OUT_OFF, rd32(OUT_OFF) & ~(1 << CLK_BIT))
def dio_high(): wr32(OEN_OFF, rd32(OEN_OFF) |  (1 << DIO_BIT))  # HiZ
def dio_low():  wr32(OEN_OFF, rd32(OEN_OFF) & ~(1 << DIO_BIT))  # força 0

def wait():
    if BIT_DELAY > 0:
        time.sleep(BIT_DELAY)

def start():
    """START: CLK=H, DIO 1→0, CLK=L"""
    dio_high(); clk_high(); wait()
    dio_low();  wait()
    clk_low();  wait()

def stop():
    """STOP: CLK=L, DIO=L, CLK=H, DIO=H"""
    clk_low(); dio_low(); wait()
    clk_high(); wait()
    dio_high(); wait()

def write_byte(byte):
    """Envia 1 byte MSB first; consome ACK no 9º ciclo"""
    for bit in range(7, -1, -1):
        if (byte >> bit) & 1:
            dio_high()
        else:
            dio_low()
        wait()
        clk_high(); wait()
        clk_low();  wait()
    # Pulso de ACK — libera DIO e pulsa CLK
    dio_high(); wait()
    clk_high(); wait()
    clk_low();  wait()

def send_cmd(addr, data):
    """Transação completa: START + ADDR + DATA + STOP"""
    start()
    write_byte(addr)
    write_byte(data)
    stop()
```

#### 4.2.4 Sequência de inicialização — descoberta crítica

**Problema:** o display funcionava após a primeira escrita, mas após `cold boot` (remoção de energia), não respondia mais.

**Investigação:** com o osciloscópio e análise do firmware Android original, identificou-se que o driver Android executava uma **rampa de brilho obrigatória** na inicialização.

**Solução — rampa de brilho:**

```python
def activate():
    """Inicialização obrigatória do FD6551 — rampa de brilho em 8 passos"""
    # Cada valor incrementa o nibble de brilho em 1 nível
    # bit[0] = enable, bits[7:4] = brilho (0x0=min, 0x7=max)
    for val in (0x01, 0x11, 0x21, 0x31, 0x41, 0x51, 0x61, 0x71):
        send_cmd(0x48, val)   # registrador de controle
        clear_display()       # limpa todos os dígitos e indicadores
    # Aplicar brilho de operação (mínimo por padrão)
    send_cmd(0x48, 0x11)  # brilho 0x10 + enable

def clear_display():
    for reg in (0x66, 0x68, 0x6A, 0x6C):  # dígitos 0-3
        send_cmd(reg, 0x00)
    send_cmd(0x6E, 0x00)  # indicadores
```

> **Por que isso era necessário:** O FD6551 precisa "acordar" gradualmente — iniciar diretamente com brilho máximo coloca o controlador em estado indeterminado. A rampa estabelece o estado interno do chip corretamente.

#### 4.2.5 Tabela de segmentos (caracteres suportados)

```python
SEG = {
    '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F,
    '4': 0x66, '5': 0x6D, '6': 0x7D, '7': 0x07,
    '8': 0x7F, '9': 0x6F,
    'A': 0x77, 'B': 0x7C, 'C': 0x39, 'D': 0x5E,
    'E': 0x79, 'F': 0x71, 'G': 0x3D, 'H': 0x76,
    'I': 0x06, 'J': 0x1E, 'L': 0x38, 'N': 0x37,
    'O': 0x3F, 'P': 0x73, 'R': 0x50, 'S': 0x6D,
    'T': 0x78, 'U': 0x3E, 'Y': 0x6E,
    '-': 0x40, '_': 0x08, ' ': 0x00, '.': 0x80,
}
```

#### 4.2.6 API de alto nível

```python
def show_number(value, leading_zeros=True):
    """Exibe número 0-9999"""
    value = max(0, min(9999, value))
    digits = [value//1000, (value//100)%10, (value//10)%10, value%10]
    segs = []
    blanking = not leading_zeros
    for i, d in enumerate(digits):
        if i == 3: blanking = False  # último dígito sempre visível
        if blanking and d == 0:
            segs.append(0x00)
        else:
            blanking = False
            segs.append(SEG[str(d)])
    write_digits(segs)
    send_cmd(0x6E, 0x00)  # apaga indicadores

def show_clock(hour, minute, colon=True, lan=False, wifi=False):
    """Exibe HH:MM com indicadores"""
    segs = [SEG[str(hour//10)], SEG[str(hour%10)],
            SEG[str(minute//10)], SEG[str(minute%10)]]
    write_digits(segs)
    ind = 0x00
    if colon: ind |= (1 << 4)   # IND_COLON
    if lan:   ind |= (1 << 0)   # IND_LAN
    if wifi:  ind |= (1 << 1)   # IND_WIFI
    send_cmd(0x6E, ind)

def scroll_text(text, step_delay=0.35):
    """Rola texto da direita para a esquerda"""
    segs = [SEG.get(c.upper(), 0x00) for c in text]
    padded = [0x00]*4 + segs + [0x00]*4
    for i in range(len(segs) + 5):
        show_segs4(padded[i:i+4])
        time.sleep(step_delay)
```

#### 4.2.7 Problema de cold boot — solução via systemd

**Sintoma:** após desligar completamente (retirar da tomada) e religar, o display não respondia.

**Causa:** os pinos GPIO ficam em estado indefinido no power-on. O controlador FD6551 precisa receber a sequência de inicialização antes de qualquer escrita.

**Solução:** dois serviços systemd em fases diferentes do boot:

```ini
# /etc/systemd/system/tx9-display-boot.service
[Unit]
Description=TX9 Display — inicialização de boot (fase early)
DefaultDependencies=no
After=local-fs.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /opt/tx9/display/display_boot.py \
    --fim 9999 --delay 0.05 --loop --manter-ao-sair
Restart=on-failure
RestartSec=3

[Install]
WantedBy=basic.target
```

```ini
# /etc/systemd/system/tx9-display.service
[Unit]
Description=TX9 Display — servidor IPC principal
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tx9/display
ExecStart=/usr/local/bin/tx9-display
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar e iniciar os serviços
sudo systemctl daemon-reload
sudo systemctl enable tx9-display-boot.service tx9-display.service
sudo systemctl start tx9-display-boot.service

# Verificar status
sudo systemctl status tx9-display-boot.service
sudo systemctl status tx9-display.service
```

#### 4.2.8 Arquitetura do serviço de display — 3 camadas

```
                     ┌─────────────────────────────┐
  qualquer processo  │  display_client.py           │
  (Python ou CLI)    │  socket Unix                 │
                     └──────────────┬──────────────┘
                                    │ JSON via /run/tx9-display.sock
                     ┌──────────────▼──────────────┐
                     │  display_server.py           │
                     │  fila de prioridade + bg     │
                     └──────────────┬──────────────┘
                                    │ mmap /dev/mem
                     ┌──────────────▼──────────────┐
                     │  display_driver.py           │
                     │  GPIO bit-bang → FD6551      │
                     └─────────────────────────────┘

  Boot inicial (antes da rede):
  ┌─────────────────────────────┐
  │  display_boot.py            │
  │  contador crescente         │
  │  acesso direto ao driver    │
  └─────────────────────────────┘
```

**Instalação do serviço:**

```bash
sudo bash install_display_server.sh install

# Ou instalação remota via SSH:
TARGET_HOST=192.168.1.106 bash install_display_server.sh install
```

**Uso via CLI após instalação:**

```bash
# Exibir texto (até 4 chars = fixo; mais de 4 = scroll automático)
tx9-show show_text "BOOT" --duration 5
tx9-show show_text "Sistema iniciado"   # rola automaticamente

# Exibir número
tx9-show show_number 42

# Scroll explícito
tx9-show scroll "TX9 Pro Armbian Linux" --speed 0.3

# Ajustar brilho (0x10 mín, 0x70 máx)
tx9-show set_brightness 0x40

# Limpar display
tx9-show clear

# Verificar servidor
tx9-show status
```

---

### 4.3 Receptor Infravermelho (IR)

#### 4.3.1 Hardware e pinagem

O receptor IR está soldado no pino **GPIOAO_7** do S905W. O domínio **Always-On (GPIOAO)** permanece energizado mesmo em standby, permitindo que o controle remoto ligue o dispositivo.

**Endereços relevantes:**

```
Controlador IR:  0xC8100580
Interrupção:     0xC4 (IRQ 196)
Pino:            GPIOAO_7
Driver Android:  aml_remote
Driver Armbian:  meson-ir
```

#### 4.3.2 Ativar o driver no Armbian

```bash
# Verificar se o overlay existe
ls /boot/dtb/amlogic/overlay/ | grep ir
# meson-ir.dtbo  ← deve existir

# Adicionar ao arquivo de configuração do Armbian
sudo nano /boot/armbianEnv.txt
```

Adicionar ou modificar a linha `overlays`:

```text
# /boot/armbianEnv.txt
overlays=meson-ir
```

```bash
# Reiniciar para aplicar
sudo reboot
```

#### 4.3.3 Verificar o driver carregado

```bash
# Após reiniciar
lsmod | grep meson_ir
# meson_ir    XXXXX  0

dmesg | grep -i "meson.*ir\|ir.*remote\|rc"
# rc rc0: meson-remote as /class/rc/rc0
# input: MCE-style keyboard ... as /class/input/input3

# Verificar dispositivo RC
ls /sys/class/rc/
# rc0

cat /sys/class/rc/rc0/protocols
# ... nec [necx] ...
```

#### 4.3.4 Testar recepção — identificação do protocolo

```bash
# Instalar ferramenta de teste
sudo apt install -y ir-keytable

# Escuta ao vivo — pressionar botões do controle
sudo ir-keytable -s rc0 -t
```

**Saída observada ao pressionar os botões:**

```
Testing events. Please, press CTRL-C to abort.
26034.064060: lirc protocol(necx): scancode = 0x40404d    ← Power
26049.084150: lirc protocol(necx): scancode = 0x404043    ← Mute
26064.344080: lirc protocol(necx): scancode = 0x40400b    ← Direcional ↑
26081.548100: lirc protocol(necx): scancode = 0x40400e    ← Direcional ↓
26106.096202: lirc protocol(necx): scancode = 0x404011    ← Direcional →
26119.424061: lirc protocol(necx): scancode = 0x404010    ← Direcional ←
26127.864063: lirc protocol(necx): scancode = 0x40400d    ← OK
26141.568067: lirc protocol(necx): scancode = 0x40401a    ← Home
26162.980073: lirc protocol(necx): scancode = 0x404045    ← Menu (≡)
26175.012143: lirc protocol(necx): scancode = 0x404042    ← Voltar
26185.752059: lirc protocol(necx): scancode = 0x404018    ← Volume +
26195.864034: lirc protocol(necx): scancode = 0x404017    ← Volume −
26205.124060: lirc protocol(necx): scancode = 0x404047    ← Cursor
```

**Análise do protocolo:**
- Todos os scancodes têm prefixo `0x4040` → **custom code 0x4040** → `amlogic-remote-1` do DTS
- Protocolo: **NECx** (NEC Extended), 3 bytes: `[custom_high=0x40][custom_low=0x40][comando]`
- Eventos `repeat` com ~60 ms de intervalo para botões mantidos pressionados

#### 4.3.5 Mapa completo de scancodes

| Botão | Scancode (NECx) | Byte de comando |
|-------|----------------|----------------|
| Power | `0x40404d` | `0x4d` |
| Mute | `0x404043` | `0x43` |
| Direcional ↑ | `0x40400b` | `0x0b` |
| Direcional ↓ | `0x40400e` | `0x0e` |
| Direcional → | `0x404011` | `0x11` |
| Direcional ← | `0x404010` | `0x10` |
| OK / Confirmar | `0x40400d` | `0x0d` |
| Home | `0x40401a` | `0x1a` |
| Menu (≡) | `0x404045` | `0x45` |
| Voltar | `0x404042` | `0x42` |
| Volume + | `0x404018` | `0x18` |
| Volume − | `0x404017` | `0x17` |
| Cursor (ativar) | `0x404047` | `0x47` |

#### 4.3.6 Habilitar protocolos e configurar mapa de teclas

```bash
# Habilitar múltiplos protocolos
sudo ir-keytable -s rc0 -p nec,necx,rc-5,rc-6

# Criar arquivo de mapa de teclas (formato toml)
sudo mkdir -p /etc/rc_keymaps
sudo tee /etc/rc_keymaps/tx9_remote.toml << 'EOF'
[[protocols]]
name = "TX9 Original Remote"
protocol = "necx"
variant = "necx"

[protocols.scancodes]
0x40404d = "KEY_POWER"
0x404043 = "KEY_MUTE"
0x40400b = "KEY_UP"
0x40400e = "KEY_DOWN"
0x404011 = "KEY_RIGHT"
0x404010 = "KEY_LEFT"
0x40400d = "KEY_ENTER"
0x40401a = "KEY_HOME"
0x404045 = "KEY_MENU"
0x404042 = "KEY_BACK"
0x404018 = "KEY_VOLUMEUP"
0x404017 = "KEY_VOLUMEDOWN"
0x404047 = "KEY_NUMERIC_STAR"
EOF

# Aplicar o mapa
sudo ir-keytable -s rc0 -p necx -w /etc/rc_keymaps/tx9_remote.toml
```

#### 4.3.7 Script de automação ouvir-ir.sh

O script `ouvir-ir.sh` automatiza a verificação e configuração completa do receptor:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -ne 0 ]] && { echo "Execute como root: sudo bash ouvir-ir.sh"; exit 1; }

echo "==> Verificando pacote ir-keytable"
if ! command -v ir-keytable >/dev/null 2>&1; then
    apt update && apt install -y ir-keytable
fi

echo "==> Carregando driver meson_ir"
modprobe meson-ir 2>/dev/null || true

echo "==> Verificando overlay em /boot/armbianEnv.txt"
if [[ -f /boot/armbianEnv.txt ]]; then
    if ! grep -Eq '^overlays=.*\bmeson-ir\b' /boot/armbianEnv.txt; then
        echo "AVISO: meson-ir não encontrado em overlays="
        echo "Adicione 'meson-ir' à linha overlays= em /boot/armbianEnv.txt"
    fi
fi

echo "==> Detectando dispositivo RC"
if [[ ! -d /sys/class/rc/rc0 ]]; then
    echo "ERRO: Nenhum dispositivo RC encontrado. Reinicie com overlay meson-ir ativo."
    exit 1
fi

RCDEV="rc0"
echo "==> Usando: $RCDEV"
ir-keytable -s "$RCDEV"

echo "==> Habilitando protocolos"
ir-keytable -s "$RCDEV" -p nec,necx,rc-5,rc-6,jvc,sony,mce_kbd 2>/dev/null || \
ir-keytable -s "$RCDEV" -p all

echo ""
echo "==> Escutando o controle remoto (CTRL+C para sair)..."
echo ""
exec ir-keytable -s "$RCDEV" -t
```

---

### 4.4 Instalação do Docker Engine

#### 4.4.1 Por que usar o repositório oficial da Docker?

O pacote `docker.io` nos repositórios Ubuntu pode estar desatualizado e conflitar com os pacotes oficiais `docker-ce`. Para plataformas ARM (arm64), é essencial usar o repositório oficial para garantir compatibilidade.

#### 4.4.2 Script completo de instalação

```bash
#!/usr/bin/env bash
# instalar_docker.sh — instalação do Docker Engine no TX9 Pro (arm64)
set -Eeuo pipefail

[[ "$EUID" -ne 0 ]] && { echo "Execute como root: sudo bash instalar_docker.sh"; exit 1; }

# Detectar arquitetura e distribuição
ARCH="$(dpkg --print-architecture)"
CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"

echo "Arquitetura: $ARCH"
echo "Codename:    $CODENAME"

# Validar arquitetura suportada
if [[ "$ARCH" != "arm64" && "$ARCH" != "armhf" && "$ARCH" != "amd64" ]]; then
    echo "ERRO: Arquitetura não suportada: $ARCH"
    exit 1
fi

echo "==> Removendo versões conflitantes..."
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
    apt-get remove -y "$pkg" >/dev/null 2>&1 || true
done

echo "==> Instalando dependências..."
apt-get update -qq
apt-get install -y ca-certificates curl gnupg

echo "==> Configurando repositório oficial da Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

cat > /etc/apt/sources.list.d/docker.list << EOF
deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu ${CODENAME} stable
EOF

echo "==> Instalando Docker Engine..."
apt-get update -qq
apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

echo "==> Habilitando serviço Docker..."
systemctl enable docker
systemctl restart docker

echo ""
echo "==> Verificação da instalação:"
docker --version
docker compose version 2>/dev/null || true
echo ""
systemctl --no-pager status docker | head -8

echo ""
echo "==> Teste funcional:"
docker run --rm hello-world

echo ""
echo "✓ Docker instalado com sucesso no TX9 Pro (${ARCH})!"
```

#### 4.4.3 Executar e verificar

```bash
# Executar script
sudo bash instalar_docker.sh

# Verificações manuais pós-instalação
docker --version
# Docker version 27.x.x, build XXXXX

docker compose version
# Docker Compose version v2.x.x

docker info | grep -E "Architecture|OS Type|Kernel"
# OS Type: linux
# Architecture: aarch64
# Kernel Version: 6.18.23-current-meson64

# Testar com container real
docker run --rm -it alpine sh -c "echo 'Container funcionando em TX9 Pro!'"
```

---

## 5. Análise de Desempenho de Rede

### 5.1 Metodologia

**Ferramenta:** `iperf3`  
**Duração por teste:** 30 segundos  
**Topologia:**

```
[TX9 Pro — cliente]                    [Servidor iperf3]
 Ethernet: 192.168.1.106  ────────────  192.168.1.111:5201
 Wi-Fi:    192.168.1.126  ─ ─ ─ ─ ─ ─
```

```bash
# No servidor (computador na rede)
iperf3 -s -p 5201

# No TX9 Pro — teste de upload (cliente envia)
iperf3 -c 192.168.1.111 -p 5201 -t 30

# No TX9 Pro — teste de download (cliente recebe)
iperf3 -c 192.168.1.111 -p 5201 -t 30 -R
```

### 5.2 Resultados

#### Ethernet — Upload

```
[ ID] Interval           Transfer     Bitrate         Retr
[  5]  0.00-30.00  sec   325 MBytes  91.4 Mbps   740 sender
Pico observado: ~115 Mbps em rajadas
```

#### Ethernet — Download

```
[ ID] Interval           Transfer     Bitrate         Retr
[  5]  0.00-30.00  sec   336 MBytes  94.1 Mbps    61 receiver
Muito estável, sem variação significativa
```

#### Wi-Fi SSV6051 — Download

```
[ ID] Interval           Transfer     Bitrate         Retr
[  5]  0.00-30.00  sec  24.7 MBytes  6.92 Mbps   386 receiver
Pico: ~9.44 Mbps | Quedas momentâneas para 0 bps observadas
```

#### Wi-Fi SSV6051 — Upload

```
[ ID] Interval           Transfer     Bitrate         Retr
[  5]  0.00-30.00  sec  26.7 MBytes  7.48 Mbps    13 sender
Pico: ~13.6 Mbps | Alta variabilidade temporal
```

### 5.3 Tabela comparativa

| Interface | Direção | Throughput médio | Máximo | Retransmissões | Estabilidade |
|-----------|---------|-----------------|--------|---------------|-------------|
| Ethernet | Upload | 91,4 Mbps | ~115 Mbps | 740 | Alta |
| Ethernet | Download | 94,1 Mbps | ~95 Mbps | 61 | Muito alta |
| Wi-Fi | Download | 6,9 Mbps | ~9,4 Mbps | 386 | Baixa |
| Wi-Fi | Upload | 7,5 Mbps | ~13,6 Mbps | 13 | Baixa |

### 5.4 Análise

**Ethernet:** operou próxima ao limite teórico de 100 Mbps (Fast Ethernet). Os 740 retransmissões no upload são concentradas em poucos momentos e não comprometem o throughput médio. Driver interno do S905W funciona corretamente no kernel mainline.

**Wi-Fi SSV6051:** throughput médio de ~7 Mbps, com alta variabilidade e quedas momentâneas. Em 48 horas de operação contínua sem reinicializações, a interface permaneceu ativa após a desativação do power management. Causas das limitações:
- Driver legado sem otimizações para kernels modernos
- Chipset de baixo custo sem suporte a 802.11n full-speed
- Ausência de DMA eficiente no driver

**Recomendação:** usar Ethernet para aplicações que exijam largura de banda (Docker containers, transferências de arquivo, SSH com muitos dados). Wi-Fi é adequado para uso leve em rede local (acesso SSH, monitoramento, IoT).

---

## 6. Limitações e Problemas Encontrados

### 6.1 Limitações de hardware

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| 1 GB RAM | Sem interface gráfica pesada; navegadores lentos | Uso headless; XFCE com poucos aplicativos abertos |
| eMMC 8 GB | Espaço limitado para Docker images | Usar cartão SD externo para armazenamento; limpeza periódica |
| CPU Cortex-A53 @1.5 GHz | Limitado para workloads computacionais | Aplicações leves: servidor web, automação, dados periódicos |
| Sem dissipação ativa | Thermal throttling em carga contínua | Monitorar `cat /sys/class/thermal/thermal_zone*/temp`; manter carga abaixo de 80% |

### 6.2 Limitações de software

| Problema | Causa | Status |
|---------|-------|--------|
| Wi-Fi instável | Driver SSV6051 legado, sem manutenção ativa | Parcialmente resolvido com power_save=off |
| Wi-Fi ~7 Mbps | Hardware SSV6051 limitado | Sem solução no driver atual |
| Variações entre placas | Diferentes revisões do TX9 Pro têm pinos ligeiramente diferentes | Testes empíricos necessários por lote |
| Display bit-bang ineficiente | Protocolo proprietário sem DMA | Impacto mínimo na prática |
| IR Blaster não funcional | Não investigado (status=disabled no DTS) | Trabalho futuro |
| Swap na eMMC não recomendado | Desgaste acelerado da memória flash | Usar cartão SD externo para swap se necessário |

### 6.3 Problemas resolvidos durante o projeto

| Problema | Causa identificada | Solução aplicada |
|---------|-------------------|-----------------|
| Display não responde após cold boot | GPIO em estado indefinido no power-on | Serviço systemd em basic.target com sequência de init |
| Display não inicializa sem rampa de brilho | FD6551 exige rampa de brilho obrigatória | Implementada sequência 0x01→0x71 em 8 passos |
| Módulo ssv6051 rejeitado pelo kernel | Incompatibilidade de version magic | Correção manual de EXTRAVERSION e utsrelease.h |
| Wi-Fi cai esporadicamente | Power management colocando chipset em sleep | Dispatcher NetworkManager desativa power_save |
| DTB não encontrado no boot.img | DTB em dispositivo de bloco separado /dev/dtb | Extração direta via dd |
| Versão Android falsa (reportava 10) | Build prop alterado pelo fabricante | Identificado via kernel version e fingerprint |

---

## 7. Conclusão

O projeto alcançou todos os objetivos propostos: a TV Box TX9 Pro foi completamente descaracterizada e migrada para **Armbian Linux (Ubuntu Noble, kernel 6.18.23-current-meson64)**, sem qualquer remanescente do Android original.

### Resultados alcançados

| Componente | Status | Detalhes |
|-----------|--------|---------|
| Sistema operacional | ✅ Funcional | Armbian Linux, boot direto sem Android |
| Display FD6551 | ✅ Funcional | Contador de boot + relógio com indicadores LAN/Wi-Fi |
| Receptor IR | ✅ Funcional | NECx 0x4040, 13 botões mapeados |
| Ethernet | ✅ Funcional | ~92 Mbps, próximo ao limite físico |
| Wi-Fi SSV6051 | ⚠️ Funcional (limitado) | ~7 Mbps, estável em 48h contínuas |
| Docker Engine | ✅ Funcional | arm64, compose plugin incluído |
| Acesso SSH | ✅ Funcional | Disponível desde o primeiro boot |
| Segurança | ✅ Melhorada | Sem processos de root desconhecidos, kernel atualizado |

### Contribuições técnicas originais

1. **Mapeamento completo do protocolo FD6551** por engenharia reversa, incluindo a documentação da rampa de brilho obrigatória (não documentada publicamente).
2. **Procedimento reprodutível para compilação do driver SSV6051** em kernels 6.x com correção de version magic.
3. **Identificação e solução do problema de cold boot** causado pelo estado indefinido dos pinos GPIO após remoção de energia.
4. **Arquitetura de serviço de display em 3 camadas** com separação entre acesso a hardware (driver), gerenciamento (servidor IPC) e interface (cliente/CLI).

### Replicabilidade

A metodologia documentada neste relatório é **replicável em outras unidades TX9 Pro** e adaptável a dispositivos similares baseados no SoC Amlogic GXL (S905W/X), contribuindo para o reaproveitamento seguro de equipamentos apreendidos ou descartados por órgãos públicos.

---

## 8. Referências

- **Armbian Project.** Armbian Linux for ARM development boards. Disponível em: https://www.armbian.com
- **Armbian Community.** aml-s9xx-box builds. Disponível em: https://github.com/armbian/community
- **FD Microelectronics.** FD6551 LED Display Driver. Sem datasheet oficial público — informações inferidas por engenharia reversa.
- **Linux Kernel Documentation.** Device Tree Usage. Disponível em: https://www.kernel.org/doc/html/latest/devicetree/usage-model.html
- **Linux Kernel Documentation.** GPIO Subsystem. Disponível em: https://www.kernel.org/doc/html/latest/driver-api/gpio/
- **Linux Media Infrastructure.** ir-keytable — configure kernel IR remotes. Disponível em: https://www.kernel.org/doc/html/latest/userspace-api/media/rc/ir-keytable.html
- **Rotava, Eloi.** ssv6051-driver: Linux driver for SSV6051/SSV6200 Wi-Fi chipset. GitHub, 2023. Disponível em: https://github.com/eloi-rotava/ssv6051
- **Docker Inc.** Install Docker Engine on Ubuntu. Disponível em: https://docs.docker.com/engine/install/ubuntu/
- **Amlogic.** S905W Datasheet (parcialmente público). GXL platform technical reference.

---

