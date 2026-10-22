import { $, el } from "./dom.mjs";

/** Decorative avatars never replace accessible names or alter search text. */
export function portrait(identity = {}, className = "") {
  const slot = el("span", "", "portrait " + className);
  slot.setAttribute("aria-hidden", "true");
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  const head = document.createElementNS(svg.namespaceURI, "circle");
  head.setAttribute("cx", "12");
  head.setAttribute("cy", "8");
  head.setAttribute("r", "3.5");
  const body = document.createElementNS(svg.namespaceURI, "path");
  body.setAttribute("d", "M5 21v-2a7 7 0 0 1 14 0v2");
  svg.append(head, body);
  slot.append(svg);
  if (identity.portrait) {
    const image = document.createElement("img");
    image.alt = "";
    image.width = 96;
    image.height = 96;
    image.loading = "lazy";
    image.decoding = "async";
    image.src = identity.portrait;
    image.addEventListener("error", () => image.remove(), { once: true });
    slot.append(image);
  }
  return slot;
}

export function setInputPortrait(id, identity) {
  const field = $(id).closest(".field");
  field.querySelector(".input-portrait")?.remove();
  field.classList.toggle("has-portrait", Boolean(identity));
  if (identity) field.prepend(portrait(identity, "input-portrait"));
}

export function setResultTitle(text, participants = {}, search = {}) {
  const title = $("results-title");
  title.replaceChildren();
  for (const key of ["speaker", "target"]) {
    if (search[key])
      title.append(portrait(participants[key] || {}, "title-portrait"));
  }
  title.append(el("span", text));
}
