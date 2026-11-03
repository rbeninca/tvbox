# Partições

## TX9: como o box descobre as partições

O TX9 tem duas "listas" de partições, e as duas precisam concordar:

1. **O U-Boot de fábrica** (de 2015) monta a tabela sozinho a partir do nó `partitions` do DTB gravado na área `reserved`.
2. **O kernel Android 4.9** (e o instalador) lê a **MPT**, uma tabela gravada no início da `reserved`. Os nomes da MPT viram
   `/dev/block/<nome>`.

A **MPT nunca é escrita à mão**. O CompSTEAM a gera a partir do DTB, com a mesma regra do U-Boot:

- primeiro as partições fixas: `bootloader` (4 MiB), 32 MiB livres, `reserved` (64 MiB), `cache` e `env` (8 MiB);
- depois as demais, **na ordem do DTB**, com 8 MiB livres após cada uma; a última vai até o fim da memória;
- consequência: nada cabe entre `cache` e `env`, e o tamanho do `cache` desloca todas as partições seguintes.

Prova de que a regra é a certa: aplicada ao DTB de fábrica, ela reproduz a MPT de fábrica byte a byte.

Formato da MPT: assinatura `MPT\0`, versão `01.00.00`, número de partições, checksum e uma entrada de 40 bytes por partição
(nome de 16 bytes, tamanho, deslocamento e máscara). O checksum segue um erro conhecido do código da Amlogic (soma dos 10 primeiros
números de 32 bits da primeira entrada vezes o número de partições); o CompSTEAM reproduz esse cálculo.

## Tabela de partições do CompSTEAM no TX9 (eMMC de 8 GB)

Valores em MiB (1 MiB = 1.048.576 bytes). O espaço usado vai até 7456 MiB.

| Partição | Offset | Tamanho | De fábrica (offset / tamanho) | Para que serve |
|---|---:|---:|---|---|
| `bootloader` | 0 | 4 | igual | U-Boot de fábrica. **Nunca gravado** |
| (livre) | 4 | 32 | igual | reservado pelo U-Boot |
| `reserved` | 36 | 64 | igual | MPT, chaves do fabricante e DTB; **identidade própria de cada box** |
| `cache` | 108 | **64** | 108 / 512 | só logs do recovery e comandos de atualização (encolhido para dar espaço aos dados) |
| `env` | 180 | 8 | 628 | variáveis do U-Boot do próprio box |
| `logo` | 196 | 32 | 644 | imagem de abertura |
| `recovery` | 236 | 32 | 684 | **o instalador de rede** |
| `rsv` | 276 | 8 | 724 | dados persistentes do CompSTEAM (configuração, redes Wi-Fi), sem sistema de arquivos |
| `tee` | 292 | 8 | 740 | área do ambiente seguro de fábrica |
| `crypt` | 308 | 32 | 756 | agente do inventário (atualizável sem reinstalar) |
| `misc` | 348 | 32 | 796 | comando de boot (zerado = nenhum) |
| `boot` | 388 | 32 | 836 | kernel e DTB do sistema |
| `system` | 428 | **1580** | 876 / 2048 | raiz do sistema (Android: `/system`) |
| `vendor` | 2016 | 320 | (nova) | Android: `/vendor` |
| `odm` | 2344 | 128 | (nova) | Android: `/odm` |
| `dtbo` | 2480 | 8 | (nova) | Android: sobreposições do DTB |
| `metadata` | 2496 | 16 | (nova) | Android: metadados de criptografia |
| `data` | 2520 | **4936** | 2932 / 4524 | Android: dados do usuário; nas variações de Linux gráficas, parte da raiz |

Até `boot` as partições mantêm a ordem e os tamanhos de fábrica; os offsets mudam porque o `cache` encolheu de 512 para 64 MiB,
o que deu 448 MiB a mais para os dados.

### Diagrama para figura (eixo da eMMC, fora de escala)

```
0        36       108   180 196 236 276 292 308 348 388  428                                   2520                          7456 MiB
|--boot--|-reserved-|cache|env|logo|recov|rsv|tee|crypt|misc|boot|----- system -----|vendor|odm|dtbo|meta|--------- data ---------|
 loader   MPT+DTB+   64    8  32   32   8   8   32   32   32   1580 MiB            320  128   8   16        4936 MiB
 (nunca)  chaves
 (só o DTB com o nó partitions trocado; chaves nunca)
```

Grupos de cores sugeridos: **nunca gravar** (`bootloader`, chaves da `reserved`); **identidade e dados do box** (`reserved`, `env`,
`logo`, `rsv`, `crypt`); **instalador** (`recovery`); **sistema** (`boot`, `system`, `vendor`, `odm`, `dtbo`, `metadata`, `data`).

## O que nunca é gravado

- A partição **`bootloader`**: com ela corrompida o box deixa de ligar e só se recupera com técnicas de bancada.
- A **área de chaves da `reserved`** (por volta de +16 KiB e uma cópia em +272 KiB dentro da partição): chaves e dados únicos do box.
- A `reserved` **inteira**: o instalador grava nela apenas a MPT (no início) e o DTB (duas cópias, em +4 MiB e +4,25 MiB).

Toda gravação é conferida: o instalador lê de volta e compara o SHA-256 de cada partição com o do manifesto.

### A `reserved` e o DTB de fábrica

O U-Boot de fábrica lê o DTB da `reserved` e dele tira muito mais do que as partições (endereço do logo, parâmetros do vídeo; ver
[dtb-e-drivers.md](dtb-e-drivers.md)). Por isso a regra é:

