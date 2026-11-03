/* Desenho animado do boot: os quadros vêm das listas <ol> da própria página. */
(function () {
  var raiz = document.getElementById('boot-player');
  if (!raiz) return;
  var NS = 'http://www.w3.org/2000/svg';
  var reduzido = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ESTACOES = ['Energia', 'BootROM', 'SRAM', 'DDR (RAM)', 'Segurança', 'U-Boot', 'Kernel', 'Sistema'];
  var svg = raiz.querySelector('svg.cena');
  var legT = raiz.querySelector('.q-titulo'), legP = raiz.querySelector('.q-texto'), logE = raiz.querySelector('.logq'), seloE = raiz.querySelector('.selo');
  var cont = raiz.querySelector('.cont'), vivo = raiz.querySelector('.q-vivo');
  var bPlay = raiz.querySelector('.b-play'), bAnt = raiz.querySelector('.b-ant'), bProx = raiz.querySelector('.b-prox'), bRein = raiz.querySelector('.b-rein');
  var selVel = raiz.querySelector('.s-vel'), chkLog = raiz.querySelector('.c-log');
  var abas = [].slice.call(raiz.querySelectorAll('.seg button'));

  function el(tag, a, pai, txt) {
    var e = document.createElementNS(NS, tag);
    for (var k in a) e.setAttribute(k, a[k]);
    if (txt != null) e.textContent = txt;
    if (pai) pai.appendChild(e);
    return e;
  }

  /* cena */
  var est = [], ze, bilhete, usb, narrow = null;
  function glifo(i, g) {
    var c = 'gl';
    switch (i) {
      case 0: el('circle', { 'class': c, cx: 0, cy: 2, r: 13 }, g); el('line', { 'class': c, x1: 0, y1: -14, x2: 0, y2: -2 }, g); break;
      case 1: el('rect', { 'class': c, x: -12, y: -12, width: 24, height: 24, rx: 3 }, g); [-6, 0, 6].forEach(function (p) { el('line', { 'class': c, x1: p, y1: -17, x2: p, y2: -12 }, g); el('line', { 'class': c, x1: p, y1: 12, x2: p, y2: 17 }, g); }); break;
      case 2: el('rect', { 'class': c, x: -10, y: -8, width: 20, height: 18 }, g); el('line', { 'class': c, x1: -10, y1: 1, x2: 10, y2: 1 }, g); break;
      case 3: el('path', { 'class': c, d: 'M-18 12 V-4 L0 -16 L18 -4 V12 Z' }, g); [-8, 0, 8].forEach(function (p, j) { el('rect', { 'class': 'ddr-b', x: p - 3, y: -2, width: 6, height: 14 }, g); }); break;
      case 4: el('rect', { 'class': c, x: -14, y: -13, width: 28, height: 26, rx: 3 }, g); el('circle', { 'class': c, cx: 0, cy: 0, r: 6 }, g); break;
      case 5: el('circle', { 'class': c, cx: 0, cy: -6, r: 7 }, g); el('path', { 'class': c, d: 'M-13 14 Q0 -4 13 14' }, g); break;
      case 6: el('rect', { 'class': c, x: -11, y: -16, width: 22, height: 32 }, g); [[-5, -9], [3, -9], [-5, -1], [3, -1]].forEach(function (p) { el('rect', { 'class': c, x: p[0], y: p[1], width: 4, height: 4 }, g); }); break;
      default: el('rect', { 'class': c, x: -10, y: -15, width: 20, height: 30 }, g); el('circle', { 'class': c, cx: 5, cy: 2, r: 1.5 }, g);
    }
  }
  function montarCena() {
    svg.textContent = '';
    est = [];
    var l = el('title', {}, svg, 'Cena do boot: um personagem percorre as etapas, da energia ao sistema.');
    var gEst = el('g', {}, svg);
    ESTACOES.forEach(function (n, i) {
      var g = el('g', { 'class': 'st' + (i === 3 ? ' ddr' : ''), 'data-i': i }, gEst);
      el('rect', { 'class': 'corpo', x: -44, y: -38, width: 88, height: 76, rx: 12 }, g);
      glifo(i, g);
      el('text', { x: 0, y: 58, 'text-anchor': 'middle' }, g, n);
      est.push(g);
    });
    ze = el('g', { 'class': 'ze' }, svg);
    bilhete = el('rect', { 'class': 'bilhete', x: 18, y: -6, width: 10, height: 14, rx: 2 }, ze);
    el('circle', { 'class': 'corpo-z', cx: 0, cy: 0, r: 22 }, ze);
    el('circle', { 'class': 'olho', cx: -8, cy: -5, r: 6 }, ze); el('circle', { 'class': 'olho', cx: 8, cy: -5, r: 6 }, ze);
    el('circle', { 'class': 'pup', cx: -7, cy: -4, r: 2.5 }, ze); el('circle', { 'class': 'pup', cx: 9, cy: -4, r: 2.5 }, ze);
    el('path', { 'class': 'boca', d: 'M-8 8 Q0 15 8 8' }, ze);
    usb = el('g', { id: 'usbg' }, svg);
    el('rect', { x: -26, y: -20, width: 52, height: 36, rx: 5, fill: 'var(--card)', stroke: 'var(--tx)', 'stroke-width': 2.5 }, usb);
    el('line', { x1: -14, y1: 22, x2: 14, y2: 22, stroke: 'var(--tx)', 'stroke-width': 3 }, usb);
    el('text', { x: 0, y: 5, 'text-anchor': 'middle' }, usb, 'PC');
    el('path', { d: 'M0 16 V30', stroke: 'var(--tx)', 'stroke-width': 2.5, 'stroke-dasharray': '4 3' }, usb);
    layout(true);
  }
  var pos = [];
  function layout(forcar) {
    var estreito = raiz.clientWidth < 640;
    if (!forcar && estreito === narrow) return;
    narrow = estreito;
    var W, H;
    if (estreito) {
      W = 400; H = 380;
      for (var i = 0; i < 8; i++) pos[i] = [60 + (i % 4) * 93, i < 4 ? 150 : 300];
    } else {
      W = 960; H = 290;
      for (var j = 0; j < 8; j++) pos[j] = [70 + j * 117, 150];
    }
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    est.forEach(function (g, k) { g.setAttribute('transform', 'translate(' + pos[k][0] + ' ' + pos[k][1] + ')'); });
    if (estreito) { est.forEach(function (g) { g.querySelector('rect').setAttribute('width', 80); g.querySelector('rect').setAttribute('x', -40); }); }
    else { est.forEach(function (g) { g.querySelector('rect').setAttribute('width', 88); g.querySelector('rect').setAttribute('x', -44); }); }
    mover(atual >= 0 && quadros[atual] ? quadros[atual].est : 0);
  }
  function mover(i) {
    var p = pos[i];
    ze.setAttribute('transform', 'translate(' + p[0] + ' ' + (p[1] - 70) + ')');
    usb.setAttribute('transform', 'translate(' + pos[1][0] + ' ' + (pos[1][1] - 125) + ')');
    if (narrow) usb.setAttribute('transform', 'translate(' + (pos[1][0] + 0) + ' ' + (pos[1][1] - 125) + ')');
  }

  /* quadros */
  var familia = null, quadros = [], atual = -1, tocando = false, tmr = null, vel = 1;
  function lerFamilia(f) {
    var ol = raiz.parentNode.querySelector('ol.boot-lista[data-familia="' + f + '"]');
    return [].map.call(ol.children, function (li) {
      return { titulo: li.querySelector('h4').textContent, texto: li.querySelector('p').textContent, log: li.getAttribute('data-log') || '',
        selo: li.getAttribute('data-selo'), seg: +li.getAttribute('data-seg') || 5, est: +li.getAttribute('data-est') || 0, ramo: li.hasAttribute('data-ramo') };
    });
  }
  function mostrar(i) {
    atual = Math.max(0, Math.min(quadros.length - 1, i));
    var q = quadros[atual];
    legT.textContent = q.titulo; legP.textContent = q.texto;
    seloE.textContent = q.selo === 'visto' ? 'visto no box' : 'deduzido';
    seloE.className = 'selo ' + q.selo;
    logE.textContent = q.log || '(sem linha de log para este quadro)';
    logE.hidden = !chkLog.checked;
    cont.textContent = 'Quadro ' + (atual + 1) + ' de ' + quadros.length;
    est.forEach(function (g, k) {
      g.classList.toggle('ativo', k === q.est);
      g.classList.toggle('feito', k < q.est);
    });
    raiz.classList.toggle('ramo-usb', q.ramo);
    mover(q.est);
    var prog = Math.min(1, (q.est + 1) / 8);
    bilhete.setAttribute('width', 10 + Math.round(prog * 40));
    vivo.textContent = 'Quadro ' + (atual + 1) + ' de ' + quadros.length + ': ' + q.titulo + '. ' + q.texto + (q.selo === 'visto' ? ' Visto no box.' : ' Deduzido.');
    bAnt.disabled = atual === 0; bProx.disabled = atual === quadros.length - 1;
  }
  function agendar() {
    clearTimeout(tmr);
    if (!tocando) return;
    tmr = setTimeout(function () {
      if (atual >= quadros.length - 1) { parar(); return; }
      mostrar(atual + 1); agendar();
    }, quadros[atual].seg * 1000 / vel);
  }
  function tocar() {
    if (atual >= quadros.length - 1) mostrar(0);
    tocando = true; raiz.classList.add('tocando'); bPlay.textContent = 'Pausar'; bPlay.setAttribute('aria-pressed', 'true'); agendar();
  }
  function parar() { tocando = false; clearTimeout(tmr); raiz.classList.remove('tocando'); bPlay.textContent = 'Tocar'; bPlay.setAttribute('aria-pressed', 'false'); }
  function trocar(f) {
    parar(); familia = f; quadros = lerFamilia(f);
    abas.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-f') === f); });
    mostrar(0);
  }

  raiz.hidden = false;
  montarCena();
  bPlay.addEventListener('click', function () { tocando ? parar() : tocar(); });
  bAnt.addEventListener('click', function () { parar(); mostrar(atual - 1); });
  bProx.addEventListener('click', function () { parar(); mostrar(atual + 1); });
  bRein.addEventListener('click', function () { parar(); mostrar(0); });
  selVel.addEventListener('change', function () { vel = +selVel.value; if (tocando) agendar(); });
  chkLog.addEventListener('change', function () { logE.hidden = !chkLog.checked; });
  abas.forEach(function (b) { b.addEventListener('click', function () { trocar(b.getAttribute('data-f')); }); });
  raiz.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
    if (e.key === 'ArrowRight') { parar(); mostrar(atual + 1); }
    else if (e.key === 'ArrowLeft') { parar(); mostrar(atual - 1); }
  });
  if (reduzido) {
    bPlay.hidden = true; selVel.parentNode.hidden = true;
  }
  var tmr2;
  window.addEventListener('resize', function () { clearTimeout(tmr2); tmr2 = setTimeout(function () { layout(false); }, 120); });
  raiz.classList.add('pronto');
  var det = document.getElementById('boot-lista-d'); if (det) det.open = false;
  trocar('amlogic');
})();
