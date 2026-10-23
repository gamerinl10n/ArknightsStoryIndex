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
    url.searchParams.set("lang", draft.lang);
    url.searchParams.set("spoilers", draft.spoilers);
    history.replaceState({ draft }, "", url);
    onReset();
  });
}
