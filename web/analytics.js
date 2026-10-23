(() => {
  // Keep development and Vercel previews out of the production property.
  if (
    !["arknightsindex.com", "www.arknightsindex.com"].includes(
      location.hostname,
    )
  )
    return;
  if (document.getElementById("asi-google-tag")) return;
  const measurementId = "G-2TEVDLNB9K";
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () {
    window.dataLayer.push(arguments);
  };
  function pageAddress(value) {
    try {
      const url = new URL(value);
      return /^https?:$/.test(url.protocol) ? url.origin + url.pathname : "";
    } catch {
      return "";
    }
  }
  window.gtag("js", new Date());
  window.gtag("config", measurementId, {
    page_location: pageAddress(location.href),
    page_referrer: pageAddress(document.referrer),
    allow_google_signals: false,
    allow_ad_personalization_signals: false,
  });
  const script = document.createElement("script");
  script.id = "asi-google-tag";
  script.async = true;
  script.dataset.state = "loading";
  script.addEventListener("load", () => {
    script.dataset.state = "loaded";
  });
  script.addEventListener("error", () => {
    script.dataset.state = "blocked";
  });
  script.src = "https://www.googletagmanager.com/gtag/js?id=" + measurementId;
  document.head.append(script);
})();
