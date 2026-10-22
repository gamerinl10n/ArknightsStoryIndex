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

function contextRows(rows, item, needle) {
  const fragment = document.createDocumentFragment();
  for (const row of rows) {
    const line = el(
      "div",
      "",
      "context-line" + (row.ordinal === item.ordinal ? " current-line" : ""),
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

function renderCard(item, needle, index) {
  const card = el("article", "", "result-card");
  card.lang = item.lang.replace("_", "-");
  card.style.setProperty("--enter-delay", Math.min(index, 5) * 35 + "ms");
  const heading = el("div", "", "card-heading");
  heading.append(portrait(item), el("h2", item.speaker), infoButton(item));
  card.append(heading, quote(item.text, needle));

  // Network, line DOM and event handlers are created only when a section is opened.
  let detailRequest;
  const details = () => {
    if (!detailRequest) {
      detailRequest = item.context
        ? Promise.resolve({
            items: item.context,
            parallel: item.parallel || [],
            has_more: true,
          })
        : api(
            "/api/context?" +
              new URLSearchParams({
                story: item.story,
                ordinal: item.ordinal,
                radius: 3,
                parallel: "1",
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
    lines.append(contextRows(data.items, item, needle));
    const expand = el("button", t("context_more"));
    expand.type = "button";
    let radius = 3;
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
        lines.replaceChildren(contextRows(data.items, item, needle));
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
  section("parallel", (content, data) => {
    const rows = data.parallel.map((row) => {
      const line = el("p", `[${row.lang}] ${row.speaker}: ${row.text}`);
      line.lang = row.lang.replace("_", "-");
      return line;
    });
    content.replaceChildren(
      ...(rows.length ? rows : [el("p", t("no_parallel"))]),
    );
  });

  return card;
}

export function renderBatch(items, needle = "") {
  const fragment = document.createDocumentFragment(),
    offset = $("results").children.length;
  items.forEach((item, index) =>
    fragment.append(renderCard(item, needle, offset + index)),
  );
  $("results").append(fragment);
}
