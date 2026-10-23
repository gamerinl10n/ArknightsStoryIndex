/* Restore L10ndiff-style arrival state before first paint; no inline script. */
(() => {
  try {
    const pending = JSON.parse(sessionStorage.getItem('asi-language-transition') || 'null');
    const root = document.documentElement;
    if (pending && /^[1-3]$/.test(String(pending.variant)) && pending.ui === root.lang && pending.expires > Date.now() && !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      root.classList.add('is-language-entering');
      root.dataset.languageSplashVariant = String(pending.variant);
      // Recover even if a later module fails to load.
      window.setTimeout(() => {
        if (root.classList.contains('is-language-entering')) {
          root.classList.remove('is-language-entering');
          delete root.dataset.languageSplashVariant;
        }
      }, 2000);
    }
  } catch {}
})();
