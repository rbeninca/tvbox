# TX9 · Exploded View 3D

Vista explodida animada do TV Box TX9, implementada com JavaScript puro e [Three.js](https://threejs.org/) (ES modules e OrbitControls).

## Executar

Acesse [a página publicada pelo GitHub Pages](https://rbeninca.github.io/tvbox/explodeview/) depois que esta branch for incorporada à `main` e o GitHub Pages atualizar, ou inicie um servidor HTTP na raiz do repositório:

```bash
python3 -m http.server 8000
# http://localhost:8000/explodeview/
```

A biblioteca Three.js é carregada por CDN; requer acesso à internet na primeira execução. Não é necessário npm, build, bundler ou backend.

## Interatividade

- Arraste para girar e use a roda do mouse ou gesto de pinça para zoom.
- Clique em um componente do modelo ou na etiqueta para abrir suas informações.
- Use **Explodir / Montar** ou o controle deslizante de 0% a 100%.
- **Animar / Pausar** inicia uma animação oscilatória contínua; é possível ajustar sua velocidade.
- Use **Reiniciar câmera** para voltar à perspectiva inicial.
- Ative ou oculte as etiquetas conforme necessário.
- A fotografia `../imgs/placa_tx9.png` está disponível no painel lateral.

## Referências e limitações

A geometria é **esquemática**, sem medidas, CAD nem inspeção de marcações de encapsulamentos. O posicionamento dos chips, as trilhas, a quantidade de memórias e o aspecto dos conectores foram aproximados. O SoC S905W integra a CPU ARM Cortex-A53 e a GPU Mali-450 MP no **mesmo circuito integrado**. A auditoria reportada no projeto encontrou **8 GB de eMMC**, embora o firmware anuncie 64 GB. O Wi-Fi foi identificado como SSV6051/SSV6200. Para detalhes de firmware, drivers e engenharia reversa, consulte [RELATORIO_TECNICO.MD](../RELATORIO_TECNICO.MD) e [TX9_PRO_HARDWARE_REPORT.md](../TX9_PRO_HARDWARE_REPORT.md).

**Importante:** não utilize este modelo para dimensionamento mecânico, reparos, pinagens físicas ou identificação definitiva de componentes sem conferir a placa.
