// Only timing/status in JS. The Points capability is an HttpOnly cookie.
export function installPointsSession({sessionId,onExpire}) {
  const badge=document.createElement('button');badge.className='points-session-state';badge.hidden=true;
  badge.type='button';badge.setAttribute('aria-label','Cerrar consulta personal de Points');document.body.append(badge);
  let authenticated=false,demo=false,privateShown=false,deadline=0,hardDeadline=0;
  const clear=(notify=false)=>{authenticated=false;privateShown=false;deadline=hardDeadline=0;badge.hidden=true;if(notify)onExpire();};
  const update=info=>{
    if(!info?.authenticated){if(authenticated)clear(true);return;}
    authenticated=true;demo=!!info.demo;deadline=performance.now()+info.expires_in_ms;
    hardDeadline=performance.now()+info.hard_expires_in_ms;badge.hidden=false;
  };
  async function end(){const sid=sessionId();clear(true);try{await fetch('/points/session/end',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid})});}catch{}}
  badge.onclick=end;
  setInterval(()=>{
    if(!authenticated&&!privateShown)return;
    const remaining=Math.ceil((Math.min(deadline,hardDeadline||deadline)-performance.now())/1000);
    if(remaining<=0){end();return;}
    if(authenticated)badge.textContent=`Points ${demo?'demo':'validado'} · ${remaining}s · Cerrar`;
  },500);
  addEventListener('pagehide',()=>{
    if(authenticated||privateShown)navigator.sendBeacon('/points/session/end',new Blob([JSON.stringify({session_id:sessionId()})],{type:'application/json'}));
    clear(true);
  });
  return {update,clear,end,markPrivate(){privateShown=true;if(!authenticated){deadline=performance.now()+90000;hardDeadline=performance.now()+600000;}},
    get active(){return authenticated;}};
}
