import { $ } from "./dom.mjs";

export function createComparisonControl(corpusControl) {
  const compare = $("compare"),
    lang = $("lang"),
    translation = $("translation-lang");
  let previousLang = { ko: "ko_KR", zh: "zh_CN", ja: "ja_JP", en: "en_US" }[
    window.ASI.ui
  ];
  const buttons = [...document.querySelectorAll("[data-translation-lang]")];
  function refresh() {
    $("translation-languages").hidden =
      !compare.checked || lang.value !== "zh_CN";
    for (const button of buttons)
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.translationLang === translation.value),
      );
  }
  function setLanguage(value) {
    lang.value = value;
    corpusControl.refresh();
    lang.dispatchEvent(new Event("change", { bubbles: true }));
  }
  compare.addEventListener("change", () => {
    if (compare.checked) {
      previousLang = lang.value;
      setLanguage("zh_CN");
    } else setLanguage(previousLang);
    refresh();
  });
  lang.addEventListener("change", refresh);
  for (const button of buttons)
    button.addEventListener("click", () => {
      translation.value = button.dataset.translationLang;
      refresh();
    });
  refresh();
  return { refresh };
}
