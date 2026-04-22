
  #Relatório de Configuração de Boot - TX9 Pro (Armbian)

  Este documento descreve as modificações realizadas na partição de boot do Armbian para garantir a compatibilidade
  com o hardware do TX9 Pro (Amlogic S905W/X - GXL).

  1. Resumo das Alterações
   * DTB Selecionado: meson-gxl-s905w-p281.dtb (Base padrão estável para clones S905W).
   * Configuração de Boot: Atualização do extlinux.conf para apontar para o novo DTB.
   * Bootloader: Criação do u-boot.ext para garantir a inicialização em dispositivos com scripts de boot antigos.
   * Compatibilidade Extra: Cópia do DTB para a raiz como dtb.img.

  2. Detalhes Técnicos
  O TX9 Pro utiliza a arquitetura Amlogic GXL. Embora o Armbian venha frequentemente configurado com o DTB p212
  (S905X), o modelo S905W responde melhor ao p281. Os LEDs e o display frontal exigem mapeamentos de GPIO específicos
  que são tratados via serviços no espaço do usuário (conforme documentado no seu Resumo.md), por isso a base p281 é a
  mais indicada para a estabilidade do sistema.

  3. Comandos para Execução Manual (Replicação)

  Caso precise preparar um novo cartão SD (/dev/sda), execute os seguintes comandos:

  Passo A: Montar as partições (se não estiverem montadas)

   1 # Criar pontos de montagem
   2 mkdir -p /mnt/boot
   3
   4 # Montar a partição de boot (sda1)
   5 mount /dev/sda1 /mnt/boot

  Passo B: Configurar o DTB no Extlinux
  Edite o arquivo de configuração para que o kernel carregue a árvore de dispositivos correta.

   1 # Substituir o DTB p212 pelo p281 (S905W)
   2 sed -i 's/meson-gxl-s905x-p212.dtb/meson-gxl-s905w-p281.dtb/' /mnt/boot/extlinux/extlinux.conf

  Passo C: Configurar o Bootloader (u-boot)
  Muitos boxes TX9 buscam o arquivo u-boot.ext na raiz da partição para iniciar o kernel mainline.

   1 # Copiar o binário compatível com S905W/X (GXL)
   2 cp /mnt/boot/u-boot-s905x-s912 /mnt/boot/u-boot.ext

  Passo D: Criar imagem de fallback do DTB
  Alguns firmwares de fábrica/scripts de transição buscam o arquivo dtb.img diretamente na raiz.

   1 # Criar cópia de segurança na raiz da partição de boot
   2 cp /mnt/boot/dtb/amlogic/meson-gxl-s905w-p281.dtb /mnt/boot/dtb.img

  4. Verificação Final
  Após executar os comandos, a estrutura de arquivos essencial deve ser:
   - /boot/extlinux/extlinux.conf -> Apontando para p281.dtb.
   - /boot/u-boot.ext -> Presente (binário GXL).
   - /boot/dtb.img -> Presente (cópia do p281).

  5. Próximos Passos recomendados
  Após o primeiro boot bem-sucedido:
   1. Rede: Execute o seu script network.sh para ajustar as métricas de Wi-Fi/Ethernet.
   2. Hardware: Execute o script TX9_PRO_SETUP_KIT/install_tx9.sh para ativar o driver de Wi-Fi SSV6051, o relógio
      frontal e os LEDs.
   3. Kernel: Note que o kernel atual é o 6.18.21-current-meson64. Se houver atualização de kernel, será necessário
      rodar o rebuild_wifi_v3.sh para recompilar o driver do Wi-Fi.

  ---
  Configuração aplicada em: terça-feira, 21 de abril de 2026.
