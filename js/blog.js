import './posts-client.js';

const POSTS_PER_PAGE = 5;
let currentPage = 1;
let filteredPosts = [];
let selectedCategories = new Set();
let selectedTags = new Set();
let searchQuery = '';
let sortBy = 'new';

async function init(){
  const posts = await window.getPosts();
  filteredPosts = [...posts];
  setupSyncCheckboxes();
  setupSearch();
  setupSort();
  setupMobileDrawer();
  setupPostClicks();
  updateSelectedFilters();
  filterAndRender();
}

function setupSyncCheckboxes(){
  function sync(sourceSel, targetSel){
    const s = document.getElementById(sourceSel); const t = document.getElementById(targetSel);
    if(!s || !t) return;
    s.querySelectorAll('input[type="checkbox"]').forEach((cb,i)=>{ cb.addEventListener('change', ()=>{ if(t.querySelectorAll('input[type="checkbox"]')[i]) t.querySelectorAll('input[type="checkbox"]')[i].checked = cb.checked; updateSelectedFilters(); filterAndRender(); }); });
  }
  sync('categoryFilters','categoryFiltersMobile'); sync('categoryFiltersMobile','categoryFilters'); sync('tagFilters','tagFiltersMobile'); sync('tagFiltersMobile','tagFilters');
  // Clear all handler (desktop)
  const clearBtn = document.getElementById('clearAll');
  clearBtn?.addEventListener('click', ()=>{ document.querySelectorAll('#categoryFilters input[type="checkbox"], #tagFilters input[type="checkbox"], #categoryFiltersMobile input[type="checkbox"], #tagFiltersMobile input[type="checkbox"]').forEach(cb=>cb.checked = false); updateSelectedFilters(); filterAndRender(); });
}

function setupSearch(){ const top = document.getElementById('searchInputTop'); const mobile = document.getElementById('searchInputMobile'); function handle(e){ searchQuery = e.target.value.toLowerCase().trim(); if (top && e.target !== top) top.value = e.target.value; if (mobile && e.target !== mobile) mobile.value = e.target.value; filterAndRender(); } top?.addEventListener('input', handle); mobile?.addEventListener('input', handle); }
function setupSort(){ const sortSelect = document.getElementById('sortSelect'); const sortSelectMobile = document.getElementById('sortSelectMobile'); function handle(e){ sortBy = e.target.value; if(sortSelect && e.target !== sortSelect) sortSelect.value = sortBy; if(sortSelectMobile && e.target !== sortSelectMobile) sortSelectMobile.value = sortBy; filterAndRender(); } sortSelect?.addEventListener('change', handle); sortSelectMobile?.addEventListener('change', handle); }

function setupMobileDrawer(){
  const toggle = document.getElementById('mobileFilterToggle');
  const drawer = document.getElementById('filterDrawer');
  const overlay = document.getElementById('mobileOverlay');
  const closeBtn = document.getElementById('closeDrawer');
  const clearAllMobile = document.getElementById('clearAllMobile');
  const applyBtn = document.getElementById('applyFilters');
  if(!drawer) return;
  function openDrawer(){ drawer.classList.add('active'); overlay?.classList.add('active'); document.body.style.overflow = 'hidden'; }
  function closeDrawer(){ drawer.classList.remove('active'); overlay?.classList.remove('active'); document.body.style.overflow = ''; }
  toggle?.addEventListener('click', openDrawer);
  closeBtn?.addEventListener('click', closeDrawer);
  overlay?.addEventListener('click', closeDrawer);
  clearAllMobile?.addEventListener('click', ()=>{
    document.querySelectorAll('#categoryFiltersMobile input[type="checkbox"], #tagFiltersMobile input[type="checkbox"]').forEach(cb => cb.checked = false);
    document.querySelectorAll('#categoryFilters input[type="checkbox"], #tagFilters input[type="checkbox"]').forEach(cb => cb.checked = false);
    updateSelectedFilters(); filterAndRender();
  });
  applyBtn?.addEventListener('click', ()=>{ updateSelectedFilters(); filterAndRender(); closeDrawer(); });
}

function updateSelectedFilters(){ selectedCategories.clear(); selectedTags.clear(); document.querySelectorAll('input[type="checkbox"]:checked').forEach(cb=>{ if(cb.dataset.type === 'category') selectedCategories.add(cb.value); if(cb.dataset.type === 'tag') selectedTags.add(cb.value); }); const total = selectedCategories.size + selectedTags.size; const mobileFilterCount = document.getElementById('mobileFilterCount'); if(total>0){ mobileFilterCount.textContent = total; mobileFilterCount.classList.remove('hidden'); }else{ mobileFilterCount.classList.add('hidden'); } updateFilterBadges(); }

function updateFilterBadges(){ const badges = document.getElementById('activeFilterBadges'); badges.innerHTML=''; const all = [...selectedCategories, ...selectedTags]; if(all.length>0){ badges.classList.remove('hidden'); all.forEach(f=>{ const div=document.createElement('div'); div.className='filter-badge'; div.innerHTML=`<span>${f}</span><button onclick="removeFilter('${f}')" aria-label="Remove ${f} filter">×</button>`; badges.appendChild(div); }); } else { badges.classList.add('hidden'); } }

