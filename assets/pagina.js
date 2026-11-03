(function(){
  document.documentElement.classList.add('js');
  var reduzido=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* menu */
  var b=document.querySelector('.menu-btn'),u=document.getElementById('menu');
  if(b&&u){
    b.addEventListener('click',function(){var o=u.classList.toggle('open');b.setAttribute('aria-expanded',o);});
    u.addEventListener('click',function(e){if(e.target.tagName==='A'){u.classList.remove('open');b.setAttribute('aria-expanded','false');}});
  }

  /* zoom das figuras */
  var d=document.getElementById('zoom');
  if(d&&d.showModal){
    var im=d.querySelector('img');
    document.querySelectorAll('figure.shot img').forEach(function(i){
      i.tabIndex=0;i.setAttribute('role','button');
      function open(){im.src=i.currentSrc||i.src;im.alt=i.alt;d.showModal();}
      i.addEventListener('click',open);
      i.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();open();}});
    });
    d.addEventListener('click',function(){d.close();});
  }

  /* abas do instalador (um painel por aparelho) */
  var paineis=[].slice.call(document.querySelectorAll('#como-instalar .painel'));
  if(paineis.length){
    var lista=document.getElementById('abas-instalar');
    paineis.forEach(function(p,i){
      var bt=document.createElement('button');
      bt.type='button';bt.setAttribute('role','tab');bt.id='aba-'+p.id;bt.setAttribute('aria-controls',p.id);
      bt.textContent=p.getAttribute('data-aba');
      bt.addEventListener('click',function(){escolher(i,true);});
      bt.addEventListener('keydown',function(e){
        var n=null;
        if(e.key==='ArrowRight')n=(i+1)%paineis.length;
        if(e.key==='ArrowLeft')n=(i+paineis.length-1)%paineis.length;
        if(n!==null){e.preventDefault();escolher(n,true);}
      });
      lista.appendChild(bt);
      p.setAttribute('role','tabpanel');p.setAttribute('aria-labelledby',bt.id);
    });
    lista.setAttribute('role','tablist');
    var escolher=function(n,foco){
      [].forEach.call(lista.children,function(bt,i){
        bt.setAttribute('aria-selected',i===n);bt.tabIndex=i===n?0:-1;
        paineis[i].hidden=i!==n;
      });
      if(foco)lista.children[n].focus();
    };
    escolher(0,false);
  }

  /* stepper do TX9 */
  var st=document.querySelector('.passos.stepper');
  if(st){
    var ps=[].slice.call(st.children),cur=0,timer=null;
    var trilha=document.getElementById('trilha'),ctl=document.getElementById('ctl-passos'),vivo=document.getElementById('passo-vivo');
    ps.forEach(function(p,i){
      var bt=document.createElement('button');bt.type='button';bt.textContent=i+1;
      bt.setAttribute('aria-label','Passo '+(i+1));
      bt.addEventListener('click',function(){ir(i);});
      trilha.appendChild(bt);
    });
    var ant=document.getElementById('p-ant'),prox=document.getElementById('p-prox'),auto=document.getElementById('p-auto');
    function ir(n){
      cur=Math.max(0,Math.min(ps.length-1,n));
      ps.forEach(function(p,i){p.classList.toggle('on',i===cur);});
      [].forEach.call(trilha.children,function(bt,i){if(i===cur)bt.setAttribute('aria-current','step');else bt.removeAttribute('aria-current');});
      ant.disabled=cur===0;prox.disabled=cur===ps.length-1;
      var t=ps[cur].querySelector('h3');
      if(vivo)vivo.textContent='Passo '+(cur+1)+' de '+ps.length+': '+(t?t.textContent:'');
    }
    function parar(){if(timer){clearInterval(timer);timer=null;}auto.textContent='Passar sozinho';auto.setAttribute('aria-pressed','false');}
    ant.addEventListener('click',function(){parar();ir(cur-1);});
    prox.addEventListener('click',function(){parar();ir(cur+1);});
    if(reduzido){auto.hidden=true;}else{
      auto.addEventListener('click',function(){
        if(timer){parar();return;}
        auto.textContent='Pausar';auto.setAttribute('aria-pressed','true');
        timer=setInterval(function(){if(cur>=ps.length-1){parar();}else ir(cur+1);},5000);
      });
    }
    st.addEventListener('keydown',function(e){
      if(e.key==='ArrowRight'){parar();ir(cur+1);}
      if(e.key==='ArrowLeft'){parar();ir(cur-1);}
    });
    st.classList.add('pronto');
    ir(0);
  }
  /* carrossel "em uso" */
  (function(car){
  if(car){
    var tr=car.querySelector('.trilho'),sl=[].slice.call(tr.children),po=car.querySelector('.pontos'),
        an=car.querySelector('.ant'),px=car.querySelector('.prox'),pts=[];
    function ir(i){i=Math.max(0,Math.min(sl.length-1,i));tr.scrollTo({left:sl[i].offsetLeft-tr.offsetLeft,behavior:reduzido?'auto':'smooth'});}
    function atual(){var x=tr.scrollLeft,m=0;sl.forEach(function(s,i){if(Math.abs(s.offsetLeft-tr.offsetLeft-x)<Math.abs(sl[m].offsetLeft-tr.offsetLeft-x))m=i;});return m;}
    function marcar(){var fim=tr.scrollLeft+tr.clientWidth>=tr.scrollWidth-4,a=fim?sl.length-1:atual();
      pts.forEach(function(p,i){p.setAttribute('aria-current',i===a?'true':'false');});an.disabled=a===0&&tr.scrollLeft<4;px.disabled=fim;}
    sl.forEach(function(s,i){var p=document.createElement('button');p.type='button';p.textContent='Item '+(i+1);
      p.setAttribute('aria-label','Item '+(i+1)+' de '+sl.length);p.addEventListener('click',function(){ir(i);});po.appendChild(p);pts.push(p);});
    an.addEventListener('click',function(){ir(atual()-1);});
    px.addEventListener('click',function(){ir(atual()+1);});
    tr.addEventListener('keydown',function(e){if(e.key==='ArrowRight'){e.preventDefault();ir(atual()+1);}if(e.key==='ArrowLeft'){e.preventDefault();ir(atual()-1);}});
    var t;tr.addEventListener('scroll',function(){clearTimeout(t);t=setTimeout(marcar,80);});
    window.addEventListener('resize',marcar);marcar();
  }
  })(document.getElementById('carrossel'));
})();
