export const $ = (id) => document.getElementById(id);
export const t = (key, values = {}) =>
  Object.entries(values).reduce(
    (text, [key, value]) => text.replaceAll("{" + key + "}", String(value)),
    window.ASI.strings[key] || key,
  );
export const el = (tag, text = "", className = "") => {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
};
export const reducedMotion = () =>
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
