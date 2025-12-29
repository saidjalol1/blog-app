import './posts-client.js';

// About page specific: wire search suggestions using posts-client and shared renderSuggestions

document.addEventListener('DOMContentLoaded', async () => {
  const searchInput = document.getElementById('searchInputTop');
  const suggestionsBox = document.getElementById('searchSuggestions');

  let posts = [];
  try{
    posts = await window.getPosts();
  }catch(e){
    // fallback small list
    posts = [
      {slug:'remote-first-companies',title:'Remote-First Companies',excerpt:'How distributed teams succeed in the modern workplace.'},
      {slug:'the-ai-revolution',title:'The AI Revolution',excerpt:'How machine learning is changing everything.'},
      {slug:'designing-a-sustainable-future',title:'Designing a Sustainable Future',excerpt:'Green tech with beautiful UX.'},
      {slug:'travel-tips-2025',title:'Travel Tips for 2025',excerpt:'Smart budgeting and off-the-beaten-path finds.'},
      {slug:'education-reform-road-ahead',title:'Education Reform: The Road Ahead',excerpt:'How accessible learning is reshaping careers.'}
    ];
  }

  searchInput?.addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    if (q.length < 2) { suggestionsBox.classList.add('hidden'); return; }
    const items = posts.filter(p => p.title.toLowerCase().includes(q) || p.excerpt.toLowerCase().includes(q));
    window.renderSuggestions(items, 'searchSuggestions', 'goToArticle');
  });

  document.addEventListener('click', (e) => {
    if (!document.getElementById('searchSuggestions')?.contains(e.target) && e.target !== searchInput) {
      suggestionsBox.classList.add('hidden');
    }
  });
});