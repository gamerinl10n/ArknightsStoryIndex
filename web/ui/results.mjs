import { $, t, el } from "./dom.mjs";
import { api } from "./api.mjs";
import { portrait } from "./portraits.mjs";
import { openDialog } from "./dialogs.mjs";

function infoButton(item, row = item) {
  const button = el("button", "?", "info-button");
  button.type = "button";
  button.title = t("source_details");
  button.setAttribute("aria-label", t("source_details"));
  button.setAttribute("aria-haspopup", "dialog");
  button.onclick = () => {
    const list = el("dl", "", "source-list");
    const fields = [
      ["source_file", item.path],
      ["source_line", String(row.ordinal + 1)],
      [
        "branch",
        !row.branch || row.branch === "main" ? t("main_branch") : row.branch,
      ],
      ["source_revision", item.revision],
      ["source", item.source],
      ["corpus", item.lang],
    ];
    for (const [key, value] of fields)
      list.append(el("dt", t(key)), el("dd", value));
    $("info-content").replaceChildren(
      list,
      el("p", t("branch_hint"), "source-hint"),
    );
    openDialog($("info-dialog"), button);
  };
  return button;
}

function quote(text, needle) {
  const node = el("p", "", "quote");
  if (!needle) {
    node.textContent = text;
    return node;
  }
  let at = 0,
    index;
  while ((index = text.indexOf(needle, at)) !== -1) {
    node.append(
      document.createTextNode(text.slice(at, index)),
      el("mark", needle),
    );
    at = index + needle.length;
  }
  node.append(document.createTextNode(text.slice(at)));
  return node;
}

function contextRows(rows, item, needle, matches = [item]) {
  const fragment = document.createDocumentFragment();
  for (const row of rows) {
    const line = el(
      "div",
      "",
      "context-line" +
        (matches.some((match) => match.ordinal === row.ordinal)
          ? " current-line"
          : ""),
    );
    const heading = el("div", "", "context-heading");
    heading.append(
      portrait(row),
      el("strong", row.speaker || t("unnamed")),
      infoButton(item, row),
    );
    line.append(heading, quote(row.text, needle));
    fragment.append(line);
  }
  return fragment;
}

function renderCard(group, needle, index) {
  const item = group[Math.floor((group.length - 1) / 2)];
  const initialRadius = Math.max(
    3,
    group[group.length - 1].ordinal - group[0].ordinal,
  );
  const card = el("article", "", "result-card");
  card.lang = item.lang.replace("_", "-");
  card.style.setProperty("--enter-delay", Math.min(index, 5) * 35 + "ms");
  if (group.some((row) => row.nearby_turns > 0))
    card.append(el("span", t("nearby_turns"), "evidence-label"));
  for (const row of group) {
    const heading = el("div", "", "card-heading");
    heading.append(
      portrait(row),
      el("h2", row.speaker || t("unnamed")),
      infoButton(row),
    );
    card.append(heading, quote(row.text, needle));
  }

  // Network, line DOM and event handlers are created only when a section is opened.
  let detailRequest;
  const details = () => {
    if (!detailRequest) {
      detailRequest = item.context
        ? Promise.resolve({
            items: item.context,
            has_more: true,
          })
        : api(
            "/api/context?" +
              new URLSearchParams({
                story: item.story,
                ordinal: item.ordinal,
                radius: initialRadius,
              }),
          );
      detailRequest = detailRequest.catch((error) => {
        detailRequest = null;
        throw error;
      });
    }
    return detailRequest;
  };
  function section(label, build) {
    const panel = el("details"),
      content = el("div");
    panel.append(el("summary", t(label)), content);
    let ready = false,
      loading = false;
    const load = async () => {
      if (ready || loading) return;
      loading = true;
      const status = el("p", t("loading"));
      status.setAttribute("role", "status");
      content.replaceChildren(status);
      try {
        const data = await details();
        if (!card.isConnected) return;
        build(content, data);
        ready = true;
      } catch {
        const retry = el("button", t("retry_action"));
        retry.type = "button";
        retry.onclick = load;
        content.replaceChildren(el("p", t("failed")), retry);
      } finally {
        loading = false;
      }
    };
    panel.addEventListener("toggle", () => {
      if (panel.open) load();
    });
    card.append(panel);
  }
  section("context", (content, data) => {
    const lines = el("div", "", "context-lines");
    lines.append(contextRows(data.items, item, needle, group));
    const expand = el("button", t("context_more"));
    expand.type = "button";
    let radius = initialRadius;
    expand.hidden = !data.has_more;
    expand.onclick = async () => {
      expand.disabled = true;
      try {
        const next = Math.min(radius + 15, 100);
        const data = await api(
          "/api/context?" +
            new URLSearchParams({
              story: item.story,
              ordinal: item.ordinal,
              radius: next,
            }),
        );
        if (!card.isConnected) return;
        lines.replaceChildren(contextRows(data.items, item, needle, group));
        radius = next;
        expand.hidden = !data.has_more || radius >= 100;
        expand.textContent = t("context_more");
      } catch {
        expand.textContent = t("retry_action");
      } finally {
        expand.disabled = false;
      }
    };
    content.replaceChildren(lines, expand);
  });

  return card;
}

export function renderBatch(items, needle = "") {
  const fragment = document.createDocumentFragment(),
    offset = $("results").children.length;
  const groups = [];
  for (const item of items) {
    const group = groups[groups.length - 1];
    const first = group?.[0];
    const previous = group?.[group.length - 1];
    // Only combine overlapping windows on this page; retain every matched quote.
    if (
      first &&
      first.story === item.story &&
      first.branch === item.branch &&
      item.ordinal > previous.ordinal &&
      item.ordinal - first.ordinal <= 6
    )
      group.push(item);
    else groups.push([item]);
  }
  groups.forEach((group, index) =>
    fragment.append(renderCard(group, needle, offset + index)),
  );
  $("results").append(fragment);
}
