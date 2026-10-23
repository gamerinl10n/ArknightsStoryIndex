import { $ } from "./dom.mjs";
import { readForm } from "./form-state.mjs";

export function bindSearchReset({ autocomplete, stopSearch }) {
  $("reset-search").addEventListener("click", () => {
    stopSearch();
    for (const id of ["query", "speaker", "target"]) {
      $(id).value = "";
      $(id).setCustomValidity("");
    }
    autocomplete.close();
    autocomplete.hydrate();
    history.replaceState({ draft: readForm() }, "", location.href);
  });
}
