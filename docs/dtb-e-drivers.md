# DTB, kernels e drivers

## O que é o DTB

O **DTB** (Device Tree Blob) é um arquivo que descreve o hardware: onde estão a memória, o vídeo, o Wi-Fi, o IR, os pinos do
display. O kernel usa essa descrição em vez de "adivinhar" a placa.

## Por que o U-Boot de fábrica precisa do DTB da `reserved`

No TX9 existem dois consumidores do DTB, com regras diferentes:

- **O U-Boot de fábrica (2015)** lê o DTB gravado na `reserved`. Dele tira as partições, o endereço do logo (`logo_addr`, para o
  framebuffer da imagem de abertura) e os parâmetros do vídeo.
- **O kernel** recebe o seu DTB dentro do `boot.img` (segunda imagem).

O framebuffer do logo ocupa cerca de 4 MB (1920×1080, 16 bits). No DTB de fábrica ele termina cerca de 1 MB abaixo do fim da RAM,
onde o próprio U-Boot reside. No DTB inteiro do sistema novo (LineageOS) o endereço era 1 MB mais alto: o framebuffer passava a
**sobrescrever o U-Boot** ao desenhar o logo, o U-Boot travava e reiniciava antes de permitir o modo de gravação pelo reset.

Por isso a regra do projeto: **na `reserved` fica o DTB de fábrica, só com o nó `partitions` trocado** (ver
[particoes.md](particoes.md)). Quem precisa do DTB completo é o kernel, e ele o recebe pelo `boot.img`: o ambiente do U-Boot
do box é ajustado (`storeboot` copia a segunda imagem do `boot.img` para a memória antes do `bootm`).

## Kernels

| Sistema | Kernel | Observação |
|---|---|---|
| Android TV (CompSTEAM TV) | Linux 4.9 da Amlogic (árvore do LineageOS) | módulos de fábrica da Amlogic para vídeo, Wi-Fi e rede; `userspace` de 32 bits |
| Variações de Linux (TX9) | Linux 6.12 **do Debian** (pacote oficial) | DTB mainline do P281 gerado pelo projeto, com memória para registro de quedas (ramoops) e suporte a interrupção SDIO |
| Variações de Linux (MXQ Pro) | Linux 6.12 compilado pelo projeto | DTB derivado do `rk3229-xms6` do kernel principal |
| Instalador | kernel Linux compilado pelo projeto + Alpine mínimo | cabe em 32 MiB (`recovery`) |

Para o 6.12 do Debian, as peças fora do kernel (driver Wi-Fi, módulo que reinicia "com o motivo update") são compiladas contra o
mesmo kernel do pacote, e o `version magic` precisa coincidir.

## Wi-Fi SSV6051 (TX9)

O chip SSV6051 não tem driver no kernel principal. O projeto usa:

- **kernel 4.9 (Android e instalador):** driver iComm SSV6051 da árvore do LineageOS, portado e corrigido;
- **kernel 6.12 (variações de Linux):** driver do Armbian com seis correções do projeto.

**Correção da calibração IQ (outubro de 2026).** Em parte das partidas o Wi-Fi associava e recebia bem, mas o envio quase não passava
(0,1 a 9 Mbit/s contra 40 a 47 numa partida boa), durante a partida inteira. A causa: o driver esperava a calibração IQ do rádio
pelo evento que o firmware manda ao subir, cerca de 1 ms depois do comando, enquanto a calibração real só termina uns 165 ms depois.
Nesse intervalo o driver já ligava o PHY e programava o canal, e o transmissor ficava mal calibrado. A correção espera o evento do
boot do firmware, envia o comando de calibração e espera o resultado dele; o log passa a mostrar a confirmação com tempo entre
152 e 168 ms. Foi provada num box na montagem em que o defeito mais aparecia, alternando o driver corrigido e o antigo na mesma
sessão. Outras correções: cifra de envio feita pelo mac80211 (melhor vazão), quadros de grupo decifrados pelo mac80211 (IPv6 pelo
Wi-Fi) e taxa mínima correta para quadros de gerência.
O relatório completo, com método e medidas, fica nos materiais do projeto (relatório "Wi-Fi SSV6051, 2026-10").

Limite do hardware: **só 2,4 GHz**.

## Display frontal

O display de 4 dígitos usa o controlador **FD6551**, ligado por dois fios (relógio no pino GPIOH_7, dados no GPIOH_9, coletor
aberto). No Android, o driver é o módulo de kernel **OpenVFD**, configurado por um nó no DTS. Nas variações Linux, um programa
próprio (`compsteam-painel`) fala o protocolo pelas GPIO do kernel. Os dois mostram o percentual de boot, o relógio, o endereço
IP e os ícones. O mapeamento do FD6551 foi levantado por engenharia reversa (ver `display/` neste repositório).
Atenção: esses pinos também servem a I2S e ao JTAG; com o JTAG ligado o display não funciona, e o instalador desliga o JTAG no
ambiente do U-Boot.

## Controle remoto IR

O receptor IR usa o pino GPIOAO_7 e o protocolo **NEC estendido**, com código de fabricante `0x4040` e 13 teclas. No Android o
mapa vem do DTB de fábrica; nas variações de Linux, de um arquivo de mapa de teclas (`rc_keymaps`) do subsistema `rc-core`,
que entrega as teclas como um teclado comum. O instalador também aceita teclado e mouse USB.

## GPU

- **TX9: Mali-450 MP.** No Linux 6.12 usa-se o driver livre **lima** (Mesa), que entrega **OpenGL ES 2.0** (60 quadros por segundo
  num teste de cubo em vsync). O hardware não tem mais que isso. O Weston e o labwc (área de trabalho) compõem a tela pela GPU.
  **Consequência para o navegador:** o WebGL (blocos de programação, GeoGebra) exige recursos além do ES 2.0 do lima. Por isso,
  nas janelas locais de blocos e GeoGebra o navegador usa **renderização WebGL por software** (SwiftShader), com limite de memória
  para não afetar o sistema; o resto da navegação continua sem aceleração 3D do navegador.
- **MXQ Pro: Mali-400.** O lima também a atende; em teste chegou a cerca de 40 quadros por segundo no `glmark2`.

## Outros itens do TX9

- **Reinício para o instalador sem apertar o reset:** módulo que reinicia o kernel 6.12 com o motivo `update`.
- **Bluetooth:** só por adaptador USB; o kernel reconhece clones CSR, mas o firmware desses clones não responde a um comando HCI
  opcional e o Android aborta a inicialização. Recomenda-se um adaptador Realtek RTL8761B.
- **Teste sem gravar:** qualquer kernel, DTB ou sistema novo pode ser carregado pela RAM via USB (modo USB do U-Boot de fábrica)
  antes de ser gravado na eMMC. É a regra do projeto.
