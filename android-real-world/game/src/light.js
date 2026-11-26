import * as T from 'three';
import {random} from './campus.js';

export const periods={
  day: {hour:11.3,top:0x5394ca,edge:0xb4d2cc,cloud:0xf3f2dd,fog:0xbacfc5,sun:0xffedc8,key:2.55,fill:1.66,env:.67,exposure:1.19,haze:.00223,cover:.50},
  overcast:{hour:14.8,top:0x8195a6,edge:0xb5c1b9,cloud:0xb5c0bd,fog:0xb8c5bd,sun:0xdde1d9,key:.84,fill:1.36,env:.54,exposure:1.20,haze:.0024,cover:.24},
  gold:{hour:17.80,top:0x5797cb,edge:0xd6cfaa,cloud:0xffe1be,fog:0xc5d2c1,sun:0xffd39b,key:2.50,fill:1.56,env:.58,exposure:1.19,haze:.00250,cover:.53},
  rain:{hour:16.0,top:0x485d69,edge:0x94a09d,cloud:0x899595,fog:0x85988f,sun:0xc6d1dc,key:.51,fill:1.17,env:.62,exposure:1.08,haze:.0041,cover:.17},
  night:{hour:22.0,top:0x0c1a2d,edge:0x3a5060,cloud:0x455a66,fog:0x263e47,sun:0x91b3e7,key:.34,fill:.50,env:.14,exposure:1.01,haze:.0028,cover:.57}
};

const vertex=`
varying vec3 vWorld;
void main(){
 vWorld = (modelMatrix * vec4(position, 1.)).xyz;
 gl_Position=projectionMatrix * modelViewMatrix * vec4(position, 1.);
}`;
const fragment=`
varying vec3 vWorld;
uniform vec3 topColor;
uniform vec3 horizonColor;
uniform vec3 cloudColor;
uniform vec3 sunColor;
uniform vec3 sunDirection;
uniform float cloudCover;
uniform float clockSeconds;
uniform float night;

float hash21(vec2 p) {p=fract(p*vec2(123.34,456.21));p+=dot(p,p+34.345);return fract(p.x*p.y);}
float noise2(vec2 p){
 vec2 i=floor(p),f=fract(p),w=f*f*(3.-2.*f);
 return mix(mix(hash21(i),hash21(i+vec2(1,0)),w.x),mix(hash21(i+vec2(0,1)),hash21(i+1.),w.x),w.y);
}
float fbm(vec2 p){
 float a=.54,s=0.;
 mat2 turn=mat2(.8,.6,-.6,.8);
 for(int i=0;i<5;i++){s+=a*noise2(p);p=turn*p*2.05+vec2(7.9,13.9);a*=.48;}
 return s;
}
void main(){
 vec3 d=normalize(vWorld-cameraPosition);
 float alt=max(0.,d.y);
 vec3 c=mix(horizonColor,topColor,pow(smoothstep(-.065,.77,d.y),.56));
 float dist=dot(d,sunDirection);
 float glare=pow(max(dist,0.),19.);
 c+=glare*sunColor*.22*(1.-night);
 if(d.y>.005){
  vec2 uv=d.xz/(d.y+.26)*5.5+vec2(0.008,-0.006)*clockSeconds;
  float n=fbm(uv);
  float cover=smoothstep(cloudCover,cloudCover+.19,n)*smoothstep(.008,.19,d.y);
  float light=smoothstep(cloudCover-.1,cloudCover+.18,fbm(uv-.24*sunDirection.xz));
  vec3 lit=mix(cloudColor*.57,cloudColor*1.14,light);
  c=mix(c,lit,cover*.95);
  c+=sunColor*smoothstep(.99951,.99990,dist)*(1.-night)*3.;
 }
 if(night>.4){
  vec2 uv=vec2(atan(d.z,d.x),d.y)*200.;
  float star=step(.995,hash21(floor(uv)))*(1.-smoothstep(0.,.19,length(fract(uv)-.5)))*smoothstep(.04,.35,alt);
  c+=star*.85;
 }
 gl_FragColor=vec4(c,1.);
 #include <tonemapping_fragment>
 #include <colorspace_fragment>
}`;

// Approximate local solar direction from day-of-year, UTC+8, and campus longitude.
function sunPosition(hour,night) {
  const phi=T.MathUtils.degToRad(3.1717);
  const longitude=101.7226;
  const day=330;
  const dec=T.MathUtils.degToRad(23.44*Math.sin(2*Math.PI*(284+day)/365));
  const b=2*Math.PI*(day-81)/364;
  const correction=(9.87*Math.sin(2*b)-7.53*Math.cos(b)-1.5*Math.sin(b))+4*(longitude-120);
  const h=T.MathUtils.degToRad(15*(hour+correction/60-12));
  if(night)return new T.Vector3(.52,.69,-.48).normalize();
  return new T.Vector3(-Math.cos(dec)*Math.sin(h),Math.sin(phi)*Math.sin(dec)+Math.cos(phi)*Math.cos(dec)*Math.cos(h),-(Math.cos(phi)*Math.sin(dec)-Math.sin(phi)*Math.cos(dec)*Math.cos(h))).normalize();
}

