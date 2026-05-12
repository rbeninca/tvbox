# Gitea no TV Box (Armbian) com Armazenamento Externo

Este projeto descreve a configuração de um servidor Git (Gitea) rodando em um TV Box TX9 Pro com Armbian, utilizando Docker e um pendrive externo para armazenamento dos repositórios.

## 🛠️ Preparação do Ambiente

1.  **Preparação do TV Box:**
    *   formtação de um pendrive USB com sistema de arquivos **EXT4** e label `repositorio`.
    *   Identificação do pendrive USB (`/dev/sda1`) com sistema de arquivos **EXT4** e label `repositorio`.
2.  **Configuração de Armazenamento:**
    *   Criação do ponto de montagem em `/mnt/pendrive`.
    *   Configuração do `/etc/fstab` para montagem automática no boot.
    *   Ajuste de permissões para o usuário Docker (UID 1000).
3.  **Deploy com Docker Compose:**
    *   Instalação do Gitea utilizando a imagem oficial `gitea/gitea:1.21`.
    *   Mapeamento de portas: `3000` (HTTP) e `2222` (SSH).
    *   Volume de dados mapeado diretamente para o pendrive (`/mnt/pendrive/gitea-data`).

## 📁 Estrutura de Pastas

*   `~/gitea-docker/docker-compose.yml`: Arquivo de orquestração do container.
*   `/mnt/pendrive/gitea-data`: Pasta no pendrive onde todos os dados e repositórios residem.

## 🚀 Como gerenciar

### Iniciar o servidor
```bash
cd ~/gitea-docker
docker compose up -d
```

### Parar o servidor
```bash
cd ~/gitea-docker
docker compose down
```

### Verificar Logs
```bash
docker logs -f gitea
```

## 📝 Notas de Configuração (Interface Web)

Ao configurar o Gitea pela primeira vez na interface web (`http://gitea:3000`):

*   **Raiz do Repositório:** `/data/git/repositories`
*   **Banco de Dados:** SQLite3 (`/data/gitea/gitea.db`)
*   **Porta SSH:** `2222`
*   **Domínio:** nome ou IP do servidor (ex: `gitea.local`)

---
