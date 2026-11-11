# Documentação técnica do CompSTEAM

O **CompSTEAM** reaproveita TV boxes baratas como computadores para escolas: um Android TV, várias variações de Linux e um
instalador que se usa só com um cartão e o controle remoto. Projeto de Romulo de Aguiar Beninca (IFSC, câmpus Gaspar).

Para técnicos e professores. O código-fonte não é publicado aqui; as imagens prontas estão nas
[releases](https://github.com/rbeninca/tvbox/releases).

## Índice

| Documento | Para quê |
|---|---|
| [como-instalar.md](como-instalar.md) | **Comece por aqui.** Passo a passo para instalar um sistema num TX9 |
| [sistemas.md](sistemas.md) | Sistemas publicados, conteúdo e links |
| [hardware.md](hardware.md) | As duas TV boxes suportadas: TX9 (Amlogic S905W) e MXQ Pro (Rockchip RK3229) |
| [particoes.md](particoes.md) | Divisão da memória, o que nunca é gravado e como as variações de Linux juntam partições |
| [dtb-e-drivers.md](dtb-e-drivers.md) | DTB, kernels, Wi-Fi SSV6051, display frontal, controle IR e GPU |
| [como-foi-construido.md](como-foi-construido.md) | Android TV, variações de Linux, instalador de rede e agente do inventário |

## Palavras que aparecem muito

- **Box**: a TV box, o aparelho.
- **Variação do sistema** (nos textos antigos, "spin"): imagem pronta com um conjunto de programas. Exemplos: Alpine (mínimo),
  Debian (linha de comando), Debian com área de trabalho, CompSTEAM Educação.
- **eMMC / NAND**: memória interna onde o sistema fica gravado (TX9: eMMC; MXQ Pro: NAND).
- **DTB**: descreve o hardware para o kernel (ver [dtb-e-drivers.md](dtb-e-drivers.md)).
- **Bootloader / U-Boot**: primeiro programa ao ligar. O do fabricante **nunca é substituído**.

## Aviso

Gravar a memória de um box apaga o sistema de fábrica. O instalador tenta guardar uma cópia da identidade do box antes de gravar
(ver [como-instalar.md](como-instalar.md)), mas a responsabilidade pelo equipamento é de quem instala. Projeto educacional,
sem vínculo com os fabricantes dos chips ou com as distribuições Linux citadas.
