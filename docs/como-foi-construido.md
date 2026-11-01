# Como o CompSTEAM foi construído

Visão de engenharia, sem código-fonte. O CompSTEAM tem quatro partes: o **Android TV**, as **variações de Linux** (imagens
prontas do sistema com conjuntos diferentes de programas; no projeto também chamadas de "spins"), o **instalador de rede** e o
**agente do inventário**.

## Princípio de projeto

O U-Boot de fábrica **nunca é regravado**. Isso mantém sempre vivo o modo USB do fabricante, que é a rede de segurança: um box
com sistema quebrado volta a ser gravável. Tudo o que o CompSTEAM faz acontece "atrás" dele: tabela de partições (MPT) e DTB na
`reserved`, e o resto nas partições seguintes (ver [particoes.md](particoes.md)). Todo sistema novo é testado **pela RAM**, via USB,
antes de qualquer gravação.

## 1. Android TV: CompSTEAM TV

- Base: **LineageOS 22.2** (Android 15), versão para TV, **userspace de 32 bits**, kernel Linux 4.9 da Amlogic.
- Compilado num **contêiner Docker** (imagem própria com o ambiente de build do Android), o que torna o processo repetível em
  outro PC. Build incremental leva cerca de 10 minutos; o completo, cerca de 7 horas.
- Árvore de dispositivo própria para a placa P281, com as partições do [particoes.md](particoes.md) (`system`, `vendor`, `odm`,
  `dtbo`, `metadata`, `data`, tamanhos ajustados).
- Itens próprios: driver Wi-Fi SSV6051 portado, display frontal (hora, IP, ícones, percentual de boot), logo no U-Boot, aplicativo de
  sistema para hotspot e ponte com o agente, USB automático para aplicativos do projeto, início de aplicativos no boot.
- Não é uma ROM oficial do LineageOS nem tem vínculo com o projeto.

## 2. Variações de Linux

- **Raiz Debian 13 montada no PC** (e Alpine para a variação mínima): o sistema de arquivos é preparado numa máquina de
  desenvolvimento, com pacotes, serviços e configurações, e depois cortado em imagens por partição.
- **Kernel 6.12 do próprio Debian** no TX9, com o DTB mainline da P281 do projeto (ver [dtb-e-drivers.md](dtb-e-drivers.md)).
- **Perfis de volume** (5a, 5b, 5c): a raiz pode juntar várias partições da MPT com o dm-linear do kernel (ver
  [particoes.md](particoes.md)). Variações de linha de comando usam o 5a; as gráficas e a Educação usam o 5b.
- Em todas: Docker, Wi-Fi, controle IR, áudio, display frontal, git, vim e htop; os comandos `compsteam-*` cuidam de partições,
  painel frontal e inventário.
- Variações: Alpine (mínimo), Debian (linha de comando), Debian com Weston e Chromium (Linux Gráfico), Debian com área de
  trabalho labwc (Área de Trabalho) e **CompSTEAM Educação** (blocos/TurboWarp, GeoGebra offline, Arduino IDE, Thonny, LibreOffice,
  GCompris, SQLite). Detalhes em [sistemas.md](sistemas.md). O Ubuntu foi deixado de lado no TX9.
- Cada variação passa por uma verificação automática de drivers e serviços (Wi-Fi, IR, display, áudio, Docker) antes de ser
  publicada.

## 3. Instalador de rede

Um **programa único, escrito em Go**, que roda no box e no PC (servidor, publicação e verificação).

**No box.** Com o reset pressionado, o U-Boot de fábrica carrega o kernel e o initramfs do instalador: um **Linux mínimo** (Alpine)
guardado na partição `recovery` (ou o `recovery.img` de um cartão). O programa desenha a interface direto no framebuffer (aceita
controle IR, teclado e mouse USB), pega a rede, procura as fontes de imagem, mostra a lista de sistemas e grava.

**Segurança e integridade**
1. O catálogo e cada manifesto (lista de partições de uma imagem, com tamanhos e somas) são **assinados com Ed25519**; a chave
   pública vai embutida no instalador. Arquivo alterado é recusado. Por isso **qualquer servidor pode distribuir as imagens**,
   mesmo não confiável.
2. Cada partição é baixada, descomprimida (zstd), conferida por **SHA-256**, gravada e **relida da memória** para nova conferência.
   Peças críticas (como `boot`) são preparadas na RAM, conferidas e gravadas por último, para que uma queda de energia não deixe
   um sistema meio gravado parecendo válido.
3. O instalador **nunca grava o `bootloader` nem a área de chaves** da `reserved`.
4. Num box de fábrica, antes de tudo, guarda no cartão uma cópia da `reserved` (identidade única do box) na pasta
   `compsteam-reserved`; sem essa cópia nada é gravado.
5. Contagem de 10 segundos para desistir após a confirmação.

**Fontes de imagem.** Procuradas em paralelo: cartão/pendrive; servidor local na rede (descoberta por UDP); espelho na nuvem;
**releases do GitHub** `rbeninca/tvbox`. No perfil público, o instalador avisa o painel do projeto que o box está ligado (uma
batida de presença, sem comandos remotos; `registro=nenhum` no `compsteam.conf` desliga isso) e, se o painel não responder em
alguns segundos, usa direto o GitHub.

**Contrato com as imagens.** O manifesto declara o que a imagem precisa (`requer`, versão mínima do instalador, perfil de
volume); instaladores antigos recusam o que não entendem e a lista indica "precisa de instalador mais novo". Quando a troca
de sistema muda o arranjo do disco, só a "Instalação limpa" é oferecida.

Também no MXQ Pro, o mesmo instalador roda (a partir da partição `instalador`) e pode ser acionado pelo painel, sem ninguém
na frente do box.

## 4. Agente do inventário

Programa em Go, único para Android e Linux, instalado na partição `crypt` (TX9) ou `agente` (MXQ Pro), atualizável sem
reinstalar o sistema. Informa ao painel do projeto o estado do box (identificação, versão, temperatura, uso) e, nas versões
internas, aceita comandos remotos.

**Nas versões públicas:**
- a **telemetria vem desligada** e só liga com o consentimento de quem está no box: o botão "Telemetria" do instalador mostra um
  QR para a pessoa entrar com a conta Google e confirmar que entendeu o que é enviado; sem isso, o sistema instalado não envia
  nada e não recebe comandos;
- com a telemetria ligada, só o dono do box (quem consentiu) envia comandos; atualizações vêm apenas das releases do GitHub;
- o identificador do box vem do número de série do chip, nunca do MAC.
