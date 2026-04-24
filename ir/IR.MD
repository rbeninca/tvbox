
# Documentação de Hardware: Infravermelho (IR) - TV Box TX9

Este documento detalha a pinagem e a configuração do receptor de infravermelho (IR) identificada a partir do dump do firmware original Android (S905W/GXL).

## 1. Origem da Informação (Fonte)
As informações foram extraídas do arquivo:
*   **Arquivo:** `tx9_pro_dump_android/extracted.dts`
*   **Modelo de Referência:** `gxl_p281_1g` (Amlogic S905W)

## 2. Configuração do Pino (Physical Layer)

O SoC Amlogic utiliza pinos dedicados para a função de controle remoto. No DTS original, o pino está mapeado sob o nó de controle de pinos (`pinctrl`).

### Trecho do DTS:
```dts
// Localizado por volta da linha 364
remote_pin {
    amlogic,setmask = <0x10 0x01>;
    amlogic,clrmask = <0x10 0x200000>;
    amlogic,pins = "GPIOAO_7";
    linux,phandle = <0x17>;
    phandle = <0x17>;
};
```

### Explicação:
*   **Pino Identificado:** `GPIOAO_7`.
*   **Função:** Este é o pino físico onde o sensor IR (receptor) está soldado na placa-mãe do TX9.
*   **GPIOAO (Always On):** Indica que o pino pertence ao domínio "Always On", o que permite que o controle remoto ligue a TV Box mesmo quando ela está em modo standby/suspend.

---

## 3. Dispositivo Receptor (Driver Layer)

O nó `rc@c8100580` define o hardware do receptor IR e como o sistema operacional deve interagir com ele.

### Trecho do DTS:
```dts
// Localizado por volta da linha 915
rc@c8100580 {
    compatible = "amlogic, aml_remote";
    dev_name = "meson-remote";
    reg = <0x00 0xc8100580 0x00 0x44 0x00 0xc8100480 0x00 0x20>;
    status = "okay";
    protocol = <0x01>;
    interrupts = <0x00 0xc4 0x01>;
    pinctrl-names = "default";
    pinctrl-0 = <0x17>; // Aponta para o GPIOAO_7 (phandle 0x17)
    ...
};
```

### Explicação:
*   **Status "okay":** O dispositivo está ativo.
*   **Endereço de Registro:** `0xc8100580` (Endereço físico no hardware do S905W para o controlador IR).
*   **Pinctrl-0:** Referencia o phandle `<0x17>`, confirmando que o driver `meson-remote` está vinculado ao pino `GPIOAO_7`.

---

## 4. Mapas de Teclas e IDs do Controle (Software Layer)

O firmware Android continha três mapas de teclas pré-configurados, o que sugere que a placa TX9 suporta diferentes modelos de controle remoto.

### Códigos Customizados (Vendor IDs):
Estes são os códigos que identificam o "fabricante" do controle remoto. Ao configurar o Armbian, você precisará saber qual destes o seu controle utiliza.

1.  **Mapa 0 (amlogic-remote-1):** `customcode = <0x4040>`
2.  **Mapa 1 (amlogic-remote-2):** `customcode = <0xfb04>`
3.  **Mapa 2 (amlogic-remote-3):** `customcode = <0x7f80>`

### Exemplo de Mapeamento de Teclas (Keymap):
Os valores no DTS seguem o formato `0x[Scancode][LinuxKeyCode]`.
*   **Exemplo no Mapa 0:** `0x180073` -> Scancode `0x18` mapeado para KeyCode `0x73` (KEY_VOLUMEUP no Linux).

---

## 5. IR Blaster (Transmissor)

O hardware também possui suporte para um transmissor IR (para controlar outros aparelhos), embora estivesse desativado por padrão no Android.

### Trecho do DTS:
```dts
meson-irblaster {
    compatible = "amlogic, am_irblaster";
    dev_name = "meson-irblaster";
    status = "disabled";
    pinctrl-0 = <0x19>; // GPIOAO_7 reconfigurado para saída
};
```

