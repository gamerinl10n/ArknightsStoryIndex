import { $ } from "./dom.mjs";

export function readForm() {
  if (!$("speaker")) return null;
  return {
    speaker: $("speaker").value.trim(),
    target: $("target").value.trim(),
    q: $("query").value.trim(),
    lang: $("lang").value,
    spoilers: $("spoilers").checked ? "1" : "0",
    story: $("story-filter").value,
  };
}

export function preserveForm(url = new URL(location.href)) {
  const draft = readForm();
  if (draft) {
    for (const [key, value] of Object.entries(draft))
      url.searchParams.set(key, value);
    url.searchParams.set("view", $("search-experience").dataset.view);
  }
  return url;
}
