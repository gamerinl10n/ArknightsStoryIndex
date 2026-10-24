import { $ } from "./dom.mjs";

/** Display toggles never change the query, pagination or open context. */
export function createComparisonControl() {
  const buttons = [...document.querySelectorAll("[data-translation-lang]")];
  const main = { ko: "ko_KR", zh: "zh_CN", ja: "ja_JP", en: "en_US" }[
    window.ASI.ui
  ];
  let selected = new Set();
  function updateRows(root) {
    if (root.nodeType !== 1 || !root.isConnected) return;
    const rows = [...root.querySelectorAll("[data-variant-lang]")];
    if (root.matches("[data-variant-lang]")) rows.unshift(root);
    for (const row of rows)
      row.hidden =
        row.dataset.primary !== "true" &&
        !selected.has(row.dataset.variantLang);
  }
  function refresh() {
    for (const button of buttons) {
      const lang = button.dataset.translationLang;
      button.setAttribute(
        "aria-pressed",
        String(lang === main || selected.has(lang)),
      );
      button.disabled = lang === main;
    }
    updateRows($("results"));
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
  const observer = new MutationObserver((records) => {
    // Appending context or another page should not rescan all existing results.
    const roots = new Set();
    for (const record of records)
      for (const node of record.addedNodes)
        if (node.nodeType === 1 && node.isConnected) roots.add(node);
    for (const node of roots) {
      let parent = node.parentElement;
      while (parent && !roots.has(parent)) parent = parent.parentElement;
      if (!parent) updateRows(node);
    }
  });
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
