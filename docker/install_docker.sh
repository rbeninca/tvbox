#!/usr/bin/env bash
set -Eeuo pipefail

echo "==> Detectando arquitetura e sistema"
ARCH="$(dpkg --print-architecture)"
CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"

echo "Arquitetura: ${ARCH}"
echo "Codename: ${CODENAME}"

if [[ "$EUID" -ne 0 ]]; then
  echo "Execute como root: sudo bash instalar-docker.sh"
  exit 1
fi

if [[ "$ARCH" != "arm64" && "$ARCH" != "armhf" && "$ARCH" != "amd64" ]]; then
  echo "Arquitetura não testada neste script: $ARCH"
  echo "As oficiais mais comuns aqui são arm64, armhf e amd64."
  exit 1
fi

if [[ -z "$CODENAME" ]]; then
  echo "Não foi possível detectar o codename da distribuição."
  exit 1
fi

echo "==> Removendo pacotes conflitantes antigos, se existirem"
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
  apt-get remove -y "$pkg" >/dev/null 2>&1 || true
done

echo "==> Atualizando índices e instalando dependências"
apt-get update
apt-get install -y ca-certificates curl gnupg

echo "==> Criando diretório da chave GPG"
install -m 0755 -d /etc/apt/keyrings

echo "==> Baixando chave oficial da Docker"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "==> Configurando repositório oficial da Docker"
cat >/etc/apt/sources.list.d/docker.list <<EOF
deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${CODENAME} stable
EOF

echo "==> Instalando Docker Engine + CLI + containerd + plugins"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "==> Habilitando e iniciando serviço"
systemctl enable docker
systemctl restart docker

echo "==> Testando instalação"
docker --version
docker compose version || true
systemctl --no-pager --full status docker | sed -n '1,12p'

echo
echo "==> Teste opcional"
echo "Execute depois:"
echo "  docker run hello-world"
echo
echo "==> Para usar docker sem sudo com seu usuário normal:"
echo "  sudo usermod -aG docker \$SUDO_USER"
echo "Depois saia e entre de novo na sessão."