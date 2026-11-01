# Hardware suportado

O CompSTEAM tem imagens para duas TV boxes. O instalador reconhece a placa e só oferece o que serve para ela.

## TX9 (placa P281)

![TX9](../imgs/compsteam/tx9-caixa.png)

| Item | Valor |
|---|---|
| SoC | Amlogic S905W (família GXL), 4 núcleos Cortex-A53 |
| RAM | 1 GB (o firmware de fábrica anuncia 4 GB, o que é falso) |
| Memória interna | eMMC de 8 GB |
| Wi-Fi | SSV6051 (iComm), **somente 2,4 GHz**, ligado por SDIO |
| Rede cabeada | Ethernet 10/100 |
| Vídeo | HDMI; GPU Mali-450 (só OpenGL ES 2.0) |
| Display frontal | controlador FD6551: 4 dígitos de 7 segmentos e ícones (LAN, Wi-Fi, Play, Pause, relógio, USB) |
| Controle remoto | receptor IR, protocolo NEC estendido, 13 teclas |
| USB | portas USB 2.0; uma delas é a porta OTG usada para gravação por cabo |
| Bluetooth | a placa não tem rádio; funciona com adaptador USB |
| Botão reset | fica no fundo do box (pelo furo, com um palito); é ele que abre o instalador |
| Sistema de fábrica | Android 7.1.2 de 32 bits com kernel 3.14 de 64 bits |

![Placa do TX9 (P281) com os componentes identificados](../imgs/compsteam/placa-tx9-componentes.jpg)

A placa do TX9 vem em revisões diferentes no mercado; o CompSTEAM foi desenvolvido e testado na placa P281 com 1 GB de RAM.
Caixas com o mesmo nome comercial e placa diferente (outra RAM, outro Wi-Fi) não são cobertas.

## MXQ Pro (Rockchip RK3229)

| Item | Valor |
|---|---|
| SoC | Rockchip RK3229, 4 núcleos Cortex-A7 (32 bits) |
| RAM | 1 GB |
| Memória interna | NAND de 8 GB (MLC), acessada por camada de tradução (FTL) |
| Wi-Fi | SSV6006C, somente 2,4 GHz |
| GPU | Mali-400 (3D funciona com o driver livre lima, cerca de 40 quadros por segundo em teste) |
| Observação | muitos boxes desse modelo trazem o mesmo MAC e número de série; o CompSTEAM cria uma identidade própria a partir do número do chip |

![Placa do MXQ Pro (R329Q V8.0) com os componentes identificados](../imgs/compsteam/placa-mxq-componentes.jpg)

Do MXQ Pro existem as variações Debian, Debian com área de trabalho, Alpine e Ubuntu com interface gráfica
(ver [sistemas.md](sistemas.md)). Não há Android CompSTEAM para ele.

## O que é igual nos dois

- O bootloader de fábrica fica como está; o sistema entra "por trás" dele.
- Um instalador de rede único, gravado numa partição própria (`recovery` no TX9; `instalador` no MXQ).
- Identidade do box derivada do número de série do chip (nunca do MAC, que pode se repetir).

Veja [particoes.md](particoes.md) para o mapa da memória e [dtb-e-drivers.md](dtb-e-drivers.md) para os drivers.
