export function cartography(data) {
  const rivers=data.areas.water||[];
  const mapCanvas=document.createElement('canvas');
  const local={x:-272,z:-151};
  const scale=1.23;
  mapCanvas.width=1060;
  mapCanvas.height=800;
  const g=mapCanvas.getContext('2d');
  g.fillStyle='#263d31';
  g.fillRect(0,0,mapCanvas.width,mapCanvas.height);
  g.translate(mapCanvas.width/2,mapCanvas.height/2);
  g.scale(scale,scale);g.translate(-local.x,-local.z);
  const trace=(p)=>{
    g.beginPath();
    p.forEach(([x,z],i)=>i?g.lineTo(x,z):g.moveTo(x,z));
  };
  const region=(p,fill)=>{
    g.fillStyle=fill;trace(p[0]);g.closePath();
    for(const ring of p.slice(1)) {
      ring.forEach(([x,z],i)=>i?g.lineTo(x,z):g.moveTo(x,z));
      g.closePath();
    }
    g.fill('evenodd');
  };
  for(const name of ['forest','park','pitch','parking'])for(const p of data.areas[name]||[])region(p,{forest:'#345442',park:'#3c5c46',pitch:'#446b50',parking:'#40554d'}[name]);
  for(const p of rivers)region(p,'#3a7273');
  if(data.boundary) {
    g.strokeStyle='#9bd381';
    g.lineWidth=1.35;
    g.setLineDash([5,4]);
    trace(data.boundary);g.stroke();
    g.setLineDash([]);
  }
  for(const kind of ['walk','road','artery']) {
    g.strokeStyle={walk:'#668071',road:'#738b7b',artery:'#a8b196'}[kind];
    g.lineCap='round';g.lineJoin='round';
    for(const r of data.roads)if(r.type===kind){g.lineWidth=Math.max(.75,r.w*.75);trace(r.p);g.stroke();}
  }
  for(const b of data.buildings)region(b.p,b.kind==='generic'?'#64786b':'#c2cec1');
  const baseX=mapCanvas.width/2-local.x*scale;
  const baseZ=mapCanvas.height/2-local.z*scale;
  function draw(canvas,who,yaw,big) {
    const ctx=canvas.getContext('2d');
    const w=canvas.width,h=canvas.height;
    const view=big?{x:-270,z:-135,width:615}:{x:Math.max(-495,Math.min(-55,who.x)),z:Math.max(-385,Math.min(95,who.z)),width:358};
    const sx=w/view.width, project=(x,z)=>[w/2+(x-view.x)*sx,h/2+(z-view.z)*sx];
    ctx.fillStyle='#273f33';ctx.fillRect(0,0,w,h);
    ctx.drawImage(mapCanvas,w/2-(baseX+view.x*scale)*sx/scale,h/2-(baseZ+view.z*scale)*sx/scale,mapCanvas.width*sx/scale,mapCanvas.height*sx/scale);
    for(const l of data.landmarks) {
      const [x,y]=project(...l.point);
      ctx.beginPath();ctx.arc(x,y,big?5:5.3,0,Math.PI*2);ctx.fillStyle='#d9f2a7';ctx.fill();
      ctx.lineWidth=1.5;ctx.strokeStyle='#26392b';ctx.stroke();
      if(big&&l.id!=='hall'){
        ctx.font='bold 11px sans-serif';ctx.lineWidth=3;ctx.strokeStyle='#263d31';ctx.fillStyle='#edf6d7';ctx.strokeText(l.name,x+8,y+3);ctx.fillText(l.name,x+8,y+3);
      }
    }
    const [x,y]=project(who.x,who.z);
    ctx.save();
    ctx.translate(x,y);ctx.rotate(-yaw);
    ctx.beginPath();ctx.moveTo(0,-12);ctx.lineTo(8,8);ctx.lineTo(0,4);ctx.lineTo(-8,8);ctx.closePath();
    ctx.fillStyle='#fffbe5';ctx.fill();ctx.strokeStyle='#142620';ctx.lineWidth=2;ctx.stroke();
    ctx.restore();
    return {screenToWorld(x,y){return [(x-w/2)/sx+view.x,(y-h/2)/sx+view.z];}};
  }
  return {draw};
}
