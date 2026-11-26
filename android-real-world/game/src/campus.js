import * as T from 'three';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const X = (x,z) => new T.Vector2(x,z);
const temp = new T.Object3D();
const color = new T.Color();

export function random(seed) {
  return () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 4294967296;
  };
}

export function inside(x,z,ring) {
  let result = false;
  for (let i=0,j=ring.length-1;i<ring.length;j=i++) {
    const a=ring[i], b=ring[j];
    if ((a[1]>z)!=(b[1]>z) && x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]) result=!result;
  }
  return result;
}

export function distanceSquared(x,z,a,b) {
  const dx=b[0]-a[0], dz=b[1]-a[1];
  const t=T.MathUtils.clamp(((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1),0,1);
  return (x-a[0]-t*dx)**2+(z-a[1]-t*dz)**2;
}

function indexedBounds(b) {
  return b.p[0].reduce(([x0,z0,x1,z1],[x,z])=>[Math.min(x,x0),Math.min(z,z0),Math.max(x,x1),Math.max(z,z1)],[Infinity,Infinity,-Infinity,-Infinity]);
}

function geometry(positions,uvs,colors) {
  const g=new T.BufferGeometry();
  g.setAttribute('position',new T.Float32BufferAttribute(positions,3));
  g.setAttribute('uv',new T.Float32BufferAttribute(uvs,2));
  if(colors)g.setAttribute('color',new T.Float32BufferAttribute(colors,3));
  g.computeVertexNormals();
  return g;
}

function surfaceMesh(scene,g,material,cast=false) {
  const m=new T.Mesh(g,material);
  m.receiveShadow=true;
  m.castShadow=cast;
  scene.add(m);
  return m;
}

function palmFrond() {
  const p=[],uv=[];
  const vertex=(x,y,z)=>{p.push(x,y,z);uv.push(x,z);};
  for(let i=0;i<13;i++){
    const t=(i+.9)/14, y=.38*Math.sin(t*2.6)-.54*t*t;
    const width=.27*Math.sin(Math.PI*t)**.73;
    for(const s of [-1,1]){
      vertex(0,y,t);vertex(s*width*.45,y+.022,t+.045);vertex(s*width,y-.10,t+.13);
      vertex(0,y,t);vertex(s*width,y-.10,t+.13);vertex(0,y-.025,t+.068);
    }
    vertex(-.009,y,t);vertex(.009,y,t);vertex(.004,y-.018,t+.095);
    vertex(-.009,y,t);vertex(.004,y-.018,t+.095);vertex(-.004,y-.018,t+.095);
  }
  return geometry(p,uv);
}

function batches(scene) {
  const items=new Map();
  const shapes={
    box:new T.BoxGeometry(),
    trunk:new T.CylinderGeometry(.34,.5,1,8),
    leaf:new T.IcosahedronGeometry(1,0),
    tree:new T.PlaneGeometry(1,1),
    frond:palmFrond(),
    dome:new T.SphereGeometry(1,36,18,0,Math.PI*2,0,Math.PI/2),
    cone:new T.ConeGeometry(.5,1,8),
    tire:new T.CylinderGeometry(.52,.52,1,12),
  };
  function place(key,material,x,y,z,sx,sy,sz,angle=0,tint=0xffffff,rx=0,rz=0) {
    if(!items.has(material))items.set(material,new Map());
    const mat=items.get(material);
    if(!mat.has(key))mat.set(key,[]);
    mat.get(key).push([x,y,z,sx,sy,sz,angle,tint,rx,rz]);
  }
  function commit() {
    for(const [material,map] of items)for(const [key,models] of map) {
      const mesh=new T.InstancedMesh(shapes[key],material,models.length);
      for(let i=0;i<models.length;i++) {
        const [x,y,z,sx,sy,sz,angle,tint,rx,rz]=models[i];
        temp.position.set(x,y,z);
        temp.scale.set(sx,sy,sz);
        temp.rotation.set(rx,angle,rz,'YXZ');
        temp.updateMatrix();
        mesh.setMatrixAt(i,temp.matrix);
        mesh.setColorAt(i,color.set(tint));
      }
      mesh.castShadow=material.userData.cast!==false;
      mesh.receiveShadow=true;
      mesh.computeBoundingSphere();
      scene.add(mesh);
    }
  }
  return {place,commit};
}

function triangleSet(rings) {
  const groups=rings.map(r=>r.map(([x,z])=>X(x,z)));
  const all=groups.flat();
  return T.ShapeUtils.triangulateShape(groups[0],groups.slice(1)).map(i=>i.map(j=>all[j]));
}

function clipTriangle(vertices, a,b,c) {
  if(!vertices.length)return vertices;
  const output=[];
  let previous=vertices[vertices.length-1];
  let last=a*previous.x+b*previous.y+c;
  for(const v of vertices){
    const next=a*v.x+b*v.y+c;
    if((last<0)!=(next<0))output.push(previous.clone().lerp(v,last/(last-next)));
    if(next>=0)output.push(v);
    previous=v;
    last=next;
  }
  return output;
}

function overlays(scene,parts,height,material,offset,scale,step,extent) {
  if(!parts?.length)return;
  const p=[],u=[];
  const push=point=>{
    p.push(point.x,height(point.x,point.y)+offset,point.y);
    u.push(point.x/scale,point.y/scale);
  };
  const index=value=>Math.floor((value+extent)/step);
  for(const rings of parts)for(const tri of triangleSet(rings)){
    const x0=index(Math.min(...tri.map(v=>v.x))), x1=index(Math.max(...tri.map(v=>v.x)));
    const z0=index(Math.min(...tri.map(v=>v.y))), z1=index(Math.max(...tri.map(v=>v.y)));
    for(let i=x0;i<=x1;i++){
      const x=i*step-extent;
      let strip=clipTriangle(tri,1,0,-x);
      strip=clipTriangle(strip,-1,0,x+step);
      if(strip.length<3)continue;
      for(let j=z0;j<=z1;j++){
        const z=j*step-extent;
        let cell=clipTriangle(strip,0,1,-z);
        cell=clipTriangle(cell,0,-1,z+step);
        if(cell.length<3)continue;
        // Separate the same two terrain triangles used by PlaneGeometry.
        const k=x+z+step;
        for(const side of [-1,1]){
          const polygon=clipTriangle(cell,side,side,-side*k);
          for(let t=1;t+1<polygon.length;t++){
            push(polygon[0]);push(polygon[t+1]);push(polygon[t]);
          }
        }
      }
    }
  }
  if(p.length)surfaceMesh(scene,geometry(p,u),material);
}

function textureMaterials(renderer) {
  const loader=new T.TextureLoader();
  const set=(url,srgb=false)=>{
    const t=loader.load('textures/'+url);
    t.wrapS=t.wrapT=T.RepeatWrapping;
    t.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
    if(srgb)t.colorSpace=T.SRGBColorSpace;
    return t;
  };
  const scan=(name,tint,scale)=>{
    const mat=new T.MeshStandardMaterial({
      color:tint,map:set(name+'_diff.jpg',true),normalMap:set(name+'_nor_gl.jpg'),roughnessMap:set(name+'_rough.jpg'),
      roughness:1,normalScale:new T.Vector2(scale,scale),
    });
    mat.userData.dry=1;
    return mat;
  };
  const make=(c,r=.83,metalness=0)=>new T.MeshStandardMaterial({color:c,roughness:r,metalness});
  const concrete=scan('wall',0xffffff,.43);
  const building=concrete.clone();
  building.vertexColors=true;
  const road=scan('road',0x969b9a,.43);
  const ground=scan('ground',0xa8cc91,.40);
  const glass=make(0xffffff,.23,.49);
  glass.envMapIntensity=1.3;
  const smallWindows=glass.clone();
  smallWindows.userData.cast=false;
  const white=make(0xd6dcd7,.64,.04);
  const frame=make(0xb8c6c1,.53,.27);
  const metal=make(0xffffff,.62,.48);
  const roof=make(0xffffff,.87,.06); roof.vertexColors=true;
  const roadLines=make(0xdfdfce,.73);
  roadLines.userData.cast=false;
  const water=make(0x456d64,.17,.37);
  const grass=ground.clone(); grass.color.set(0x9ac093);
  const wood=make(0xffffff,.97);
  const leaf=make(0xffffff,.95);
  const frond=make(0xffffff,.88);frond.side=T.DoubleSide;
  const treeCards=Array.from({length:2},(_,tree)=>Array.from({length:3},(_,angle)=>new T.MeshStandardMaterial({color:0xf6ffec,map:set(`tree${tree}-${angle}.png`,true),alphaTest:.38,side:T.DoubleSide,roughness:.95})));
  const parking=road.clone(); parking.color.set(0x827f7d);
  const foot=concrete.clone(); foot.color.set(0xa5aaa0);
  return {concrete,building,road,ground,glass,smallWindows,white,frame,metal,roof,roadLines,water,grass,wood,leaf,parking,foot,frond,treeCards};
}

function sectionSign(scene, text, x,y,z,yaw,w,h,bg='#e4eadf',fg='#244039') {
  const c=document.createElement('canvas');
  c.width=1024;
  c.height=Math.max(96,Math.min(400,Math.round(1024*h/w)));
  const ctx=c.getContext('2d');
  ctx.fillStyle=bg;
  ctx.fillRect(0,0,c.width,c.height);
  ctx.fillStyle=fg;
  ctx.font='700 '+Math.floor(c.height*.58)+'px sans-serif';
  ctx.textAlign='center';
  ctx.textBaseline='middle';
  ctx.fillText(text,c.width/2,c.height*.53,c.width*.92);
  const tex=new T.CanvasTexture(c);
  tex.colorSpace=T.SRGBColorSpace;
  tex.anisotropy=4;
  const sign=new T.Mesh(new T.PlaneGeometry(w,h),new T.MeshStandardMaterial({map:tex,roughness:.8}));
  sign.position.set(x,y,z);
  sign.rotation.y=yaw;
  scene.add(sign);
}

function roofCurve(scene, material, place, x,z,base, directionX,directionZ,len) {
  const p=[],uv=[];
  function at(i,j) {
    const along=(i/20-.5)*(len+5);
    const across=(j-.5)*13;
    return [x+directionX*along-directionZ*across, base+1.3*Math.sin(i/20*Math.PI)+(.5-j)*.95, z+directionZ*along+directionX*across];
  }
  for(let i=0;i<20;i++) {
    const quad=[at(i,0),at(i+1,0),at(i+1,1),at(i,1)];
    for(const j of [0,2,1,0,3,2]){p.push(...quad[j]);uv.push(i/20,j%2);}
    const a=quad[0],b=quad[1];
    place('box',material,(a[0]+b[0])/2,(a[1]+b[1])/2-.17,(a[2]+b[2])/2,Math.hypot(b[0]-a[0],b[2]-a[2])+.12,.32,.3,-Math.atan2(directionZ,directionX),0xd2d7cb);
  }
  const shell=material.clone();shell.side=T.DoubleSide;
  surfaceMesh(scene,geometry(p,uv),shell,true);
}

function buildFabric(scene, data, height, mat, place, rnd, referenceIds) {
  const walls=[],wallUv=[],wallColors=[], roofs=[],roofUv=[],roofColors=[];
  const collisions=[];
  const palettes=[0xbcb8ab,0xd4d1c8,0xa9b5ac,0xd1c9ac,0xaaa8a0,0xc5b9a3];
  const allGlazing=[0x497181,0x315463,0x406a77,0x719298,0x385b70,0x54767e];
  for(const b of data.buildings) {
    const bounds=indexedBounds(b);
    collisions.push({bounds, rings:b.p});
    if(referenceIds.has(b.osm))continue;
    const [cx,cz]=b.center;
    const base=height(cx,cz);
    const floor=Math.max(1,b.floors), tall=b.h;
    const detailed=b.kind!=='generic';
    const close=Math.hypot(cx+270,cz+100)<180;
    const isTower=b.kind==='razak', isMjiit=b.kind==='mjiit', isMosque=b.kind==='mosque';
    const wallTint=isMjiit?0x9eb3bd:isTower?0xbdcaca:isMosque?0xbec4a5:b.kind==='inn'?0xd4c4a9:palettes[Math.floor(rnd()*palettes.length)];
    const topColor=isTower?0x777f78:isMosque?0x666d55:(rnd()>.68?0x82695d:0x7f8276);
    const top=base+tall;
    for(const tri of triangleSet(b.p))for(const pt of [tri[0],tri[2],tri[1]]) {
      roofs.push(pt.x,top,pt.y); roofUv.push(pt.x/9,pt.y/9);
      color.set(topColor);
      roofColors.push(color.r,color.g,color.b);
    }
    let best=null;
    let front=null;
    for(const ring of b.p) {
      let sign=0;
      for(let i=0;i<ring.length;i++){const a=ring[i],c=ring[(i+1)%ring.length];sign+=a[0]*c[1]-c[0]*a[1];}
      const orientation=sign<0?-1:1;
      for(let i=0;i<ring.length;i++) {
        const a=ring[i], c=ring[(i+1)%ring.length];
        const dx=c[0]-a[0], dz=c[1]-a[1], len=Math.hypot(dx,dz);
        if(len<.09)continue;
        const ax=dx/len, az=dz/len;
        const nx=orientation*az, nz=-orientation*ax;
        const yaw=-Math.atan2(az,ax);
        const mx=(a[0]+c[0])/2,mz=(a[1]+c[1])/2;
        const face={mx,mz,nx,nz,yaw,len,ax,az};
        if(!best || best.len<len)best=face;
        if(isMjiit && nx<-.76 && len>6 && Math.abs(mz+78)<51 && (!front || Math.abs(mz+78)<Math.abs(front.mz+78)))front=face;
        const floorDepth=Math.max(1,tall/floor);
        const low1=Math.min(base-.16,height(a[0],a[1])-.22);
        const low2=Math.min(base-.16,height(c[0],c[1])-.22);
        const corners=[[a[0],low1,a[1],0],[c[0],low2,c[1],len],[c[0],top,c[1],len],[a[0],top,a[1],0]];
        const order=orientation>0?[0,3,2,0,2,1]:[0,1,2,0,2,3];
        for(const j of order){const v=corners[j];walls.push(...v.slice(0,3)); wallUv.push(v[3]/3,(v[1]-base)/3); color.set(wallTint);wallColors.push(color.r,color.g,color.b);}
        if(len<1.7)continue;
        if(!detailed&&!close)continue;
        if(detailed || close)place('box',mat.metal,mx+nx*.04,top+.19,mz+nz*.04,len+.04,.38,.28,yaw,topColor);
        const bays=Math.max(1,Math.round(len/(isTower?2.55:isMjiit?3.1:3.7)));
        const floorStart=isTower?0:0;
        const modules=Math.min(floor,(!detailed&&!close)?5:25);
        for(let k=floorStart;k<modules;k++) {
          const wy=base+(k+.53)*floorDepth;
          const winH=floorDepth*(isTower?.72:isMjiit?.61:.49);
          if(isTower||isMjiit) {
            const bandColor=isMjiit&&k<2?0xd8b76e:0xe5e8dc;
            place('box',mat.white,mx+nx*.12,base+k*floorDepth+.23,mz+nz*.12,len+.09,isMjiit?.48:.35,isMjiit?.54:.44,yaw,bandColor);
          }
          for(let j=0;j<bays;j++) {
            const t=(j+.5)/bays;
            const px=a[0]+dx*t, pz=a[1]+dz*t;
            const ww=len/bays*(isTower?.96:isMjiit?.73:.66);
            const glassColor=allGlazing[Math.floor(rnd()*allGlazing.length)];
            if(isMjiit || isTower)place('box',mat.frame,px+nx*.075,wy,pz+nz*.075,ww+.07,winH+.12,.16,yaw);
            place('box',detailed?mat.glass:mat.smallWindows,px+nx*.16,wy,pz+nz*.16,ww,winH,.07,yaw,glassColor);
            if((isTower||isMjiit)&&ww>.7)place('box',mat.frame,px+nx*.215,wy,pz+nz*.215,.044,winH,.042,yaw);
            if(isMjiit&&ww>1)place('box',mat.frame,px+nx*.215,wy,pz+nz*.215,ww,.048,.047,yaw);
          }
        }
      }
    }
    if(!best)continue;
    if(detailed) {
      const {mx,mz,ax,az,nx,nz,len,yaw}=front||best;
      const outwardAngle=Math.atan2(nx,nz);
      if(isTower) {
        roofCurve(scene,mat.metal,place,(best.mx+cx)*.5,(best.mz+cz)*.5,top+.8,best.ax,best.az,best.len);
        const face=b.p[0].slice(0,-1).map((a,i)=>[a,b.p[0][i+1]]).filter(([a,c])=>Math.hypot(c[0]-a[0],c[1]-a[1])>4).slice(1,7);
        for(const [a,c] of face) {
          const len=Math.hypot(c[0]-a[0],c[1]-a[1]), dx=(c[0]-a[0])/len,dz=(c[1]-a[1])/len;
          const t=.35;
          place('box',mat.white,a[0]+(c[0]-a[0])*t-dz*.14,base+tall*.55,a[1]+(c[1]-a[1])*t+dx*.14,.51,tall*.79,.42,-Math.atan2(dz,dx));
        }
        sectionSign(scene,'MENARA RAZAK',mx+nx*.42,base+tall*.86,mz+nz*.42,outwardAngle,9,1.3,'#811c37','#f4eacb');
      }
      if(isMjiit) {
        const w=12;
        for(const s of [-1,1]) {
          place('box',mat.white,mx+ax*6.8*s+nx*.63,base+tall*.59,mz+az*6.8*s+nz*.63,2.5,tall*.77,1.4,yaw);
          place('box',mat.metal,mx+ax*6.8*s+nx*.63,top+.7,mz+az*6.8*s+nz*.63,3.1,.24,3.4,yaw,0x727e80);
          place('trunk',mat.concrete,mx+ax*4.6*s+nx*2.9,base+2.05,mz+az*4.6*s+nz*2.9,.48,4.1,.48);
        }
        place('box',mat.metal,mx+nx*2.2,base+4.1,mz+nz*2.2,w,.35,4.5,yaw,0xadb5b0);
        place('box',mat.glass,mx+nx*3.3,base+4.35,mz+nz*3.3,w+.4,.10,2.5,yaw,0x6fa3af);
        sectionSign(scene,'MJIIT',mx+nx*4.48,base+4.0,mz+nz*4.48,outwardAngle,8,.98,'#791c41','#f4f5e9');
      }
      if(isMosque) {
        place('dome',mat.metal,cx,top-.38,cz,12,6.6,12,.3,0x477b6c);
        place('cone',mat.metal,cx,top+7.0,cz,.5,2.8,.5,0,0xb39452);
        const tx=mx+ax*len*.65, tz=mz+az*len*.65;
        const tb=height(tx,tz);
        place('trunk',mat.white,tx,tb+9.8,tz,1.6,19.6,1.6);
        place('trunk',mat.metal,tx,tb+18.7,tz,2.15,.5,2.15,0,0x486754);
        place('cone',mat.metal,tx,tb+21.1,tz,1.65,4,1.65,0,0x477b6c);
      }
      if(b.kind==='inn'||b.kind==='hall')sectionSign(scene,b.name,mx+nx*.32,base+2.9,mz+nz*.32,outwardAngle,Math.min(8,len*.8),.65,'#526758','#f9f4db');
    }
    if((detailed||close)&&bounds[2]-bounds[0]>11&&bounds[3]-bounds[1]>7) {
      const n=isTower?5:2;
      for(let k=0;k<n;k++) {
        const x=cx+(rnd()-.5)*8,z=cz+(rnd()-.5)*7;
        if(!inside(x,z,b.p[0]))continue;
        const size=1.0+rnd()*1.5;
        place('box',mat.metal,x,top+.49,z,size,.98,.81,rnd()*.1,0xa3a5a1);
        place('box',mat.metal,x,top+.98,z,size*.80,.06,.67,0,0x666c65);
      }
    }
  }
  surfaceMesh(scene,geometry(walls,wallUv,wallColors),mat.building,true);
  surfaceMesh(scene,geometry(roofs,roofUv,roofColors),mat.roof,true);
  return collisions;
}

function flora(place, data, mat, height, rnd, collides) {
  const colors=[0x426332,0x436d3a,0x597942,0x658046,0x365a32,0x7d914f,0x547344,0x405e2e];
  const trees=[...data.trees];
  const candidates=[];
  for(let i=0;i<650;i++)candidates.push([-482+rnd()*470,-422+rnd()*535]);
  for(let i=0;i<440;i++)candidates.push([(rnd()-.5)*1310,(rnd()-.5)*1360]);
  const roadSegments=data.roads.flatMap(r=>r.p.slice(1).map((b,i)=>[r.p[i],b,r.w*.59+2.0]));
  const core=data.landmarks.map(l=>l.point);
  for(const [x,z] of candidates) {
    if(trees.some(([tx,tz])=>(tx-x)**2+(tz-z)**2<44)||collides(x,z,3.8))continue;
    if(roadSegments.some(([a,b,r])=>distanceSquared(x,z,a,b)<r*r))continue;
    if(core.some(([a,b])=>(x-a)**2+(z-b)**2<190))continue;
    trees.push([x,z]);
  }
  for(const [x,z] of trees) {
    const y=height(x,z),angle=rnd()*Math.PI*2,h=4+rnd()*8.6;
    if(rnd()>.87){
      place('trunk',mat.wood,x,y+h*.459,z,.37,h*.94,.35,angle,0x837462,0,.025);
      for(let i=0;i<13;i++){
        const frondAngle=i/13*Math.PI*2+angle;
        const span=2.0+rnd()*2.0;
        place('frond',mat.frond,x-.04,y+h*.92,z,span,.87*span,span,frondAngle,colors[i%colors.length],-.07+rnd()*.23);
      }
      continue;
    }
    const variant=rnd()>.61?1:0;
    const widths=[[1.156,.698,1.124],[1.747,1.434,1.695]][variant];
    const sampledAngles=[0,.96,2.15];
    const color=colors[Math.floor(rnd()*colors.length)];
    for(let i=0;i<3;i++){
      const yaw=angle+sampledAngles[i];
      const h2=h*(variant?0.78:1);
      const tint=new T.Color(color).lerp(new T.Color(0xffffff),.62+rnd()*.24);
      place('tree',mat.treeCards[variant][i],x,y+h2*.48,z,h2*widths[i]*.82,h2,1,yaw,tint);
    }
  }
  for(let i=0;i<152;i++) {
    const x=-452+rnd()*315,z=-265+rnd()*335;
    if(collides(x,z,1.7)||roadSegments.some(([a,b,r])=>distanceSquared(x,z,a,b)<r*r))continue;
    const y=height(x,z);
    for(let j=0;j<3;j++)place('leaf',mat.leaf,x+(rnd()-.5)*2.3,y+.42+rnd()*.33,z+(rnd()-.5)*2.3,.77,.54,.52,rnd()*6,colors[Math.trunc(rnd()*colors.length)]);
  }
}

function streets(scene,place,data,mat,height,rnd) {
  const primary=data.roads.filter(r=>r.type==='artery' || (r.type==='road'&&r.lanes>=2&&!r.parking));
  for(const road of primary)for(let i=1;i<road.p.length;i++) {
    const [ax,az]=road.p[i-1],[bx,bz]=road.p[i];
    const dx=bx-ax,dz=bz-az,len=Math.hypot(dx,dz);
    if(len<5)continue;
    const angle=-Math.atan2(dz,dx);
    const nx=-dz/len,nz=dx/len;
    for(let k=0;k<road.lanes-1;k++)for(let s=4;s<len-3;s+=9.0) {
      const w=(k+1-road.lanes*.5)*(road.w-.35)/road.lanes;
      const x=ax+dx*s/len+nx*w,z=az+dz*s/len+nz*w;
      place('box',mat.roadLines,x,height(x,z)+.125,z,2.4,.017,.093,angle);
    }
    if(Math.hypot(ax+291,az+95)>350 || rnd()<.39)continue;
    for(let s=7;s<len-5;s+=28) {
      const x=ax+dx*s/len+nx*(road.w*.51+.7), z=az+dz*s/len+nz*(road.w*.51+.7);
      const y=height(x,z);
      place('trunk',mat.metal,x,y+2.7,z,.145,5.4,.145,0,0x626b64);
      place('box',mat.metal,x-nx*.48,y+5.31,z-nz*.48,.085,.105,1.05,angle,0x626b64);
      place('box',mat.white,x-nx*.92,y+5.28,z-nz*.92,.22,.13,.48,angle,0xf4e8c9);
    }
  }
  const lot=data.areas.parking||[];
  const paint=[0xbfc6c1,0x42464b,0x6e7c77,0xb9a9a0,0x725249,0x253e4e];
  for(const part of lot) {
    const bounds=indexedBounds({p:part});
    const cx=(bounds[0]+bounds[2])/2, cz=(bounds[1]+bounds[3])/2;
    if(Math.hypot(cx+300,cz+90)>230)continue;
    const p=part[0];
    let best=0, edge=[0,0,0,0];
    for(let i=0;i<p.length;i++) {
      const [ax,az]=p[i],[bx,bz]=p[(i+1)%p.length];
      const len=Math.hypot(bx-ax,bz-az);
      if(len>best){best=len;edge=[ax,az,bx,bz];}
    }
    const [ax,az,bx,bz]=edge;
    const dx=(bx-ax)/best,dz=(bz-az)/best;
    const sign=inside(ax+dx*4-dz*3,az+dz*4+dx*3,p)?1:-1;
    const nx=-dz*sign,nz=dx*sign,yaw=-Math.atan2(dz,dx);
    for(let s=3.5;s<best-2.8;s+=3.05) {
      const x=ax+dx*s+nx*2.8,z=az+dz*s+nz*2.8;
      if(!inside(x,z,p))continue;
      const y=height(x,z);
      place('box',mat.roadLines,x-dx*1.49,y+.095,z-dz*1.49,.075,.014,4.2,yaw);
      if(rnd()>.48)continue;
      place('box',mat.metal,x,y+.63,z,1.83,.55,4.32,yaw,paint[Math.floor(rnd()*paint.length)]);
      place('box',mat.glass,x-nx*.05,y+1.02,z-nz*.05,1.53,.38,2.02,yaw,0x51717a);
      place('box',mat.metal,x-nx*.14,y+1.24,z-nz*.14,1.43,.13,1.48,yaw,0x7c8987);
      for(const d of [-1,1])for(const f of [-1,1]) {
        place('tire',mat.metal,x+dx*.91*d+nx*1.26*f,y+.32,z+dz*.91*d+nz*1.26*f,.58,.25,.58,yaw,0x242a28,0,Math.PI/2);
      }
      for(const d of [-1,1]) {
        place('box',mat.white,x+nx*2.16+dx*.59*d,y+.64,z+nz*2.16+dz*.59*d,.44,.14,.054,yaw,0xfcf5d4);
        place('box',mat.metal,x-nx*2.16+dx*.62*d,y+.63,z-nz*2.16+dz*.62*d,.37,.14,.064,yaw,0x9f352c);
      }
    }
  }
  const loc=[[-272,-171,'MJIIT  ›'],[-347,-135,'MENARA RAZAK'],[-269,13,'MASJID UTM']];
  for(const [x,z,txt] of loc) {
    const y=height(x,z);
    place('box',mat.metal,x,y+.81,z,.075,1.63,.075,0,0x5c6a5d);
    sectionSign(scene,txt,x,y+1.37,z+.06,0,2.25,.48,'#234e40','#e7ecca');
  }
}

const landmarkModels={
  '552610255':{slug:'menara_razak',altitude:46.31,twoLods:true,sign:['MENARA RAZAK',-1.19,3.69,15.15,-.656,9]},
  '733313948':{slug:'mjiit',altitude:40.88,twoLods:true,sign:['MJIIT',108,15.3,46,-Math.PI/2,5.5]},
  '772103594':{slug:'masjid',altitude:40.63,twoLods:false},
  '524812098':{slug:'residensi',altitude:38.38,twoLods:true},
};

async function architecture(scene,data,height) {
  const loader=new GLTFLoader(), active=new Map();
  const models=Object.entries(landmarkModels);
  const promise=models.map(async ([id,entry])=>{
    const building=data.buildings.find(building=>building.osm===id);
    if(!building)return;
    const model=await loader.loadAsync('architecture/'+entry.slug+'_lod'+(entry.twoLods?1:0)+'.glb');
    const base=entry.altitude-data.elevationBase;
    const root=new T.Group();
    root.name=entry.slug;
    root.userData.architecture=true;
    root.matrixAutoUpdate=false;
    // Affine alignment from matching OSM boundary vertices between UTM 47N and the local grid.
    root.matrix.set(.99926239,0,-.00262310,-341.89687,0,1,0,base,.00263042,0,.99924381,-119.86437,0,0,0,1);
    function configure(s){
      s.traverse(node=>{
        if(!node.isMesh)return;
        node.castShadow=true;node.receiveShadow=true;
        const mats=Array.isArray(node.material)?node.material:[node.material];
        for(const m of mats)if(m.name?.startsWith('Glass'))m.envMapIntensity=1.12;
      });
      root.add(s);
    }
    configure(model.scene);
    scene.add(root);
    if(entry.sign) {
      const [label,x,y,z,yaw,width]=entry.sign;
      const point=new T.Vector3(x,y,z).applyMatrix4(root.matrix);
      sectionSign(scene,label,point.x,point.y,point.z,yaw-.00263,width,width*.15,'#6d2436','#f5eee3');
    }
    const self={building,low:model.scene,high:null,busy:null,entry,configure};
    active.set(id,self);
  });
  for(const result of await Promise.allSettled(promise))if(result.status==='rejected')console.warn('Using a footprint-based landmark model',result.reason);
  async function loadHigh(obj) {
    if(!obj.entry.twoLods||obj.high)return;
    obj.busy ||= loader.loadAsync('architecture/'+obj.entry.slug+'_lod0.glb').then(gltf=>{
      obj.high=gltf.scene;obj.high.visible=false;obj.configure(obj.high);
    }).catch(error=>console.warn('High-detail landmark model unavailable',error));
    await obj.busy;
  }
  function update(camera,level){
    let changed=false;
    for(const obj of active.values()){
      if(!obj.entry.twoLods)continue;
      const [x,z]=obj.building.center;
      const d=Math.hypot(camera.position.x-x,camera.position.z-z,camera.position.y-height(x,z));
      const high=level>0&&d<[0,87,148,295][level];
      if(high&&!obj.high)loadHigh(obj);
      if(obj.high&&obj.high.visible!==high){
        obj.high.visible=high;obj.low.visible=!high;changed=true;
      }
    }
    return changed;
  }
  async function allHigh(){
    await Promise.all(Array.from(active.values(),loadHigh));
    for(const obj of active.values())if(obj.high){obj.high.visible=true;obj.low.visible=false;}
  }
  return {ids:new Set(active.keys()),update,allHigh};
}

export async function buildCampus(renderer,scene,data) {
  const mat=textureMaterials(renderer);
  const rnd=random(834021);
  const {extent,heights,grid}=data;
  const span=extent*2;
  const step=span/(grid-1);
  const height=(x,z)=>{
    const gx=T.MathUtils.clamp((x+extent)/span*(grid-1),0,grid-1.001), gz=T.MathUtils.clamp((z+extent)/span*(grid-1),0,grid-1.001);
    const i=Math.floor(gx),j=Math.floor(gz);
    const u=gx-i,v=gz-j,index=j*grid+i;
    const a=heights[index],b=heights[index+1],c=heights[index+grid],d=heights[index+grid+1];
    return u+v<1 ? a+(b-a)*u+(c-a)*v : d+(c-d)*(1-u)+(b-d)*(1-v);
  };
  const ground=new T.PlaneGeometry(span,span,grid-1,grid-1);
  ground.rotateX(-Math.PI/2);
  const g=ground.attributes.position,u=ground.attributes.uv;
  for(let i=0;i<g.count;i++){
    g.setY(i,height(g.getX(i),g.getZ(i)));
    u.setXY(i,g.getX(i)/9,g.getZ(i)/9);
  }
  ground.computeVertexNormals();
  surfaceMesh(scene,ground,mat.ground);
  for(const [name,parts] of Object.entries(data.areas)) {
    const attr={
      park:[mat.grass,.035,8],forest:[mat.grass,.042,7],
      pitch:[mat.grass,.049,12],parking:[mat.parking,.066,5],water:[mat.water,.073,14],
    }[name];
    overlays(scene,parts,height,...attr,step,extent);
  }
  overlays(scene,data.roadShapes.walk,height,mat.foot,.083,4,step,extent);
  overlays(scene,data.roadShapes.road,height,mat.road,.095,5,step,extent);
  overlays(scene,data.roadShapes.artery,height,mat.road,.105,5,step,extent);
  const refs=await architecture(scene,data,height);
  const batch=batches(scene);
  const collisions=buildFabric(scene,data,height,mat,batch.place,rnd,refs.ids);
  const cells=new Map(), tile=32;
  for(const {bounds,rings} of collisions) {
    for(let i=Math.floor(bounds[0]/tile);i<=Math.floor(bounds[2]/tile);i++)for(let j=Math.floor(bounds[1]/tile);j<=Math.floor(bounds[3]/tile);j++) {
      const key=i+','+j;
      if(!cells.has(key))cells.set(key,[]);
      cells.get(key).push({bounds,rings});
    }
  }
  function collides(x,z,r=.44) {
    const ix0=Math.floor((x-r)/tile),ix1=Math.floor((x+r)/tile);
    const iz0=Math.floor((z-r)/tile),iz1=Math.floor((z+r)/tile);
    for(let i=ix0;i<=ix1;i++)for(let j=iz0;j<=iz1;j++)for(const {bounds,rings} of cells.get(i+','+j)||[]) {
      if(x<bounds[0]-r || x>bounds[2]+r || z<bounds[1]-r || z>bounds[3]+r)continue;
      if(inside(x,z,rings[0])&&!rings.slice(1).some(ring=>inside(x,z,ring)))return true;
      if(rings.some(ring=>ring.some((a,index)=>distanceSquared(x,z,a,ring[(index+1)%ring.length])<r*r)))return true;
    }
    return false;
  }
  flora(batch.place,data,mat,height,rnd,collides);
  streets(scene,batch.place,data,mat,height,rnd);
  batch.commit();
  new HDRLoader().load('textures/sky_hdri.hdr', tex=>{
    tex.mapping=T.EquirectangularReflectionMapping;
    scene.environment=tex;
  },undefined,error=>console.warn('Environment lighting texture unavailable',error));
  return {height,collides,mat,refs};
}

export function makeWalker() {
  const walker=new T.Group();
  const skin=new T.MeshStandardMaterial({color:0x9f654a,roughness:.82});
  const shirt=new T.MeshStandardMaterial({color:0xbbb6a2,roughness:.96});
  const trousers=new T.MeshStandardMaterial({color:0x273738,roughness:.85});
  const shoes=new T.MeshStandardMaterial({color:0x434649,roughness:.88});
  const pack=new T.MeshStandardMaterial({color:0x63553f,roughness:.94});
  const hair=new T.MeshStandardMaterial({color:0x312824,roughness:.98});
  function ell(parent,m,x,y,z,sx,sy,sz) {
    const obj=new T.Mesh(new T.SphereGeometry(1,14,10),m);
    obj.position.set(x,y,z);obj.scale.set(sx,sy,sz);obj.castShadow=true;parent.add(obj);return obj;
  }
  ell(walker,trousers,0,.91,0,.166,.185,.111);
  ell(walker,shirt,0,1.23,0,.198,.26,.124);
  ell(walker,skin,0,1.53,0,.058,.083,.055);
  ell(walker,skin,0,1.66,-.012,.092,.119,.093);
  ell(walker,hair,0,1.712,.009,.095,.072,.092);
  ell(walker,pack,0,1.253,.118,.144,.225,.12);
  const legs=[],arms=[];
  for(const sign of [-1,1]) {
    const hip=new T.Group(), knee=new T.Group(), shoulder=new T.Group();
    hip.position.set(sign*.091,.91,0);knee.position.y=-.417;
    shoulder.position.set(sign*.193,1.41,0);
    ell(hip,trousers,0,-.197,0,.077,.23,.087);
    ell(knee,trousers,0,-.191,0,.062,.22,.062);
    ell(knee,shoes,0,-.396,-.042,.066,.054,.114);
    ell(shoulder,shirt,sign*.019,-.09,0,.062,.127,.063);
    ell(shoulder,skin,sign*.023,-.237,0,.046,.142,.046);
    ell(walker,pack,sign*.116,1.33,-.097,.022,.175,.015);
    hip.add(knee);walker.add(hip,shoulder);
    legs.push([hip,knee]);arms.push(shoulder);
  }
  let avatar=null,mixer=null,walkAction=null,runAction=null,current=null,avatarLoad=null;
  const placeholder=new T.Group();
  for(const child of [...walker.children])placeholder.add(child);
  walker.add(placeholder);
  function loadAvatar(){
    avatarLoad ||= new GLTFLoader().loadAsync('people/sam.glb').then(gltf=>{
      avatar=gltf.scene;
      avatar.rotation.y=Math.PI;
      avatar.traverse(node=>{if(node.isMesh){node.castShadow=true;node.receiveShadow=true;}});
      mixer=new T.AnimationMixer(avatar);
      walkAction=mixer.clipAction(T.AnimationClip.findByName(gltf.animations,'Walk_Relaxed'));
      runAction=mixer.clipAction(T.AnimationClip.findByName(gltf.animations,'Run'));
      walkAction.play();walkAction.time=.15;walkAction.paused=true;current=walkAction;
      placeholder.visible=false;walker.add(avatar);mixer.update(.001);
    }).catch(error=>console.warn('Using the bundled lightweight walker',error));
  }
  return {
    walker, loadAvatar,
    animate(phase,stride,dt,running){
      if(mixer){
        if(stride<.055){current.paused=true;return;}
        const next=running?runAction:walkAction;
        if(next!==current){current.fadeOut(.16);next.reset().fadeIn(.16).play();current=next;}
        current.paused=false;current.timeScale=running?1.25:1.38;mixer.update(dt);
        return;
      }
      for(let i=0;i<2;i++){
        const wave=Math.sin(phase+i*Math.PI);
        legs[i][0].rotation.x=wave*stride*.65;
        legs[i][1].rotation.x=Math.min(0,Math.sin(phase+i*Math.PI-.35))*stride*.77;
        arms[i].rotation.x=-wave*stride*.62;
        arms[i].rotation.z=(i?1:-1)*.08;
      }
    }
  };
}
