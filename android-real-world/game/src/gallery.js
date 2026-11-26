import * as T from 'three';
import {SparkRenderer,SplatMesh} from '@sparkjsdev/spark';

export function makeGallery(renderer) {
  const scene=new T.Scene();
  scene.background=new T.Color(0x101f1b);
  scene.fog=new T.FogExp2(0x101f1b,.073);
  const spark=new SparkRenderer({renderer});
  scene.add(spark);
  const floor=new T.Mesh(new T.CircleGeometry(38,96),new T.MeshStandardMaterial({color:0x293e36,roughness:.88}));
  floor.rotation.x=-Math.PI/2;floor.position.y=-.15;
  scene.add(floor);
  const plinth=new T.Mesh(new T.CylinderGeometry(.82,.98,.24,48),new T.MeshStandardMaterial({color:0x52665a,roughness:.64,metalness:.18}));
  plinth.position.y=-.03;
  scene.add(plinth);
  for(let i=0;i<4;i++) {
    const r=new T.Mesh(new T.RingGeometry(1.48+i*.52,1.488+i*.52,96),new T.MeshBasicMaterial({color:i===0?0xc8f19d:0x59776b}));
    r.rotation.x=-Math.PI/2;r.position.y=-.143;
    scene.add(r);
  }
  const hemi=new T.HemisphereLight(0xecf1dd,0x5a7770,1.8);
  const spot=new T.DirectionalLight(0xffe4af,2.5);spot.position.set(-3,6,2);
  scene.add(hemi,spot);
  let mesh,count=0,loading,revision=0;
  let park=null, parkPromise=null;
  const trail=new T.Scene();
  trail.background=new T.Color(0x57624e);
  function loadPark() {
    parkPromise ||= (async()=>{
      const response=await fetch('park.json');
      if(!response.ok)throw new Error('Outdoor exhibit metadata unavailable');
      const data=await response.json();
      const scan=new SplatMesh({url:'park.spz'});
      try{
        await scan.initialized;
        if(scan.packedSplats.numSplats!==data.count)throw new Error('Outdoor exhibit did not decode completely');
        const q=new T.Quaternion().setFromUnitVectors(new T.Vector3(...data.up).normalize(),new T.Vector3(0,1,0));
        scan.quaternion.copy(q);
        trail.add(scan);
        park={
          eye:new T.Vector3(...data.eye).applyQuaternion(q),
          forward:new T.Vector3(...data.forward).applyQuaternion(q),
          count:data.count,
        };
        return park;
      }catch(error){scan.dispose();throw error;}
    })().catch(error=>{parkPromise=null;throw error;});
    return parkPromise;
  }
  function criticalBounds(m) {
    const fields=[[],[],[]];
    m.forEachSplat((i,center,scales,rotation,opacity)=>{
      if(i%13===0&&opacity>.19)fields.forEach((arr,j)=>arr.push(center.getComponent(j)));
    });
    if(fields[0].length<20)return m.getBoundingBox(true);
    const low=[],high=[];
    for(const arr of fields){
      arr.sort((a,b)=>a-b);
      low.push(arr[Math.trunc(arr.length*.013)]);
      high.push(arr[Math.min(arr.length-1,Math.trunc(arr.length*.987))]);
    }
    return new T.Box3(new T.Vector3(...low),new T.Vector3(...high));
  }
  function setup(options) {
    const version=++revision;
    const next=new SplatMesh(options);
    loading=next.initialized.then(()=>{
      if(revision!==version){next.dispose();return count;}
      const bounds=criticalBounds(next);
      if(!Number.isFinite(bounds.min.x)||bounds.isEmpty())throw new Error('No usable splats');
      const size=bounds.getSize(new T.Vector3()),mid=bounds.getCenter(new T.Vector3());
      const s=1.55/Math.max(size.x,size.y,size.z,.001);
      next.scale.setScalar(s);
      next.rotation.x=Math.PI;
      next.position.set(-mid.x*s,.095+bounds.max.y*s,mid.z*s);
      if(mesh){scene.remove(mesh);mesh.dispose();}
      scene.add(next);
      mesh=next;
      count=mesh.packedSplats.numSplats;
      return count;
    }).catch(err=>{
      next.dispose();
      if(revision===version)loading=null;
      throw err;
    });
    return loading;
  }
  return {
    loadPark,
    renderScene(outdoor){
      const next=outdoor?trail:scene;
      if(spark.parent!==next)next.add(spark);
      return next;
    },
    defaultSample:()=>loading||setup({url:'plant.splat'}),
    openFile:async file=>{
      if(file.size>120*1024*1024)throw new Error('Choose a splat file up to 120 MB');
      if(!/\.(splat|spz|ply|ksplat)$/i.test(file.name))throw new Error('Choose a PLY, SPLAT, SPZ or KSPLAT file');
      return setup({fileBytes:await file.arrayBuffer(),fileName:file.name});
    },
    count:()=>count,
  };
}
