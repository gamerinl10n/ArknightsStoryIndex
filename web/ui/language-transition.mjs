/* Leave → navigation → enter lifecycle adapted from the owner's L10ndiff. */
const MARKER = "asi-language-transition";
const COUNTER = "asi-language-splash-variant";
const LEAVE_MS = 380;
const ENTER_MS = 300;

export function setupLanguageTransitions({
  documentRef = document,
  windowRef = window,
  splashController,
  navigate = (url) => windowRef.location.assign(url),
} = {}) {
  const root = documentRef.documentElement;
  const links = [...documentRef.querySelectorAll(".language-switch a")];
  const timers = new Set();
  let navigating = false;
  const reduced = () =>
    windowRef.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const read = (key) => {
    try {
      return windowRef.sessionStorage.getItem(key);
    } catch {
      return null;
    }
  };
  const write = (key, value) => {
    try {
      windowRef.sessionStorage.setItem(key, value);
    } catch {}
  };
  const remove = (key) => {
    try {
      windowRef.sessionStorage.removeItem(key);
    } catch {}
  };
  const later = (callback, delay) => {
    const timer = windowRef.setTimeout(() => {
      timers.delete(timer);
      callback();
    }, delay);
    timers.add(timer);
  };
  const reset = () => {
    navigating = false;
    timers.forEach((timer) => windowRef.clearTimeout(timer));
    timers.clear();
    root.classList.remove("is-language-entering", "is-language-leaving");
    splashController?.reset();
  };
  let pending;
  try {
    pending = JSON.parse(read(MARKER) || "null");
  } catch {}
  remove(MARKER);
  root.classList.remove("is-language-entering");
  if (
    pending &&
    /^[1-3]$/.test(String(pending.variant)) &&
    pending.ui === root.lang &&
    pending.expires > Date.now() &&
    !reduced()
  ) {
    splashController?.show(pending.variant, "enter");
    root.classList.add("is-language-entering");
    later(reset, ENTER_MS);
  }
  const click = (event) => {
    const link = event.currentTarget;
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey ||
      link.target === "_blank"
    )
      return;
    if (navigating) {
      event.preventDefault();
      return;
    }
    const destination = new URL(link.href, windowRef.location.href);
    if (destination.origin !== windowRef.location.origin) return;
    if (
      link.getAttribute("aria-current") === "page" ||
      destination.href === windowRef.location.href
    ) {
      event.preventDefault();
      return;
    }
    if (reduced()) return;
    event.preventDefault();
    reset();
    navigating = true;
    const current = Number(read(COUNTER));
    const variant =
      current >= 1 && current <= 3 && Number.isInteger(current)
        ? (current % 3) + 1
        : 1;
    write(COUNTER, String(variant));
    write(
      MARKER,
      JSON.stringify({
        variant,
        ui: link.dataset.ui,
        expires: Date.now() + 15000,
      }),
    );
    splashController?.show(variant, "leave");
    root.classList.add("is-language-leaving");
    later(() => {
      try {
        navigate(destination.href);
      } catch {
        remove(MARKER);
        reset();
      }
    }, LEAVE_MS);
    // A failed or cancelled navigation must not leave the whole site covered.
    later(() => {
      remove(MARKER);
      reset();
    }, 5000);
  };
  const pageShow = (event) => {
    if (event.persisted || navigating) {
      remove(MARKER);
      reset();
    }
  };
  links.forEach((link) => link.addEventListener("click", click));
  windowRef.addEventListener("pageshow", pageShow);
  return () => {
    links.forEach((link) => link.removeEventListener("click", click));
    windowRef.removeEventListener("pageshow", pageShow);
    reset();
  };
}
