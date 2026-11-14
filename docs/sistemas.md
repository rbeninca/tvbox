# Sistemas publicados

Os sistemas (Linux ou Android) são escolhidos **na TV pelo instalador** (ver [como-instalar.md](como-instalar.md)), que baixa os
arquivos das releases; **não baixe à mão**. "Variação do sistema" (antes, "spin") é uma imagem pronta.

**Desenho atual (novembro de 2026):** cada placa tem duas versões de Linux, **CompSTEAM Linux** (texto) e **CompSTEAM Linux Gráfico**
(área de trabalho leve), e o Android onde a placa tem (TX9 e BTV11). Os programas extras são **kits opcionais**, instalados pelo menu
do box, e voltam sozinhos depois de atualizar o sistema. As variações Educação, Área de Trabalho e Mínimo deixam de ser oferecidas:
o box que as usa é levado à versão que as substitui. As releases antigas continuam no GitHub até saírem as novas.

## TX9 (Amlogic S905W)

| Sistema (nome na lista) | Para quê | Release |
|---|---|---|
| **Instalador** 1.2.62 (zip para o cartão) | programa que instala os demais | [`instalador-tx9-1.2.62`](https://github.com/rbeninca/tvbox/releases/tag/instalador-tx9-1.2.62) (Latest) |
| **Linux Gráfico** (Debian 13, labwc) | área de trabalho leve com barra, arquivos, navegador, Docker e Wi-Fi; sem os programas da aula (kit opcional) | em preparo |
| **Linux** 1.2.69 (Debian 13) | linha de comando, com Docker | [`debian-1.2.69`](https://github.com/rbeninca/tvbox/releases/tag/debian-1.2.69) |

As duas versões de Linux trazem Docker, Wi-Fi, git, vim, htop, controle IR, áudio e display frontal.
O Android CompSTEAM TV (LineageOS 22.2) não é release pública.

## MXQ Pro (Rockchip RK3229)

| Sistema | Release |
|---|---|
| **Instalador** 1.2.57 (imagem para o cartão microSD) | [`instalador-mxq-1.2.57`](https://github.com/rbeninca/tvbox/releases/tag/instalador-mxq-1.2.57) |
| Linux Gráfico (Debian, labwc) | em preparo |
| Debian (linha de comando) | [`mxqpro-debian-0.2.43`](https://github.com/rbeninca/tvbox/releases/tag/mxqpro-debian-0.2.43) |

## BTV11 (Amlogic S905X3)

| Sistema | Release |
|---|---|
| **Instalador** 1.2.57 (zip para o pendrive) | [`instalador-btv11-1.2.57`](https://github.com/rbeninca/tvbox/releases/tag/instalador-btv11-1.2.57) |
| Linux Gráfico (Debian, labwc) | em preparo |
| Debian (linha de comando) | [`btv11-debian-0.1.8`](https://github.com/rbeninca/tvbox/releases/tag/btv11-debian-0.1.8) |

O Android do BTV11 ainda não é público.

## Canais usados pelo instalador

O instalador os lê sozinho.

| Canal | Função |
|---|---|
| [`catalogo`](https://github.com/rbeninca/tvbox/releases/tag/catalogo) | lista assinada das imagens disponíveis |
| [`instalador-publico`](https://github.com/rbeninca/tvbox/releases/tag/instalador-publico) | versão do instalador guardado no box, para atualização |

## Kit Educação (opcional) em detalhe

![Área de trabalho com o kit Educação](../imgs/compsteam/educacao-area-de-trabalho.png)

- **Blocos** (TurboWarp, compatível com Scratch) e **GeoGebra Classic** funcionam **sem internet**; há manual do GeoGebra em português.
- **Arduino IDE** (com exemplos), **Thonny** e Python 3, **LibreOffice** (Writer, Calc, Impress), **GCompris**, **Tux Paint**,
  **SQLite** e **DB Browser for SQLite**, **Bluefish** e Falkon.
- O kit é instalado da internet (cerca de 2,5 GB no disco) sobre o **CompSTEAM Linux Gráfico**, pelo menu do box, e volta sozinho depois de atualizar o sistema.
- O WebGL do navegador usa renderização por software nas janelas locais (ver [dtb-e-drivers.md](dtb-e-drivers.md)).

![TurboWarp e GeoGebra abertos](../imgs/compsteam/educacao-geogebra-e-blocos.png)
