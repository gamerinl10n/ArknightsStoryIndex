import { createComparisonControl } from "./comparison-control.mjs";
const control = createComparisonControl();
control.restore(new URLSearchParams(location.search).get("show") || "");
window.addEventListener("popstate", () =>
  control.restore(new URLSearchParams(location.search).get("show") || ""),
);

function preserveLanguages() {
  const show = new URLSearchParams(location.search).get("show") || "";
  document.querySelector('#voice-search-form [name="show"]').value = show;
  for (const link of document.querySelectorAll(
    ".voice-pagination a, .voice-reset",
  )) {
    const url = new URL(link.href);
    url.searchParams.set("show", show);
    link.href = url.href;
  }
}
for (const button of document.querySelectorAll("[data-translation-lang]"))
  button.addEventListener("click", preserveLanguages);
window.addEventListener("popstate", preserveLanguages);
preserveLanguages();
