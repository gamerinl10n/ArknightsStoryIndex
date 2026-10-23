import { $ } from "./dom.mjs";
import { readForm } from "./form-state.mjs";

export function bindSearchReset({
  autocomplete,
  stopSearch,
  onReset = () => {},
}) {
  $("reset-search").addEventListener("click", () => {
    stopSearch();
    for (const id of ["query", "speaker", "target"]) {
      $(id).value = "";
      $(id).setCustomValidity("");
    }
    autocomplete.close();
    autocomplete.hydrate();
    const draft = readForm();
    const url = new URL("/", location.href);
    url.searchParams.set("ui", window.ASI.ui);
    for (const key of ["lang", "spoilers", "compare", "translation_lang"])
      url.searchParams.set(key, draft[key]);
    history.replaceState({ draft }, "", url);
    onReset();
  });
}
