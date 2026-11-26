import * as T from 'three';
import {buildCampus,makeWalker} from './campus.js';
import {lightWorld,periods} from './light.js';
import {cartography} from './cartography.js';
import './style.css';

const $=id=>document.getElementById(id);
const clamp=T.MathUtils.clamp;
const ACTIONS=['forward','back','left','right','run','up','down'];
const PORTS={
  start:{x:-279,z:-134,tx:-324,tz:-109},
  razak:{x:-275,z:-108,tx:-326,tz:-109},
  mjiit:{x:-262,z:-75,tx:-220,tz:-78},
  mosque:{x:-273,z:32,tx:-236,tz:43},
  inn:{x:-450,z:-40,tx:-430,tz:-61},
  hall:{x:-245,z:-174,tx:-245,tz:-220},
  residensi:{x:-184,z:20,tx:-106,tz:-27},
};
const GALLERY={id:'gallery',name:'Gaussian gallery',note:'An independent 3D Gaussian exhibit. Includes Marcel Padilla’s Houseplant and a crop of Necessity Robotics’ Shaded park walk, recorded in India. You can also open a local splat file.'};
const qualityScale=[.7,1,1.5,2];
const introEye=new T.Vector3(-163,83,89),introLook=new T.Vector3(-318,20,-131);
function bearing(x,z,tx,tz){return Math.atan2(x-tx,z-tz);}
const getTime=hour=>String(Math.trunc(hour)).padStart(2,'0')+':'+String(Math.round((hour%1)*60)).padStart(2,'0')+' MYT';

