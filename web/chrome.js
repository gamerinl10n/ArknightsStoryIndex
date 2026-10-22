import { preserveForm } from "./ui/form-state.mjs";
import { initDialogs } from "./ui/dialogs.mjs";

(() => {
  const { key, apply } = window.ASITheme;
  apply(document.documentElement.dataset.theme || "light");
  document.getElementById("themeButton")?.addEventListener("click", () => {
    const theme =
      document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    apply(theme);
    try {
      localStorage.setItem(key, theme);
    } catch {}
  });
  window.addEventListener("storage", (event) => {
    if (event.key === key || event.key === null)
      apply(event.newValue || "light");
  });
})();
document.querySelectorAll(".language-switch a").forEach((link) => {
  const refresh = () => {
    const url = preserveForm();
    url.searchParams.set("ui", link.dataset.ui);
    url.searchParams.set(
      "lang",
      { ko: "ko_KR", zh: "zh_CN", ja: "ja_JP", en: "en_US" }[link.dataset.ui],
    );
    link.href = url.href;
  };
  for (const event of ["pointerdown", "focus", "click"])
    link.addEventListener(event, refresh);
});
initDialogs();
const footer = document.querySelector(".site-footer");
if (footer) {
  const reserve = () =>
    document.documentElement.style.setProperty(
      "--footer-space",
      footer.getBoundingClientRect().height + "px",
    );
  reserve();
  if ("ResizeObserver" in window) new ResizeObserver(reserve).observe(footer);
  window.addEventListener("resize", reserve);
}
