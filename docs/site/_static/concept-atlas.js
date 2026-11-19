const conceptDialog = document.querySelector("#concept-atlas");

if (conceptDialog) {
  const search = conceptDialog.querySelector("[data-concept-search]");
  const filters = [...conceptDialog.querySelectorAll("[data-concept-filter]")];
  const groups = [...conceptDialog.querySelectorAll("[data-concept-group]")];
  const terms = [...conceptDialog.querySelectorAll("[data-concept]")];
  const status = conceptDialog.querySelector(".concept-status");
  const lens = conceptDialog.querySelector("[data-concept-lens]");
  const map = conceptDialog.querySelector("[data-concept-map]");
  const lines = conceptDialog.querySelector(".concept-lines");
  const closeButton = conceptDialog.querySelector(".concept-close");
  const defaultLens = lens.innerHTML;
  const byId = new Map(terms.map((term) => [term.dataset.concept, term]));
  const conceptField = document.querySelector(".concept-field");
  const conceptWords = [...document.querySelectorAll("[data-concept-wall-item]")];
  const topicFilters = [...document.querySelectorAll("[data-topic-filter]")];
  const topicLinks = [...document.querySelectorAll("[data-topic]")];
  const language = document.documentElement.lang.startsWith("zh") ? "zh" : "en";
  const relationLabels = {
    zh: {
      depends_on: "依赖",
      related: "相关",
      contrasts_with: "对照",
      part_of: "属于",
    },
    en: {
      depends_on: "Depends on",
      related: "Related",
      contrasts_with: "Contrasts with",
      part_of: "Part of",
    },
  }[language];
  let activeFilter = "all";
  let activeTerm = null;

  topicFilters.forEach((button) => {
    button.addEventListener("click", () => {
      const topic = button.dataset.topicFilter;
      topicFilters.forEach((candidate) => {
        candidate.setAttribute(
          "aria-pressed",
          candidate === button ? "true" : "false",
        );
      });
      topicLinks.forEach((link) => {
        link.hidden = topic !== "all" && link.dataset.topic !== topic;
      });
    });
  });

  function parseRelations(term) {
    try {
      return JSON.parse(term.dataset.relations || "[]");
    } catch {
      return [];
    }
  }

  function openAtlas(event) {
    const requestedConcept =
      event?.currentTarget?.dataset.conceptTarget || null;
    if (event) {
      event.preventDefault();
    }
    if (!conceptDialog.open) {
      conceptDialog.showModal();
      document.body.classList.add("concept-dialog-open");
    }
    activeConceptWord?.classList.remove("is-active");
    activeConceptWord = null;
    conceptField?.classList.remove("is-concept-hover");
    requestAnimationFrame(() => {
      const requestedTerm = requestedConcept
        ? byId.get(requestedConcept)
        : null;
      if (requestedTerm && !requestedTerm.hidden) {
        requestedTerm.focus();
      } else {
        closeButton?.focus();
      }
    });
    drawLines(activeTerm);
  }

  document.querySelectorAll("[data-concept-open]").forEach((trigger) => {
    trigger.addEventListener("click", openAtlas);
  });

  let activeConceptWord = null;
  conceptWords.forEach((word) => {
    word.addEventListener("pointerenter", () => {
      if (activeConceptWord === word) {
        return;
      }
      activeConceptWord?.classList.remove("is-active");
      activeConceptWord = word;
      word.classList.add("is-active");
      conceptField?.classList.add("is-concept-hover");
    });
    word.addEventListener("pointerleave", () => {
      if (activeConceptWord !== word) {
        return;
      }
      word.classList.remove("is-active");
      activeConceptWord = null;
      conceptField?.classList.remove("is-concept-hover");
    });
  });

  conceptDialog.addEventListener("close", () => {
    document.body.classList.remove("concept-dialog-open");
    clearActive();
  });

  closeButton?.addEventListener("click", () => conceptDialog.close());

  function applyFilters() {
    const query = (search?.value || "").trim().toLocaleLowerCase();
    let visible = 0;
    groups.forEach((group) => {
      const groupVisible =
        activeFilter === "all" || group.dataset.conceptGroup === activeFilter;
      let groupCount = 0;
      group.querySelectorAll("[data-concept]").forEach((term) => {
        const matchesText = !query || term.dataset.search.includes(query);
        const show = groupVisible && matchesText;
        term.hidden = !show;
        if (show) {
          groupCount += 1;
          visible += 1;
        }
      });
      group.hidden = groupCount === 0;
    });
    if (status) {
      const label =
        language === "zh" ? `${visible} 个词条` : `${visible} ${visible === 1 ? "entry" : "entries"}`;
      status.textContent = visible ? label : language === "zh" ? "没有匹配词条" : "No matching entries";
    }
    clearActive();
  }

  search?.addEventListener("input", applyFilters);

  filters.forEach((button) => {
    button.addEventListener("click", () => {
      activeFilter = button.dataset.conceptFilter;
      filters.forEach((candidate) => {
        candidate.setAttribute(
          "aria-pressed",
          candidate === button ? "true" : "false",
        );
      });
      applyFilters();
    });
  });

  function clearLines() {
    if (lines) {
      lines.replaceChildren();
      lines.style.width = "";
      lines.style.height = "";
      lines.removeAttribute("viewBox");
    }
  }

  function clearActive() {
    activeTerm = null;
    terms.forEach((term) => {
      term.classList.remove("is-related", "is-contrast", "is-dimmed");
    });
    clearLines();
    if (lens) {
      lens.innerHTML = defaultLens;
    }
  }

  function drawLines(term) {
    clearLines();
    if (!lines || !map || !term || term.hidden) {
      return;
    }
    const mapRect = map.getBoundingClientRect();
    const sourceRect = term.getBoundingClientRect();
    const width = map.scrollWidth;
    const height = map.scrollHeight;
    lines.setAttribute("viewBox", `0 0 ${width} ${height}`);
    lines.style.width = `${width}px`;
    lines.style.height = `${height}px`;
    parseRelations(term).forEach((relation) => {
      const target = byId.get(relation.id);
      if (!target || target.hidden) {
        return;
      }
      const targetRect = target.getBoundingClientRect();
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute(
        "x1",
        sourceRect.left + sourceRect.width / 2 - mapRect.left + map.scrollLeft,
      );
      line.setAttribute(
        "y1",
        sourceRect.top + sourceRect.height / 2 - mapRect.top + map.scrollTop,
      );
      line.setAttribute(
        "x2",
        targetRect.left + targetRect.width / 2 - mapRect.left + map.scrollLeft,
      );
      line.setAttribute(
        "y2",
        targetRect.top + targetRect.height / 2 - mapRect.top + map.scrollTop,
      );
      line.dataset.kind = relation.type;
      lines.append(line);
    });
  }

  function activate(term) {
    if (!term || activeTerm === term || term.hidden) {
      return;
    }
    clearActive();
    activeTerm = term;
    const relations = parseRelations(term).filter((relation) => {
      const target = byId.get(relation.id);
      return target && !target.hidden;
    });
    terms.forEach((candidate) => {
      if (candidate !== term) {
        candidate.classList.add("is-dimmed");
      }
    });
    relations.forEach((relation) => {
      const target = byId.get(relation.id);
      target?.classList.remove("is-dimmed");
      target?.classList.add(
        relation.type === "contrasts_with" ? "is-contrast" : "is-related",
      );
    });
    if (lens) {
      const context = (term.dataset.context || "").trim();
      const related = relations
        .map((relation) => {
          const target = byId.get(relation.id);
          return `${relationLabels[relation.type]} · ${target.dataset.name}`;
        })
        .join(language === "zh" ? "；" : "; ");
      lens.innerHTML = `
        <p class="concept-lens-name">${escapeHtml(term.dataset.name)}</p>
        <p class="concept-lens-summary">${escapeHtml(term.dataset.summary)}</p>
        ${
          context
            ? `<p class="concept-lens-context"><strong>${
                language === "zh" ? "登记上下文" : "Registered contexts"
              }</strong> · ${escapeHtml(context)}</p>`
            : ""
        }
        <p class="concept-lens-relations">${escapeHtml(
          related ||
            (language === "zh"
              ? "这个词条暂未登记关系。"
              : "No relations are registered for this entry yet."),
        )}</p>
        <a class="concept-lens-link" href="${term.href}">${
          term.dataset.kind === "synthesis"
            ? (language === "zh" ? "阅读研究总论 →" : "Read the research synthesis →")
            : (language === "zh" ? "打开完整词条 →" : "Open full entry →")
        }</a>`;
    }
    drawLines(term);
  }

  function escapeHtml(value) {
    const node = document.createElement("span");
    node.textContent = value;
    return node.innerHTML;
  }

  terms.forEach((term) => {
    term.addEventListener("pointerenter", () => activate(term));
    term.addEventListener("focus", () => activate(term));
    term.addEventListener("pointerleave", (event) => {
      if (!event.relatedTarget?.closest?.("[data-concept]")) {
        clearActive();
      }
    });
    term.addEventListener("blur", () => clearActive());
    term.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) {
        return;
      }
      const visible = terms.filter((candidate) => !candidate.hidden);
      const index = visible.indexOf(term);
      const delta = event.key === "ArrowLeft" || event.key === "ArrowUp" ? -1 : 1;
      const next = visible[(index + delta + visible.length) % visible.length];
      event.preventDefault();
      next?.focus();
    });
  });

  window.addEventListener("resize", () => {
    if (activeTerm) {
      drawLines(activeTerm);
    }
  });
}
