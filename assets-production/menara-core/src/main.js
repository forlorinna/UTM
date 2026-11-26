import * as T from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import { createSite, spawn } from './site.js';
import './style.css';

const $=id=>document.getElementById(id);
const renderModes={
  High:{ratio:1, shadows:1024, radius:2, exposure:1.10, photo:1920, transmission:0},
  Ultra:{ratio:1.45, shadows:1536, radius:3, exposure:1.12, photo:2560, transmission:.45},
  Cinematic:{ratio:2, shadows:2048, radius:4, exposure:1.17, photo:3840, transmission:1},
};
const obsolete=/^(Immediate plaza seatwall|Curved canopy forecourt paving|Light concrete perimeter walk|Light concrete apron|Seatwall stone planter|Inset dark planter bed|Small forecourt planting)/i;

function addTrees(scene, group, configs, terrain) {
  group.updateMatrixWorld(true);
  const bounds=new T.Box3().setFromObject(group);
  const center=bounds.getCenter(new T.Vector3());
  center.y=bounds.min.y;
  const toOrigin=new T.Matrix4().makeTranslation(-center.x,-center.y,-center.z);
  const helper=new T.Object3D();
  const m=new T.Matrix4();
  group.traverse(node=>{
    if(!node.isMesh)return;
    const trees=new T.InstancedMesh(node.geometry,node.material,configs.length);
    for(let i=0;i<configs.length;i++){
      const [x,y,height]=configs[i];
      helper.position.set(x,terrain(x,y)+.02,-y);
      helper.scale.setScalar(height/(bounds.max.y-bounds.min.y));
      helper.rotation.y=(i*2.399)%(2*Math.PI);
      helper.updateMatrix();
      trees.setMatrixAt(i,m.copy(helper.matrix).multiply(toOrigin).multiply(node.matrixWorld));
    }
    trees.castShadow=true;trees.receiveShadow=true;
    trees.computeBoundingSphere();
    scene.add(trees);
  });
}

