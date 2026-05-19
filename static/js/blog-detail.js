import './posts-client.js';

function parseQuery(){ const q = new URLSearchParams(window.location.search); let slug = q.get('post'); if(slug) return slug; // fallback to hash or hash-like params
  if(window.location.hash){ const h = window.location.hash.replace(/^#/, ''); // if hash is simple slug
    if(h && !h.includes('=')) return h; // if hash like #post=slug
    try{ const hs = new URLSearchParams(h.replace(/^\?/, '')); if(hs.get('post')) return hs.get('post'); }catch(e){} }
  return null; }

async function renderArticle(slug){ console.debug('renderArticle called with slug:', slug); const container = document.getElementById('articleContainer'); if(!container) return; const postsData = await window.getPosts(); const posts = postsData.results; const p = posts.find(x=>x.slug===slug); if(!p){ container.innerHTML = `<div class="min-h-screen flex items-center justify-center px-2"><div class="text-center fade-in-up"><h2 class="text-4xl font-bold mb-4">Article not found</h2><p class="text-slate-400 mb-6">The article you're looking for doesn't exist.</p><a href="blog.html" class="btn-primary">Back to blog</a></div></div>`; return; }
  const relatedPosts = posts.filter(x => x.slug !== slug).slice(0,2);
  container.innerHTML = `
    <article>
      <div class="article-hero" style="background-image:url('${p.img}')">
        <div class="hero-content">
          <div class="max-w-4xl mx-auto px-2">
            <div class="flex items-center gap-3 mb-4 fade-in-up">
              <span class="tag">${p.category}</span>
              <span class="text-sm text-white">${new Date(p.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
              <span class="text-sm text-white">•</span>
              <span class="text-sm text-white">${p.views.toLocaleString()} views</span>
            </div>
            <h1 class="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4 fade-in-up drop-shadow-lg" style="animation-delay: 0.1s">${p.title}</h1>
            <p class="text-lg text-white drop-shadow fade-in-up" style="animation-delay: 0.2s">${p.excerpt}</p>
          </div>
        </div>
      </div>
      
      <div class="max-w-4xl mx-auto px-2">
        <div class="content-card fade-in-up" style="animation-delay: 0.3s">
          <div class="flex flex-wrap items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-200">
            <div class="flex items-center gap-4">
              <div class="avatar"><img src="${p.avatar}" alt="${p.author}" class="w-full h-full object-cover"></div>
              <div><div class="font-semibold text-slate-900 text-lg">${p.author}</div><div class="text-sm text-slate-500">${p.read}</div></div>
            </div>
            <div class="flex items-center gap-2">
              <button class="share-button" onclick="shareArticle('twitter')" title="Share on Twitter"><i class="bi bi-twitter"></i></button>
              <button class="share-button" onclick="shareArticle('facebook')" title="Share on Facebook"><i class="bi bi-facebook"></i></button>
              <button class="share-button" onclick="shareArticle('linkedin')" title="Share on LinkedIn"><i class="bi bi-linkedin"></i></button>
              <button class="share-button" onclick="shareArticle('copy')" title="Copy link"><i class="bi bi-link-45deg"></i></button>
            </div>
          </div>
          <div class="prose">${p.content}</div>
          <div class="flex flex-wrap gap-2 mt-8 pt-6 border-t border-slate-200">${p.tags.map(tag => `<span class="px-4 py-2 bg-slate-100 text-slate-700 rounded-full text-sm font-medium">#${tag}</span>`).join('')}</div>
          <div class="author-card mt-8"><div class="flex items-start gap-4"><div class="avatar"><img src="${p.avatar}" alt="${p.author}" class="w-full h-full object-cover"></div><div class="flex-1"><h3 class="font-bold text-slate-900 text-xl mb-2">About ${p.author}</h3><p class="text-slate-600 mb-4">Passionate writer and thought leader in ${p.category.toLowerCase()}. Sharing insights and experiences to help others grow.</p></div></div></div>
        </div>

        ${relatedPosts.length > 0 ? `
          <div class="mt-16 mb-8">
            <h2 class="text-3xl font-bold text-slate-900 mb-8">Related Articles</h2>
            <div class="grid md:grid-cols-2 gap-6">
              ${relatedPosts.map(rp => `
                <a href="/blogs/post/${rp.slug}/" class="related-article block group">
                  <div class="overflow-hidden"><img src="${rp.img}" alt="${rp.title}" class="w-full"></div>
                  <div class="p-6"><div class="flex items-center gap-2 mb-3"><span class="text-xs font-semibold text-blue-600">${rp.category}</span><span class="text-xs text-slate-400">•</span><span class="text-xs text-slate-500">${rp.read}</span></div><h3 class="text-xl font-bold text-slate-900 mb-2 group-hover:text-blue-600 transition">${rp.title}</h3><p class="text-slate-600 text-sm">${rp.excerpt}</p></div>
                </a>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    </article>
  `;
  document.title = p.title + ' — My Logo';
}

window.shareArticle = function(platform){
  const url = window.location.href;
  const text = document.title;
  // Map platform names for the tracking API
  const platformMap = { twitter: 'twitter', facebook: 'facebook', linkedin: 'linkedin', copy: 'copy_link' };
  const trackPlatform = platformMap[platform] || platform;
  // Track share
  const slug = parseQuery();
  if (slug) {
    const csrfToken = document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
    fetch(`/blogs/post/${slug}/share/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ platform: trackPlatform }),
    }).catch(() => {});
  }
  switch(platform){
    case 'twitter': window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`, '_blank'); break;
    case 'facebook': window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank'); break;
    case 'linkedin': window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`, '_blank'); break;
    case 'copy': navigator.clipboard.writeText(url).then(()=> alert('Link copied to clipboard!')); break;
  }
};

// search suggestions on detail page
;(function(){ const input = document.getElementById('searchInputTop'); const box = document.getElementById('searchSuggestions'); input?.addEventListener('input', async (e)=>{ const q = e.target.value.trim().toLowerCase(); if(q.length <2){ box?.classList.add('hidden'); return; } const postsData = await window.getPosts(); const posts = postsData.results; const items = posts.filter(p => p.title.toLowerCase().includes(q) || p.excerpt.toLowerCase().includes(q));
  // call renderSuggestions safely; main.js may not have defined it yet
  function callRenderSuggestions(items, targetId, onSelect, attempts = 0){
    if(typeof window.renderSuggestions === 'function'){ window.renderSuggestions(items, targetId, onSelect); return; }
    if(attempts > 10){ console.warn('renderSuggestions not available after retries'); return; }
    setTimeout(()=> callRenderSuggestions(items, targetId, onSelect, attempts+1), 50);
  }
  callRenderSuggestions(items, 'searchSuggestions', 'goToArticle');
  }); document.addEventListener('click',(e)=>{ const suggestionsBox = document.getElementById('searchSuggestions'); if(suggestionsBox && !suggestionsBox.contains(e.target) && e.target !== input) suggestionsBox.classList.add('hidden'); }); })();

// init
;(function(){ document.addEventListener('DOMContentLoaded', ()=>{ renderArticle(parseQuery()); }); })();