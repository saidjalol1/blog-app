import './posts-client.js';

const POSTS_PER_PAGE = 5;
let currentPage = 1;
let filteredPosts = [];
let selectedCategories = new Set();
let selectedTags = new Set();
let searchQuery = '';
let sortBy = 'new';

function formatDate(d) {
  if (!d) return '';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatViews(v) {
  if (v == null) return '0';
  return Number(v).toLocaleString();
}

async function init(){
  // Use server-rendered posts if available
  if(window.initialPosts){
    filteredPosts = window.initialPosts;
    currentPage = window.currentPage || 1;
    // Set filters from server
    if(window.initialFilters){
      selectedCategories = new Set(window.initialFilters.categories || []);
      selectedTags = new Set(window.initialFilters.tags || []);
      searchQuery = window.initialFilters.q || '';
      sortBy = window.initialFilters.sort || 'new';
    }
  }
  setupSearch();
  setupSort();
  await loadFilters();
  setupSyncCheckboxes();
  setupMobileDrawer();
  setupPostClicks();
  updateSelectedFilters();
  if(!window.initialPosts){
    filterAndRender();
  } else {
    renderPosts();
    renderPagination(window.totalPages, currentPage);
  }
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

function filterAndRender(){ 
  const params = {
    page: currentPage,
    per_page: POSTS_PER_PAGE,
    q: searchQuery,
    categories: Array.from(selectedCategories).join(','),
    tags: Array.from(selectedTags).join(','),
    sort: sortBy
  };
  window.getPosts(params).then(data=>{
    filteredPosts = data.results;
    document.getElementById('resultCount').textContent = data.total;
    renderPosts();
    renderPagination(data.total_pages, data.page);
  });
}

function renderPosts(){ const container = document.getElementById('posts'); const noRes = document.getElementById('noResults'); if(filteredPosts.length === 0){ container.innerHTML = ''; noRes.classList.remove('hidden'); return;} noRes.classList.add('hidden'); container.innerHTML = filteredPosts.map(post=>`<article class="post-card post-item modern-card scroll-reveal active" data-slug="${post.slug}"><div class="post-img"><img src="${post.img}" alt="${post.title}"><div class="gradient-overlay"></div></div><div class="post-content"><div><div class="post-meta"><div class="tag">${post.category}</div><div class="meta-right"><i class="bi bi-calendar3"></i>${formatDate(post.date)}<span>•</span><i class="bi bi-eye"></i>${formatViews(post.views)}</div></div><h3 class="post-title mt-2"><a href="/blogs/post/${post.slug}/" class="hover:underline text-slate-900">${post.title}</a></h3><p class="excerpt">${post.excerpt}</p></div><div class="flex items-center justify-end mt-4"><a href="/blogs/post/${post.slug}/" class="inline-flex items-center gap-2 text-blue-600 font-semibold hover:gap-3 transition-all group"><span>O'qish</span><i class="bi bi-arrow-right group-hover:translate-x-1 transition-transform"></i></a></div></div></article>`).join(''); }

function setupPostClicks(){
  const postsContainer = document.getElementById('posts');
  postsContainer?.addEventListener('click', (e)=>{
    const card = e.target.closest('.post-item');
    if(!card) return;
    // If target was an actual link, let it proceed
    if(e.target.closest('a')) return;
    const link = card.querySelector('a[href*="/blogs/post/"]');
    if(link){ console.debug('Post card clicked — navigating to', link.getAttribute('href')); window.location.href = link.getAttribute('href'); }
  });
}

function renderPagination(totalPages, currentPage){ const container = document.getElementById('pagination'); if(totalPages <= 1){ container.innerHTML = ''; return; } let html = `<button onclick="changePage(${currentPage -1})" ${currentPage===1 ? 'disabled' : ''}><i class="bi bi-chevron-left"></i></button>`; for(let i=1;i<=totalPages;i++){ if(i===1 || i=== totalPages || (i>= currentPage-1 && i<= currentPage+1)) html += `<button onclick="changePage(${i})" class="${i===currentPage ? 'active' : ''}">${i}</button>`; else if(i=== currentPage-2 || i=== currentPage+2) html += `<span class="px-2 text-slate-400">...</span>`; } html += `<button onclick="changePage(${currentPage+1})" ${currentPage===totalPages ? 'disabled' : ''}><i class="bi bi-chevron-right"></i></button>`; container.innerHTML = html; }

window.changePage = function(page){ currentPage = page; filterAndRender(); document.getElementById('posts').scrollIntoView({behavior:'smooth', block:'start'}); }

async function loadFilters(){
  try {
    const data = await window.getFilters();
    populateFilters(data.categories, data.tags);
  } catch (err) {
    console.error('Failed to load filters', err);
  }
}

function populateFilters(categories, tags){
  const catContainer = document.getElementById('categoryFilters');
  const catMobile = document.getElementById('categoryFiltersMobile');
  const tagContainer = document.getElementById('tagFilters');
  const tagMobile = document.getElementById('tagFiltersMobile');

  const filterItemClass = "flex items-center gap-3 mb-3 cursor-pointer group";
  const checkboxClass = "w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 transition-colors";
  const textClass = "text-slate-600 text-sm font-medium group-hover:text-slate-900 transition-colors";

  catContainer.innerHTML = categories.map(c => `<label class="${filterItemClass}"><input type="checkbox" class="${checkboxClass}" data-type="category" value="${c.name}"> <span class="${textClass}">${c.name} <span class="text-slate-400 font-normal">(${c.post_count})</span></span></label>`).join('');
  catMobile.innerHTML = categories.map(c => `<label class="${filterItemClass}"><input type="checkbox" class="${checkboxClass}" data-type="category" value="${c.name}"> <span class="${textClass}">${c.name} <span class="text-slate-400 font-normal">(${c.post_count})</span></span></label>`).join('');
  tagContainer.innerHTML = tags.map(t => `<label class="${filterItemClass}"><input type="checkbox" class="${checkboxClass}" data-type="tag" value="${t.name}"> <span class="${textClass}">${t.name} <span class="text-slate-400 font-normal">(${t.post_count})</span></span></label>`).join('');
  tagMobile.innerHTML = tags.map(t => `<label class="${filterItemClass}"><input type="checkbox" class="${checkboxClass}" data-type="tag" value="${t.name}"> <span class="${textClass}">${t.name} <span class="text-slate-400 font-normal">(${t.post_count})</span></span></label>`).join('');
}

// Expose init
window.blogInit = init;

// Attach DOMContentLoaded init
document.addEventListener('DOMContentLoaded', init);