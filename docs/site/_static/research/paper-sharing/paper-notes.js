(() => {
  const reader = document.querySelector(".paper-reader");
  const article = reader.querySelector("article");
  const paperId = reader.dataset.paperId;
  const paperTitle = article.querySelector("h1 .paper-zh").textContent.trim();
  const papersRoot = new URL(".", document.currentScript.src);
  const tools = reader.querySelector(".paper-notes-tools");
  const addButton = tools.querySelector("[data-paper-highlight]");
  const notesButton = tools.querySelector("[data-paper-notes-open]");
  const feedback = tools.querySelector(".paper-notes-feedback");
  const dialog = document.querySelector(".paper-notes");
  if (typeof dialog.showModal !== "function") return;

  const message = dialog.querySelector(".paper-notes-message");
  const list = dialog.querySelector(".paper-notes-list");
  const storagePrefix = "dexlab:paper-note:v1:";
  const fragmentPrefix = "#paper-note-";
  const highlightName = "dexlab-paper-note";
  const canPaint = Boolean(window.CSS?.highlights && window.Highlight);
  let notes = [];
  let selectionAtPress;
  let selectionAtFocus;

  function report(text, quiet = false) {
    feedback.textContent = text;
    feedback.toggleAttribute("data-quiet", quiet);
  }

  function readNote(storage, key) {
    try {
      const note = JSON.parse(storage.getItem(key));
      if (note && typeof note.id === "string" && /^[a-f0-9-]{36}$/.test(note.id) &&
          key === storagePrefix + note.id && typeof note.paper === "string" &&
          /^(?:[a-z0-9_-]+\/)*[a-z0-9_.-]+\.html$/i.test(note.paper) &&
          typeof note.title === "string" && typeof note.section === "string" &&
          Number.isSafeInteger(note.start) && note.start >= 0 &&
          typeof note.quote === "string" && note.quote.trim() &&
          Number.isFinite(note.created)) {
        return note;
      }
    } catch {
      // A malformed entry cannot prevent the rest of the notebook from loading.
    }
    return null;
  }

  function selectionInPaper() {
    const selection = window.getSelection();
    if (!selection?.rangeCount || selection.isCollapsed) return null;
    const range = selection.getRangeAt(0);
    return article.contains(range.startContainer) && article.contains(range.endContainer)
      ? range.cloneRange()
      : null;
  }

  function describeRange(range) {
    const ancestor = range.commonAncestorContainer;
    const element = ancestor.nodeType === Node.ELEMENT_NODE ? ancestor : ancestor.parentElement;
    const scope = element.closest("section[id], .ltx_abstract[id]") || article;
    const selected = range.toString();
    const quote = selected.trim();
    const leadingSpace = selected.length - selected.trimStart().length;
    const prefix = document.createRange();
    prefix.selectNodeContents(scope);
    prefix.setEnd(range.startContainer, range.startOffset);
    return { section: scope === article ? "" : scope.id, start: prefix.toString().length + leadingSpace, quote };
  }

  function scopeFor(note) {
    const section = note.section && document.getElementById(note.section);
    return section && article.contains(section) ? section : article;
  }

  function rangeFor(note) {
    const scope = scopeFor(note);
    const text = scope.textContent;
    const { quote } = note;
    let start = note.start;
    if (text.slice(start, start + quote.length) !== quote) {
      start = text.indexOf(quote);
      if (start < 0 || start !== text.lastIndexOf(quote)) return null;
    }

    const end = start + quote.length;
    const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    let offset = 0;
    let started = false;
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const next = offset + node.length;
      if (!started && start < next) {
        range.setStart(node, start - offset);
        started = true;
      }
      if (started && end <= next) {
        range.setEnd(node, end - offset);
        return range;
      }
      offset = next;
    }
    return null;
  }

  function revealNote(note) {
    const range = rangeFor(note);
    const target = range?.startContainer.parentElement.closest("p, li, figcaption, h1, h2, h3, h4") ||
      scopeFor(note);
    if (!target.hasAttribute("tabindex")) target.tabIndex = -1;
    target.focus({ preventScroll: true });
    const offset = matchMedia("(min-width: 1000px)").matches ? 24 : reader.querySelector(".paper-index").offsetHeight + 16;
    const top = (range?.getClientRects()[0] || target.getBoundingClientRect()).top;
    window.scrollBy(0, top - offset);
    report(range ? "" : "原文有改动，请在该小节查找摘录。");
  }

  function element(tag, text) {
    const node = document.createElement(tag);
    node.textContent = text;
    return node;
  }

  function renderList() {
    list.replaceChildren();
    if (!notes.length) {
      list.append(element("p", "暂无高亮摘录。"));
      return;
    }

    const groups = new Map();
    for (const note of notes) {
      if (!groups.has(note.paper)) {
        const entries = document.createElement("ul");
        list.append(element("h3", note.title), entries);
        groups.set(note.paper, entries);
      }
      const item = document.createElement("li");
      const quote = element("blockquote", note.quote.replace(/\s+/g, " "));
      const actions = document.createElement("div");
      actions.className = "paper-note-actions";
      const jump = element("a", "回到原文");
      jump.href = new URL(note.paper + fragmentPrefix + encodeURIComponent(note.id), papersRoot).href;
      jump.addEventListener("click", (event) => {
        if (note.paper !== paperId || event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) return;
        event.preventDefault();
        dialog.close();
        requestAnimationFrame(() => revealNote(note));
      });
      const remove = element("button", "删除");
      remove.type = "button";
      remove.addEventListener("click", () => {
        try {
          localStorage.removeItem(storagePrefix + note.id);
        } catch {
          message.textContent = "删除失败，请检查浏览器的本地存储设置。";
          return;
        }
        message.textContent = "";
        refresh();
        dialog.querySelector("button").focus();
      });
      actions.append(jump, remove);
      item.append(quote, actions);
      groups.get(note.paper).append(item);
    }
  }

  function refresh() {
    try {
      const storage = window.localStorage;
      notes = Object.keys(storage).filter((key) => key.startsWith(storagePrefix))
        .map((key) => readNote(storage, key)).filter(Boolean)
        .sort((a, b) => b.created - a.created);
    } catch {
      report("浏览器未开放本地存储，无法保存笔记。");
      message.textContent = feedback.textContent;
      return;
    }

    notesButton.textContent = notes.length ? `笔记 ${notes.length}` : "笔记";
    if (canPaint) {
      const highlight = new Highlight();
      for (const note of notes) {
        if (note.paper !== paperId) continue;
        const range = rangeFor(note);
        if (range) highlight.add(range);
      }
      CSS.highlights.set(highlightName, highlight);
    }
    if (dialog.open) renderList();
  }

  function jumpFromFragment() {
    const note = notes.find((entry) =>
      entry.paper === paperId && location.hash === fragmentPrefix + encodeURIComponent(entry.id));
    if (note) requestAnimationFrame(() => revealNote(note));
  }

  document.addEventListener("selectionchange", () => {
    const selection = selectionInPaper();
    if (selection || document.activeElement !== addButton) selectionAtFocus = selection;
    addButton.toggleAttribute("data-ready", Boolean(selectionAtFocus));
    if (selection) report("");
  });
  addButton.addEventListener("pointerdown", () => { selectionAtPress = selectionInPaper(); });
  addButton.addEventListener("pointercancel", () => { selectionAtPress = null; });
  addButton.addEventListener("mousedown", (event) => event.preventDefault());
  addButton.addEventListener("click", () => {
    const range = selectionInPaper() || selectionAtPress || selectionAtFocus;
    selectionAtPress = null;
    if (!range || !range.toString().trim()) {
      report("先选中需要高亮的文字。");
      return;
    }
    const anchor = describeRange(range);
    if (notes.some((note) => note.paper === paperId && note.section === anchor.section &&
        note.start === anchor.start && note.quote === anchor.quote)) {
      report("这段文字已在笔记中。");
      return;
    }
    try {
      const note = { ...anchor, id: crypto.randomUUID(), paper: paperId, title: paperTitle, created: Date.now() };
      localStorage.setItem(storagePrefix + note.id, JSON.stringify(note));
    } catch {
      report("无法保存摘录，请检查浏览器的本地存储空间或设置。");
      return;
    }
    selectionAtFocus = null;
    addButton.removeAttribute("data-ready");
    window.getSelection().removeAllRanges();
    refresh();
    report(canPaint ? "已存入笔记。" : "已保存摘录。当前浏览器不支持正文高亮。", canPaint);
  });
  notesButton.addEventListener("click", () => {
    report("");
    dialog.showModal();
    renderList();
  });
  window.addEventListener("storage", (event) => {
    if (event.key === null || event.key.startsWith(storagePrefix)) refresh();
  });
  window.addEventListener("hashchange", jumpFromFragment);
  tools.hidden = false;
  refresh();
  jumpFromFragment();
})();
