import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const $ = (id) => document.getElementById(id);
const canvas = $("scene");
const stage = $("stage");
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 200);
camera.position.set(13, 11, 15);
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, alpha: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.45;
const orbit = new OrbitControls(camera, canvas);
orbit.enableDamping = true; orbit.dampingFactor = .07;
orbit.minDistance = 8; orbit.maxDistance = 36;
orbit.target.set(0, 0, 0);
scene.add(new THREE.HemisphereLight(0xb5d5ff, 0x17202c, 2.6));
const key = new THREE.DirectionalLight(0xffffff, 3.2);
key.position.set(8, 13, 6); scene.add(key);
const fill = new THREE.DirectionalLight(0x78a7ff, 1.3);
fill.position.set(-9, 4, -7); scene.add(fill);

const materials = {
  case: new THREE.MeshStandardMaterial({color:0x161c25, roughness:.68, metalness:.12, transparent:true, opacity:.88, side:THREE.DoubleSide, depthWrite:false}),
  base: new THREE.MeshStandardMaterial({color:0x202731, roughness:.85}),
  pcb: new THREE.MeshStandardMaterial({color:0xa51e2b, metalness:.18, roughness:.65}),
  edge: new THREE.MeshStandardMaterial({color:0xd84244, roughness:.55}),
  chip: new THREE.MeshStandardMaterial({color:0x171c23, metalness:.12, roughness:.68}),
  metal: new THREE.MeshStandardMaterial({color:0xa6b1c3, metalness:.78, roughness:.32}),
  darkMetal: new THREE.MeshStandardMaterial({color:0x4a5463,metalness:.7,roughness:.45}),
  gold: new THREE.MeshStandardMaterial({color:0xe9b96e,metalness:.7,roughness:.34}),
  silk: new THREE.MeshBasicMaterial({color:0xf3ced0}),
  display: new THREE.MeshStandardMaterial({color:0x0c1018,roughness:.18,metalness:.22}),
  green: new THREE.MeshBasicMaterial({color:0x45e4a3}),
};
const parts = [];
const clickable = [];
function box(w,h,d, material, parent, x=0,y=0,z=0) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), material);
  mesh.position.set(x,y,z); parent.add(mesh); return mesh;
}
function part(id, name, type, desc, specs, note, icon, offset, anchor=[0,0,0]) {
  const group=new THREE.Group();scene.add(group);
  const info={id,name,type,desc,specs,note,icon,offset:new THREE.Vector3(...offset),anchor:new THREE.Vector3(...anchor),group};
  group.userData.part=info; parts.push(info); return info;
}
function chip(p,x,z,w,d,thickness=.15){
  const m=box(w,thickness,d,materials.chip,p.group,x,.38+thickness/2,z);
  m.userData.part=p; clickable.push(m);
  for(let i=0;i<Math.floor(w/.16);i++){
    box(.06,.014,.14,materials.metal,p.group,x-w/2+.09+i*.16,.38,z-d/2-.03);
    box(.06,.014,.14,materials.metal,p.group,x-w/2+.09+i*.16,.38,z+d/2+.03);
  }
  return m;
}
function labelTexture(text,color="#e8e9ed",scale=1){
  const c=document.createElement("canvas");c.width=512;c.height=128;
  const ctx=c.getContext("2d");ctx.clearRect(0,0,512,128);
  ctx.fillStyle=color;ctx.textAlign="center";ctx.textBaseline="middle";ctx.font="bold 50px sans-serif";ctx.fillText(text,256,64,492);
  const texture=new THREE.CanvasTexture(c);texture.colorSpace=THREE.SRGBColorSpace;
  return new THREE.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false,side:THREE.DoubleSide});
}
function textOnTop(p,txt,x,y,z,w=.9,h=.22){
  const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),labelTexture(txt));
  m.rotation.x=-Math.PI/2;m.position.set(x,y,z);p.group.add(m);
}
const genericNote="Representação esquemática baseada nas fotografias. Dimensões, serigrafia e posicionamento não foram aferidos fisicamente.";
const bottom=part("bottom","Base inferior","ESTRUTURA · CARCAÇA","Parte inferior da carcaça que suporta a PCB e os pontos de fixação.",[["Material","Plástico"],["Função","Fixação e proteção"]],genericNote,"▱",[0,-3.1,0],[0,-.6,0]);
box(9.4,.4,8.6,materials.base,bottom.group,0,-.55,0);
for(const x of [-3.9,3.9])for(const z of [-3.45,3.45]){
  box(.35,.35,.35,materials.darkMetal,bottom.group,x,-.21,z);
}
const pcb=part("pcb","Placa de circuito impresso","PCB · INTERCONEXÃO","Placa vermelha com trilhas, planos de referência e os componentes eletrônicos da TV Box.",[["Tipo","PCB multicamadas"],["Cor","Vermelho"],["Uso","Interconexão do hardware"]],genericNote,"▤",[0,-.35,0],[0,.2,0]);
const board=box(8.55,.14,7.7,materials.pcb,pcb.group,0,0,0);board.userData.part=pcb;clickable.push(board);
for(let i=0;i<65;i++){
  const x=Math.sin(i*14.73)*3.7,z=Math.cos(i*8.17)*3.3;
  const trace=box(.22+((i*7)%8)*.12,.009,.018,materials.gold,pcb.group,x,.079,z);
  trace.rotation.y=(i%3)*Math.PI/4;trace.material=materials.edge;
}
for(const x of [-3.8,3.8])for(const z of [-3.25,3.25]){
  const hole=new THREE.Mesh(new THREE.TorusGeometry(.11,.035,8,24),materials.gold);
  hole.rotation.x=-Math.PI/2;hole.position.set(x,.083,z);pcb.group.add(hole);
}
const soc=part("soc","Amlogic S905W","SOC · PROCESSAMENTO","Processador principal ARM Cortex-A53 (AArch64), família GXL. A GPU Mali-450 MP está integrada ao mesmo encapsulamento.",[["CPU","ARM Cortex-A53"],["Arquitetura","AArch64 / GXL"],["GPU","Mali-450 MP"],["Kernel original","Linux 3.14.29"]],"SoC e GPU são uma peça física única: a Mali não é um chip separado.", "▣",[0,2.9,0],[-.65,.55,-.35]);
chip(soc,-.65,-.35,1.65,1.65,.19);textOnTop(soc,"AMLOGIC",-.65,.69,-.35,1.35,.27);
const ram=part("ram","Memórias RAM","MEMÓRIA · VOLÁTIL","Circuitos de memória usados pelo processador; quantidade e fabricante devem ser conferidos nas marcações da PCB ou nos registros do sistema.",[["Função","Memória de trabalho"],["Capacidade","Não confirmada"]],genericNote,"▥",[2.4,2.25,-1.4],[1.3,.52,-1.15]);
chip(ram,1.32,-1.2,1.1,1.5,.14);chip(ram,1.32,.7,1.1,1.5,.14);
const emmc=part("emmc","Armazenamento eMMC","FLASH · NÃO VOLÁTIL","Memória interna da unidade: a auditoria do repositório indica 8 GB reais, apesar da alegação de 64 GB do Android original.",[["Capacidade real","8 GB"],["Anunciada","64 GB (incorreto)"],["Dispositivo","mmcblk0 / mmcblk1"]],"A capacidade foi inferida de testes do sistema; a marca do encapsulamento não foi confirmada.", "▣",[-2.45,2.15,1.25],[-1.8,.55,1.4]);
chip(emmc,-1.78,1.43,1.6,1.05,.16);textOnTop(emmc,"eMMC", -1.78,.66,1.43,1.0,.24);
const wifi=part("wifi","Wi-Fi SSV6051 / 6200","REDE · SEM FIO","Controlador Wi-Fi documentado por logs ssv6200 e módulo ssv6051; requer driver específico no Linux.",[["Chipset","SSV6051 / 6200"],["Interface","wlan0"],["Driver","ssv6051"]],"A variante exata pode depender da revisão da placa. A antena é representada esquematicamente.", "⌁",[3.5,1.5,1],[2.65,.5,1.9]);
chip(wifi,2.62,1.83,.9,.9,.13);
for(let i=0;i<3;i++){
 const a=box(.9,.012,.045,materials.gold,wifi.group,3.05+i*.22,.09,2.58+i*.20);a.rotation.y=-Math.PI/4;
}
const display=part("display","Display frontal","VISUALIZAÇÃO · VFD/LED","Módulo de indicadores frontal, controlado por FD650/FD6551 ou variante compatível, conforme o relatório de engenharia reversa.",[["Controle","FD650 / FD6551"],["Sinais","GPIOX_27 / GPIOX_29"],["Protocolo","Serial bit-bang"]],"A aparência geométrica foi simplificada; a variante precisa do controlador depende da unidade.", "▦",[0,2.55,-4.1],[0,.45,-3.45]);
const disp=box(2.6,.55,.3,materials.display,display.group,0,.34,-3.72);disp.userData.part=display;clickable.push(disp);
for(let i=0;i<4;i++){const seg=box(.3,.32,.012,materials.green,display.group,-.78+i*.5,.38,-3.889);seg.material=new THREE.MeshBasicMaterial({color:0x50e4a1,transparent:true,opacity:.75});}
const hdmi=part("hdmi","Saída HDMI","PORTA · VÍDEO","Conector digital HDMI, usado para saída de vídeo e áudio ao monitor ou televisor.",[["Interface","HDMI"],["Local","Borda da PCB"]],genericNote,"▭",[-3,1.2,-2.9],[-3.15,.35,-3.6]);
const hm=box(1.4,.48,.78,materials.metal,hdmi.group,-2.95,.31,-3.73);hm.userData.part=hdmi;clickable.push(hm);
box(1.12,.2,.01,materials.display,hdmi.group,-2.95,.28,-4.13);
const usb=part("usb","Portas USB","PORTAS · CONECTIVIDADE","Conectores USB utilizados para periféricos, armazenamento e operações de manutenção.",[["Tipo","USB-A"],["Quantidade","2 (representação)"]],genericNote,"▭",[3.9,1.25,-2.7],[2.8,.35,-3.6]);
for(const x of [2.28,3.42]){const m=box(.86,.52,.94,materials.metal,usb.group,x,.33,-3.73);m.userData.part=usb;clickable.push(m);box(.65,.25,.013,materials.display,usb.group,x,.33,-4.205);}
const eth=part("ethernet","Ethernet RJ45","REDE · CABEADA","Interface Ethernet integrada à plataforma Amlogic; os ensaios do repositório apontam comportamento próximo de 100 Mb/s.",[["Porta","RJ45"],["Interface","eth0"],["Classe","Fast Ethernet"]],genericNote,"⌁",[-4.2,1.4,1.5],[-3.65,.35,1.05]);
const en=box(1.32,.75,1.4,materials.metal,eth.group,-3.8,.48,1.2);en.userData.part=eth;clickable.push(en);
box(.9,.44,.012,materials.display,eth.group,-3.8,.46,1.92);
const ports=part("av","AV / Energia","PORTAS · ALIMENTAÇÃO","Conectores auxiliares de alimentação e saída analógica AV. A porta AV pode abrigar o acesso ao botão reset.",[["Função","Energia / AV"],["Reset","Verificar na unidade"]],genericNote,"◉",[-4,1.7,3.1],[-3.55,.4,3.25]);
for(const x of [-3.75,-2.65]){
 const cylinder=new THREE.Mesh(new THREE.CylinderGeometry(.29,.29,.55,24),materials.darkMetal);
 cylinder.rotation.x=Math.PI/2;cylinder.position.set(x,.42,3.72);ports.group.add(cylinder);cylinder.userData.part=ports;clickable.push(cylinder);
}
const ir=part("ir","Receptor infravermelho","ENTRADA · CONTROLE REMOTO","Receptor IR original, identificado no relatório técnico ligado ao GPIOAO_7.",[["GPIO","GPIOAO_7"],["Driver Linux","meson-ir"],["Protocolo","NECx"]],genericNote,"◉",[1.9,1.7,-3.7],[1.6,.4,-3.45]);
const irchip=box(.43,.5,.37,materials.display,ir.group,1.64,.37,-3.55);irchip.userData.part=ir;clickable.push(irchip);
const cover=part("cover","Tampa superior TX9","ESTRUTURA · GABINETE","Carcaça superior preta com acabamento retangular. O modelo mostra a tampa sem textura fotográfica para permitir a inspeção interna.",[["Material","Plástico preto"],["Acabamento","Fosco"],["Logo","TX9"]],genericNote,"▱",[0,5.1,0],[0,1.13,0]);
// Open-bottom roof with thin sidewalls instead of an opaque solid blocking the PCB.
const roof=box(9.6,.24,8.8,materials.case,cover.group,0,1.55,0);roof.userData.part=cover;clickable.push(roof);
for(const z of [-4.33,4.33]){const m=box(9.6,.86,.18,materials.case,cover.group,0,1.02,z);m.userData.part=cover;clickable.push(m);}
for(const x of [-4.73,4.73]){const m=box(.16,.86,8.7,materials.case,cover.group,x,1.02,0);m.userData.part=cover;clickable.push(m);}
const windowTop=box(4.1,.015,3.35,new THREE.MeshStandardMaterial({color:0x0b121d,roughness:.15,metalness:.18,transparent:true,opacity:.8}),cover.group,1.1,1.69,-.25);
windowTop.userData.part=cover;clickable.push(windowTop);
textOnTop(cover,"TX9",1.1,1.705,-.25,1.7,.5);

