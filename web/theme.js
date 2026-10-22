/* Theme chrome adapted from gamerinl10n/l10ndiff with the owner's permission. */
(() => {
  const key = 'asi-theme-v1';
  function apply(theme) {
    const dark = theme === 'dark';
    if (dark) document.documentElement.dataset.theme = 'dark';
    else delete document.documentElement.dataset.theme;
    document.getElementById('themeColorMeta')?.setAttribute('content', dark ? '#1a1a1a' : '#f0f0f0');
    document.getElementById('colorSchemeMeta')?.setAttribute('content', dark ? 'dark light' : 'light dark');
    const button = document.getElementById('themeButton');
    if (button) {
      const label = dark ? '라이트 모드' : '다크 모드';
      button.setAttribute('title', label); button.setAttribute('aria-label', label); button.setAttribute('aria-pressed', String(dark));
    }
  }
  let saved = 'light';
  try { saved = localStorage.getItem(key) || 'light'; } catch {}
  apply(saved);
  window.ASITheme = {key, apply};
})();
