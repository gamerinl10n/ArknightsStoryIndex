import { $, t, el } from "./dom.mjs";
export function storyOptions(stories, selected) {
  const select = $("story-filter");
  select.replaceChildren();
  const all = el("option", t("all_stories"));
  all.value = "";
  select.append(all);
  stories.forEach((row) => {
    const option = el(
      "option",
      t("story_count", { path: row.path, n: row.count }),
    );
    option.value = row.path;
    select.append(option);
  });
  if (selected && !stories.some((row) => row.path === selected)) {
    const option = el("option", selected);
    option.value = selected;
    select.append(option);
  }
  select.value = selected || "";
  $("result-filters").hidden = stories.length < 2 && !selected;
}
