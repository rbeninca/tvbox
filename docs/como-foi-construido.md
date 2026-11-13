# Como o CompSTEAM é composto

Visão geral, sem código-fonte nem método de engenharia. Quatro partes: o **Android TV**, as **variações de Linux** (imagens prontas
com conjuntos diferentes de programas; também chamadas de "spins"), o **instalador de rede** e o **agente do inventário**.

## Princípio de projeto

O U-Boot de fábrica **nunca é regravado**. Assim o modo USB do fabricante, a rede de segurança, continua vivo: um box com sistema
quebrado volta a ser gravável. Todo sistema novo é testado **pela RAM**, via USB, antes de gravar (ver [particoes.md](particoes.md)).

## 1. Android TV: CompSTEAM TV

- Base: **LineageOS 22.2** (Android 15), versão para TV, para a placa P281.
- Inclui Wi-Fi, display frontal, logo de abertura e apps do projeto.
- Não é ROM oficial do LineageOS nem tem vínculo com o projeto.

## 2. Variações de Linux

- Base **Debian 13**.
- Em todas: Docker, Wi-Fi, controle IR, áudio, display frontal, git, vim e htop.
- Variações: Linux texto (linha de comando) e Linux Gráfico (labwc e Chromium), com o kit opcional
  **Educação** (blocos/TurboWarp, GeoGebra offline, Arduino IDE, Thonny, LibreOffice, GCompris, SQLite). Detalhes em
  [sistemas.md](sistemas.md).
- Cada variação passa por verificação de drivers e serviços antes de publicada.

## 3. Instalador de rede

Programa que roda no box a partir do cartão ou da partição de recuperação (reset pressionado) e mostra a lista de sistemas na TV
(aceita controle IR, teclado e mouse USB).

**Segurança e integridade**
1. O catálogo e cada imagem são **assinados**; arquivo alterado é recusado. Por isso qualquer servidor pode distribuir as imagens.
2. Cada partição é conferida por **SHA-256** depois de baixada e de gravada.
3. **Nunca grava o `bootloader` nem a área de chaves** da `reserved`.
4. Num box de fábrica, antes de tudo, tenta guardar no cartão uma cópia da `reserved` (identidade única) na pasta
   `compsteam-reserved`; se não conseguir, avisa e instala assim mesmo.
5. Contagem de 10 segundos para desistir após a confirmação.

**Fontes de imagem:** cartão/pendrive, servidor local, espelho na nuvem e **releases do GitHub** `rbeninca/tvbox`. No perfil
público, o instalador envia ao painel só uma batida de presença, sem comandos remotos (`registro=nenhum` no `compsteam.conf`
desliga); se o painel não responder, usa o GitHub.

Imagens que exigem instalador mais novo aparecem como "precisa de instalador mais novo". No MXQ Pro o mesmo instalador roda da
partição `instalador`.

## 4. Agente do inventário

Programa único para Android e Linux, atualizável sem reinstalar o sistema, que informa ao painel o estado do box (identificação,
versão, temperatura, uso).

**Nas versões públicas:**
- a **telemetria vem ligada** (desde o instalador 1.2.47); quem não quiser a desliga no botão "Telemetria" do instalador ou com
  `telemetria=off` no `compsteam.conf`; desligada, o sistema não envia nada nem recebe comandos, e uma escolha anterior é mantida;
- com a telemetria ligada, só o dono do box envia comandos; atualizações vêm apenas das releases do GitHub;
- o identificador do box vem do número de série do chip, nunca do MAC.
