# Sistemas publicados

Os sistemas (Linux ou Android) são escolhidos **na TV pelo instalador** (ver [como-instalar.md](como-instalar.md)), que baixa os
arquivos das releases; **não baixe à mão**. "Variação do sistema" (antes, "spin") é uma imagem pronta com um conjunto de programas.

## TX9 (Amlogic S905W)

| Sistema (nome na lista) | Para quê | Release |
|---|---|---|
| **Instalador** 1.2.45 (zip para o cartão) | programa que instala os demais | [`instalador-tx9-1.2.45`](https://github.com/rbeninca/tvbox/releases/tag/instalador-tx9-1.2.45) (Latest) |
| **CompSTEAM Educação** 1.3.12 (Debian 13) | blocos/TurboWarp, GeoGebra offline, Arduino IDE, Thonny, LibreOffice, GCompris; **precisa do instalador 1.2.44 ou mais novo** (usa a memória toda) | [`debian-educacao-gui-1.3.12`](https://github.com/rbeninca/tvbox/releases/tag/debian-educacao-gui-1.3.12) |
| **Área de Trabalho** 1.2.69 (Debian 13, labwc) | área de trabalho leve, com painel, navegador e arquivos | [`debian-labwc-gui-1.2.69`](https://github.com/rbeninca/tvbox/releases/tag/debian-labwc-gui-1.2.69) |
| **Linux Gráfico** 1.2.69 (Debian 13, Weston) | Chromium e terminal | [`debian-gui-1.2.69`](https://github.com/rbeninca/tvbox/releases/tag/debian-gui-1.2.69) |
| **Linux** 1.2.69 (Debian 13) | linha de comando, com Docker | [`debian-1.2.69`](https://github.com/rbeninca/tvbox/releases/tag/debian-1.2.69) |
| **Mínimo** 1.2.70 (Alpine Linux) | linha de comando mínima, com Docker | [`alpine-1.2.70`](https://github.com/rbeninca/tvbox/releases/tag/alpine-1.2.70) |

Todas as variações de Linux trazem Docker, Wi-Fi, git, vim, htop, controle IR, áudio e display frontal.
O Android CompSTEAM TV (LineageOS 22.2) não é release pública.

## MXQ Pro (Rockchip RK3229)

| Sistema | Release |
|---|---|
| **Instalador** 1.2.46 (imagem para o cartão microSD) | [`instalador-mxq-1.2.46`](https://github.com/rbeninca/tvbox/releases/tag/instalador-mxq-1.2.46) |
| Educação | [`mxqpro-debian-educacao-gui-0.2.43`](https://github.com/rbeninca/tvbox/releases/tag/mxqpro-debian-educacao-gui-0.2.43) |
| Área de trabalho leve (labwc) | [`mxqpro-debian-labwc-gui-0.2.43`](https://github.com/rbeninca/tvbox/releases/tag/mxqpro-debian-labwc-gui-0.2.43) |
| Debian com área de trabalho | [`mxqpro-debian-gui-0.2.43`](https://github.com/rbeninca/tvbox/releases/tag/mxqpro-debian-gui-0.2.43) |
| Debian (linha de comando) | [`mxqpro-debian-0.2.43`](https://github.com/rbeninca/tvbox/releases/tag/mxqpro-debian-0.2.43) |
| Alpine (mínimo) | [`mxqpro-alpine-0.2.43`](https://github.com/rbeninca/tvbox/releases/tag/mxqpro-alpine-0.2.43) |

## BTV11 (Amlogic S905X3)

| Sistema | Release |
|---|---|
| **Instalador** 1.2.45 (zip para o pendrive) | [`instalador-btv11-1.2.45`](https://github.com/rbeninca/tvbox/releases/tag/instalador-btv11-1.2.45) |
| Área de trabalho leve (labwc) | [`btv11-debian-labwc-gui-0.1.8`](https://github.com/rbeninca/tvbox/releases/tag/btv11-debian-labwc-gui-0.1.8) |
| Debian com Weston | [`btv11-debian-gui-0.1.8`](https://github.com/rbeninca/tvbox/releases/tag/btv11-debian-gui-0.1.8) |
| Debian (linha de comando) | [`btv11-debian-0.1.8`](https://github.com/rbeninca/tvbox/releases/tag/btv11-debian-0.1.8) |
| Alpine (mínimo) | [`btv11-alpine-0.1.8`](https://github.com/rbeninca/tvbox/releases/tag/btv11-alpine-0.1.8) |
| CompSTEAM Educação | [`btv11-debian-educacao-gui-0.1.8`](https://github.com/rbeninca/tvbox/releases/tag/btv11-debian-educacao-gui-0.1.8) |

O Android do BTV11 ainda não é público.

## Canais usados pelo instalador

O instalador os lê sozinho.

| Canal | Função |
|---|---|
| [`catalogo`](https://github.com/rbeninca/tvbox/releases/tag/catalogo) | lista assinada das imagens disponíveis |
| [`instalador-publico`](https://github.com/rbeninca/tvbox/releases/tag/instalador-publico) | versão do instalador guardado no box, para atualização |

## CompSTEAM Educação em detalhe

![Área de trabalho do CompSTEAM Educação](../imgs/compsteam/educacao-area-de-trabalho.png)

- **Blocos** (TurboWarp, compatível com Scratch) e **GeoGebra Classic** funcionam **sem internet**; há manual do GeoGebra em português.
- **Arduino IDE** (com exemplos), **Thonny** e Python 3, **LibreOffice** (Writer, Calc, Impress), **GCompris**, **Tux Paint**,
  **SQLite** e **DB Browser for SQLite**, **Bluefish** e Falkon.
- Raiz grande (perfil 5b, ver [particoes.md](particoes.md)): baixa cerca de 1,2 GiB, ocupa cerca de 4,6 GiB e usa a memória toda.
- O WebGL do navegador usa renderização por software nas janelas locais (ver [dtb-e-drivers.md](dtb-e-drivers.md)).

![TurboWarp e GeoGebra abertos](../imgs/compsteam/educacao-geogebra-e-blocos.png)