async function main() {
  const result=await fetch('campus.json');
  if(!result.ok)throw new Error('Campus map could not be read.');
  const data=await result.json();
  const renderer=new T.WebGLRenderer({antialias:true,powerPreference:'high-performance',alpha:false});
  renderer.outputColorSpace=T.SRGBColorSpace;
  renderer.toneMapping=T.ACESFilmicToneMapping;
  renderer.shadowMap.type=T.PCFShadowMap;
  renderer.shadowMap.autoUpdate=false;
  renderer.setClearColor(0x284137);
  $('viewport').appendChild(renderer.domElement);
  renderer.domElement.addEventListener('webglcontextlost',e=>{
    e.preventDefault();$('loader').hidden=false;$('loadError').textContent='Graphics interrupted. Waiting for recovery…';
  });
  renderer.domElement.addEventListener('webglcontextrestored',()=>{
    $('loader').hidden=true;$('loadError').textContent='';lights.settings(quality);
  });
  const scene=new T.Scene();
  const camera=new T.PerspectiveCamera(55,1,.075,2400);
  const {height,collides,mat,refs}=await buildCampus(renderer,scene,data);
  const lights=lightWorld(scene,renderer,mat);
  const {walker,animate,loadAvatar}=makeWalker();
  scene.add(walker);
  const map=cartography(data);
  const views=document.querySelectorAll('.panel');
  const viewport=$('viewport');
  const state={mode:'intro',first:false,run:false,photo:false,yaw:0,pitch:0,ev:0,lens:55,zoom:3.8};
  const position=new T.Vector3(),target=new T.Vector3(),aim=new T.Vector3(),look=new T.Vector3(),desired=new T.Vector3();
  const mapPos=new T.Vector3(-269,0,-127);
  const movement={x:0,z:0};
  const keys=new Set();
  let quality=1, startTime=performance.now(), previous=startTime,phase=0, activePanel=null;
  let jumpSpeed=0, jumpHeight=0, flightHeight=38, pointer=null, touch=null, menuPlace=null, mapProject=null,toastTimer;
  let gallery=null,galleryPromise=null, orbit=.36, orbitHeight=.22, orbitRadius=3.05, scanReturn='intro';
  let trail=null, trailYaw=0, trailPitch=0;
  let fps=60, frames=0, recent=1, lastMap=0, lastStats=0;
  let previousQuality=-1,lastWeather='gold';
  const ui={};
  for(const id of ['intro','walkHud','flightHud','modeName','scanMark','grid','locationHint','locationName','coordinates','clock','diagnostic','view','sprint'])ui[id]=$(id);

  function setCanvas() {
    const w=viewport.clientWidth,h=viewport.clientHeight;
    renderer.setPixelRatio(Math.min(devicePixelRatio,qualityScale[quality]));
    renderer.setSize(w,h,false);
    camera.aspect=Math.max(1,w)/Math.max(1,h);
    camera.updateProjectionMatrix();
  }
  addEventListener('resize',setCanvas);
  function toast(message) {
    $('toast').textContent=message;$('toast').hidden=false;clearTimeout(toastTimer);
    toastTimer=setTimeout(()=>$('toast').hidden=true,2600);
  }
  function showPanel(panel) {
    activePanel=activePanel===panel?null:panel;
    for(const view of views)view.hidden=view!==activePanel;
    if(activePanel===$('mapPanel'))mapProject=map.draw($('largeMap'),state.mode==='intro'?mapPos:position,state.yaw,true);
  }
  function dismiss(){
    for(const view of views)view.hidden=true;
    activePanel=null;
  }
  function setMode(mode) {
    state.mode=mode;
    const scanning=mode==='gallery',walking=mode==='walk';
    document.body.classList.toggle('intro',mode==='intro');
    ui.intro.hidden=mode!=='intro';
    ui.walkHud.hidden=!walking||state.photo;
    ui.flightHud.hidden=mode!=='fly'||state.photo;
    const joystickParent=scanning||mode!=='fly'?ui.walkHud:ui.flightHud;
    const joystick=$('joystick');
    if(joystick.parentElement!==joystickParent)joystickParent.prepend(joystick);
    joystick.style.visibility=walking||mode==='fly'?'visible':'hidden';
    ui.scanMark.hidden=!scanning;
    $('miniFrame').hidden=scanning||state.photo;
    ui.modeName.textContent=scanning?'3D GAUSSIAN':state.photo?'PHOTO MODE':walking?(state.first?'FIRST PERSON':'ON FOOT'):mode==='fly'?'DRONE':'AERIAL VIEW';
    walker.visible=walking&&!state.first;
    if(walker.visible)loadAvatar();
    ui.grid.hidden=!state.photo||!$('gridToggle').checked;
    ui.view.textContent=state.first?'1ST':'3RD';
    ui.sprint.classList.toggle('active',state.run);
    ui.locationName.textContent=scanning?'Houseplant':'UTM Kuala Lumpur';
    ui.locationHint.textContent=scanning?'Marcel Padilla · CC BY 4.0':'Explore the landmarks';
  }
  function safePoint(x,z) {
    const edge=data.extent-19;
    x=clamp(x,-edge,edge);z=clamp(z,-edge,edge);
    if(!collides(x,z))return [x,z];
    for(let r=2;r<108;r+=2)for(let j=0;j<16;j++){
      const a=j*Math.PI/8,nx=x+Math.cos(a)*r,nz=z+Math.sin(a)*r;
      if(!collides(nx,nz)&&Math.abs(nx)<edge&&Math.abs(nz)<edge)return [nx,nz];
    }
    return [PORTS.start.x,PORTS.start.z];
  }
  function relocate(port,mode='walk') {
    const [x,z]=safePoint(port.x,port.z);
    position.set(x,height(x,z),z);
    movement.x=movement.z=jumpHeight=jumpSpeed=0;
    state.yaw=bearing(x,z,port.tx,port.tz);
    walker.position.copy(position);
    walker.rotation.y=state.yaw;
    state.pitch=mode==='fly'?-.31:.10;
    flightHeight=mode==='fly'?38:flightHeight;
    setMode(mode);
    updateCamera(1,0);
  }
  function togglePhoto() {
    if(state.mode==='intro') {
      const x=introEye.x,z=introEye.z;
      relocate({x,z,tx:introLook.x,tz:introLook.z},'fly');
      flightHeight=introEye.y-height(x,z);
      state.pitch=Math.atan2(introLook.y-introEye.y,Math.hypot(introLook.x-x,introLook.z-z));
    }
    state.photo=!state.photo;
    if(!state.photo)state.ev=0;
    $('exposure').value=String(state.ev);
    $('expValue').textContent=state.ev.toFixed(1)+' EV';
    setMode(state.mode);
    if(state.photo)showPanel($('photoPanel'));
    else dismiss();
    updateProjection();
  }
  function updateProjection() {
    camera.fov=state.photo?state.lens:state.mode==='intro'?46:state.mode==='gallery'?43:55;
    camera.updateProjectionMatrix();
  }
  function setQuality(index){
    if(previousQuality===index)return;
    quality=index;previousQuality=index;
    lights.settings(index);
    setCanvas();
  }
  function setWeather(weather) {
    lastWeather=weather;lights.setWeather(weather);
    ui.clock.textContent=getTime(periods[weather].hour);
    try{localStorage.setItem('utm-weather',weather);}catch{}
  }
  function updateCamera(dt,t) {
    if(state.mode==='intro') {
      camera.position.copy(introEye);
      camera.position.x+=Math.sin(t*.19)*12;
      camera.position.z+=Math.sin(t*.12)*11;
      camera.lookAt(introLook);
      return;
    }
    if(state.mode==='gallery') {
      if(trail){
        camera.position.copy(trail.eye);
        look.copy(trail.forward).applyAxisAngle(T.Object3D.DEFAULT_UP,trailYaw);
        look.y+=trailPitch;
        camera.lookAt(aim.copy(camera.position).add(look));
        return;
      }
      camera.position.set(Math.sin(orbit)*orbitRadius,1.04+orbitHeight,Math.cos(orbit)*orbitRadius);
      camera.lookAt(0,.85,0);
      return;
    }
    const horizontal=Math.cos(state.pitch);
    look.set(-Math.sin(state.yaw)*horizontal,Math.sin(state.pitch),-Math.cos(state.yaw)*horizontal);
    if(state.mode==='fly') {
      target.set(position.x,height(position.x,position.z)+flightHeight,position.z);
      camera.position.lerp(target,1-Math.exp(-dt*13));
      camera.lookAt(aim.copy(camera.position).add(look));
      return;
    }
    target.copy(position);target.y+=state.first?1.59:1.40;
    if(state.first) {
      camera.position.lerp(target,1-Math.exp(-dt*21));
      camera.lookAt(aim.copy(camera.position).add(look));
      return;
    }
    desired.copy(target).addScaledVector(look,-state.zoom);
    desired.y=Math.max(desired.y+.57,height(desired.x,desired.z)+.53);
    for(let factor=1;factor>=.12;factor-=.13) {
      aim.copy(target).lerp(desired,factor);
      if(!collides(aim.x,aim.z,.18)){desired.copy(aim);break;}
    }
    camera.position.lerp(desired,1-Math.exp(-dt*13));
    camera.lookAt(aim.copy(target).addScaledVector(look,3.0));
  }
  function move(dt) {
    if(state.mode==='intro'||state.mode==='gallery')return;
    const stickX=touch?.x||0,stickZ=touch?.z||0;
    let sx=stickX+(keys.has('left')?-1:0)+(keys.has('right')?1:0);
    let sz=stickZ+(keys.has('forward')?-1:0)+(keys.has('back')?1:0);
    const len=Math.hypot(sx,sz);
    if(len>1){sx/=len;sz/=len;}
    if(state.photo && !keys.size){sx=0;sz=0;}
    const c=Math.cos(state.yaw),s=Math.sin(state.yaw);
    const flying=state.mode==='fly',running=state.run||keys.has('run');
    const speed=flying?(running?36:17):running?6.35:2.8;
    const alpha=1-Math.exp(-dt*11);
    movement.x+=(speed*(sx*c+sz*s)-movement.x)*alpha;
    movement.z+=(speed*(-sx*s+sz*c)-movement.z)*alpha;
    const lx=clamp(position.x+movement.x*dt,-data.extent+8,data.extent-8);
    const lz=clamp(position.z+movement.z*dt,-data.extent+8,data.extent-8);
    if(flying || !collides(lx,position.z))position.x=lx;
    if(flying || !collides(position.x,lz))position.z=lz;
    if(flying) {
      flightHeight=clamp(flightHeight+dt*((keys.has('up')?16:0)-(keys.has('down')?16:0)),3,270);
      return;
    }
    jumpSpeed-=dt*14.5;jumpHeight+=jumpSpeed*dt;
    if(jumpHeight<=0){jumpHeight=0;jumpSpeed=0;}
    position.y=height(position.x,position.z)+jumpHeight;
    walker.position.copy(position);
    const velocity=Math.hypot(movement.x,movement.z), stride=clamp(velocity/2.5,0,1.32);
    phase+=dt*(4.0+velocity*1.6);
    if(velocity>.16){
      const turn=bearing(0,0,movement.x,movement.z);
      walker.rotation.y+=Math.atan2(Math.sin(turn-walker.rotation.y),Math.cos(turn-walker.rotation.y))*alpha;
    }
    animate(phase,stride,dt,running);
  }
  function jump(){
    if(state.mode==='walk'&&jumpHeight===0)jumpSpeed=5.2;
  }
  function info(l) {
    menuPlace=l;$('placeTitle').textContent=l.name;$('placeDescription').textContent=l.note;
    $('visit').textContent=l.id==='gallery'?'Open gallery':'Visit location';
    showPanel($('placePanel'));
  }
  for(const l of [...data.landmarks,GALLERY]) {
    const button=document.createElement('button'), chevron=document.createElement('b');
    chevron.textContent='›';button.append(l.name,chevron);
    button.addEventListener('click',()=>info(l));$('places').append(button);
  }
  async function openGallery() {
    scanReturn=state.mode;
    if(scanReturn==='gallery')scanReturn='intro';
    dismiss();
    state.photo=false;
    setMode('gallery');updateProjection();
    $('scanText').textContent='Loading exhibit…';
    $('scanFileButton').hidden=true;
    $('exhibitSwitch').hidden=true;
    trail=null;
    try {
      galleryPromise ||= import('./gallery.js').then(({makeGallery})=>makeGallery(renderer)).catch(e=>{galleryPromise=null;throw e;});
      gallery=await galleryPromise;
      const count=await gallery.defaultSample();
      $('scanText').textContent=count.toLocaleString()+' Gaussians · Houseplant';
      $('scanFileButton').hidden=false;
      $('exhibitSwitch').hidden=false;
      $('exhibitSwitch').textContent='Outdoor scan';
    }catch(error){
      $('scanText').textContent='Exhibit unavailable on this graphics device';
      console.error(error);
    }
  }
  $('begin').onclick=()=>{dismiss();relocate(PORTS.start);updateProjection();};
  function launchDrone() {
    const {x,z}=position;
    const port=state.mode==='walk'?{x,z,tx:x-Math.sin(state.yaw)*10,tz:z-Math.cos(state.yaw)*10}:PORTS.start;
    state.photo=false;dismiss();relocate(port,'fly');updateProjection();
  }
  $('flyIntro').onclick=launchDrone;
  $('fly').onclick=launchDrone;
  $('view').onclick=()=>{state.first=!state.first;setMode('walk');};
  $('sprint').onclick=()=>{state.run=!state.run;setMode(state.mode);};
  $('jump').onclick=jump;
  $('land').onclick=()=>{const [x,z]=safePoint(position.x,position.z);relocate({x,z,tx:x-Math.sin(state.yaw)*10,tz:z-Math.cos(state.yaw)*10});};
  $('up').onclick=()=>{flightHeight=clamp(flightHeight+9,3,270);};
  $('down').onclick=()=>{flightHeight=clamp(flightHeight-9,3,270);};
  $('photoButton').onclick=togglePhoto;
  $('mapButton').onclick=()=>showPanel($('mapPanel'));
  $('miniFrame').onclick=()=>showPanel($('mapPanel'));
  $('miniFrame').onkeydown=e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();showPanel($('mapPanel'));}};
  $('settingsButton').onclick=()=>showPanel($('settingsPanel'));
  $('sourcesButton').onclick=()=>showPanel($('sourcePanel'));
  document.querySelectorAll('.close').forEach(b=>b.onclick=dismiss);
  $('exitScan').onclick=()=>{
    state.photo=false;dismiss();setMode(scanReturn);updateProjection();
  };
  $('exhibitSwitch').onclick=async()=>{
    if(!gallery)return;
    const button=$('exhibitSwitch');
    if(trail){
      trail=null;
      button.textContent='Outdoor scan';
      $('scanText').textContent=gallery.count().toLocaleString()+' Gaussians · object exhibit';
      ui.locationName.textContent='Houseplant';ui.locationHint.textContent='Marcel Padilla · CC BY 4.0';
      return;
    }
    button.disabled=true;$('scanText').textContent='Loading outdoor scan…';
    try{
      const next=await gallery.loadPark();
      if(state.mode!=='gallery')return;
      trail=next;trailYaw=trailPitch=0;
      button.textContent='Object scan';
      $('scanText').textContent=trail.count.toLocaleString()+' Gaussians · outdoor scan';
      ui.locationName.textContent='Shaded park walk · India';
      ui.locationHint.textContent='Necessity Robotics · CC BY 4.0';
    }catch(error){
      $('scanText').textContent='Outdoor exhibit unavailable';
      console.error(error);
    }finally{button.disabled=false;}
  };
  $('scanFile').onchange=async e=>{
    const file=e.target.files[0];e.target.value='';
    if(!file||!gallery)return;
    $('scanText').textContent='Reading local splat…';
    try{
      const count=await gallery.openFile(file);
      trail=null;$('exhibitSwitch').textContent='Outdoor scan';
      $('scanText').textContent=count.toLocaleString()+' Gaussians · local file';
      ui.locationName.textContent='Local exhibit';
      ui.locationHint.textContent=file.name;
    }catch(error){$('scanText').textContent=error.message||'Could not read splat';}
  };
  $('visit').onclick=()=>{
    if(menuPlace.id==='gallery'){openGallery();return;}
    state.photo=false;dismiss();relocate(PORTS[menuPlace.id]);updateProjection();toast(menuPlace.name);
  };
  $('largeMap').onclick=e=>{
    if(!mapProject)return;
    const rect=e.currentTarget.getBoundingClientRect(),c=e.currentTarget;
    const [x,z]=mapProject.screenToWorld((e.clientX-rect.left)*c.width/rect.width,(e.clientY-rect.top)*c.height/rect.height);
    let nearest=null,distance=29;
    for(const l of data.landmarks) {
      const d=Math.hypot(l.point[0]-x,l.point[1]-z);
      if(d<distance){nearest=l;distance=d;}
    }
    if(nearest)info(nearest);
    else {
      dismiss();state.photo=false;relocate({x,z,tx:x-15,tz:z-20});updateProjection();
    }
  };
  $('quality').onchange=e=>{
    setQuality(e.target.selectedIndex);
    try{localStorage.setItem('utm-quality',String(quality));}catch{}
  };
  $('weather').onchange=e=>setWeather(e.target.value);
  $('stats').onchange=e=>ui.diagnostic.hidden=!e.target.checked;
  $('gridToggle').onchange=e=>ui.grid.hidden=!e.target.checked;
  $('lens').oninput=e=>{state.lens=+e.target.value;$('lensValue').textContent=state.lens+'°';updateProjection();};
  $('exposure').oninput=e=>{state.ev=+e.target.value;$('expValue').textContent=state.ev.toFixed(1)+' EV';};
  $('offlineStill').onclick=()=>{
    $('cyclesImage').src='campus-cycles.jpg';
    showPanel($('stillPanel'));
  };
  $('capture').onclick=()=>{
    const width=+$('resolution').value, h=Math.round(width*9/16);
    const oldRatio=renderer.getPixelRatio(), oldAspect=camera.aspect;
    try {
      if(width>renderer.capabilities.maxTextureSize)throw new Error('Capture size exceeds this device’s graphics limit');
      renderer.setPixelRatio(1);renderer.setSize(width,h,false);
      camera.aspect=width/h;camera.updateProjectionMatrix();
      renderer.render(state.mode==='gallery'&&gallery?gallery.renderScene(Boolean(trail)):scene,camera);
      const name='UTMKL-'+new Date().toISOString().replace(/[:.]/g,'-')+'.jpg';
      const image=renderer.domElement.toDataURL('image/jpeg',.94);
      if(image==='data:,')throw new Error('This device could not capture this resolution');
      if(globalThis.CampusAndroid){
        const result=CampusAndroid.savePhoto(name,image);
        if(result!=='ok')throw new Error(result);
        toast('Saved to Pictures / UTMKL');
      }else{
        const link=document.createElement('a');link.download=name;link.href=image;link.click();toast('Photo saved');
      }
      $('flash').style.opacity='.62';
      setTimeout(()=>$('flash').style.opacity='0',80);
    }catch(error){toast(error.message);}
    finally {
      camera.aspect=oldAspect;camera.updateProjectionMatrix();
      renderer.setPixelRatio(oldRatio);renderer.setSize(viewport.clientWidth,viewport.clientHeight,false);
    }
  };

  const keyboard={KeyW:'forward',ArrowUp:'forward',KeyA:'left',ArrowLeft:'left',KeyD:'right',ArrowRight:'right',KeyS:'back',ArrowDown:'back',ShiftLeft:'run',ShiftRight:'run',KeyE:'up',KeyQ:'down'};
  addEventListener('keydown',e=>{
    if(['INPUT','SELECT'].includes(e.target.tagName))return;
    if(e.code==='Escape'){dismiss();return;}
    if(e.code==='Space'&&e.target.tagName!=='BUTTON'){e.preventDefault();jump();}
    if(e.code==='KeyV'&&state.mode==='walk')$('view').click();
    if(e.code==='KeyM')$('mapButton').click();
    if(e.code==='KeyP')togglePhoto();
    if(ACTIONS.includes(keyboard[e.code])){e.preventDefault();keys.add(keyboard[e.code]);}
  });
  addEventListener('keyup',e=>keys.delete(keyboard[e.code]));
  addEventListener('blur',()=>{keys.clear();touch=null;$('stick').style.transform='';});
  viewport.addEventListener('pointerdown',e=>{
    if(state.mode==='intro'||pointer)return;
    if(document.activeElement instanceof HTMLElement)document.activeElement.blur();
    pointer={id:e.pointerId,x:e.clientX,y:e.clientY};
    viewport.setPointerCapture(e.pointerId);
  });
  viewport.addEventListener('pointermove',e=>{
    if(pointer?.id!==e.pointerId)return;
    const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;
    pointer.x=e.clientX;pointer.y=e.clientY;
    if(state.mode==='gallery'){
      if(trail){trailYaw=clamp(trailYaw-dx*.006,-1.0,1.0);trailPitch=clamp(trailPitch-dy*.004,-.55,.55);}
      else {orbit-=dx*.009;orbitHeight=clamp(orbitHeight+dy*.014,-.43,2.4);}
      return;
    }
    state.yaw-=dx*.0058;
    state.pitch=clamp(state.pitch-dy*.0054,-1.32,1.25);
  });
  for(const n of ['pointerup','pointercancel','lostpointercapture']) viewport.addEventListener(n,e=>{if(pointer?.id===e.pointerId)pointer=null;});
  viewport.addEventListener('wheel',e=>{
    if(state.mode==='gallery')orbitRadius=clamp(orbitRadius+e.deltaY*.006,1.2,7);
    else if(state.mode==='fly')flightHeight=clamp(flightHeight-e.deltaY*.05,3,270);
    else state.zoom=clamp(state.zoom+e.deltaY*.004,1.7,7);
  },{passive:true});
  const joy=$('joystick');
  function shiftStick(e){
    if(touch?.id!==e.pointerId)return;
    const dx=e.clientX-touch.sx,dy=e.clientY-touch.sy;
    const magnitude=Math.max(24,Math.hypot(dx,dy));
    touch.x=dx/magnitude;
    touch.z=dy/magnitude;
    $('stick').style.transform='translate('+touch.x*24+'px,'+touch.z*24+'px)';
  }
  joy.addEventListener('pointerdown',e=>{
    if(touch)return;
    touch={id:e.pointerId,sx:e.clientX,sy:e.clientY,x:0,z:0};
    joy.setPointerCapture(e.pointerId);
  });
  joy.addEventListener('pointermove',shiftStick);
  for(const n of ['pointerup','pointercancel','lostpointercapture']) joy.addEventListener(n,e=>{
    if(touch?.id===e.pointerId){touch=null;$('stick').style.transform='';}
  });
  function frame(now) {
    const actualDt=Math.max(.001,(now-previous)/1000);
    const dt=clamp(actualDt,.001,.20);
    previous=now;
    const time=(now-startTime)/1000;
    frames++;recent+=actualDt;
    if(recent>.58){fps=Math.round(frames/recent);frames=0;recent=0;}
    const substeps=Math.max(1,Math.ceil(dt/.035));
    for(let i=0;i<substeps;i++)move(dt/substeps);
    if(state.mode==='gallery'&&!pointer)orbit+=dt*.145;
    updateCamera(dt,time);
    const scanning=state.mode==='gallery'&&gallery;
    if(scanning)renderer.toneMappingExposure=.97*(2**state.ev);
    else lights.tick(dt,time,camera,state.mode==='intro'?mapPos:position,state.ev);
    if(!scanning&&refs.update(camera,quality))renderer.shadowMap.needsUpdate=true;
    renderer.render(scanning?gallery.renderScene(Boolean(trail)):scene,camera);
    if(now-lastMap>155&&state.mode!=='gallery'){
      lastMap=now;
      const nowPos=state.mode==='intro'?mapPos:position;
      const currentYaw=state.mode==='intro'?bearing(introEye.x,introEye.z,introLook.x,introLook.z):state.yaw;
      map.draw($('mini'),nowPos,currentYaw,false);
      if(activePanel===$('mapPanel'))mapProject=map.draw($('largeMap'),nowPos,currentYaw,true);
      if(state.mode!=='intro'){
        let nearest=null,distance=Infinity;
        for(const l of data.landmarks){
          const d=Math.hypot(nowPos.x-l.point[0],nowPos.z-l.point[1]);
          if(d<distance){nearest=l;distance=d;}
        }
        ui.locationName.textContent=distance<108?nearest.name:'UTM Kuala Lumpur';
        ui.locationHint.textContent=distance<108?Math.round(distance)+' M FROM LANDMARK':'UTM CAMPUS DISTRICT';
        ui.coordinates.textContent=(data.origin[1]-nowPos.z/data.metersPerDegree[1]).toFixed(5)+' N  '+(data.origin[0]+nowPos.x/data.metersPerDegree[0]).toFixed(5)+' E';
      }
    }
    if(!ui.diagnostic.hidden&&now-lastStats>530){
      lastStats=now;
      const info=renderer.info;
      ui.diagnostic.textContent=fps+' FPS · '+(1000/Math.max(1,fps)).toFixed(1)+' ms\n'+info.render.calls+' draw calls · '+info.render.triangles.toLocaleString()+' triangles\n'+info.memory.textures+' textures · '+(scanning?(trail?.count||gallery.count()):0).toLocaleString()+' Gaussians\nWebGL2 · '+$('quality').value;
    }
    requestAnimationFrame(frame);
  }
  let savedQuality=1,savedWeather='gold';
  try {
    const q=localStorage.getItem('utm-quality');
    if(q!==null)savedQuality=clamp(Number(q)||0,0,3);
    const w=localStorage.getItem('utm-weather');
    if(w&&periods[w])savedWeather=w;
  }catch{}
  $('quality').selectedIndex=savedQuality;setQuality(savedQuality);
  $('weather').value=savedWeather;setWeather(savedWeather);
  setMode('intro');updateProjection();setCanvas();
  $('loader').hidden=true;
  requestAnimationFrame(frame);
  // Expose live state for repeatable graphics and traversal verification.
  if(import.meta.env.DEV) {
    globalThis.exportCampusForBlender=async()=>{
      const {GLTFExporter}=await import('three/addons/exporters/GLTFExporter.js');
      await refs.allHigh();
      const selected=scene.children.filter(node=>node.userData.architecture||node.isMesh&&node.material.isMeshStandardMaterial);
      const portable=new T.Scene();
      const matrix=new T.Matrix4(), tint=new T.Color();
      for(const node of selected){
        if(!node.isInstancedMesh||!node.instanceColor){portable.add(node.clone());continue;}
        const buckets=new Map();
        for(let i=0;i<node.count;i++){
          node.getColorAt(i,tint);
          const key=tint.getHex();
          if(!buckets.has(key))buckets.set(key,[]);
          buckets.get(key).push(i);
        }
        const groups=buckets.size>45?new Map([[0xdadfd3,Array.from({length:node.count},(_,i)=>i)]]):buckets;
        for(const [hex,instances] of groups) {
          const mat=node.material.clone();
          mat.color.multiply(new T.Color(hex));
          const copy=new T.InstancedMesh(node.geometry,mat,instances.length);
          instances.forEach((src,index)=>{node.getMatrixAt(src,matrix);copy.setMatrixAt(index,matrix);});
          portable.add(copy);
        }
      }
      const glb=await new GLTFExporter().parseAsync(portable,{binary:true});
      const a=document.createElement('a');
      a.href=URL.createObjectURL(new Blob([glb],{type:'model/gltf-binary'}));
      a.download='utmkl-core.glb';
      a.click();
      setTimeout(()=>URL.revokeObjectURL(a.href),12000);
    };
    globalThis.campusQA=()=>({mode:state.mode,keyboard:[...keys],world:position.toArray(),camera:camera.position.toArray(),quality,weather:lastWeather,splats:trail?.count||gallery?.count()||0,triangles:renderer.info.render.triangles,height:height(position.x,position.z),collides});
  }
}

main().catch(error=>{
  console.error(error);
  $('loadError').textContent='Could not start the 3D campus. This build requires hardware-accelerated Android System WebView with WebGL 2.';
  document.querySelector('.loadingBar')?.remove();
});
