# Relatório de Hardware - TV Box TX9 Pro (192.168.1.2)

## Informações Gerais do Sistema
- **Modelo:** TX9
- **Plataforma:** Amlogic GXL (S905W/X)
- **Versão Original do Android:** 10.0
- **Build ID:** [Coletado via getprop]

## Mapeamento de Hardware
- **CPU:** Amlogic S905 series (Architecture: AArch64)
- **GPU:** ARM Mali
- **Wi-Fi Chipset:** SSV6051 / SSV6200 (Interface: wlan0)
- **Ethernet:** Integrada Amlogic (dwc3/eth0)
- **Memória:** [Informação em system_info.txt]

## Partições Extraídas (Backup)
Os seguintes arquivos foram extraídos e devem ser mantidos para referência ou restauração:
- `boot.img`: Contém o Kernel e o Device Tree Blob (DTB).
- `logo.img`: Contém as imagens de boot e, em alguns casos, configurações de display.
- `recovery.img`: Partição de recuperação original.

## Instruções para Substituição do Firmware
1. **Preservação do DTB:** O DTB é essencial para que o Wi-Fi e a Ethernet funcionem no novo firmware. Se o novo firmware não for específico para o TX9 com chip SSV6051, você deverá extrair o DTB do `boot.img` original e injetá-lo no novo firmware.
2. **Backdoor Check:** Firmware original contém serviços suspeitos. Recomenda-se o uso de builds limpas como **SlimBoxTV** ou **AidansROM**, desde que compatíveis com o processador S905W/X e o chip de Wi-Fi SSV6051.
3. **Procedimento de Flash:**
   - Use o **Amlogic USB Burning Tool**.
   - Conecte o TV Box via cabo USB Macho-Macho na porta USB lateral (geralmente a porta 2).
   - Pressione o botão de reset (dentro da entrada AV) ao ligar o cabo USB.

## Arquivos Extraídos e Mapeamento
Os seguintes arquivos foram extraídos do dispositivo (IP: 192.168.1.2) para garantir a integridade da reinstalação:
- `dtb.img`: Extraído diretamente de `/dev/dtb` (256 KB). Este é o binário crítico que define as configurações de hardware para o kernel Amlogic.
- `boot.img`: Contém o kernel original (3.14.29) e o ramdisk do Android 7.1.2.
- `logo.img`: Imagens de boot e splash original.
- `recovery.img`: Imagem de recuperação stock.

### Importância do DTB
Muitas ROMs genéricas para o chipset S905W/X falham no Wi-Fi devido ao chipset **SSV6051**. Se após instalar uma nova firmware o Wi-Fi não funcionar, você deve usar o `dtb.img` extraído aqui para substituir o DTB da nova ROM.

## Análise de Armazenamento (eMMC Real vs. Propaganda)
Realizamos uma auditoria profunda no hardware de armazenamento (chip eMMC) conectando via SSH (Armbian) e ADB (Android) em múltiplas unidades:

- **Armazenamento Anunciado (Android):** 64 GB
- **Armazenamento Real (Hardware):** **8 GB** (`mmcblk0` / `mmcblk1` = ~7.4 GB a 7.6 GB utilizáveis)
- **Evidência Técnica:** 
  - O kernel Linux reporta `7.634.944 blocks` (unidade 192.168.1.14) e `7.3 GB` (unidade 192.168.1.13).
  - O sistema Android está particionado em apenas **1.9 GB** para `/system` e **4.2 GB** para `/data`.
- **Veredito:** O firmware original do Android (TX9) utiliza uma técnica de maquiagem de software no `build.prop` e nos binários do sistema para exibir 64GB falsos. Fisicamente, o dispositivo possui apenas um chip de **8GB eMMC**.

## Análise de Segurança (Backdoor)
- O firmware original reporta Android 10, mas a versão real do kernel e os fingerprints indicam **Android 7.1.2**.
- Existem serviços rodando em background que utilizam privilégios de root sem autorização (como o próprio `su` acessível via rede).
- Recomenda-se a limpeza completa das partições `system` e `vendor`.