---

## 6. Como aplicar no Armbian (Guia Prático)

Com base nas informações acima, veja como ativar o IR no Armbian:

### A. Verificar Driver e Pino
O kernel moderno do Armbian usa o driver `meson-ir`. O pino `GPIOAO_7` é o padrão para o S905W. 
Certifique-se de que o overlay `meson-ir` está ativo no seu arquivo `/boot/armbianEnv.txt`:
```text
overlays=meson-ir
```

### B. Testar a Recepção
Instale as ferramentas de infravermelho:
```bash
sudo apt update
sudo apt install ir-keytable
```

Execute o teste em tempo real:
```bash
sudo ir-keytable -t
```
*Se o hardware estiver correto (GPIOAO_7), ao apertar botões no controle remoto, você verá "scancodes" aparecerem na tela.*

### C. Criar o Mapa de Teclas
Se você quiser que o controle funcione como um teclado, você deve criar um arquivo de configuração usando os `customcode` identificados. 
Exemplo: Se o seu controle for o `0x4040`, você usará o protocolo NEC.

```bash
# Exemplo para associar o botão OK (scancode 0x13 no Mapa 2)
sudo ir-keytable -s rc0 -p NEC -w /etc/rc_keymaps/meu_controle.toml
```

---
**Conclusão:** O receptor IR está fisicamente conectado ao **`GPIOAO_7`**. Este pino é o padrão "de fábrica" para o hardware e deve funcionar no Armbian sem necessidade de solda ou modificações físicas, apenas configuração de software.

## 7. Comandos utilitarios do projeto

Depois de instalar com `sudo bash install_ir_service.sh install`, os seguintes comandos ficam disponiveis no sistema:

- `ir-listen` — mostra os scancodes recebidos do controle ao vivo
- `ir-map` — gera ou atualiza um arquivo `.conf` de mapeamento
- `ir-log` — equivalente a `journalctl -u tx9-ir.service -f`
- `ir-reload` — recarrega o arquivo `/etc/tx9-ir/ir_daemon.conf` sem reiniciar o servico
- `ir-help` — mostra um manual rapido de uso

Fluxo recomendado:

