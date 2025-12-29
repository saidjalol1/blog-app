// Index-specific code: featured slider, latest slider, search suggestions
import './posts-client.js';

class Slider {
  constructor(wrapperId, dotsId, autoplayDelay = 5000) {
    this.wrapper = document.getElementById(wrapperId);
    this.dotsContainer = document.getElementById(dotsId);
    this.currentIndex = 0;
    this.items = this.wrapper ? this.wrapper.querySelectorAll('.slider-item') : [];
    this.autoplayDelay = autoplayDelay;
    this.autoplayInterval = null;
    this.init();
  }
  createDots(){ this.items.forEach((_,i)=>{ const dot=document.createElement('div'); dot.className='slider-dot'+(i===0?' active':''); dot.onclick=()=>this.goToSlide(i); this.dotsContainer.appendChild(dot); }); }
  updateSlider(){ if(!this.wrapper) return; this.wrapper.style.transform = `translateX(-${this.currentIndex * 100}%)`; const dots=this.dotsContainer.querySelectorAll('.slider-dot'); dots.forEach((dot,i)=>dot.classList.toggle('active', i===this.currentIndex)); }
  next(){ this.currentIndex = (this.currentIndex+1) % this.items.length; this.updateSlider(); this.resetAutoplay(); }
  prev(){ this.currentIndex = (this.currentIndex -1 + this.items.length) % this.items.length; this.updateSlider(); this.resetAutoplay(); }
  goToSlide(i){ this.currentIndex = i; this.updateSlider(); this.resetAutoplay(); }
  startAutoplay(){ this.autoplayInterval = setInterval(()=>this.next(), this.autoplayDelay); }
  resetAutoplay(){ clearInterval(this.autoplayInterval); this.startAutoplay(); }
  init(){ if(!this.wrapper || !this.dotsContainer) return; this.createDots(); this.updateSlider(); this.startAutoplay(); }
}

class SliderLatest {
  constructor(wrapperId) {
    this.wrapper = document.getElementById(wrapperId);
    if(!this.wrapper) return;
    this.items = this.wrapper.querySelectorAll('.slider-item-latest');
    this.index = 0;
    this.update();
    window.addEventListener('resize', ()=>this.update());
  }
  slideWidth(){ return this.items[0].getBoundingClientRect().width; }
  visibleCount(){ const containerWidth = this.wrapper.parentElement.offsetWidth; return Math.round(containerWidth / this.slideWidth()); }
  maxIndex(){ return Math.max(0, this.items.length - this.visibleCount()); }
  update(){ const translateX = this.index * this.slideWidth(); this.wrapper.style.transform = `translateX(-${translateX}px)`; }
  next(){ if(this.index < this.maxIndex()){ this.index++; this.update(); } }
  prev(){ if(this.index > 0){ this.index--; this.update(); } }
}

document.addEventListener('DOMContentLoaded', async ()=>{
  // Initialize sliders
  window.featuredSlider = new Slider('featuredSlider', 'featuredDots', 5000);
  window.latestSlider = new SliderLatest('latestSlider');

  // Load posts for search suggestions
  try{
    const posts = await window.getPosts();
    const searchInputTop = document.getElementById('searchInputTop');
    const suggestionsBox = document.getElementById('searchSuggestions');
    searchInputTop?.addEventListener('input', (e)=>{
      const q = e.target.value.trim().toLowerCase();
      if(q.length < 2){ suggestionsBox.classList.add('hidden'); return; }
      const items = posts.filter(p => p.title.toLowerCase().includes(q) || p.excerpt.toLowerCase().includes(q));
      window.renderSuggestions(items, 'searchSuggestions', 'goToArticle');
    });
    document.addEventListener('click', (e)=>{ if (!document.getElementById('searchSuggestions')?.contains(e.target) && e.target !== searchInputTop) { suggestionsBox.classList.add('hidden'); } });
  }catch(err){ console.warn('Could not load posts for suggestions', err); }

  // Newsletter form handler
  document.querySelectorAll('form[onsubmit="handleSubscribe(event)"]').forEach(f => f.addEventListener('submit', (e)=>{ e.preventDefault(); const emailInput = e.target.querySelector('input[type="email"]'); if(emailInput && emailInput.value){ alert('Thank you for subscribing!'); emailInput.value = ''; } }));
});