const raycaster=new THREE.Raycaster(), mouse=new THREE.Vector2();
let current=soc, target=0, explosion=0, playing=false, t=0, lastTime=performance.now(), pointerStart=null;
function select(p) {
 current=p;
 $("partName").textContent=p.name;$("partType").textContent=p.type;
 $("partDesc").textContent=p.desc;$("partIcon").textContent=p.icon;
 $("partCount").textContent=String(parts.indexOf(p)+1).padStart(2,"0")+" / "+String(parts.length).padStart(2,"0");
 $("partNote").textContent=p.note;
 $("partSpecs").replaceChildren();
 for(const [k,v] of p.specs){const row=document.createElement("div"),dt=document.createElement("dt"),dd=document.createElement("dd");dt.textContent=k;dd.textContent=v;row.append(dt,dd);$("partSpecs").append(row);}
 $("annotation").querySelector("strong").textContent="SELECIONADO / "+p.name.toUpperCase();
 for(const pin of document.querySelectorAll(".pin"))pin.classList.toggle("selected",pin.dataset.id===p.id);
}
const pins=$("pins");
for(const p of parts){
 const el=document.createElement("button");el.className="pin";el.type="button";el.textContent=p.name;el.dataset.id=p.id;
 el.addEventListener("click",()=>select(p));pins.append(el);p.pin=el;
}
function pick(e){
 const b=canvas.getBoundingClientRect();mouse.x=((e.clientX-b.left)/b.width)*2-1;mouse.y=-((e.clientY-b.top)/b.height)*2+1;
 raycaster.setFromCamera(mouse,camera);const hits=raycaster.intersectObjects(clickable,false);
 if(hits.length && hits[0].object.userData.part)select(hits[0].object.userData.part);
}
canvas.addEventListener("pointerdown",e=>{pointerStart=[e.clientX,e.clientY]});
canvas.addEventListener("pointerup",e=>{if(pointerStart&&Math.hypot(e.clientX-pointerStart[0],e.clientY-pointerStart[1])<5)pick(e);pointerStart=null;});
function setProgress(v){
 target=Math.min(1,Math.max(0,v));
 $("progress").value=Math.round(target*100);
 $("progressValue").textContent=Math.round(target*100)+"%";
 $("toggleExplode").querySelector("span").textContent=target>.5?"MONTAR":"EXPLODIR";
}
$("progress").addEventListener("input",e=>{playing=false;updatePlay();setProgress(Number(e.target.value)/100)});
$("toggleExplode").addEventListener("click",()=>{playing=false;updatePlay();setProgress(target>.5?0:1)});
$("autoplay").addEventListener("click",()=>{playing=!playing;t=explosion;updatePlay()});
function updatePlay(){$("autoplay").innerHTML=playing?"Ⅱ PAUSAR":"▶ ANIMAR";$("autoplay").setAttribute("aria-pressed",String(playing));}
$("resetCamera").addEventListener("click",()=>{camera.position.set(13,11,15);orbit.target.set(0,0,0);orbit.update();});
$("showLabels").addEventListener("change",()=>{pins.hidden=!$("showLabels").checked});
$("speed").addEventListener("change",()=>{});
const v=new THREE.Vector3();
function frame(now){
 requestAnimationFrame(frame);
 const dt=Math.min((now-lastTime)/1000,.05);lastTime=now;
 if(playing){t+=dt*.22*Number($("speed").value);setProgress((1-Math.cos(t*Math.PI*2))/2);}
 explosion+= (target-explosion)*Math.min(1,dt*6.5);
 for(const p of parts){p.group.position.copy(p.offset).multiplyScalar(explosion);}
 orbit.update();
 for(const p of parts){
  v.copy(p.anchor).add(p.group.position);v.project(camera);
  const visible=v.z>-1&&v.z<1;
  const width=stage.clientWidth,height=stage.clientHeight;
  p.pin.style.display=visible && $("showLabels").checked && explosion>.33?"block":"none";
  if(visible){p.pin.style.left=((v.x+1)*width/2)+"px";p.pin.style.top=((1-v.y)*height/2)+"px";}
 }
 renderer.render(scene,camera);
}
function resize(){const w=stage.clientWidth,h=stage.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);}
new ResizeObserver(resize).observe(stage);resize();select(soc);requestAnimationFrame(frame);
window.addEventListener("error",e=>{if(e.message?.includes("WebGL"))$("stageError").hidden=false});
