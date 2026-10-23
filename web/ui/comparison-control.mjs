import { $ } from "./dom.mjs";

/** Display toggles never change the query, pagination or open context. */
export function createComparisonControl() {
  const buttons = [...document.querySelectorAll("[data-translation-lang]")];
  const main = { ko: "ko_KR", zh: "zh_CN", ja: "ja_JP", en: "en_US" }[
    window.ASI.ui
  ];
  let selected = new Set();
  function refresh() {
    for (const button of buttons) {
      const lang = button.dataset.translationLang;
      button.setAttribute(
        "aria-pressed",
        String(lang === main || selected.has(lang)),
      );
      button.disabled = lang === main;
    }
    for (const row of $("results").querySelectorAll("[data-variant-lang]"))
      row.hidden =
        row.dataset.primary !== "true" &&
        !selected.has(row.dataset.variantLang);
  }
  for (const button of buttons)
    button.addEventListener("click", () => {
      const lang = button.dataset.translationLang;
      if (lang === main) return;
      if (selected.has(lang)) selected.delete(lang);
      else selected.add(lang);
      refresh();
      const show = [...selected].join(",");
      const url = new URL(location.href);
      url.searchParams.set("show", show);
      history.replaceState(
        { ...history.state, draft: { ...history.state?.draft, show } },
        "",
        url,
      );
    });
  const observer = new MutationObserver(refresh);
  observer.observe($("results"), { childList: true, subtree: true });
  return {
    refresh,
    restore(value) {
      selected = new Set(
        value
          .split(",")
          .filter(
            (lang) =>
              lang !== main &&
              buttons.some((b) => b.dataset.translationLang === lang),
          ),
      );
      refresh();
    },
  };
}
