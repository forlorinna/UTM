import {chromium} from 'playwright-core';
import assert from 'node:assert/strict';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
try{
const p=await browser.newPage({viewport:{width:700,height:420},acceptDownloads:true});
await p.addInitScript(()=>localStorage.setItem('utm-quality','0'));
await p.goto('http://127.0.0.1:4173/');
await p.waitForFunction(()=>globalThis.campusQA);
await p.evaluate(()=>{
  document.querySelector('#photoButton').click();
  document.querySelector('#resolution').value='3840';
});
const saved=p.waitForEvent('download',{timeout:120000});
await p.evaluate(()=>document.querySelector('#capture').click());
await (await saved).saveAs('qa/captured-4k.jpg');
assert.ok(await p.locator('#toast').count());
console.log('4K photo download completed');
}finally{await browser.close();}
