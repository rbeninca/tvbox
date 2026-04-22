# Editado em: 2026-04-21 10:32:03
# Procedimento de Atualização de Kernel - TX9 Pro (Armbian)

Este documento descreve o processo de atualização do kernel na TV Box TX9 Pro (Amlogic S905W/X), garantindo a persistência e funcionalidade do driver de Wi-Fi **SSV6051**.

---

## 1. Visão Geral
A atualização foi realizada do kernel **6.18.21** para o **6.18.23-current-meson64** (versão estável mais recente do repositório beta Armbian Noble). 

O maior desafio em kernels mainline para o TX9 é a compilação de drivers externos (out-of-tree), que exige cabeçalhos de kernel perfeitamente alinhados com a string de versão do kernel em execução.

---

## 2. Preparação e Sincronização
Antes de iniciar, certifique-se de que o código-fonte do driver está disponível localmente no computador e sincronizado com a TV Box.

```bash
# No computador local, envie a pasta de drivers para o root da TV Box
sshpass -p 'aluno123' rsync -avz ssv6051-driver/ root@192.168.1.106:/root/ssv6051-driver/
```

---

## 3. Atualização do Kernel
Execute a atualização dos pacotes e instale a imagem e os headers correspondentes.

```bash
# Na TV Box
apt update
apt install -y linux-image-current-meson64 linux-headers-current-meson64
```

**Nota:** O Armbian geralmente instala a versão mais recente disponível no branch (neste caso, a .23 substituiu a .22 solicitada por ser a correção imediata de segurança/estabilidade).

---

## 4. Reinicialização e Verificação
Após a instalação, é obrigatório reiniciar para carregar o novo kernel.

```bash
reboot
# Após o retorno, verifique a versão ativa:
uname -r  # Deve retornar 6.18.23-current-meson64
```

---

## 5. Correção do "Version Magic" (Headers)
Para que o driver compilado seja aceito pelo kernel (`insmod`), os cabeçalhos precisam ter exatamente a mesma string de versão. O processo padrão do Armbian às vezes omite o sufixo no arquivo de configuração.

```bash
# Definir a versão alvo
KVER=$(uname -r)
HDIR="/usr/src/linux-headers-$KVER"

# Ajustar o EXTRAVERSION no Makefile dos headers
sed -i 's/^EXTRAVERSION =.*/EXTRAVERSION = -current-meson64/' $HDIR/Makefile

# Forçar a geração correta do utsrelease.h
echo "#define UTS_RELEASE \"$KVER\"" > $HDIR/include/generated/utsrelease.h
```

---

## 6. Reconstrução do Driver Wi-Fi (SSV6051)
Utilize o script `rebuild_wifi_v3.sh` que automatiza a compilação contra os headers corrigidos.

```bash
bash /root/ssv6051-driver/rebuild_wifi_v3.sh
```

**O que este script faz:**
1. Valida a existência dos headers.
2. Entra na pasta `/root/ssv6051-driver/6051/ssv6xxx`.
3. Executa `make clean`.
4. Compila o módulo `ssv6051.ko`.
5. Move o binário para `/lib/modules/$(uname -r)/kernel/drivers/net/wireless/ssv6051/`.
6. Executa `depmod -a` e `modprobe ssv6051`.

---

## 7. Persistência e Estabilidade do Wi-Fi (Pós-Reboot)
O chip **SSV6051** é sensível e exige que o firmware e o driver estejam configurados corretamente no sistema para que a conexão suba automaticamente após o reboot.

### A. Instalação de Firmware e Configuração
O driver busca os arquivos de suporte em `/lib/firmware/`. Se não estiverem lá, o Wi-Fi falhará ao inicializar.

```bash
# Copiar firmware e configuração para o diretório do sistema
cp /root/ssv6051-driver/6051/ssv6xxx/ssv6051-wifi.cfg /lib/firmware/ssv6051-wifi.cfg
cp /root/ssv6051-driver/6051/ssv6xxx/ssv6051-sw.bin /lib/firmware/ssv6051-sw.bin
```

### B. Carregamento Automático do Módulo
Para evitar que o NetworkManager tente configurar a rede antes do driver estar pronto, force o carregamento do módulo no boot:

```bash
echo 'ssv6051' > /etc/modules-load.d/ssv6051.conf
```

### C. Desativação do Power Management (Estabilidade)
O modo de economia de energia (`power_save`) causa quedas constantes no chip SSV. Criamos um script no dispatcher do NetworkManager para desativá-lo automaticamente sempre que a interface `wlan0` subir.

```bash
cat <<EOF > /etc/NetworkManager/dispatcher.d/99-ssv6051-fix
#!/bin/sh
INTERFACE=\$1
ACTION=\$2

if [ "\$INTERFACE" = "wlan0" ] && [ "\$ACTION" = "up" ]; then
    /usr/sbin/iw dev wlan0 set power_save off
fi
EOF

# Dar permissão de execução
chmod +x /etc/NetworkManager/dispatcher.d/99-ssv6051-fix
```

### D. Configuração da Rede Wi-Fi
Para conectar a uma rede específica e garantir a reconexão automática:

```bash
# Escanear redes
nmcli device wifi rescan

# Conectar (Substitua SSID e PASSWORD pelos seus dados)
nmcli device wifi connect 'NOME_DA_REDE' password 'SENHA_AQUI'

# Garantir autoconnect
nmcli connection modify 'NOME_DA_REDE' connection.autoconnect yes
```

---

## 8. Validação Final
Após seguir todos os passos, execute um reboot e valide:

1. **Kernel:** `uname -r` deve mostrar a versão atualizada.
2. **Módulo:** `lsmod | grep ssv6051` deve mostrar o driver carregado.
3. **Rede:** `ip addr show wlan0` deve mostrar um IP atribuído.
4. **Estabilidade:** `iw dev wlan0 get power_save` deve retornar `Power save: off`.

---

## 9. Reprodutibilidade (Resumo de Comandos)
Para replicar em uma nova unidade TX9 com os arquivos desta pasta:

```bash
# 1. Instalar headers
apt install -y linux-headers-current-meson64

# 2. Corrigir Version Magic nos headers
KVER=$(uname -r)
HDIR="/usr/src/linux-headers-$KVER"
sed -i "s/^EXTRAVERSION =.*/EXTRAVERSION = -current-meson64/" $HDIR/Makefile
echo "#define UTS_RELEASE \"$KVER\"" > $HDIR/include/generated/utsrelease.h

# 3. Compilar e Instalar Driver
bash /root/ssv6051-driver/rebuild_wifi_v3.sh

# 4. Configurar Persistência (Passos A, B e C da seção 7)
# ... (comandos de cópia de firmware e dispatcher)
```
