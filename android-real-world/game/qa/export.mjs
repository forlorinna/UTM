import {chromium} from 'playwright-core';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
try{
  const p=await browser.newPage({viewport:{width:530,height:300},acceptDownloads:true});
  p.on('pageerror',error=>console.error('Page:',error));
  p.on('console',msg=>{if(msg.type()!=='debug')console.log(msg.type(),msg.text().slice(0,230));});
  await p.addInitScript(()=>localStorage.setItem('utm-quality','0'));
  await p.goto('http://127.0.0.1:4173/',{waitUntil:'networkidle'});
  await p.waitForFunction(()=>globalThis.exportCampusForBlender);
  const dl=p.waitForEvent('download',{timeout:150000});
  await p.evaluate(()=>window.exportCampusForBlender());
  await (await dl).saveAs('utmkl-core.glb');
}finally{await browser.close();}
