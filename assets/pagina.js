(function(){
  var b=document.querySelector('.menu-btn'),u=document.getElementById('menu');
  if(b&&u){
    b.addEventListener('click',function(){var o=u.classList.toggle('open');b.setAttribute('aria-expanded',o);});
    u.addEventListener('click',function(e){if(e.target.tagName==='A'){u.classList.remove('open');b.setAttribute('aria-expanded','false');}});
  }
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
})();
