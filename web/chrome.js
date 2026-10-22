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