```bash
sudo ir-map /etc/tx9-ir/ir_daemon.conf
sudo ir-reload
sudo ir-log
```



  Documentação de Hardware: Infravermelho (IR) - TV Box TX9

  Este documento detalha a pinagem e a configuração do receptor de infravermelho (IR) identificada a partir do dump do firmware original Android (S905W/GXL).

  1. Origem da Informação (Fonte)
  As informações foram extraídas do arquivo:
   * Arquivo: tx9_pro_dump_android/extracted.dts
   * Modelo de Referência: gxl_p281_1g (Amlogic S905W)

  2. Configuração do Pino (Physical Layer)

  O SoC Amlogic utiliza pinos dedicados para a função de controle remoto. No DTS original, o pino está mapeado sob o nó de controle de pinos (pinctrl).

  Trecho do DTS:

   1 // Localizado por volta da linha 364
   2 remote_pin {
   3     amlogic,setmask = <0x10 0x01>;
   4     amlogic,clrmask = <0x10 0x200000>;
   5     amlogic,pins = "GPIOAO_7";
   6     linux,phandle = <0x17>;
   7     phandle = <0x17>;
   8 };

  Explicação:
   * Pino Identificado: GPIOAO_7.
   * Função: Este é o pino físico onde o sensor IR (receptor) está soldado na placa-mãe do TX9.
   * GPIOAO (Always On): Indica que o pino pertence ao domínio "Always On", o que permite que o controle remoto ligue a TV Box mesmo quando ela está em modo standby/suspend.

  ---

  3. Dispositivo Receptor (Driver Layer)

  O nó rc@c8100580 define o hardware do receptor IR e como o sistema operacional deve interagir com ele.

  Trecho do DTS:

    1 // Localizado por volta da linha 915
    2 rc@c8100580 {
    3     compatible = "amlogic, aml_remote";
    4     dev_name = "meson-remote";
    5     reg = <0x00 0xc8100580 0x00 0x44 0x00 0xc8100480 0x00 0x20>;
    6     status = "okay";
    7     protocol = <0x01>;
    8     interrupts = <0x00 0xc4 0x01>;
    9     pinctrl-names = "default";
   10     pinctrl-0 = <0x17>; // Aponta para o GPIOAO_7 (phandle 0x17)
   11     ...
   12 };

  Explicação:
   * Status "okay": O dispositivo está ativo.
   * Endereço de Registro: 0xc8100580 (Endereço físico no hardware do S905W para o controlador IR).
   * Pinctrl-0: Referencia o phandle <0x17>, confirmando que o driver meson-remote está vinculado ao pino GPIOAO_7.

  ---

  4. Mapas de Teclas e IDs do Controle (Software Layer)

  O firmware Android continha três mapas de teclas pré-configurados, o que sugere que a placa TX9 suporta diferentes modelos de controle remoto.

  Códigos Customizados (Vendor IDs):
  Estes são os códigos que identificam o "fabricante" do controle remoto. Ao configurar o Armbian, você precisará saber qual destes o seu controle utiliza.

   1. Mapa 0 (amlogic-remote-1): customcode = <0x4040>
   2. Mapa 1 (amlogic-remote-2): customcode = <0xfb04>
   3. Mapa 2 (amlogic-remote-3): customcode = <0x7f80>

  Exemplo de Mapeamento de Teclas (Keymap):
  Os valores no DTS seguem o formato 0x[Scancode][LinuxKeyCode].
   * Exemplo no Mapa 0: 0x180073 -> Scancode 0x18 mapeado para KeyCode 0x73 (KEY_VOLUMEUP no Linux).

  ---

  5. IR Blaster (Transmissor)

  O hardware também possui suporte para um transmissor IR (para controlar outros aparelhos), embora estivesse desativado por padrão no Android.

  Trecho do DTS:

   1 meson-irblaster {
   2     compatible = "amlogic, am_irblaster";
   3     dev_name = "meson-irblaster";
   4     status = "disabled";
   5     pinctrl-0 = <0x19>; // GPIOAO_7 reconfigurado para saída
   6 };

  ---

  6. Como aplicar no Armbian (Guia Prático)

  Com base nas informações acima, veja como ativar o IR no Armbian:

  A. Verificar Driver e Pino
  O kernel moderno do Armbian usa o driver meson-ir. O pino GPIOAO_7 é o padrão para o S905W. 
  Certifique-se de que o overlay meson-ir está ativo no seu arquivo /boot/armbianEnv.txt:
   1 overlays=meson-ir

  B. Testar a Recepção
  Instale as ferramentas de infravermelho:

   1 sudo apt update
   2 sudo apt install ir-keytable

  Execute o teste em tempo real:
   1 sudo ir-keytable -t
  Se o hardware estiver correto (GPIOAO_7), ao apertar botões no controle remoto, você verá "scancodes" aparecerem na tela.

  C. Criar o Mapa de Teclas
  Se você quiser que o controle funcione como um teclado, você deve criar um arquivo de configuração usando os customcode identificados. 
  Exemplo: Se o seu controle for o 0x4040, você usará o protocolo NEC.

   1 # Exemplo para associar o botão OK (scancode 0x13 no Mapa 2)
   2 sudo ir-keytable -s rc0 -p NEC -w /etc/rc_keymaps/meu_controle.toml

  ---
  Conclusão: O receptor IR está fisicamente conectado ao GPIOAO_7. Este pino é o padrão "de fábrica" para o hardware e deve funcionar no Armbian sem necessidade de solda ou modificações físicas, apenas configuração de software.






















