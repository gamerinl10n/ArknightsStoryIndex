import { $, t, reducedMotion } from "./ui/dom.mjs";
import { api } from "./ui/api.mjs";
import { readForm } from "./ui/form-state.mjs";
import { createNavigation } from "./ui/navigation.mjs";
import { createAutocomplete } from "./ui/autocomplete.mjs";
import { renderBatch } from "./ui/results.mjs";
import { storyOptions } from "./ui/filters.mjs";

let offset = 0,
  last = null,
  requestVersion = 0,
  controller,
  renderedKey = null,
  cachedStories = [];
const setView = createNavigation($("search-experience"));
const autocomplete = createAutocomplete();
function stopSearch() {
  ++requestVersion;
  controller?.abort();
  $("submit-search").disabled = false;
  $("submit-search").textContent = t("search");
  $("results").setAttribute("aria-busy", "false");
  $("story-filter").disabled = false;
  $("search-loading").hidden = true;
}
function goHome(event) {
  event?.preventDefault();
  const draft = readForm();
  history.pushState(
    { draft },
    "",
    "/?" + new URLSearchParams({ ui: window.ASI.ui }),
  );
  stopSearch();
  autocomplete.close();
  setView("home");
  $("speaker").focus({ preventScroll: true });
  window.scrollTo?.({
    top: 0,
    behavior: reducedMotion() ? "instant" : "smooth",
  });
}
$("back-search").onclick = goHome;
document.querySelector(".brand").addEventListener("click", (event) => {
  if (
    event.button === 0 &&
    !event.ctrlKey &&
    !event.metaKey &&
    !event.shiftKey &&
    !event.altKey
  )
    goHome(event);
});
function empty(title, description) {
  $("empty-state").hidden = false;
  $("empty-state").querySelector("h3").textContent = title;
  $("empty-state").querySelector("p").textContent = description;
}
async function run(append = false) {
  const version = ++requestVersion,
    search = { ...last };
  controller?.abort();
  controller = new AbortController();
  $("more").disabled = true;
  $("submit-search").disabled = true;
  $("submit-search").textContent = t("loading");
  $("results").setAttribute("aria-busy", "true");
  if (!append) {
    $("results").replaceChildren();
    $("more").hidden = true;
    $("result-count").textContent = "";
    $("empty-state").hidden = true;
  }
  $("notice").textContent = t("loading");
  $("story-filter").disabled = true;
  $("search-loading").hidden = false;
  $("search-loading").dataset.append = String(append);
  renderedKey = null;
  try {
    const params = new URLSearchParams(search);
    params.set("offset", offset);
    params.set("details", "0");
    const data = await api("/api/search?" + params, {
      signal: controller.signal,
    });
    if (version !== requestVersion) return;
    if (!append) {
      cachedStories = data.stories || [];
      storyOptions(cachedStories, search.story);
    }
    renderBatch(data.items, search.q);
    offset += data.items.length;
    renderedKey = JSON.stringify(search);
    $("more").hidden = offset >= data.total;
    $("results-title").textContent = search.target
      ? t("search_pair", { a: search.speaker, b: search.target })
      : t("search_solo", { a: search.speaker });
    $("result-count").textContent = t("count", {
      n: data.total.toLocaleString(),
    });
    $("notice").textContent = "";
    $("share-search").hidden = false;
    if (!data.total) empty(t("no_results"), t("broaden"));
  } catch (error) {
    if (version !== requestVersion || error.name === "AbortError") return;
    $("notice").textContent = t("failed");
    if (!append) empty(t("failed"), t("retry"));
  } finally {
    if (version === requestVersion) {
      $("more").disabled = false;
      $("submit-search").disabled = false;
      $("submit-search").textContent = t("search");
      $("results").setAttribute("aria-busy", "false");
      $("story-filter").disabled = false;
      $("search-loading").hidden = true;
    }
  }
}
function submit(updateUrl = true, keepStory = false) {
  if (!$("speaker").value.trim()) {
    $("speaker").setCustomValidity(t("search_error"));
    $("speaker").reportValidity();
    return;
  }
  if (!keepStory) $("story-filter").value = "";
  const draft = readForm();
  if (updateUrl) {
    history.replaceState({ ...history.state, draft }, "", location.href);
    const params = new URLSearchParams(draft);
    params.set("ui", window.ASI.ui);
    history.pushState({ draft }, "", "/search?" + params);
  }
  offset = 0;
  last = draft;
  autocomplete.close();
  setView("results");
  run();
}
function restore(initial = false) {
  const params = new URLSearchParams(location.search),
    draft = history.state?.draft || {};
  for (const key of ["speaker", "target"])
    $(key).value = (params.get(key) ?? draft[key] ?? "").slice(0, 300);
  const story = (params.get("story") ?? draft.story ?? "").slice(0, 300);
  storyOptions(cachedStories, story);
  $("query").value = (params.get("q") ?? draft.q ?? "").slice(0, 300);
  const lang = params.get("lang") || draft.lang;
  $("lang").value = [...$("lang").options].some((o) => o.value === lang)
    ? lang
    : { ko: "ko_KR", zh: "zh_CN", ja: "ja_JP", en: "en_US" }[window.ASI.ui];
  $("spoilers").checked = (params.get("spoilers") ?? draft.spoilers) === "1";
  autocomplete.load();
  const showResults =
    $("speaker").value &&
    params.get("view") !== "home" &&
    (location.pathname === "/search" || params.has("speaker"));
  if (showResults) {
    const search = readForm();
    setView("results", !initial);
    if (renderedKey !== JSON.stringify(search)) {
      offset = 0;
      last = search;
      run();
    }
  } else {
    stopSearch();
    setView("home", !initial);
  }
}
$("story-filter").addEventListener("change", () => submit(true, true));
$("search").onsubmit = (event) => {
  event.preventDefault();
  submit();
};
$("more").onclick = () => run(true);
$("share-search").onclick = async () => {
  try {
    await navigator.clipboard.writeText(location.href);
    $("share-search").textContent = t("shared");
  } catch {
    $("share-search").textContent = t("copy_failed");
  }
};
window.addEventListener("popstate", () => restore(false));
restore(true);