window.removeFilter = function(filter){ document.querySelectorAll('input[type="checkbox"]').forEach(cb=>{ if(cb.value === filter) cb.checked = false; }); updateSelectedFilters(); filterAndRender(); }

function filterAndRender(){ window.getPosts().then(posts=>{
  filteredPosts = posts.filter(post=>{ const categoryMatch = selectedCategories.size === 0 || selectedCategories.has(post.category); const tagMatch = selectedTags.size === 0 || post.tags.some(tag => selectedTags.has(tag)); const searchMatch = !searchQuery || post.title.toLowerCase().includes(searchQuery) || post.excerpt.toLowerCase().includes(searchQuery); return categoryMatch && tagMatch && searchMatch; });

  if(sortBy === 'new') filteredPosts.sort((a,b)=> b.date.localeCompare(a.date)); else if(sortBy === 'old') filteredPosts.sort((a,b)=> a.date.localeCompare(b.date)); else if(sortBy === 'popular') filteredPosts.sort((a,b)=> b.views - a.views);

  document.getElementById('resultCount').textContent = filteredPosts.length;
  currentPage = 1; renderPosts(); renderPagination();
}); }

function renderPosts(){ const container = document.getElementById('posts'); const noRes = document.getElementById('noResults'); if(filteredPosts.length === 0){ container.innerHTML = ''; noRes.classList.remove('hidden'); return;} noRes.classList.add('hidden'); const start = (currentPage -1) * POSTS_PER_PAGE; const end = start + POSTS_PER_PAGE; const postsToShow = filteredPosts.slice(start,end); container.innerHTML = postsToShow.map(post=>`<article class="post-card post-item modern-card scroll-reveal active" data-slug="${post.slug}"><div class="post-img"><img src="${post.img}" alt="${post.title}"><div class="gradient-overlay"></div></div><div class="post-content"><div><div class="post-meta"><div class="tag">${post.category}</div><div class="meta-right"><i class="bi bi-calendar3"></i>${formatDate(post.date)}<span>•</span><i class="bi bi-eye"></i>${formatViews(post.views)}</div></div><h3 class="post-title mt-2"><a href="blog-detail.html?post=${post.slug}" class="hover:underline text-slate-900">${post.title}</a></h3><p class="excerpt">${post.excerpt}</p></div><div class="flex items-center justify-between mt-4"><div class="flex items-center gap-3"><div class="avatar"><img src="${post.avatar}" alt="${post.author}"></div><div><div class="text-sm font-medium text-slate-700">${post.author}</div><div class="text-xs text-slate-500">${post.read}</div></div></div><a href="blog-detail.html?post=${post.slug}" class="inline-flex items-center gap-2 text-blue-600 font-semibold hover:gap-3 transition-all group"><span>Read</span><i class="bi bi-arrow-right group-hover:translate-x-1 transition-transform"></i></a></div></div></article>`).join(''); }

function setupPostClicks(){
  const postsContainer = document.getElementById('posts');
  postsContainer?.addEventListener('click', (e)=>{
    const card = e.target.closest('.post-item');
    if(!card) return;
    // If target was an actual link, let it proceed
    if(e.target.closest('a')) return;
    const link = card.querySelector('a[href*="blog-detail.html"]');
    if(link){ console.debug('Post card clicked — navigating to', link.getAttribute('href')); window.location.href = link.getAttribute('href'); }
  });
}

function renderPagination(){ const container = document.getElementById('pagination'); const total = Math.ceil(filteredPosts.length / POSTS_PER_PAGE); if(total <= 1){ container.innerHTML = ''; return; } let html = `<button onclick="changePage(${currentPage -1})" ${currentPage===1 ? 'disabled' : ''}><i class="bi bi-chevron-left"></i></button>`; for(let i=1;i<=total;i++){ if(i===1 || i=== total || (i>= currentPage-1 && i<= currentPage+1)) html += `<button onclick="changePage(${i})" class="${i===currentPage ? 'active' : ''}">${i}</button>`; else if(i=== currentPage-2 || i=== currentPage+2) html += `<span class="px-2 text-slate-400">...</span>`; } html += `<button onclick="changePage(${currentPage+1})" ${currentPage===total ? 'disabled' : ''}><i class="bi bi-chevron-right"></i></button>`; container.innerHTML = html; }

window.changePage = function(page){ const total = Math.ceil(filteredPosts.length / POSTS_PER_PAGE); if(page <1 || page > total) return; currentPage = page; renderPosts(); renderPagination(); document.getElementById('posts').scrollIntoView({behavior:'smooth', block:'start'}); }

function formatDate(d){ const date = new Date(d); const options = { month: 'short', day: 'numeric', year: 'numeric' }; return date.toLocaleDateString('en-US', options); }
function formatViews(v){ if(v >= 1000) return (v/1000).toFixed(1) + 'k'; return v.toString(); }

// Expose init
window.blogInit = init;

// Attach DOMContentLoaded init
document.addEventListener('DOMContentLoaded', init);