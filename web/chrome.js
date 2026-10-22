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
function languageUrl(code) {
  const url=new URL(location.href);url.searchParams.set('ui',code);
  if(document.getElementById('speaker')) {url.searchParams.set('view',document.getElementById('search-experience').dataset.view==='home'?'home':'results');for(const id of ['speaker','target','lang'])url.searchParams.set(id,document.getElementById(id).value);url.searchParams.set('q',document.getElementById('query').value);url.searchParams.set('spoilers',document.getElementById('spoilers').checked?'1':'0');url.searchParams.set('story',document.getElementById('story-filter').value);}
  return url;
}
document.querySelectorAll('.language-switch a').forEach(link=>{
  // Refresh href before native navigation, including modifier-clicks and new tabs.
  const refresh=()=>{link.href=languageUrl(link.dataset.ui).href;};
  link.addEventListener('pointerdown',refresh);link.addEventListener('focus',refresh);link.addEventListener('click',refresh);
});
(() => {
  let opener;
  const dialogs=[...document.querySelectorAll('dialog.modal')];
  const open=(dialog,trigger)=>{if(dialog.open)return;opener=trigger||document.activeElement;dialog.showModal();document.documentElement.classList.add('modal-open');};
  dialogs.forEach(dialog=>{
    dialog.querySelector('[data-close-dialog]').addEventListener('click',()=>dialog.close());
    dialog.addEventListener('click',event=>{const r=dialog.getBoundingClientRect();if(event.target===dialog&&(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom))dialog.close();});
    dialog.addEventListener('close',()=>{document.documentElement.classList.remove('modal-open');if(opener?.isConnected)opener.focus({preventScroll:true});});
  });
  window.ASIDialog={open};
  const help=document.getElementById('help-dialog'),button=document.getElementById('help-button');
  button.addEventListener('click',()=>open(help,button));
  if(new URLSearchParams(location.search).get('help')==='1')open(help,button);
})();
const footer=document.querySelector('.site-footer');
if(footer){const reserve=()=>document.documentElement.style.setProperty('--footer-space',footer.getBoundingClientRect().height+'px');reserve();if('ResizeObserver' in window)new ResizeObserver(reserve).observe(footer);window.addEventListener('resize',reserve);}

const header=document.querySelector('header');
if(header){const measure=()=>document.documentElement.style.setProperty('--header-space',header.getBoundingClientRect().height+'px');measure();if('ResizeObserver' in window)new ResizeObserver(measure).observe(header);window.addEventListener('resize',measure);}
