import { Capacitor, registerPlugin } from '@capacitor/core';

export const native = Capacitor.isNativePlatform();
export const mobile = native || new URLSearchParams(location.search).has('mobileQA');
export const bridge = registerPlugin('SceneBridge');
export const report = event => {
  if (native) bridge.report({event}).catch(console.warn);
};

export function gpuProfile(gl) {
  const info = gl.getExtension('WEBGL_debug_renderer_info');
  const name = info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
  const textureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
  const adreno = /adreno|qualcomm/i.test(name);
  const olderAdreno = /adreno.*[345]\d\d/i.test(name);
  const software = /swiftshader|llvmpipe|software/i.test(name);
  return {name, textureSize, adreno, olderAdreno, software,
    constrained: software || olderAdreno || textureSize < 8192 || (navigator.deviceMemory ?? 8) <= 4};
}

export function touchInput(canvas, turn, zoom, flags) {
  const pad = document.getElementById('joystick');
  const thumb = pad.querySelector('span');
  const pointers = new Map();
  let stickId;
  const stick = {x:0,y:0};
  const placeStick = event => {
    const rect = pad.getBoundingClientRect();
    const radius = rect.width * .38;
    let x = (event.clientX - rect.left - rect.width / 2) / radius;
    let y = (event.clientY - rect.top - rect.height / 2) / radius;
    const length = Math.hypot(x,y);
    if (length > 1) { x /= length; y /= length; }
    stick.x = Math.abs(x) < .08 ? 0 : x;
    stick.y = Math.abs(y) < .08 ? 0 : -y;
    thumb.style.transform = `translate(-50%, -50%) translate(${x*radius}px, ${y*radius}px)`;
  };
  pad.addEventListener('pointerdown', event => {
    if (stickId !== undefined) return;
    stickId = event.pointerId;
    pad.setPointerCapture(stickId);
    placeStick(event);
  });
  pad.addEventListener('pointermove', event => { if (event.pointerId === stickId) placeStick(event); });
  function releaseStick(event) {
    if (event.pointerId !== stickId) return;
    stickId = undefined;
    stick.x = stick.y = 0;
    thumb.style.transform = 'translate(-50%, -50%)';
  }
  pad.addEventListener('lostpointercapture', releaseStick);
  pad.addEventListener('pointercancel', releaseStick);

  canvas.addEventListener('pointerdown', event => {
    if (event.pointerType === 'mouse') return;
    pointers.set(event.pointerId, [event.clientX,event.clientY]);
    canvas.setPointerCapture(event.pointerId);
  });
  const distance = () => {
    const [a,b] = pointers.values();
    return Math.hypot(a[0]-b[0],a[1]-b[1]);
  };
  canvas.addEventListener('pointermove', event => {
    const last = pointers.get(event.pointerId);
    if (!last) return;
    const before = pointers.size === 2 ? distance() : 0;
    pointers.set(event.pointerId, [event.clientX,event.clientY]);
    if (before > 8) zoom(distance()/before);
    else if (pointers.size === 1) turn(event.clientX-last[0],event.clientY-last[1]);
  });
  for (const event of ['pointerup','pointercancel','lostpointercapture']) {
    canvas.addEventListener(event, e => pointers.delete(e.pointerId));
  }
  for (const action of ['run','up','down']) {
    const button = document.getElementById(action);
    button.addEventListener('pointerdown', event => {
      button.setPointerCapture(event.pointerId);
      flags[action] = true;
      if (action === 'up') flags.jump = true;
    });
    for (const event of ['pointerup','pointercancel','lostpointercapture']) {
      button.addEventListener(event, () => { flags[action] = false; });
    }
  }
  return stick;
}

export async function savePhoto(canvas, fileName) {
  const blob = await new Promise(resolve => canvas.toBlob(resolve,'image/png'));
  if (!blob) throw Error('PNG unavailable');
  if (native) {
    const encoded = await new Promise((resolve,reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
    await bridge.savePhoto({base64:encoded});
    return;
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url),60000);
}
