# Documentação técnica do CompSTEAM

O **CompSTEAM** reaproveita TV boxes baratas (que iriam para o lixo eletrônico) como computadores para escolas:
um sistema Android TV, várias variações de Linux e um instalador que o professor ou técnico usa só com um cartão e o controle remoto.
Projeto de Romulo de Aguiar Beninca (IFSC, câmpus Gaspar).

Esta documentação é para técnicos e professores. O código-fonte do CompSTEAM não é publicado aqui; as imagens prontas estão nas
[releases](https://github.com/rbeninca/tvbox/releases).

## Índice

| Documento | Para quê |
|---|---|
| [como-instalar.md](como-instalar.md) | **Comece por aqui.** Passo a passo para instalar um sistema num TX9 com o instalador público |
| [sistemas.md](sistemas.md) | Os sistemas publicados, o que cada um traz e os links de download |
| [hardware.md](hardware.md) | As duas TV boxes suportadas: TX9 (Amlogic S905W) e MXQ Pro (Rockchip RK3229) |
| [particoes.md](particoes.md) | Como a memória do box é dividida, o que nunca é gravado e como as variações de Linux juntam partições |
| [dtb-e-drivers.md](dtb-e-drivers.md) | DTB, kernels, Wi-Fi SSV6051, display frontal, controle IR e GPU |
| [como-foi-construido.md](como-foi-construido.md) | Android TV, variações de Linux, instalador de rede e agente do inventário |

## Palavras que aparecem muito

- **Box**: a TV box, o aparelho.
- **Variação do sistema** (nos textos antigos do projeto, "spin"): uma imagem pronta de sistema, com um conjunto de programas.
  Exemplos: Alpine (mínimo), Debian (linha de comando), Debian com área de trabalho, CompSTEAM Educação.
- **eMMC / NAND**: a memória interna onde o sistema fica gravado (TX9: eMMC; MXQ Pro: NAND).
- **DTB**: arquivo que descreve o hardware para o kernel (ver [dtb-e-drivers.md](dtb-e-drivers.md)).
- **Bootloader / U-Boot**: o primeiro programa que roda ao ligar. O do fabricante **nunca é substituído** pelo CompSTEAM.

## Aviso

Gravar a memória de um box apaga o sistema de fábrica. O instalador guarda uma cópia da identidade do box antes de gravar
(ver [como-instalar.md](como-instalar.md)), mas a responsabilidade pelo equipamento é de quem instala. Projeto educacional,
sem vínculo com os fabricantes dos chips ou com as distribuições Linux citadas.

Documentos antigos deste repositório (`README.MD`, `RELATORIO_TECNICO.MD`, `TX9_PRO_HARDWARE_REPORT.md`) tratam do primeiro
trabalho, com Armbian no TX9 Pro, e continuam válidos como história e como referência de engenharia reversa.
