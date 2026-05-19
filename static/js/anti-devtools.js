// Anti-devtools: deterrence (not foolproof) - disables right-click, common devtools key combos, and overrides console methods
(function(){
  // Disable common shortcuts and right-click
  document.addEventListener('contextmenu', function(e){ e.preventDefault(); });
  document.addEventListener('keydown', function(e){
    // F12, Ctrl+Shift+I/J/C, Ctrl+U
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && ['I','J','C'].includes(e.key.toUpperCase())) || (e.ctrlKey && e.key.toLowerCase()==='u')) {
      e.preventDefault();
      showBlockedToast();
    }
  });

  // Overwrite console methods to no-op
  ['log','debug','info','warn','error','table','dir'].forEach(k => { try{ console[k] = function(){}; }catch(e){} });

  // Detect developer tools by checking window outer-inner size difference
  function isDevToolsOpen(){
    const threshold = 160; // px
    return (window.outerWidth - window.innerWidth > threshold) || (window.outerHeight - window.innerHeight > threshold);
  }

  let lastState = false;
  setInterval(()=>{
    const open = isDevToolsOpen();
    if(open && !lastState){ lastState = true; showDevtoolsOverlay(); }
    if(!open && lastState){ lastState = false; removeDevtoolsOverlay(); }
  }, 1000);

  function showDevtoolsOverlay(){ if(document.getElementById('devtools-blocker')) return; const d = document.createElement('div'); d.id = 'devtools-blocker'; d.style.position='fixed'; d.style.inset='0'; d.style.background='rgba(0,0,0,0.85)'; d.style.color='white'; d.style.zIndex='99999'; d.style.display='flex'; d.style.alignItems='center'; d.style.justifyContent='center'; d.style.fontSize='18px'; d.innerText = 'DevTools access disabled for security reasons.'; document.body.appendChild(d); }
  function removeDevtoolsOverlay(){ const el = document.getElementById('devtools-blocker'); if(el) el.remove(); }

  function showBlockedToast(){ // small notice
    if(document.getElementById('devtools-toast')) return;
    const t = document.createElement('div'); t.id = 'devtools-toast'; t.style.position='fixed'; t.style.bottom='20px'; t.style.right='20px'; t.style.background='rgba(0,0,0,0.75)'; t.style.color='white'; t.style.padding='10px 14px'; t.style.borderRadius='8px'; t.style.zIndex='99999'; t.style.fontSize='14px'; t.innerText = 'Action blocked.'; document.body.appendChild(t); setTimeout(()=>{ const el=document.getElementById('devtools-toast'); if(el) el.remove(); }, 2000); }
})();