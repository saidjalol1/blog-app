// Shared site functions: mobile menu, language sync, scroll reveal, search render
(function(){
  function setupMobileMenu() {
    const toggle = document.getElementById('mobileMenuToggle');
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('mobileOverlay');
    function open() { menu.classList.add('active'); overlay.classList.add('active'); toggle.setAttribute('aria-expanded','true'); document.body.style.overflow='hidden'; const icon=toggle.querySelector('i'); if(icon){icon.classList.replace('bi-list','bi-x')} }
    function close(){ menu.classList.remove('active'); overlay.classList.remove('active'); toggle.setAttribute('aria-expanded','false'); document.body.style.overflow=''; const icon=toggle.querySelector('i'); if(icon){icon.classList.replace('bi-x','bi-list')} }
    toggle?.addEventListener('click', ()=> menu.classList.contains('active') ? close() : open());
    overlay?.addEventListener('click', close);
    document.addEventListener('keydown', (e)=>{ if(e.key==='Escape') close(); });
    menu.querySelectorAll('a')?.forEach(a=>a.addEventListener('click', ()=> setTimeout(close, 80)));
  }

  function setupLangSelectors() {
    const desktop = document.getElementById('langSelect');
    const mobile = document.getElementById('langSelectMobile');
    function set(val){ document.documentElement.lang = val; localStorage.setItem('site-lang', val); if(desktop) desktop.value = val; if(mobile) mobile.value = val; }
    const saved = localStorage.getItem('site-lang');
    if(saved) set(saved);
    desktop?.addEventListener('change', e=> set(e.target.value));
    mobile?.addEventListener('change', e=> set(e.target.value));
  }

  function scrollRevealInit(){
    const els = document.querySelectorAll('.scroll-reveal');
    const run = ()=>{ const h = window.innerHeight; els.forEach(el=>{ if(el.getBoundingClientRect().top < h - 150) el.classList.add('active'); }); };
    run(); window.addEventListener('scroll', run);
  }

  window.renderSuggestions = function(items, targetId, onSelect){
    const box = document.getElementById(targetId);
    if(!box) return;
    if(!items || items.length === 0){ box.classList.add('hidden'); box.innerHTML = ''; box.onclick = null; return; }
    box.classList.remove('hidden');
    // Support either passing a function reference or a function name string
    if(typeof onSelect === 'function'){
      box.innerHTML = items.slice(0,6).map(p=>`<a data-slug="${p.slug}" class="suggestion-item block px-4 py-3 hover:bg-slate-50 cursor-pointer"><div class="text-sm font-medium">${p.title}</div><div class="text-xs text-slate-500 mt-1">${p.excerpt}</div></a>`).join('');
      box.onclick = (e)=>{ const a = e.target.closest('a[data-slug]'); if(!a) return; onSelect(a.dataset.slug); };
    } else {
      const name = String(onSelect);
      box.innerHTML = items.slice(0,6).map(p=>`<a onclick="${name}('${p.slug}')" class="suggestion-item block px-4 py-3 hover:bg-slate-50 cursor-pointer"><div class="text-sm font-medium">${p.title}</div><div class="text-xs text-slate-500 mt-1">${p.excerpt}</div></a>`).join('');
      box.onclick = null;
    }
  };

  // Expose helper to navigate to an article
  window.goToArticle = function(slug){ window.location.href = `/blogs/post/${slug}/`; };

  // Init
  document.addEventListener('DOMContentLoaded', ()=>{
    setupMobileMenu(); setupLangSelectors(); scrollRevealInit();
  });
})();