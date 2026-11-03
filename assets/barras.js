/* Barras proporcionais das partições (esquemas; valores em MiB). */
(function () {
  var C = { fab: 'var(--fab)', box: 'var(--box)', ins: 'var(--ins)', sys: 'var(--sys)', dat: 'var(--dat)', livre: '' };
  var TX9 = [['bootloader', 0, 4, 'fab'], ['reserved', 36, 64, 'fab'], ['cache', 108, 64, 'box'], ['env', 180, 8, 'box'], ['logo', 196, 32, 'box'],
    ['recovery', 236, 32, 'ins'], ['rsv', 276, 8, 'box'], ['tee', 292, 8, 'fab'], ['crypt', 308, 32, 'box'], ['misc', 348, 32, 'box'], ['boot', 388, 32, 'sys'],
    ['system', 428, 1580, 'sys'], ['vendor', 2016, 320, 'sys'], ['odm', 2344, 128, 'sys'], ['dtbo', 2480, 8, 'sys'], ['metadata', 2496, 16, 'sys'], ['data', 2520, 4936, 'dat']];
  var BTV = [['bootloader', 0, 4, 'fab'], ['reserved', 36, 64, 'fab'], ['env', 116, 1, 'box'], ['p1 FAT32 (kernel, DTB, initramfs)', 117, 255, 'sys'],
    ['p2 ext4 (raiz)', 373, 14537, 'sys'], ['p3 rsv + crypt (decidida)', 14910, 40, 'box']];
  var MXQ = [['uboot', 4, 4, 'fab'], ['trust', 8, 8, 'fab'], ['misc', 16, 4, 'box'], ['baseparamer', 20, 1, 'fab'], ['resource (DTB e logo)', 21, 15, 'box'], ['kernel', 36, 12, 'sys'],
    ['boot (initramfs)', 48, 12, 'sys'], ['instalador', 60, 32, 'ins'], ['agente', 92, 64, 'box'], ['cache', 156, 128, 'livre'], ['config', 284, 16, 'box'], ['kpanic', 300, 4, 'livre'],
    ['p13 /home (1536 MiB)', 304, 1536, 'dat'], ['p14 raiz (o resto)', 1840, 3600, 'sys']];
  function pintar(id, lista, total, nomeOk) {
    var b = document.getElementById('b-' + id), l = document.getElementById('l-' + id);
    if (!b) return;
    var fim = 0;
    function seg(nome, tam, cls, desc) {
      var s = document.createElement('span');
      s.style.flex = tam + ' 1 0';
      if (cls === 'livre') s.className = 'livre'; else s.style.background = C[cls];
      s.title = desc;
      b.appendChild(s);
    }
    lista.forEach(function (p) {
      if (p[1] > fim) seg('', p[1] - fim, 'livre', 'livre');
      seg(p[0], p[2], p[3], p[0] + ': ' + p[2] + ' MiB');
      fim = p[1] + p[2];
      var li = document.createElement('li');
      var i = document.createElement('i'); if (p[3] === 'livre') i.style.background = 'var(--free)'; else i.style.background = C[p[3]];
      li.appendChild(i); li.appendChild(document.createTextNode(p[0] + ' ' + p[2] + ' MiB'));
      l.appendChild(li);
    });
    if (total && total > fim) seg('', total - fim, 'livre', 'livre');
  }
  pintar('tx9', TX9, 7456);
  pintar('btv', BTV, 14950);
  pintar('mxq', MXQ, 0);
})();
