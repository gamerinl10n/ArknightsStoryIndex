(() => {
  const {key, apply} = window.ASITheme;
  apply(document.documentElement.dataset.theme || 'light');
  document.getElementById('themeButton')?.addEventListener('click', () => {
    const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    apply(theme);
    try { localStorage.setItem(key, theme); } catch {}
  });
  window.addEventListener('storage', event => { if (event.key === key || event.key === null) apply(event.newValue || 'light'); });
})();
document.getElementById('ui-language')?.addEventListener('change', event => {
  const url=new URL(location.href);url.searchParams.set('ui',event.target.value);
  if(document.getElementById('speaker')) {url.searchParams.set('view',document.getElementById('search-experience').dataset.view==='home'?'home':'results');for(const id of ['speaker','target','lang'])url.searchParams.set(id,document.getElementById(id).value);url.searchParams.set('q',document.getElementById('query').value);url.searchParams.set('spoilers',document.getElementById('spoilers').checked?'1':'0');}
  location.assign(url);
});
const footer=document.querySelector('.site-footer');
if(footer){const reserve=()=>document.documentElement.style.setProperty('--footer-space',footer.getBoundingClientRect().height+'px');reserve();if('ResizeObserver' in window)new ResizeObserver(reserve).observe(footer);window.addEventListener('resize',reserve);}

const header=document.querySelector('header');
if(header){const measure=()=>document.documentElement.style.setProperty('--header-space',header.getBoundingClientRect().height+'px');measure();if('ResizeObserver' in window)new ResizeObserver(measure).observe(header);window.addEventListener('resize',measure);}
