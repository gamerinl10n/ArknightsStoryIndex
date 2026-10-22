import { $, el } from "./dom.mjs";

/** Native form value with a styled, keyboard-operated listbox. */
export function createCorpusControl() {
  const select = $("lang"),
    button = $("corpus-button"),
    menu = $("corpus-options");
  const options = [...select.options];
  let active = select.selectedIndex;
  function close() {
    menu.hidden = true;
    button.setAttribute("aria-expanded", "false");
    button.removeAttribute("aria-activedescendant");
  }
  function paint() {
    [...menu.children].forEach((node, index) => {
      node.setAttribute(
        "aria-selected",
        String(index === select.selectedIndex),
      );
      node.classList.toggle("is-active", index === active);
    });
    button.setAttribute("aria-activedescendant", menu.children[active].id);
  }
  function refresh() {
    $("corpus-value").textContent = options[select.selectedIndex].textContent;
    active = select.selectedIndex;
    paint();
    if (menu.hidden) button.removeAttribute("aria-activedescendant");
  }
  function open() {
    active = select.selectedIndex;
    menu.hidden = false;
    button.setAttribute("aria-expanded", "true");
    paint();
  }
  function choose(index) {
    const changed = select.selectedIndex !== index;
    select.selectedIndex = index;
    refresh();
    close();
    button.focus();
    if (changed) select.dispatchEvent(new Event("change", { bubbles: true }));
  }
  options.forEach((option, index) => {
    const node = el("div", "", "corpus-option");
    node.id = "corpus-option-" + index;
    node.setAttribute("role", "option");
    node.lang = option.value.replace("_", "-");
    node.append(
      el("span", option.textContent),
      el("span", "✓", "corpus-check"),
    );
    node.lastChild.setAttribute("aria-hidden", "true");
    node.addEventListener("pointerdown", (event) => event.preventDefault());
    node.addEventListener("click", () => choose(index));
    menu.append(node);
  });
  button.addEventListener("click", () => (menu.hidden ? open() : close()));
  button.addEventListener("keydown", (event) => {
    if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      if (menu.hidden) {
        open();
        return;
      }
      active =
        event.key === "Home"
          ? 0
          : event.key === "End"
            ? options.length - 1
            : (active + (event.key === "ArrowDown" ? 1 : -1) + options.length) %
              options.length;
      paint();
    } else if ((event.key === "Enter" || event.key === " ") && !menu.hidden) {
      event.preventDefault();
      choose(active);
    } else if (event.key === "Escape" && !menu.hidden) {
      event.preventDefault();
      close();
    } else if (event.key === "Tab") close();
  });
  button.addEventListener("blur", close);
  document.addEventListener("pointerdown", (event) => {
    if (!button.parentElement.contains(event.target)) close();
  });
  select.addEventListener("change", refresh);
  refresh();
  return { refresh };
}
