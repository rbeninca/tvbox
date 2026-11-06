# Kernels e drivers

O **DTB** (Device Tree Blob) descreve o hardware ao kernel. No TX9, o DTB de fábrica na `reserved` é mantido (só a tabela de
partições muda), pois o U-Boot de fábrica depende dele (ver [particoes.md](particoes.md)).

## Kernels

| Sistema | Kernel |
|---|---|
| Android TV (CompSTEAM TV) | Linux 4.9 da Amlogic |
| Variações de Linux (TX9) | Linux 6.12 do Debian |
| Variações de Linux (MXQ Pro) | Linux 6.12 |
| Instalador | Linux mínimo com Alpine (cabe em 32 MiB na `recovery`) |

## Wi-Fi SSV6051 (TX9)

O chip não tem driver no kernel principal; o projeto usa um driver adaptado. Limite do hardware: **só 2,4 GHz**.

## Display frontal

O display de 4 dígitos (controlador **FD6551**) mostra percentual de boot, relógio, endereço IP e ícones, no Android e no Linux.
Com o JTAG ligado o display não funciona; o instalador o desliga.

## Controle remoto IR

Protocolo **NEC estendido**, 13 teclas; o Linux o trata como teclado comum. O instalador também aceita teclado e mouse USB.

## GPU

- **TX9: Mali-450 MP.** No Linux 6.12 usa o driver livre **lima** (Mesa): **OpenGL ES 2.0**, o máximo do hardware. Weston e labwc
  compõem a tela pela GPU. O WebGL (blocos, GeoGebra) pede mais que o ES 2.0; nas janelas locais o navegador usa renderização por
  software, com limite de memória.
- **MXQ Pro: Mali-400.** O lima também a atende; cerca de 40 quadros por segundo no `glmark2`.

## Outros itens do TX9

- **Bluetooth:** só por adaptador USB; clones CSR podem abortar a inicialização no Android. Recomenda-se um adaptador Realtek RTL8761B.
- **Teste sem gravar:** kernel ou sistema novo pode ser carregado pela RAM via USB antes de gravar na eMMC.
