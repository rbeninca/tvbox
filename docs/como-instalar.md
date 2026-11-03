# Como instalar um sistema CompSTEAM num TX9

Instalador público, versão **1.2.45** (release [`instalador-tx9-1.2.45`](https://github.com/rbeninca/tvbox/releases/tag/instalador-tx9-1.2.45)).
Serve para o **TX9 com SoC Amlogic S905W (placa P281)**. Você não baixa as imagens dos sistemas à mão: o instalador baixa
sozinho a que você escolher.

## O que você precisa

- Um TX9 (ver [hardware.md](hardware.md)).
- Um cartão microSD ou pendrive **formatado em FAT32**, que não esteja protegido contra escrita.
- Cabo de **rede (Ethernet) com internet**, e TV ligada pelo HDMI.
- Um palito ou clipe para apertar o botão reset (no fundo do box).
- Controle remoto do box, ou teclado e mouse USB.

## Passo a passo

1. **Baixe o zip** `instalador-publico-tx9-1.2.45.zip` na página da release acima.
   SHA-256: `c36acc1dc37b0d23e8eb46833b297816f708ba7d1ac4f6e464db979f6ce838a6` (confira, se quiser).
2. **Descompacte TODOS os arquivos na raiz** do cartão/pendrive (sem criar pasta). Não deixe nele os arquivos `aml_autoscript`
   nem `aml_sdc_burn.ini`.
3. (Opcional) Edite o `compsteam.conf` do cartão com um editor de texto (ver abaixo).
4. Com o box **desligado**: ligue o cabo de rede, a TV no HDMI e coloque o cartão/pendrive no box.
5. **Segure o botão reset** com o palito e **ligue** o box (conecte a fonte). Solte depois de cerca de 5 segundos.
6. A TV mostra a lista de sistemas. Escolha com o controle, teclado ou mouse e confirme.

   ![Lista de sistemas do instalador](../imgs/compsteam/instalador-lista-de-sistemas.png)

7. Se o box já tem um sistema CompSTEAM, aparece **"O que fazer?"**:
   - **Atualizar**: troca o sistema (programas instalados e configurações são apagados; a pasta `/dados` é mantida);
   - **Instalação limpa**: apaga tudo.

   ![Atualizar ou instalação limpa](../imgs/compsteam/instalador-atualizar-ou-limpa.png)

   Quando a troca de sistema **muda o arranjo do disco** (por exemplo de uma variação de linha de comando para o CompSTEAM
   Educação, que usa a memória toda), o instalador só oferece a **"Instalação limpa"**.
8. **10 segundos para desistir.** Depois da confirmação há uma contagem; **Voltar / Esc** ou **Cancelar** desiste sem gravar nada.
   Passado o tempo, a instalação **grava a memória do box**.

   ![Contagem de 10 segundos](../imgs/compsteam/instalador-contagem-antes-de-gravar.png)

9. **Não desligue nem mexa no box durante a gravação.** A tela mostra o progresso por partição; leva de poucos minutos a cerca
   de 20 minutos, conforme o sistema e a rede (o Mínimo, cerca de 2 minutos; o Educação, de 17 a 21 minutos na rede local). O box reinicia sozinho no sistema novo.

   ![Progresso da gravação](../imgs/compsteam/instalador-progresso-gravacao.png)

10. **Tire o cartão/pendrive depois de instalar.** Com o cartão no box, o instalador do cartão é sempre o que abre.

## Box de fábrica: guarde a pasta `compsteam-reserved`

Num box que ainda tem o sistema de fábrica, antes de gravar, o instalador **copia para o cartão a pasta `compsteam-reserved`**:
é a cópia da identidade do box (a partição `reserved`, única de cada aparelho). **Guarde essa pasta.** O cartão não pode estar
protegido contra escrita; sem a cópia, **nada é gravado**.

## Depois da instalação

- **Reset sem cartão** abre o **instalador guardado no próprio box** (partição `recovery`), que também baixa as imagens do
  GitHub. Assim você pode trocar de sistema depois sem cartão.
- Todo o conteúdo baixado é conferido pela assinatura do CompSTEAM; um arquivo alterado é recusado.

## O arquivo `compsteam.conf`

Texto simples; `#` começa um comentário. Padrão da versão pública:

```
fonte=github:rbeninca/tvbox   # de onde baixar as imagens (releases do GitHub)
telemetria=off                # o sistema instalado não envia nada ao painel
registro=instalacao           # só a "batida" de presença no instalador; nenhum = nem isso
# catalogo=publico            # limita a lista às imagens públicas e às do cartão
# wifi_rede=...               # (opcional) rede Wi-Fi para o instalador
```

Telemetria: o botão **Telemetria**, no rodapé do instalador, explica o que seria enviado; ela só liga com o seu consentimento
(QR na TV e login com a conta Google). `telemetria=sem_agente` instala o sistema sem o agente do inventário.

## Se algo der errado

- A TV fica sem imagem ou o instalador não abre: confira o cartão (FAT32, arquivos na raiz, sem `aml_autoscript`), e repita o reset.
- A lista vem vazia: confira a internet do cabo; o instalador tenta o GitHub alguns segundos depois da rede subir.
- A TV mostra "precisa de instalador mais novo" ao lado de um sistema: use o instalador 1.2.44 ou mais novo (por exemplo o do
  zip acima, no cartão).
- Um box travado, que nem liga: o modo USB do fabricante (que o CompSTEAM nunca apaga) continua disponível para recuperação por
  cabo com um PC; ver a documentação do projeto.

## MXQ Pro

As imagens do MXQ Pro estão listadas em [sistemas.md](sistemas.md). O zip `instalador-publico-tx9-1.2.45.zip` é só para o TX9;
o MXQ tem o seu: [instalador-mxq-1.2.45](https://github.com/rbeninca/tvbox/releases/tag/instalador-mxq-1.2.45)
(`instalador-publico-mxq-1.2.45.zip`).

1. Confira o `SHA256SUMS` e grave o arquivo `compsteam-mxq-publico-1.2.45.img` num cartão microSD de 1 GB ou mais
   (balenaEtcher, Raspberry Pi Imager ou `dd`). O cartão é apagado.
2. Se quiser, edite o `compsteam.conf` da unidade `COMPSTEAM` do cartão (telemetria, registro).
3. Box desligado, cabo de rede com internet, TV no HDMI. Ponha o cartão no slot microSD e ligue a fonte: o box sobe pelo cartão.
4. Escolha o sistema na TV e confirme. Há 10 s para desistir; depois a instalação grava a memória (NAND) do box.
5. No fim, tire o cartão e ligue o box de novo.

O Wi-Fi do instalador não vem configurado: use o cabo de rede.