async function run() {
  const world=$('world');
  const renderer=new T.WebGLRenderer({ antialias:true, alpha:false, powerPreference:'high-performance' });
  renderer.setClearColor(0xbfd1d5);
  renderer.outputColorSpace=T.SRGBColorSpace;
  renderer.toneMapping=T.ACESFilmicToneMapping;
  renderer.shadowMap.type=T.PCFShadowMap;
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.autoUpdate=false;
  renderer.domElement.setAttribute('aria-label','Menara Razak 环境');
  world.appendChild(renderer.domElement);
  const scene=new T.Scene();
  scene.background=new T.Color(0xc9dde4);
  scene.fog=new T.FogExp2(0xc2d4db,.0043);
  const camera=new T.PerspectiveCamera(67,1,.055,325);
  camera.rotation.order='YXZ';
  const sun=new T.DirectionalLight(0xffead0,2.7);
  sun.position.set(-42,68,69);
  sun.target.position.set(6,0,3);
  sun.castShadow=true;
  Object.assign(sun.shadow.camera,{left:-63,right:63,top:66,bottom:-66,near:4,far:161});
  sun.shadow.normalBias=.045;
  sun.shadow.bias=-.00010;
  scene.add(sun,sun.target,new T.HemisphereLight(0xe9f1ff,0x69634d,1.48));
  const gltf=new GLTFLoader();
  const pending=Promise.all([
    fetch('assets/site.json').then(r=>{if(!r.ok)throw Error('Site file missing');return r.json();}),
    gltf.loadAsync('assets/Menara_Razak_Runtime.glb'),
    gltf.loadAsync('assets/Core_Site.glb'),
    gltf.loadAsync('assets/Core_Tree.glb'),
    new HDRLoader().loadAsync('assets/Daylight.hdr'),
  ]);
  const [data,tower,setting,tree,sky]=await pending;
  const site=createSite(data);
  const stale=[];
  tower.scene.traverse(node=>{if(obsolete.test(node.name.replaceAll('_',' ')))stale.push(node);});
  for(const node of stale)node.removeFromParent();
  scene.add(tower.scene,setting.scene);
  const views=[tower.scene,setting.scene];
  const glass=new Map();
  for(const group of views) group.traverse(node=>{
    if(!node.isMesh)return;
    node.castShadow=!/^(Terrain|Road|Plaza|Walk|Curb|Platform|Roundabout)/.test(node.name);
    node.receiveShadow=true;
    const mats=Array.isArray(node.material)?node.material:[node.material];
    for(const material of mats){
      if(material.transmission>0)glass.set(material,material.transmission);
      if(material.map)material.map.anisotropy=4;
      if(material.normalMap)material.normalMap.anisotropy=4;
    }
  });
  addTrees(scene,tree.scene,data.trees,site.terrain);
  sky.mapping=T.EquirectangularReflectionMapping;
  scene.environment=sky;
  scene.environmentIntensity=.67;
  scene.background=sky;
  scene.backgroundIntensity=.48;
  scene.backgroundBlurriness=.12;

  let x=spawn.x,y=spawn.y,pitch=.16,yaw=-.19;
  let mode='High', level=renderModes.High, toastTimer;
  let dirty=true;
  const pressed=new Set();
  const movementCodes=new Set(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight']);
  const canvas=renderer.domElement;
  const pointer={id:null,x:0,y:0,drag:false};
  const eyeHeight=1.67;
  let eye=site.ground(x,y)+eyeHeight;

  function syncCamera(){
    camera.position.set(x,eye,-y);
    camera.rotation.set(pitch,yaw,0,'YXZ');
  }
  function resize(){
    dirty=true;
    renderer.setPixelRatio(Math.min(devicePixelRatio,level.ratio));
    renderer.setSize(world.clientWidth,world.clientHeight,false);
    camera.aspect=world.clientWidth/Math.max(1,world.clientHeight);
    camera.updateProjectionMatrix();
  }
  function setQuality(name) {
    mode=name;level=renderModes[name];
    sun.shadow.map?.dispose();sun.shadow.map=null;
    sun.shadow.mapSize.set(level.shadows,level.shadows);
    sun.shadow.radius=level.radius;
    renderer.shadowMap.needsUpdate=true;
    renderer.toneMappingExposure=level.exposure;
    for(const [material,value] of glass){
      const transmission=level.transmission*value;
      if((material.transmission>0)!==(transmission>0))material.needsUpdate=true;
      material.transmission=transmission;
    }
    resize();
  }
  $('quality').addEventListener('change',e=>setQuality(e.target.value));
  addEventListener('resize',resize);
  function toast(message){
    $('toast').textContent=message;$('toast').hidden=false;
    clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,1800);
  }
  function reset(){
    x=spawn.x;y=spawn.y;pitch=.16;yaw=-.19;
    eye=site.ground(x,y)+eyeHeight;syncCamera();dirty=true;
  }
  function capture(){
    const width=Math.min(level.photo,renderer.capabilities.maxTextureSize);
    const height=Math.round(width*9/16);
    const aspect=camera.aspect, ratio=renderer.getPixelRatio();
    try {
      renderer.setPixelRatio(1);renderer.setSize(width,height,false);
      camera.aspect=width/height;camera.updateProjectionMatrix();
      renderer.render(scene,camera);
      const link=document.createElement('a');
      link.href=canvas.toDataURL('image/png');
      if(link.href==='data:,')throw Error('Capture unavailable');
      link.download='Menara-Razak-'+mode+'.png';link.click();
      toast(width+' × '+height+' 截图已保存');
    }catch{toast('截图失败，请切换到 High 再试');}
    finally {
      camera.aspect=aspect;camera.updateProjectionMatrix();
      renderer.setPixelRatio(ratio);renderer.setSize(world.clientWidth,world.clientHeight,false);
      dirty=true;
    }
  }
  $('capture').addEventListener('click',capture);
  addEventListener('keydown',e=>{
    if(['INPUT','SELECT'].includes(e.target.tagName))return;
    if(movementCodes.has(e.code)){pressed.add(e.code);e.preventDefault();}
    if(e.code==='KeyR')reset();
    if(e.code==='KeyP'&&!e.repeat)capture();
  });
  addEventListener('keyup',e=>pressed.delete(e.code));
  addEventListener('blur',()=>pressed.clear());
  document.addEventListener('pointerlockchange',()=>{
    $('reticle').hidden=document.pointerLockElement!==canvas;
    if(document.pointerLockElement!==canvas)pressed.clear();
  });
  function turn(dx,dy){
    dirty=true;
    yaw-=dx*.0031;
    pitch=T.MathUtils.clamp(pitch-dy*.0031,-1.39,1.39);
  }
  canvas.addEventListener('pointerdown',e=>{
    document.activeElement?.blur();
    if(document.pointerLockElement===canvas)return;
    pointer.id=e.pointerId;pointer.x=e.clientX;pointer.y=e.clientY;pointer.drag=false;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove',e=>{
    if(document.pointerLockElement===canvas){turn(e.movementX,e.movementY);return;}
    if(pointer.id!==e.pointerId)return;
    const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;
    pointer.x=e.clientX;pointer.y=e.clientY;
    if(Math.abs(dx)+Math.abs(dy)>1)pointer.drag=true;
    if(pointer.drag)turn(dx,dy);
  });
  canvas.addEventListener('pointerup',e=>{
    if(pointer.id!==e.pointerId)return;
    pointer.id=null;
    if(!pointer.drag&&e.pointerType==='mouse'&&canvas.requestPointerLock){
      Promise.resolve(canvas.requestPointerLock()).catch(()=>{});
    }
  });
  canvas.addEventListener('pointercancel',()=>pointer.id=null);
  let last=performance.now(), frames=0;
  function tick(now){
    const dt=Math.min(.10,Math.max(.001,(now-last)/1000));last=now;
    const sx=Number(pressed.has('KeyD')||pressed.has('ArrowRight'))-Number(pressed.has('KeyA')||pressed.has('ArrowLeft'));
    const sy=Number(pressed.has('KeyW')||pressed.has('ArrowUp'))-Number(pressed.has('KeyS')||pressed.has('ArrowDown'));
    if(sx||sy){
      const speed=(pressed.has('ShiftLeft')||pressed.has('ShiftRight')?4.8:2.9)*dt/Math.hypot(sx,sy);
      const c=Math.cos(yaw),s=Math.sin(yaw);
      const next=site.move(x,y,(sx*c-sy*s)*speed,(sx*s+sy*c)*speed);
      dirty ||= next.x!==x || next.y!==y;
      x=next.x;y=next.y;
    }
    const targetHeight=site.ground(x,y)+eyeHeight;
    if(Math.abs(targetHeight-eye)>.001){
      eye+=(targetHeight-eye)*(1-Math.exp(-14*dt));
      dirty=true;
    }
    if(dirty){
      syncCamera();
      renderer.render(scene,camera);
      frames++;dirty=false;
    }
    requestAnimationFrame(tick);
  }

  // Enable state observation on the built artifact only for explicit QA runs.
  if(new URLSearchParams(location.search).has('qa')) {
    globalThis.coreQA=()=>({x,y,eye,frames,mode,shadows:sun.shadow.mapSize.x,triangles:renderer.info.render.triangles,wall:site.allowed(0,0),view:camera.position.toArray(),stale:stale.length});
    globalThis.coreQAPosition=(px,py,heading=0,tilt=.10)=>{
      if(!site.allowed(px,py))throw Error('QA position outside site');
      x=px;y=py;yaw=heading;pitch=tilt;eye=site.ground(x,y)+eyeHeight;syncCamera();dirty=true;
    };
  }
  setQuality('High');reset();
  $('loading').hidden=true;$('capture').disabled=false;
  requestAnimationFrame(tick);
}
run().catch(error=>{
  console.error(error);
  $('loading').textContent='场景无法启动。请通过本地服务器打开，并确认浏览器支持 WebGL 2。';
});
