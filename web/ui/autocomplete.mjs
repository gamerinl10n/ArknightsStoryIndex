import { $, el } from "./dom.mjs";
import { api } from "./api.mjs";
export function createAutocomplete() {
  let suggestions = [],
    suggestionVersion = 0;
  function completion(id) {
    const input = $(id),
      list = $(id + "-options");
    let active = -1,
      rows = [];
    const close = () => {
      list.hidden = true;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      active = -1;
    };
    function draw() {
      const query = input.value.trim().toLocaleLowerCase();
      const exact = suggestions.find((row) => row.key === query);
      rows = exact ? [exact] : [];
      for (const row of suggestions) {
        if (rows.length === 12) break;
        if (row !== exact && (!query || row.search.includes(query)))
          rows.push(row);
      }
      active = -1;
      list.replaceChildren();
      input.removeAttribute("aria-activedescendant");
      rows.forEach((row, index) => {
        const option = el("div", "", "suggestion");
        option.id = id + "-option-" + index;
        option.setAttribute("role", "option");
        option.setAttribute("aria-selected", "false");
        option.append(el("span", row.value));
        if (row.label !== row.value) option.append(el("small", row.label));
        option.addEventListener("pointerdown", (event) =>
          event.preventDefault(),
        );
        option.addEventListener("click", () => {
          input.value = row.value;
          input.setCustomValidity("");
          close();
          input.focus();
        });
        list.append(option);
      });
      list.hidden = !rows.length;
      input.setAttribute("aria-expanded", String(rows.length > 0));
    }
    input.addEventListener("input", () => {
      input.setCustomValidity("");
      draw();
    });
    input.addEventListener("focus", draw);
    input.addEventListener("blur", close);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        return;
      }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        if (list.hidden) draw();
        if (!rows.length) return;
        active =
          (active + (event.key === "ArrowDown" ? 1 : -1) + rows.length) %
          rows.length;
        [...list.children].forEach((node, i) =>
          node.setAttribute("aria-selected", String(i === active)),
        );
        input.setAttribute("aria-activedescendant", list.children[active].id);
        list.children[active].scrollIntoView?.({ block: "nearest" });
      } else if (event.key === "Enter" && !list.hidden && active >= 0) {
        event.preventDefault();
        input.value = rows[active].value;
        close();
      }
    });
    return {
      refresh: () => {
        if (document.activeElement === input) draw();
      },
      close,
    };
  }
  const completions = [completion("speaker"), completion("target")];
  $("swap").onclick = () => {
    const a = $("speaker").value;
    $("speaker").value = $("target").value;
    $("target").value = a;
    completions.forEach((c) => c.close());
  };
  async function loadSpeakers() {
    const version = ++suggestionVersion;
    suggestions = [];
    completions.forEach((c) => c.close());
    try {
      const params = new URLSearchParams({
        lang: $("lang").value,
        spoilers: $("spoilers").checked ? "1" : "0",
      });
      const rows = await api("/api/suggestions?" + params);
      if (version !== suggestionVersion) return;
      suggestions = rows
        .map((row) => ({
          ...row,
          key: row.value.toLocaleLowerCase(),
          search: (row.value + " " + row.label).toLocaleLowerCase(),
        }))
        .sort((a, b) => b.count - a.count);
      completions.forEach((c) => c.refresh());
    } catch {
      if (version === suggestionVersion) suggestions = [];
    }
  }
  $("lang").addEventListener("change", loadSpeakers);
  $("spoilers").addEventListener("change", loadSpeakers);
  return {
    close: () => completions.forEach((c) => c.close()),
    load: loadSpeakers,
  };
}
