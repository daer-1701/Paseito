// QR flow adapted from the companion kiosk. No tokens go through chat or the LLM.
export function installCouponReader({api, onOpen, onResult, onError, sessionId}) {
  const dialog = document.createElement('dialog');
  dialog.className = 'coupon-reader';
  dialog.setAttribute('aria-labelledby','coupon-title');
  dialog.innerHTML = `<div class="coupon-heading"><h2 id="coupon-title">Mis cupones de Paseo Points</h2><button type="button" data-close aria-label="Cerrar lector">✕</button></div>
    <p>Muestra el QR de cliente o de un cupón de la app. Paseito consulta su estado; el canje se hace en la app o en el comercio.</p>
    <video playsinline muted hidden aria-label="Vista de la cámara para leer el QR"></video>
    <p role="status" aria-live="polite" data-status>Elige cámara o escribe el código del cupón.</p>
    <button type="button" data-camera>📷 Abrir cámara</button>
    <form><label for="coupon-code">Código del cupón o texto del QR</label><input id="coupon-code" maxlength="500" autocomplete="off" spellcheck="false" required placeholder="ABCDE-12345"><button type="submit">Consultar cupón</button></form>
    <button type="button" data-demo hidden>Ver ejemplo local</button><button type="button" data-demo-identity hidden>Probar identidad de demo</button><small>El ejemplo no se puede canjear. Tu QR no se envía al modelo. La identidad se cierra tras 90 segundos sin actividad o al reiniciar.</small>`;
  document.body.append(dialog);
  const status=dialog.querySelector('[data-status]'), video=dialog.querySelector('video');
  const camera=dialog.querySelector('[data-camera]'), form=dialog.querySelector('form');
  const input=dialog.querySelector('input'), demo=dialog.querySelector('[data-demo]');
  let generation=0, stream=null, controller=null, frame=0, jsqr=null;
  const stopCamera=()=>{cancelAnimationFrame(frame);stream?.getTracks().forEach(t=>t.stop());stream=null;video.srcObject=null;video.hidden=true;camera.disabled=false;};
  const close=()=>{
    generation++;
    if(controller){
      controller.abort();
      navigator.sendBeacon(`${api}/points/session/end`,new Blob([JSON.stringify({session_id:sessionId()})],{type:'application/json'}));
    }
    controller=null;stopCamera();input.value='';form.querySelector('button').disabled=false;if(dialog.open)dialog.close();
  };
  dialog.querySelector('[data-close]').onclick=close;
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});
  dialog.addEventListener('close',()=>{if(stream||controller)close();});
  async function verify(code) {
    controller?.abort();stopCamera();
    const current=++generation, abort=new AbortController();controller=abort;
    const timeout=setTimeout(()=>abort.abort(),12000);
    status.textContent='Consultando el cupón…';form.querySelector('button').disabled=true;
    try {
      const r=await fetch(`${api}/cupones/verificar`,{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({codigo:code,session_id:sessionId()}),signal:abort.signal});
      const data=await r.json();
      if(current!==generation || controller!==abort)return;
      if(!r.ok||data.error)throw new Error(data.error||data.detail||'No pude consultar el cupón.');
      controller=null;close();await onResult(data);
    } catch(e) {
      if(current!==generation || controller!==abort)return;
      status.textContent=abort.signal.aborted?'Points tardó en responder al primer intento. Continúa desde la web de Paseo Points.':e.message;
    } finally {clearTimeout(timeout);if(controller===abort){controller=null;form.querySelector('button').disabled=false;}}
  }
  form.onsubmit=e=>{e.preventDefault();verify(input.value.trim());};
  demo.onclick=()=>verify('DEMO-PASEITO');
  dialog.querySelector('[data-demo-identity]').onclick=()=>verify('DEMO-PUNTOS');
  camera.onclick=async()=>{
    const current=generation;camera.disabled=true;status.textContent='Abriendo cámara…';
    try {
      jsqr??=new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/vendor/jsqr/jsQR.js';script.onload=()=>resolve(window.jsQR);script.onerror=()=>{script.remove();jsqr=null;reject(new Error('No pude cargar el lector. Escribe el código.'));};document.head.append(script);});
      const scan=await jsqr;
      if(current!==generation)return;
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('Este navegador necesita HTTPS o localhost para usar la cámara. Escribe el código.');
      const capture=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
      if(current!==generation){capture.getTracks().forEach(t=>t.stop());return;}
      stream=capture;video.srcObject=stream;video.hidden=false;await video.play();
      if(current!==generation)return;
      status.textContent='Muestra el QR dentro de la cámara.';
      const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d',{willReadFrequently:true});
      const started=performance.now();let last=0;
      function tick(now){
        if(current!==generation||!stream)return;
        if(now-started>30000){stopCamera();status.textContent='No alcancé a leerlo. Intenta otra vez o escribe el código.';return;}
        if(now-last>180&&video.readyState>=2){
          last=now;canvas.width=Math.min(640,video.videoWidth);canvas.height=Math.round(video.videoHeight*canvas.width/video.videoWidth);
          ctx.drawImage(video,0,0,canvas.width,canvas.height);
          const found=scan(ctx.getImageData(0,0,canvas.width,canvas.height).data,canvas.width,canvas.height);
          if(found){verify(found.data);return;}
        }
        frame=requestAnimationFrame(tick);
      }
      frame=requestAnimationFrame(tick);
    }catch(e){if(current===generation){stopCamera();status.textContent=e.name==='NotAllowedError'?'No se dio permiso de cámara. Puedes escribir el código.':e.message;}}
  };
  return {close,async open(){close();onOpen();dialog.showModal();status.textContent='Elige cámara o escribe el código del cupón.';
    const current=generation;
    try{const r=await fetch(`${api}/cupones/status`);const data=await r.json();if(current===generation){demo.hidden=!data.demo_enabled;dialog.querySelector('[data-demo-identity]').hidden=!data.demo_enabled;}}catch{if(current===generation)onError('No pude consultar el estado del lector.');}
  }};
}
