# IDEIA
Configurar um tvbox tx9  com Android 7, para rodar armbian, usando o sistema operacional Armbian , com a imagem Armbian_community_26.2.0-trunk.703_Aml-s9xx-box_noble_current_6.18.21_xfce_desktop.img

## Passo 1: Preparar o ambiente
1. Baixe a imagem do Armbian para o seu dispositivo TV Box TX9:
- Acesse o site oficial do Armbian e baixe a imagem correspondente ao seu dispositivo

2. Prepare um cartão SD ou um pendrive com pelo menos 8GB de espaço para armazenar a imagem do Armbian.
## Passo 2: Gravar a imagem no cartão SD ou pendrive
1. Use um software de gravação de imagem como o Balena Etcher ou o Rufus para gravar a imagem do Armbian no cartão SD ou pendrive. Aqui no tutorial vou usar dd no Linux:
```bash
sudo dd if=Armbian_community_26.2.0-trunk.703_Aml-s9xx-box_noble_current_6.18.21_xfce_desktop.img of=/dev/sda bs=4M status=progress conv=fsync
```

## Passo 3: Configurar o dtb para o TV Box TX9

arquivo configuraçao_sdcard.md

1. Após gravar a imagem, acesse a partição de boot do cartão SD ou pendrive e localize o arquivo dtb correspondente ao seu dispositivo TV Box TX9. O arquivo dtb é responsável por fornecer informações de hardware para o sistema operacional.
2. Copie o arquivo dtb correto para a partição de boot do cartão SD ou pendrive, substituindo o arquivo dtb existente, se necessário. Certifique-se de que o arquivo dtb seja compatível com o seu modelo específico de TV Box TX9 para garantir que o

## Passo 4: Configurar o Armbian
Ao iniciar o Armbian pela primeira vez, siga as instruções na tela para configurar o sistema, incluindo a criação de um usuário e senha.
usuario root sugerido senha aluno123


## Passo 5: Instalar o armbian na memória interna do TV Box TX9
1. Após configurar o Armbian, abra um terminal e execute o seguinte comando para instalar
```bash
sudo armbian-install
```








