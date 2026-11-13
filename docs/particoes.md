# Partições

Resumo do que o instalador grava e do que nunca toca. Nada aqui é para gravar à mão.

## O que nunca é gravado

- A partição **`bootloader`**: corrompida, o box deixa de ligar e só se recupera com técnicas de bancada.
- A **área de chaves da `reserved`**: chaves e dados únicos do box.
- A `reserved` **inteira**: o instalador grava nela só a tabela de partições e o DTB de fábrica com o nó `partitions` trocado.

Toda gravação é conferida: o instalador lê de volta e compara o SHA-256 de cada partição com o do manifesto.

## TX9 (eMMC de 8 GB)

| Partição | Tamanho (MiB) | Para que serve |
|---|---:|---|
| `bootloader` | 4 | U-Boot de fábrica. **Nunca gravado** |
| `reserved` | 64 | tabela de partições, chaves do fabricante e DTB; **identidade própria de cada box** |
| `cache` | 64 | logs do recovery e comandos de atualização |
| `env` | 8 | variáveis do U-Boot do box |
| `logo` | 32 | imagem de abertura |
| `recovery` | 32 | **o instalador de rede** |
| `rsv` | 8 | dados persistentes do CompSTEAM (configuração, redes Wi-Fi) |
| `tee` | 8 | ambiente seguro de fábrica |
| `crypt` | 32 | agente do inventário (atualizável sem reinstalar) |
| `misc` | 32 | comando de boot |
| `boot` | 32 | kernel e DTB do sistema |
| `system` | 1580 | raiz do sistema (Android: `/system`) |
| `vendor`, `odm`, `dtbo`, `metadata` | 320, 128, 8, 16 | Android |
| `data` | 4936 | Android: dados do usuário; nas variações de Linux gráficas, parte da raiz |

## Perfis de volume das variações de Linux

A raiz de uma variação de Linux precisa de mais espaço que a partição `system`; o kernel junta várias partições em um volume só.

| Perfil | Raiz formada por | Tamanho da raiz | `/home` | Usado em |
|---|---|---:|---|---|
| **5a** | `system` + `vendor` + `odm` + `dtbo` + `metadata` | 2052 MiB | a partição `data` | linha de comando (Debian) |
| **5b** | as seis, com `data` | 6988 MiB | dentro da raiz | desenho anterior (variações gráficas e Educação) |
| **5c** | as cinco do 5a + o começo da `data` | 2892 MiB | o fim da `data` (4096 MiB) | layout v2 (Linux texto e Linux Gráfico) |

Cuidado: sair de uma variação com raiz grande para uma clássica por "Atualizar" pode reformatar a partição de dados; por isso o
instalador só oferece **"Instalação limpa"** quando o arranjo do disco muda (ver [como-instalar.md](como-instalar.md)).

## MXQ Pro (NAND)

O CompSTEAM **não mexe** em `uboot`, `trust`, `baseparamer` nem no parâmetro de fábrica.

| Partição | Tamanho | Uso |
|---|---:|---|
| `uboot`, `trust`, `baseparamer` | 4 MiB, 8 MiB, 1 MiB | de fábrica; não gravadas |
| `misc` | 4 MiB | comando de boot |
| `resource` | 15 MiB | DTB e logo |
| `kernel` | 12 MiB | kernel Linux 6.12 |
| `boot` | 12 MiB | initramfs |
| `instalador` | 32 MiB | o instalador de rede |
| `agente` | 64 MiB | agente do inventário |
| `cache` | 128 MiB | livre |
| `config` | 16 MiB | identidade, configuração e redes Wi-Fi |
| `kpanic` | 4 MiB | livre |
| `reserva` | 4096 MiB | `/home` |
| `sistema` | o restante | raiz do sistema |

Não há perfis de volume. No layout l3, o `/home` (`reserva`) tem **4096 MiB** e a raiz (`sistema`) fica com
**o restante** da NAND (cerca de 2896 MiB na NAND de 8 GB); o kit Educação cabe na camada gravável do `/home`.

## BTV11 (eMMC de 16 GB)

Mantém as áreas de fábrica (bootloader, `reserved`, `env`). Depois delas, o Linux usa duas partições comuns: p1 (FAT32, 255 MiB)
com kernel e boot, e p2 (ext4) com a raiz, até o fim. Uma p3 de 40 MiB (identidade e agente) entra na próxima versão.
O bootloader de fábrica nunca é gravado.