> o DTB gravado na `reserved` é o **DTB de fábrica com apenas o nó `partitions` trocado**.

O kernel do CompSTEAM recebe o DTB próprio dentro do `boot.img` e lê as partições pela MPT, então não precisa dele na `reserved`.
Como a MPT e o nó `partitions` saem da mesma fonte, concordam sempre.

## Perfis de volume das variações de Linux (dm-linear)

Uma variação de Linux (imagem pronta de sistema Linux) precisa de uma raiz maior que a partição `system` (1580 MiB), mas a MPT não
pode mudar (outros sistemas e o instalador dependem dela). A solução é o **dm-linear**, do próprio kernel Linux: um volume
virtual que junta várias partições seguidas e aparece como um disco só. O instalador grava a imagem em pedaços, um por partição.

| Perfil | Raiz formada por | Tamanho da raiz | `/home` | Usado em |
|---|---|---:|---|---|
| **5a** | `system` + `vendor` + `odm` + `dtbo` + `metadata` | 2052 MiB | a partição `data` | variações de linha de comando (Alpine, Debian) |
| **5b** | as seis: 5a + `data` | 6988 MiB | dentro da raiz | variações gráficas e Educação |
| **5c** | as cinco do 5a + o começo da `data` | 4096 MiB | o fim da `data` (2892 MiB) | previsto; ainda não publicado |

Tabela do perfil 5b (cada linha vira uma linha `linear` do device-mapper; setores de 512 bytes):

| Segmento | Início no volume | Tamanho | Posição na eMMC | Linha dm |
|---|---:|---:|---:|---|
| `system` | 0 | 1580 MiB | 428 MiB | `0 3235840 linear <system> 0` |
| `vendor` | 1580 MiB | 320 MiB | 2016 MiB | `3235840 655360 linear <vendor> 0` |
| `odm` | 1900 MiB | 128 MiB | 2344 MiB | `3891200 262144 linear <odm> 0` |
| `dtbo` | 2028 MiB | 8 MiB | 2480 MiB | `4153344 16384 linear <dtbo> 0` |
| `metadata` | 2036 MiB | 16 MiB | 2496 MiB | `4169728 32768 linear <metadata> 0` |
| `data` | 2052 MiB | 4936 MiB | 2520 MiB | `4202496 10108928 linear <data> 0` |

O perfil 5a usa só as cinco primeiras linhas; o 5c usa a sexta com 2044 MiB. O perfil que a imagem usa vem do parâmetro de boot
`compsteam.raiz=` do `boot.img`. A imagem pode ser menor que o volume (o sistema de arquivos ext4 cresce no primeiro boot).

Cuidado conhecido: sair de uma variação com raiz grande para uma variação clássica por "Atualizar" pode reformatar a partição
de dados; por isso o instalador só oferece **"Instalação limpa"** quando o arranjo do disco muda (ver [como-instalar.md](como-instalar.md)).

## MXQ Pro: a NAND em resumo

A NAND do RK3229 é acessada por uma camada de tradução (FTL) que o U-Boot de fábrica e o parâmetro de fábrica definem.
O CompSTEAM **não mexe** em `uboot`, `trust`, `baseparamer` e no parâmetro. Os nomes das partições são rótulos do lado do Linux; offsets e
tamanhos são os de fábrica.

| Partição | Tamanho | Uso no CompSTEAM |
|---|---:|---|
| `uboot`, `trust`, `baseparamer` | 4 MiB, 8 MiB, 1 MiB | de fábrica; não gravadas |
| `misc` | 4 MiB | comando de boot |
| `resource` | 15 MiB | DTB e logo do CompSTEAM |
| `kernel` | 12 MiB | kernel Linux 6.12 |
| `boot` | 12 MiB | initramfs que monta a raiz |
| `instalador` (era `recovery`) | 32 MiB | o instalador de rede |
| `agente` (era `backup`) | 64 MiB | agente do inventário |
| `cache` | 128 MiB | livre |
| `config` (era `metadata`) | 16 MiB | identidade, configuração e redes Wi-Fi |
| `kpanic` | 4 MiB | livre |
| `reserva` (era `system`) | 3 GiB | `/home` (dados do usuário) |
| `sistema` (era `userdata`) | o restante | raiz do sistema |

No MXQ não há perfis de volume: a raiz é uma partição só e o `/home` é outra.

No novo desenho aprovado em 2026-11-03, o `/home` (partição 13, `reserva`) passa de 3 GiB para **1536 MiB** e a raiz (partição 14, `sistema`) fica com **o restante** da NAND. A variação Educação do MXQ precisa deste desenho e está em teste.

## BTV11: a eMMC em resumo

A eMMC de 16 GB (14,6 GiB) mantém as áreas de fábrica (bootloader, `reserved` com MPT, chaves e DTB, e o `env` do U-Boot). Depois delas o Linux usa duas partições comuns:

| Partição | Início | Tamanho | Uso |
|---|---:|---:|---|
| p1 (FAT32, `BOOT_EMMC`) | 117 MiB | 255 MiB | kernel, DTB, initramfs, script de boot |
| p2 (ext4) | 373 MiB | até o fim | raiz do sistema |
| p3 (decidida) | fim da eMMC | 40 MiB | identidade e agente do inventário (`rsv` 8 MiB + `crypt` 32 MiB); entra com a próxima versão |

O bootloader de fábrica nunca é gravado. Estes valores são um esquema; nada aqui é para gravar à mão.
