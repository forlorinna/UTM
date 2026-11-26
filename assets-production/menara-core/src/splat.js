import * as T from 'three';
import { SparkRenderer, SplatMesh } from '@sparkjsdev/spark';

export async function openScan(renderer) {
  const request = await fetch('mobile-assets/park.json');
  if (!request.ok) throw Error('Scan metadata unavailable');
  const data = await request.json();
  const scan = new SplatMesh({url:new URL('mobile-assets/park.spz',document.baseURI).href});
  try {
    await scan.initialized;
    if (scan.packedSplats.numSplats !== data.count) throw Error('SPZ count mismatch');
    const up = new T.Vector3(...data.up).normalize();
    const transform = new T.Quaternion().setFromUnitVectors(up,new T.Vector3(0,1,0));
    scan.quaternion.copy(transform);
    const spark = new SparkRenderer({renderer, minPixelRadius:.35});
    const scene = new T.Scene();
    scene.background = new T.Color(0x586450);
    scene.add(scan,spark);
    const camera = new T.PerspectiveCamera(68,1,.05,120);
    camera.position.set(...data.eye).applyQuaternion(transform);
    const forward = new T.Vector3(...data.forward).applyQuaternion(transform);
    camera.lookAt(camera.position.clone().add(forward));
    camera.rotation.order = 'YXZ';
    return {scene,camera,spark,scan,count:data.count};
  } catch (error) {
    scan.dispose();
    throw error;
  }
}
