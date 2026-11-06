/* Gráficos de temperatura: SVG inline, sem biblioteca. Dados vêm do JSON embutido na página. */
(function () {
  var NS = 'http://www.w3.org/2000/svg';
  var BOX = {
    tx9: { nome: 'TX9', cor: 'var(--s1)', forma: 'circulo' },
    mxq: { nome: 'MXQ Pro', cor: 'var(--s2)', forma: 'quadrado' },
    btv: { nome: 'BTV11', cor: 'var(--s3)', forma: 'triangulo' }
  };
  var dadosEl = document.getElementById('dados-termica');
  if (!dadosEl) return;
  var D;
  try { D = JSON.parse(dadosEl.textContent); } catch (e) { return; }

  function el(tag, attrs, pai, txt) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (txt != null) e.textContent = txt;
    if (pai) pai.appendChild(e);
    return e;
  }
  function fmt(n) { return String(Math.round(n * 10) / 10).replace('.', ','); }

  function marcador(pai, forma, x, y, cor, r) {
    r = r || 5;
    var a = { fill: cor, stroke: 'var(--card)', 'stroke-width': 1.5 };
    if (forma === 'circulo') { a.cx = x; a.cy = y; a.r = r; return el('circle', a, pai); }
    if (forma === 'quadrado') { a.x = x - r; a.y = y - r; a.width = 2 * r; a.height = 2 * r; return el('rect', a, pai); }
    a.points = [x, y - r - 1, x + r + 1, y + r, x - r - 1, y + r].join(',');
    return el('polygon', a, pai);
  }

  function legenda(ul, itens) {
    itens.forEach(function (it) {
      var li = document.createElement('li');
      var s = el('svg', { viewBox: '0 0 34 14', 'aria-hidden': 'true' });
      if (it.tipo === 'linha') {
        el('line', { x1: 2, y1: 7, x2: 32, y2: 7, stroke: it.cor, 'stroke-width': 2.5, 'stroke-dasharray': it.dash || '' }, s);
        marcador(s, it.forma, 17, 7, it.cor, 4);
      } else {
        marcador(s, it.forma, 17, 7, it.cor, 5);
      }
      li.appendChild(s);
      li.appendChild(document.createTextNode(it.texto));
      ul.appendChild(li);
    });
  }

  /* ---------- gráfico de linhas ---------- */
  function linhas(alvo, cfg) {
    alvo.textContent = '';
    var W = Math.max(280, alvo.clientWidth || 600);
    var H = W < 520 ? 270 : 340;
    var m = { l: 40, r: (cfg.lim ? 44 : 12), t: 14, b: 34 };
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': cfg.rotulo }, alvo);
    var pw = W - m.l - m.r, ph = H - m.t - m.b;
    function X(t) { return m.l + (t - (cfg.xmin || 0)) / (cfg.xmax - (cfg.xmin || 0)) * pw; }
    function Y(v) { return m.t + (cfg.ymax - v) / (cfg.ymax - cfg.ymin) * ph; }
    var ax = el('g', { 'class': 'ax', 'aria-hidden': 'true' }, svg);
    var v, t;
    for (v = Math.ceil(cfg.ymin / 10) * 10; v <= cfg.ymax; v += 10) {
      el('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }, ax);
      el('text', { x: m.l - 6, y: Y(v) + 4, 'text-anchor': 'end' }, ax, v + '');
    }
    var passo = cfg.xmax <= 300 ? 60 : 100;
    for (t = 0; t <= cfg.xmax; t += passo) {
      el('text', { x: X(t), y: H - 12, 'text-anchor': 'middle' }, ax, t + ' s');
    }
    el('text', { x: 4, y: 10, 'text-anchor': 'start' }, ax, '°C');
    (cfg.lim || []).forEach(function (l, i) {
      el('line', { 'class': 'lim', x1: m.l, x2: W - m.r, y1: Y(l[0]), y2: Y(l[0]) }, svg);
      el('text', { 'class': 'limt', x: W - m.r + 4, y: Y(l[0]) + 4, 'text-anchor': 'start' }, svg, l[0] + ' °C');
    });
    cfg.series.forEach(function (s, idx) {
      var b = BOX[s.box];
      var tmin = Math.min.apply(null, s.pts.map(function (p) { return p[1]; }));
      var tmax = Math.max.apply(null, s.pts.map(function (p) { return p[1]; }));
      var g = el('g', { tabindex: '0', role: 'img',
        'aria-label': s.nome + ': de ' + fmt(tmin) + ' a ' + fmt(tmax) + ' graus Celsius em ' + s.pts[s.pts.length - 1][0] + ' segundos. ' + (s.nota || '') }, svg);
      el('title', {}, g, s.nome + ': ' + fmt(tmin) + ' a ' + fmt(tmax) + ' °C');
      var dpath = s.pts.map(function (p, i) { return (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1); }).join('');
      var pa = el('path', { 'class': 'linha-g anim', d: dpath, stroke: b.cor, 'stroke-dasharray': s.dash || 'none' }, g);
      if (!s.dash) {
        try { var len = Math.ceil(pa.getTotalLength()); pa.style.setProperty('--len', len); } catch (e) { pa.setAttribute('class', 'linha-g'); }
      } else { pa.setAttribute('class', 'linha-g'); }
      var passoM = Math.max(1, Math.round(s.pts.length / 6));
      s.pts.forEach(function (p, i) {
        if (i % passoM === 0 || i === s.pts.length - 1) marcador(g, b.forma, X(p[0]), Y(p[1]), b.cor, 4);
      });
      var ult = s.pts[s.pts.length - 1];
      var mxp = s.pts.reduce(function (a, p) { return p[1] > a[1] ? p : a; }, s.pts[0]);
      if (cfg.valores) el('text', { 'class': 'vl', x: Math.min(X(mxp[0]), W - m.r - 16), y: Y(mxp[1]) - 9, 'text-anchor': 'middle' }, g, fmt(mxp[1]));
    });
  }

  /* ---------- barras agrupadas ---------- */
  function barras(alvo, cfg) {
    alvo.textContent = '';
    var W = Math.max(280, alvo.clientWidth || 500);
    var H = W < 520 ? 300 : 320;
    var m = { l: 36, r: 8, t: 22, b: cfg.baixo || 64 };
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': cfg.rotulo }, alvo);
    var pw = W - m.l - m.r, ph = H - m.t - m.b;
    function Y(v) { return m.t + (cfg.ymax - v) / cfg.ymax * ph; }
    var ax = el('g', { 'class': 'ax', 'aria-hidden': 'true' }, svg);
    for (var v = 0; v <= cfg.ymax; v += (cfg.passo || 20)) {
      el('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }, ax);
      el('text', { x: m.l - 6, y: Y(v) + 4, 'text-anchor': 'end' }, ax, v + '');
    }
    var gw = pw / cfg.groups.length;
    var nv = cfg.groups[0].vals.length;
    var bw = Math.min(46, (gw - 16) / nv);
    cfg.groups.forEach(function (gr, gi) {
      var b = BOX[gr.box];
      var cx = m.l + gw * gi + gw / 2;
      var desc = gr.label.replace(/\|/g, ' ') + ': ' + gr.vals.map(function (x, i) { return cfg.names[i] + ' ' + fmt(x) + (cfg.unit || ''); }).join(', ');
      var g = el('g', { tabindex: '0', role: 'img', 'aria-label': desc }, svg);
      el('title', {}, g, desc);
      gr.vals.forEach(function (val, i) {
        var x = cx - (nv * bw) / 2 + i * bw + 3;
        var leve = (nv > 1 && i === 0);
        var r = el('rect', { x: x, y: Y(val), width: bw - 6, height: Math.max(1, Y(0) - Y(val)), fill: b.cor,
          'fill-opacity': leve ? '.35' : '1', stroke: b.cor, 'stroke-width': 2, rx: 3 }, g);
        if (leve) r.setAttribute('stroke-dasharray', '4 3');
        el('text', { 'class': 'vl', x: x + (bw - 6) / 2, y: Y(val) - 6, 'text-anchor': 'middle' }, g, fmt(val) + (cfg.unitCurta || ''));
      });
      var linhasT = gr.label.split('|');
      linhasT.forEach(function (tx, li) {
        el('text', { 'class': 'ct', x: cx, y: H - m.b + 34 + li * 14, 'text-anchor': 'middle', 'font-weight': li ? '400' : '700' }, svg, tx);
      });
      marcador(svg, b.forma, cx, H - m.b + 12, b.cor, 5);
    });
  }

  function tabela(det, cab, linhasT) {
    var tb = det.querySelector('.tbl');
    var h = '<table><thead><tr>' + cab.map(function (c) { return '<th scope="col">' + c + '</th>'; }).join('') + '</tr></thead><tbody>';
    linhasT.forEach(function (l) { h += '<tr>' + l.map(function (c, i) { return (i ? '<td>' : '<th scope="row">') + c + (i ? '</td>' : '</th>'); }).join('') + '</tr>'; });
    tb.innerHTML = h + '</tbody></table>';
  }

  function resumoSerie(s) {
    var ts = s.pts.map(function (p) { return p[1]; });
    return [s.nome, fmt(Math.min.apply(null, ts)), fmt(Math.max.apply(null, ts)), s.pts[s.pts.length - 1][0] + ' s', s.nota || (s.ops ? fmt(s.ops) + ' operações/s' : '')];
  }

  var g1 = document.getElementById('g1'), g2 = document.getElementById('g2'), g3 = document.getElementById('g3'), g4a = document.getElementById('g4a'), g4b = document.getElementById('g4b');

  function legBox(ul, extra) {
    ul.textContent = '';
    var it = [];
    ['tx9', 'mxq', 'btv'].forEach(function (k) { it.push({ tipo: 'ponto', forma: BOX[k].forma, cor: BOX[k].cor, texto: BOX[k].nome }); });
    legenda(ul, it.concat(extra || []));
  }

  function desenhar() {
    if (g1) linhas(g1, { rotulo: 'Temperatura ao longo do tempo sob carga de 4 núcleos, por aparelho', xmax: D.g1.xmax, ymin: D.g1.ymin, ymax: D.g1.ymax, lim: D.g1.lim, series: D.g1.series, valores: true });
    if (g2) barras(g2, { rotulo: 'Temperatura parado e sob carga, por aparelho', unit: ' °C', ymax: D.g2.ymax, names: D.g2.names, groups: D.g2.groups, baixo: 50 });
    if (g3) barras(g3, { rotulo: 'Temperatura antes e depois de um ajuste', unit: ' °C', ymax: D.g3.ymax, names: D.g3.names, groups: D.g3.groups, baixo: 78, passo: 10 });
    if (g4a) linhas(g4a, { rotulo: 'Temperatura do MXQ Pro com três pontos de redução de clock', xmin: 0, xmax: D.g4.xmax, ymin: D.g4.ymin, ymax: D.g4.ymax, series: D.g4.series, valores: true });
    if (g4b) {
      var gs = D.g4.series.map(function (s, i) { return { label: ['70 °C|(fábrica)', '80 °C', '85 °C'][i], box: 'mxq', vals: [s.ops] }; });
      barras(g4b, { rotulo: 'Trabalho feito em 5 minutos, em operações por segundo', ymax: 600, passo: 100, names: ['Operações por segundo'], groups: gs, baixo: 56, unit: ' operações/s' });
    }
  }

  function montarTabelas() {
    var t;
    if ((t = document.getElementById('t1'))) tabela(t, ['Curva', 'Mínimo (°C)', 'Máximo (°C)', 'Duração', 'Observação'], D.g1.series.map(resumoSerie));
    if ((t = document.getElementById('t2'))) tabela(t, ['Aparelho', D.g2.names[0] + ' (°C)', D.g2.names[1] + ' (°C)'], D.g2.groups.map(function (g) { return [g.label, fmt(g.vals[0]), fmt(g.vals[1])]; }));
    if ((t = document.getElementById('t3'))) tabela(t, ['Situação', 'Antes (°C)', 'Depois (°C)'], D.g3.groups.map(function (g) { return [g.label.replace(/\|/g, ' '), fmt(g.vals[0]), fmt(g.vals[1])]; }));
    if ((t = document.getElementById('t4'))) {
      var base = D.g4.series[0].ops;
      tabela(t, ['Ponto de redução', 'Máximo (°C)', 'Operações por segundo', 'Ganho sobre o de fábrica'], D.g4.series.map(function (s, i) {
        var mx = Math.max.apply(null, s.pts.map(function (p) { return p[1]; }));
        return [s.nome, fmt(mx), fmt(s.ops), i ? '+' + Math.round((s.ops / base - 1) * 100) + ' %' : 'base'];
      }));
    }
  }

  legBox(document.getElementById('leg1'), [{ tipo: 'linha', forma: 'circulo', cor: 'var(--tx)', dash: '7 4', texto: 'tracejado: TX9 empilhado' }, { tipo: 'linha', forma: 'quadrado', cor: 'var(--nao)', dash: '6 4', texto: 'linha vermelha: onde o clock começa a cair' }]);
  var l2 = document.getElementById('leg2'); if (l2) legBox(l2);
  var l4 = document.getElementById('leg4');
  if (l4) {
    var e4 = [
      { tipo: 'linha', forma: 'quadrado', cor: 'var(--s2)', dash: '2 5', texto: 'limite de fábrica 70 °C' },
      { tipo: 'linha', forma: 'quadrado', cor: 'var(--s2)', dash: '8 4', texto: 'limite 80 °C' },
      { tipo: 'linha', forma: 'quadrado', cor: 'var(--s2)', dash: '', texto: 'limite 85 °C' }
    ];
    legenda(l4, e4);
  }
  desenhar();
  montarTabelas();
  var tm;
  var larg = window.innerWidth;
  window.addEventListener('resize', function () {
    if (window.innerWidth === larg) return;
    larg = window.innerWidth;
    clearTimeout(tm); tm = setTimeout(desenhar, 150);
  });
})();
