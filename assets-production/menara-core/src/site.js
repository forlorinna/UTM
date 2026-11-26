const AREA_EPSILON = 0.000001;

function inRing(x, y, ring) {
  let hit = false;
  for (let i = 0, previous = ring.length - 1; i < ring.length; previous = i++) {
    const [ax, ay] = ring[previous];
    const [bx, by] = ring[i];
    if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) hit = !hit;
  }
  return hit;
}

function distanceSquared(x, y, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const t = Math.max(0, Math.min(1, ((x-a[0])*dx+(y-a[1])*dy) / (dx*dx+dy*dy || 1)));
  return (x-a[0]-t*dx)**2 + (y-a[1]-t*dy)**2;
}

function inPolygon(x, y, rings) {
  return inRing(x, y, rings[0]) && !rings.slice(1).some(ring => inRing(x,y,ring));
}

export const spawn = Object.freeze({x:-7.8, y:-34.2});
export const stepLimit = 0.26;
export const playerRadius = 0.36;

export function createSite(data) {
  const { x:gx, y:gy, spacing, nx, ny, height } = data.grid;
  const { walkable, trees, lamps, geometry } = data;
  const blockers = [
    ...trees.map(([x,y,h]) => [x,y,.13+h*.019]),
    ...lamps.map(([x,y]) => [x,y,.20]),
    [-8.05,-17.10,.24], [.90,-17.10,.24],
    ...[5.55,11.49,15.51].map(x=>[x,-12.44,.42]),
  ];
  const benches = [[-13,-15.8],[-18,-15.6]];
  const stairRails = [-7.97,1.48].map(x=>[[x,-11.19],[x,-9.55]]);
  const [left,bottom,right,top] = data.extent;
  const raised = [['platform',.105],['curb',.162],['walk',.099],['plaza',.069],['roundabout',.085],['road',.030]];

  function terrain(x,y) {
    const px=Math.max(0,Math.min(nx-1.001,(x-gx)/spacing)), py=Math.max(0,Math.min(ny-1.001,(y-gy)/spacing));
    const i=Math.floor(px), j=Math.floor(py), u=px-i, v=py-j;
    const idx=j*nx+i;
    const a=height[idx],b=height[idx+1],c=height[idx+nx],d=height[idx+nx+1];
    return u+v<=1 ? a+(b-a)*u+(c-a)*v : d+(c-d)*(1-u)+(b-d)*(1-v);
  }

  function ground(x,y) {
    // Tread faces copied from the authored entrance mesh dimensions.
    if (x>=-8.29 && x<=1.83 && y>=-11.22 && y<=-9.31) {
      if (y>=-10.14) return .559;
      if (y>=-10.50) return .426;
      if (y>=-10.86) return .293;
      return .16;
    }
    const offset=raised.find(([kind])=>geometry[kind].some(polygon=>inPolygon(x,y,polygon)))?.[1] ?? 0;
    return terrain(x,y)+offset;
  }

  function allowed(x,y,radius=playerRadius) {
    if (x<left+radius || x>right-radius || y<bottom+radius || y>top-radius) return false;
    const containing = walkable.find(polygon=>inPolygon(x,y,polygon));
    if (!containing) return false;
    for (const ring of containing) {
      for (let i=0;i<ring.length;i++) {
        if (distanceSquared(x,y,ring[i],ring[(i+1)%ring.length]) < radius*radius-AREA_EPSILON) return false;
      }
    }
    if (blockers.some(([bx,by,r])=>(bx-x)**2+(by-y)**2 < (r+radius)**2)) return false;
    if (benches.some(([bx,by])=>Math.abs(bx-x)<.83+radius && Math.abs(by-y)<.29+radius)) return false;
    if (stairRails.some(([a,b])=>distanceSquared(x,y,a,b)<(radius+.065)**2)) return false;
    return true;
  }

  function move(x,y,dx,dy) {
    const count=Math.max(1,Math.ceil(Math.hypot(dx,dy)/.12));
    for(let i=0;i<count;i++){
      const nx=x+dx/count, ny=y+dy/count;
      if(allowed(nx,y) && ground(nx,y)-ground(x,y)<=stepLimit) x=nx;
      if(allowed(x,ny) && ground(x,ny)-ground(x,y)<=stepLimit) y=ny;
    }
    return {x,y,z:ground(x,y)};
  }

  return {terrain,ground,allowed,move};
}
