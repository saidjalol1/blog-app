// Posts client: fetch posts via API
window.getPosts = async function(params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = `/blogs/fetch_blogs/?${query}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('network');
  const data = await res.json();
  return data;
};

window.getFilters = async function() {
  const res = await fetch('/blogs/filters/');
  if (!res.ok) throw new Error('network');
  return await res.json();
};