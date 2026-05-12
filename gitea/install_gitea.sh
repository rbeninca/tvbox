#!/bin/bash

# Script para instalação automatizada do Gitea no TV Box Armbian
# Focado em economia de recursos e armazenamento em pendrive externo.

set -e

# Configurações
USB_DEV="/dev/sda1"
MOUNT_POINT="/mnt/pendrive"
GITEA_DATA="$MOUNT_POINT/gitea-data"
DOCKER_DIR="$HOME/gitea-docker"

echo "--- Iniciando Instalação do Gitea ---"

# 1. Montagem do Pendrive
echo "Configurando Pendrive..."
sudo mkdir -p $MOUNT_POINT
if ! mount | grep -q $MOUNT_POINT; then
    sudo mount $USB_DEV $MOUNT_POINT
fi

# Adicionar ao fstab se não existir
if ! grep -q $MOUNT_POINT /etc/fstab; then
    echo "$USB_DEV $MOUNT_POINT ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
    echo "Pendrive adicionado ao /etc/fstab para montagem automática."
fi

# 2. Preparar Pastas
echo "Preparando diretórios..."
sudo mkdir -p $GITEA_DATA
sudo chown -R 1000:1000 $GITEA_DATA
mkdir -p $DOCKER_DIR

# 3. Criar Docker Compose
echo "Gerando docker-compose.yml..."
cat <<EOF > $DOCKER_DIR/docker-compose.yml
services:
  server:
    image: gitea/gitea:1.21
    container_name: gitea
    restart: always
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - GITEA__database__DB_TYPE=sqlite3
    volumes:
      - $GITEA_DATA:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "3000:3000"
      - "2222:22"
EOF

# 4. Iniciar Container
echo "Iniciando Gitea via Docker Compose..."
cd $DOCKER_DIR
docker compose up -d

echo "--- Instalação Concluída ---"
echo "Acesse: http://$(hostname -I | awk '{print $1}'):3000"
echo "Lembre-se de usar caminhos iniciando com /data na configuração web."
