import * as T from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
import { bridge, gpuProfile, mobile, native, report, savePhoto, touchInput } from './mobile.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import { createSite, spawn } from './site.js';
import './style.css';

const $=id=>document.getElementById(id);
const renderModes={
  Low:{ratio:.75,shadows:512,radius:1,exposure:1.10,photo:1920,transmission:0},
  Medium:{ratio:.95,shadows:768,radius:1.5,exposure:1.10,photo:1920,transmission:0},
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

function avatar() {
  const group=new T.Group();
  const navy=new T.MeshStandardMaterial({color:0x223846});
  const cream=new T.MeshStandardMaterial({color:0xd7b28d});
  const green=new T.MeshStandardMaterial({color:0xb8cd87});
  function part(geometry,material,x,y,z) {
    const mesh=new T.Mesh(geometry,material);
    mesh.position.set(x,y,z);group.add(mesh);return mesh;
  }
  part(new T.CapsuleGeometry(.22,.42,5,10),green,0,1.11,0);
  part(new T.SphereGeometry(.141,12,8),cream,0,1.66,0);
  part(new T.BoxGeometry(.32,.43,.12),navy,0,1.15,.21);
  const legs=[-.115,.115].map(x=>part(new T.CapsuleGeometry(.087,.49,4,8),navy,x,.39,0));
  const arms=[-.29,.29].map(x=>part(new T.CapsuleGeometry(.055,.42,4,8),green,x,1.08,0));
  group.visible=false;
  return {group,legs,arms};
}

function progress(value,message) {
  $('progress').value=value;
  $('load-status').textContent=message;
}

function safeRestart() {
  sessionStorage.setItem('utm-safe','1');
  location.reload();
}
$('retry').addEventListener('click',safeRestart);

async function run() {
  const world=$('world');
  if(mobile){
    document.body.classList.add('mobile');
    if(native) document.title='UTMKL REAL WORLD';
  }
  const device=native ? await bridge.device().catch(()=>({})) : {};
  const safe=device.safe || sessionStorage.getItem('utm-safe')==='1';
  sessionStorage.removeItem('utm-safe');
  const canvasElement=document.createElement('canvas');
  const attributes={antialias:!mobile,alpha:false,powerPreference:'high-performance'};
  const context=canvasElement.getContext('webgl2',attributes);
  if(!context)throw Error('当前 WebView 无法创建 WebGL 2，请更新 Android System WebView。');
  const gpu=gpuProfile(context);
  report(`WebGL2 ready; renderer=${gpu.name}; maxTexture=${gpu.textureSize}; API=${device.sdk}; ABI=${device.abi}; WebView=${device.webView}`);
  const renderer=new T.WebGLRenderer({canvas:canvasElement,context,...attributes});
  canvasElement.addEventListener('webglcontextlost',event=>{
    event.preventDefault();
    $('loading').hidden=false;$('retry').hidden=false;
    progress(0,'GPU 渲染已中断，可使用安全画质重新加载。');
    report('WebGL2 context lost');
  });
  canvasElement.addEventListener('webglcontextrestored',safeRestart,{once:true});
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
  let ktx;
  const root=mobile ? 'mobile-assets' : 'assets';
  if(mobile) {
    ktx=new KTX2Loader().setTranscoderPath('mobile-assets/').setWorkerLimit(gpu.constrained ? 1 : 2);
    ktx.detectSupport(renderer);
    gltf.setKTX2Loader(ktx);
  }
  let loaded=0;
  const step=()=>progress(14+ ++loaded*22,'正在读取塔楼、地形与材质…');
  const load=file=>gltf.loadAsync(`${root}/${file}`).then(asset=>{step();return asset;});
  const timeout=setTimeout(()=>{
    $('retry').hidden=false;
    $('load-status').textContent='场景载入较慢，可继续等待或使用安全画质重试。';
  },90000);
  progress(14,'正在读取塔楼、地形与材质…');
  const data=await fetch('assets/site.json').then(r=>{if(!r.ok)throw Error('Site file missing');return r.json();});
  const [tower,setting]=mobile
    ? [await load('Menara_Razak_Runtime.glb'), await load('Core_Site.glb')]
    : await Promise.all([load('Menara_Razak_Runtime.glb'),load('Core_Site.glb')]);
  clearTimeout(timeout);
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
  let mode='High', level=renderModes.High, toastTimer, dynamicScale=1;
  let x=spawn.x,y=spawn.y,pitch=.16,yaw=-.19;
  let dirty=true, third=false, flying=false, jump=0, lift=0, velocity=0, pace=0;
  let photoPending=false, captureBusy=false, scanView=null, scanReady=false, scanStarted=0;
  let benchFrames=0, benchDt=0;
  const player=mobile ? avatar() : null;
  if(player)scene.add(player.group);
  const pressed=new Set();
  const movementCodes=new Set(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight']);
  const canvas=renderer.domElement;
  const pointer={id:null,x:0,y:0,drag:false};
  const eyeHeight=1.67;
  let eye=site.ground(x,y)+eyeHeight;
  const flags={run:false,jump:false,up:false,down:false};
  const stick=mobile ? touchInput(canvas,turn,zoom,flags) : {x:0,y:0};

  async function finishSite() {
    try {
      const tree=await gltf.loadAsync(`${root}/Core_Tree.glb`);
      addTrees(scene,tree.scene,data.trees,site.terrain);
      const sky=await new HDRLoader().loadAsync('assets/Daylight.hdr');
      sky.mapping=T.EquirectangularReflectionMapping;
      scene.environment=sky;
      scene.environmentIntensity=.67;
      scene.background=sky;
      scene.backgroundIntensity=.48;
      scene.backgroundBlurriness=.12;
      renderer.shadowMap.needsUpdate=true;
      dirty=true;
      report(`Optional site chunks ready; textures=${renderer.info.memory.textures}`);
    } catch(error) {
      report('Optional vegetation or HDR chunk failed');
      console.warn(error);
      if(!mobile)throw error;
      toast('环境细节载入失败，可继续探索核心区。');
    } finally { ktx?.dispose(); }
  }

  function zoom(factor){
    const view=scanView?.camera ?? camera;
    view.fov=T.MathUtils.clamp(view.fov/factor,34,82);
    view.updateProjectionMatrix();dirty=true;
  }

  function syncCamera(){
    const c=Math.cos(yaw),s=Math.sin(yaw);
    camera.position.set(x,eye,-y);
    camera.rotation.set(pitch,yaw,0,'YXZ');
    if(!player)return;
    player.group.visible=third;
    if(!third)return;
    player.group.position.set(x,eye-eyeHeight,-y);
    player.group.rotation.y=yaw;
    const stride=pace ? Math.sin(performance.now()*.012)*.34*pace : 0;
    for(let i=0;i<2;i++){
      player.legs[i].rotation.x=(i ? -1 : 1)*stride;
      player.arms[i].rotation.x=(i ? 1 : -1)*stride;
    }
    const distance=3.15;
    const back=flying ? {x:x+s*distance,y:y-c*distance} : site.move(x,y,s*distance,-c*distance);
    camera.position.set(back.x,eye+1.08,-back.y);
    camera.lookAt(x-s*2.4,eye+Math.tan(pitch)*3-.12,-y-c*2.4);
  }
  function resize(){
    dirty=true;
    renderer.setPixelRatio(Math.min(devicePixelRatio,level.ratio)*dynamicScale);
    renderer.setSize(world.clientWidth,world.clientHeight,false);
    camera.aspect=world.clientWidth/Math.max(1,world.clientHeight);
    camera.updateProjectionMatrix();
    if(scanView){scanView.camera.aspect=camera.aspect;scanView.camera.updateProjectionMatrix();}
  }
  function setQuality(name) {
    mode=name;level=renderModes[name];dynamicScale=1;benchDt=0;benchFrames=0;
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
    renderer.shadowMap.enabled=!mobile||mode!=='Low';
    resize();
    report(`Preset ${name}; pixelRatio=${renderer.getPixelRatio().toFixed(2)}`);
  }
  $('quality').addEventListener('change',e=>setQuality(e.target.value));
  addEventListener('resize',resize);
  function toast(message){
    $('toast').textContent=message;$('toast').hidden=false;
    clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,1800);
  }
  function reset(){
    x=spawn.x;y=spawn.y;pitch=.16;yaw=-.19;
    eye=site.ground(x,y)+eyeHeight;jump=lift=velocity=0;syncCamera();dirty=true;
  }

  async function capture(){
    if(captureBusy)return;
    captureBusy=true;photoPending=true;
    const largest=mobile&&gpu.constrained ? 2560 : 3840;
    const width=Math.min(level.photo,largest,renderer.capabilities.maxTextureSize);
    const height=Math.round(width*9/16);
    const view=scanView?.camera??camera;
    const content=scanView?.scene??scene;
    const aspect=view.aspect,ratio=renderer.getPixelRatio();
    try {
      renderer.setPixelRatio(1);renderer.setSize(width,height,false);
      view.aspect=width/height;view.updateProjectionMatrix();
      renderer.render(content,view);
      await savePhoto(canvas,`UTMKL-${mode}.png`);
      toast(`${width} × ${height} 截图已保存${native?'至相册':''}`);
      report(`Photo saved ${width}x${height}`);
    }catch(error){console.warn(error);toast('截图失败，请切换到 High 再试');}
    finally {
      view.aspect=aspect;view.updateProjectionMatrix();
      renderer.setPixelRatio(ratio);renderer.setSize(world.clientWidth,world.clientHeight,false);
      captureBusy=false;photoPending=false;dirty=true;
    }
  }
  $('capture').addEventListener('click',capture);
  if(mobile){
    $('camera-mode').addEventListener('click',()=>{
      third=!third;$('camera-mode').textContent=third?'第一人称':'第三人称';dirty=true;
      report(third?'Camera third person':'Camera first person');
    });
    $('flight').addEventListener('click',()=>{
      flying=!flying;velocity=jump=0;
      if(!flying){
        if(!site.allowed(x,y))reset();
        lift=0;
      }
      $('flight').setAttribute('aria-pressed',String(flying));
      $('up').textContent=flying?'上升':'跳跃';
      $('down').hidden=!flying;
      dirty=true;
      report(flying?'Flight enabled':'Flight disabled');
    });
    $('scan').addEventListener('click',async()=>{
      if(scanView){
        scanView.scene.remove(scanView.scan,scanView.spark);
        scanView.scan.dispose();
        scanView.spark.defaultView.dispose();
        scanView.spark.material.dispose();
        scanView=null;$('scan-label').hidden=true;
        $('scan').textContent='高斯测试';$('joystick').hidden=false;
        document.querySelector('.actions').hidden=false;
        renderer.shadowMap.needsUpdate=true;dirty=true;
        return;
      }
      $('scan').disabled=true;$('loading').hidden=false;$('retry').hidden=true;
      progress(30,'正在加载独立高斯测试场景…');
      try {
        const {openScan}=await import('./splat.js');
        scanView=await openScan(renderer);
        scanView.camera.aspect=camera.aspect;
        scanView.camera.updateProjectionMatrix();
        scanStarted=performance.now();scanReady=false;
        $('scan-label').hidden=false;$('scan').textContent='返回校园';
        $('joystick').hidden=true;document.querySelector('.actions').hidden=true;
        dirty=true;
      } catch(error){
        console.warn(error);report('Spark asset failed');toast('高斯场景载入失败');
      } finally{
        $('scan').disabled=false;$('loading').hidden=true;
      }
    });
  }
  addEventListener('keydown',e=>{
    if(['INPUT','SELECT'].includes(e.target.tagName))return;
    if(e.code==='Space'&&mobile){flags.jump=true;e.preventDefault();}
    if(movementCodes.has(e.code)){pressed.add(e.code);e.preventDefault();}
    if(e.code==='KeyR')reset();
    if(e.code==='KeyP'&&!e.repeat)capture();
  });
  addEventListener('keyup',e=>pressed.delete(e.code));
  addEventListener('blur',()=>{pressed.clear();flags.up=flags.down=flags.run=flags.jump=false;});
  canvas.addEventListener('wheel',event=>{if(mobile){event.preventDefault();zoom(Math.exp(-event.deltaY*.004));}},{passive:false});
  document.addEventListener('pointerlockchange',()=>{
    $('reticle').hidden=document.pointerLockElement!==canvas;
    if(document.pointerLockElement!==canvas)pressed.clear();
  });
  function turn(dx,dy){
    dirty=true;
    if(scanView){
      const rotation=scanView.camera.rotation;
      rotation.y-=dx*.0031;
      rotation.x=T.MathUtils.clamp(rotation.x-dy*.0031,-1.39,1.39);
      return;
    }
    yaw-=dx*.0031;
    pitch=T.MathUtils.clamp(pitch-dy*.0031,-1.39,1.39);
  }
  canvas.addEventListener('pointerdown',e=>{
    document.activeElement?.blur();
    if(document.pointerLockElement===canvas||(mobile&&e.pointerType!=='mouse'))return;
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
    const frameTime=(now-last)/1000;
    const dt=Math.min(.10,Math.max(.001,frameTime));last=now;
    requestAnimationFrame(tick);
    if(photoPending || document.hidden || context.isContextLost())return;
    if(scanView){
      if(dirty || !scanReady){
        renderer.render(scanView.scene,scanView.camera);
        const drawn=scanView.spark.uniforms.numSplats.value;
        dirty=false;
        if(!scanReady&&drawn>0){
          scanReady=true;report(`Spark draw: decoded=${scanView.count}; GPU splats=${drawn}; triangles=${renderer.info.render.triangles}`);
        }else if(!scanReady&&now-scanStarted>30000){
          scanReady=true;report('Spark GPU sort did not finish');toast('高斯排序未完成，可返回校园');
        }
      }
      return;
    }
    const sx=stick.x+Number(pressed.has('KeyD')||pressed.has('ArrowRight'))-Number(pressed.has('KeyA')||pressed.has('ArrowLeft'));
    const sy=stick.y+Number(pressed.has('KeyW')||pressed.has('ArrowUp'))-Number(pressed.has('KeyS')||pressed.has('ArrowDown'));
    const previousPace=pace;
    pace=Math.min(1,Math.hypot(sx,sy));
    if(pace){
      const speed=(flags.run||pressed.has('ShiftLeft')||pressed.has('ShiftRight')?5.8:2.9)*dt/Math.max(1,Math.hypot(sx,sy));
      const c=Math.cos(yaw),s=Math.sin(yaw);
      const dx=(sx*c-sy*s)*speed,dy=(sx*s+sy*c)*speed;
      const next=flying ? {x:T.MathUtils.clamp(x+dx,-54,69),y:T.MathUtils.clamp(y+dy,-47,32)} : site.move(x,y,dx,dy);
      dirty ||= next.x!==x || next.y!==y;
      if(flying && !site.allowed(next.x,next.y) && eye<56){
        if(site.allowed(x,y)){report('Flight blocked by core geometry below roof');}
      }else{x=next.x;y=next.y;}
    }
    dirty ||= third && previousPace!==pace;
    if(flying){
      const scale=flags.run?11:5.1;
      const floor=site.allowed(x,y)?0:56-site.ground(x,y)-eyeHeight;
      const next=T.MathUtils.clamp(lift+(Number(flags.up)-Number(flags.down))*dt*scale,floor,66);
      dirty ||= next!==lift;
      lift=next;
    }else{
      if(flags.jump&&jump===0&&velocity===0){velocity=4.15;report('Jump started');}
      if(jump>0||velocity>0){
        velocity-=11.3*dt;
        jump=Math.max(0,jump+velocity*dt);
        if(!jump)velocity=0;
        dirty=true;
      }
    }
    flags.jump=false;
    const targetHeight=site.ground(x,y)+eyeHeight+jump+lift;
    if(Math.abs(targetHeight-eye)>.001){
      eye+=(targetHeight-eye)*(1-Math.exp(-14*dt));
      dirty=true;
    }
    if(dirty){
      syncCamera();
      renderer.render(scene,camera);
      frames++;dirty=false;
      if(frames===1)report(`Campus draw: triangles=${renderer.info.render.triangles}; textures=${renderer.info.memory.textures}`);
      if(mobile&&pace&&frameTime<.6) {
        benchDt+=frameTime;benchFrames++;
        if(benchFrames===20){
          const avg=benchDt/benchFrames;
          const scale=avg>.042?Math.max(.56,dynamicScale-.12):avg<.025?Math.min(1,dynamicScale+.08):dynamicScale;
          benchDt=0;benchFrames=0;
          if(scale!==dynamicScale){dynamicScale=scale;resize();}
        }
      }
    }
  }

  // Enable state observation on the built artifact only for explicit QA runs.
  if(new URLSearchParams(location.search).has('qa')) {
    globalThis.coreQA=()=>({x,y,eye,frames,mode,shadows:sun.shadow.mapSize.x,triangles:renderer.info.render.triangles,yaw,pitch,third,flying,lift,fov:camera.fov,jump,splats:scanReady&&scanView?scanView.spark.uniforms.numSplats.value:0,wall:site.allowed(0,0),view:camera.position.toArray(),stale:stale.length});
    globalThis.coreQAPosition=(px,py,heading=0,tilt=.10)=>{
      if(!site.allowed(px,py))throw Error('QA position outside site');
      x=px;y=py;yaw=heading;pitch=tilt;eye=site.ground(x,y)+eyeHeight;syncCamera();dirty=true;
    };
  }
  if(!mobile)await finishSite();
  const initial=mobile ? (safe || gpu.constrained ? 'Low' : gpu.adreno ? 'Medium' : 'High') : 'High';
  $('quality').value=initial;
  setQuality(initial);reset();
  $('mobile-controls').hidden=!mobile;
  progress(100,'场景就绪');$('loading').hidden=true;$('capture').disabled=false;
  requestAnimationFrame(tick);
  if(mobile) {
    // Wait for the first visible campus frame before decoding the vegetation chunk.
    requestAnimationFrame(()=>requestAnimationFrame(finishSite));
  }
}
run().catch(error=>{
  console.error(error);report(`Startup failed: ${error.message}`);
  $('loading').hidden=false;$('retry').hidden=false;
  progress(0, error.message || '场景无法启动，请尝试安全画质。');
});
