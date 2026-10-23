/* Splash controller structure adapted from the owner's L10ndiff. */
export function createLanguageSplashController({
  documentRef = document,
} = {}) {
  const root = documentRef.documentElement;
  const splash = documentRef.getElementById("languageSplash");
  return {
    show(variant, phase) {
      const normalized = /^[1-3]$/.test(String(variant))
        ? String(variant)
        : "1";
      root.dataset.languageSplashVariant = normalized;
      if (!splash) return;
      splash.dataset.variant = normalized;
      splash.dataset.phase = phase;
    },
    reset() {
      delete root.dataset.languageSplashVariant;
      if (splash) delete splash.dataset.phase;
    },
  };
}