export function lightWorld(scene,renderer,mat) {
  const uniform={
    topColor:{value:new T.Color()}, horizonColor:{value:new T.Color()}, cloudColor:{value:new T.Color()}, sunColor:{value:new T.Color()},
    sunDirection:{value:new T.Vector3()},cloudCover:{value:.55},clockSeconds:{value:0},night:{value:0},
  };
  const sky=new T.Mesh(new T.SphereGeometry(1640,32,18),new T.ShaderMaterial({uniforms:uniform,vertexShader:vertex,fragmentShader:fragment,side:T.BackSide,depthWrite:false,fog:false}));
  sky.renderOrder=-100;
  scene.add(sky);
  const ambient=new T.HemisphereLight(0xcee7fb,0x918866,1.4);
  const sun=new T.DirectionalLight(0xffdfac,2.5);
  sun.castShadow=true;
  sun.shadow.camera.near=4;sun.shadow.camera.far=330;
  sun.shadow.normalBias=.13;sun.shadow.bias=-.00006;
  sun.shadow.radius=2;
  scene.add(ambient,sun,sun.target);
  scene.fog=new T.FogExp2(0xc6d0bd,.0015);
  const rainGeo=new T.BufferGeometry();
  const rng=random(912);
  const count=460, rainVertices=new Float32Array(count*6), drops=[];
  for(let i=0;i<count;i++)drops.push([(rng()-.5)*22, rng()*15, (rng()-.5)*22, .42+rng()*.37,10+rng()*9]);
  rainGeo.setAttribute('position',new T.BufferAttribute(rainVertices,3).setUsage(T.DynamicDrawUsage));
  const rain=new T.LineSegments(rainGeo,new T.LineBasicMaterial({color:0xbfdbdc,transparent:true,opacity:.33,depthWrite:false}));
  rain.visible=false;rain.frustumCulled=false;scene.add(rain);
  let current=periods.gold;
  let anchor=new T.Vector3(Infinity,0,0);
  let mapWidth=108;
  function setWeather(name) {
    current=periods[name];
    const night=name==='night',wet=name==='rain';
    uniform.topColor.value.set(current.top);
    uniform.horizonColor.value.set(current.edge);
    uniform.cloudColor.value.set(current.cloud);
    uniform.sunColor.value.set(current.sun);
    uniform.sunDirection.value.copy(sunPosition(current.hour,night));
    uniform.cloudCover.value=current.cover;
    uniform.night.value=night?1:0;
    sun.color.set(current.sun);sun.intensity=current.key;
    ambient.color.set(night?0x7c9db4:0xb6d2e6);
    ambient.groundColor.set(night?0x666a52:0x9b9779);
    ambient.intensity=current.fill;
    scene.fog.color.set(current.fog);scene.fog.density=current.haze;
    scene.environmentIntensity=current.env;
    rain.visible=wet;
    mat.road.roughness=wet?.35:1;
    mat.road.metalness=wet?.22:0;
    mat.parking.roughness=wet?.47:1;
    anchor.set(Infinity,0,0);
    sun.shadow.needsUpdate=true;
  }
  function settings(level) {
    const sizes=[0,1024,1536,2048];
    mapWidth=[85,110,140,182][level];
    renderer.shadowMap.enabled=level>0;
    if(level) {
      sun.shadow.map?.dispose();sun.shadow.map=null;
      sun.shadow.mapSize.set(sizes[level],sizes[level]);
    }
    const cam=sun.shadow.camera;
    cam.left=cam.bottom=-mapWidth;cam.top=cam.right=mapWidth;
    cam.updateProjectionMatrix();
    anchor.set(Infinity,0,0);
    renderer.shadowMap.needsUpdate=true;
  }
  function tick(dt,time,camera,focus,exposure) {
    uniform.clockSeconds.value=time;
    sky.position.copy(camera.position);
    renderer.toneMappingExposure=current.exposure*(2**exposure);
    if(anchor.distanceToSquared(focus)>144) {
      anchor.set(focus.x,focus.y,focus.z);
      sun.target.position.copy(anchor);
      sun.position.copy(anchor).addScaledVector(uniform.sunDirection.value,176);
      sun.shadow.needsUpdate=true;
      renderer.shadowMap.needsUpdate=true;
    }
    if(rain.visible) {
      rain.position.copy(camera.position);
      for(let i=0;i<count;i++){
        const drop=drops[i];drop[1]=(drop[1]-dt*drop[4]+15)%15;
        const [x,y,z,len]=drop,k=i*6;
        rainVertices.set([x,y-8,z,x+.09,y-8+len,z+.045],k);
      }
      rainGeo.attributes.position.needsUpdate=true;
    }
  }
  return {setWeather,settings,tick};
}
