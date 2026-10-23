import { el, t } from "./dom.mjs";

const LABELS = {
  zh_CN: "中文",
  ko_KR: "한국어",
  ja_JP: "日本語",
  en_US: "English",
};

export function pairedQuote(item, needle, quote, infoButton) {
  const comparison = item.comparison;
  const box = el("div", "", "paired-quote");
  const matched = comparison.status === "matched";
  const rows = matched
    ? [item, ...comparison.items].sort((a, b) =>
        a.lang === "zh_CN" ? -1 : b.lang === "zh_CN" ? 1 : 0,
      )
    : [item];
  for (const row of rows) {
    const section = el("div", "", "paired-line");
    section.lang = row.lang.replace("_", "-");
    const heading = el("div", "", "paired-heading");
    const suffix =
      row.lang === "zh_CN" ? t("original_text") : row.speaker || t("unnamed");
    heading.append(el("span", `${LABELS[row.lang]} · ${suffix}`));
    if (row !== item) heading.append(infoButton(row));
    section.append(heading, quote(row.text, row === item ? needle : ""));
    box.append(section);
  }
  if (!matched)
    box.append(
      el(
        "p",
        t(
          comparison.status === "unavailable"
            ? comparison.lang === "zh_CN"
              ? "original_unavailable"
              : "translation_unavailable"
            : "translation_unverified",
        ),
        "pair-status",
      ),
    );
  return box;
}
