# Gerenciador de Hotspot TX9

Este diretório contém ferramentas para gerenciar conexões Wi-Fi e criar Pontos de Acesso (Hotspot) no TV Box TX9.

## Scripts

### `manage_hotspot.sh`
Um script interativo que permite:
1.  **Listar Interfaces:** Mostra todas as interfaces Wi-Fi detectadas no sistema.
2.  **Teste de Velocidade:** Realiza um teste de download simples em uma interface selecionada para verificar a qualidade do link.
3.  **Criar Hotspot:** Configura um Ponto de Acesso Wi-Fi usando `nmcli`.
4.  **Conectar Wi-Fi:** Conecta o TX9 a uma rede Wi-Fi existente (modo cliente).
5.  **Gerenciar Conexões:** Desconecta interfaces ou remove configurações de hotspot.

## Como usar

1.  Dê permissão de execução ao script:
    ```bash
    chmod +x manage_hotspot.sh
    ```
2.  Execute como root:
    ```bash
    sudo ./manage_hotspot.sh
    ```

## Requisitos
- `NetworkManager` (`nmcli`)
- `curl` (para o teste de velocidade)
- `iw` (para detecção avançada de capacidades)

## Nota sobre o Driver ssv6051
Se você estiver usando o Wi-Fi interno do TX9 (driver `ssv6051`), certifique-se de que o modo AP foi habilitado previamente usando o script na pasta `ssv6051-driver`, pois esse driver requer patches específicos no kernel para suportar o modo Ponto de Acesso.
