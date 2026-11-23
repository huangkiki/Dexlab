/* Use the same Sphinx index and ranking in the masthead and on search.html. */
(() => {
  "use strict";

  if (!document.currentScript.hasAttribute("data-search-page")) {
    // Sphinx's initializer clears the query field and expects a full results page.
    document.removeEventListener("DOMContentLoaded", Search.init);
    document.addEventListener("DOMContentLoaded", SphinxHighlight.highlightSearchWords);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-site-search]");
    const input = form.querySelector('input[name="q"]');
    const panel = form.querySelector(".site-search-results");
    const status = panel.querySelector('[role="status"]');
    const results = panel.querySelector("ul");
    const searchPage = new URL(form.action);
    const zh = document.documentElement.lang.startsWith("zh");
    const recommendations = zh
      ? ["斜面", "接触力", "切割", "Sim-to-Real", "NeuralActuator", "LIBERO"]
      : ["incline", "contact force", "cutting", "Sim-to-Real", "NeuralActuator", "LIBERO"];

    let indexPromise;
    let timer;
    let preview;

    function loadIndex() {
      if (Search.hasIndex()) return Promise.resolve();

      indexPromise ??= new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = new URL("searchindex.js", searchPage);
        script.onload = () => Search.hasIndex() ? resolve() : reject();
        script.onerror = () => {
          script.remove();
          reject();
        };
        document.head.append(script);
      }).catch((error) => {
        indexPromise = undefined;
        throw error;
      });
      return indexPromise;
    }

    function showStatus(message) {
      panel.hidden = false;
      status.textContent = message;
      results.replaceChildren();
    }

    function addResult(element) {
      const item = document.createElement("li");
      item.append(element);
      results.append(item);
    }

    function showRecommendations() {
      showStatus(zh ? "推荐搜索" : "Suggested searches");
      for (const term of recommendations) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = term;
        button.onclick = () => {
          input.focus();
          input.value = term;
          scheduleSearch();
        };
        addResult(button);
      }
    }

    function highlight(element, text, pattern) {
      for (const [index, part] of text.split(pattern).entries()) {
        if (index % 2 === 0) {
          element.append(part);
        } else {
          const mark = document.createElement("mark");
          mark.textContent = part;
          element.append(mark);
        }
      }
    }

    function addExcerpt(link, text, pattern) {
      const excerpt = document.createElement("span");
      excerpt.className = "site-search-excerpt";
      highlight(excerpt, text, pattern);
      link.append(excerpt);
    }

    async function loadExcerpt(link, url, anchor, pattern, signal) {
      try {
        const response = await fetch(url, { signal });
        if (!response.ok) return;
        const html = await response.text();
        if (signal.aborted) return;

        const text = Search.htmlToText(html, anchor).replace(/\s+/g, " ").trim();
        const match = text.search(pattern);
        if (match < 0) return;

        const start = Math.max(0, match - 24);
        const end = Math.min(text.length, match + 96);
        const excerpt = `${start ? "…" : ""}${text.slice(start, end).trim()}${end < text.length ? "…" : ""}`;
        addExcerpt(link, excerpt, pattern);
      } catch {
        // The title remains a usable link when an excerpt cannot be loaded.
      }
    }

    async function showMatches(query, signal) {
      try {
        await loadIndex();
        if (signal.aborted) return;

        const matches = Search._performSearch(...Search._parseQuery(query));
        const pages = new Set();
        const words = query.split(/\s+/).sort((left, right) => right.length - left.length);
        const pattern = new RegExp(`(${words.map(_escapeRegExp).join("|")})`, "giu");

        if (matches.length === 0) {
          showStatus(zh ? "没有匹配的文章" : "No matching pages");
          return;
        }

        showStatus(zh ? "匹配文章" : "Matching pages");
        // Sphinx returns the best matches last. Show each article once.
        for (const [docName, title, anchor, description] of matches.reverse()) {
          if (pages.has(docName)) continue;
          pages.add(docName);

          const url = new URL(`${docName}.html`, searchPage);
          const link = document.createElement("a");
          link.href = `${url}${anchor}`;
          highlight(link, title, pattern);
          addResult(link);
          if (description) {
            addExcerpt(link, description, pattern);
          } else {
            loadExcerpt(link, url, anchor, pattern, signal);
          }
          if (pages.size === 6) break;
        }

        const more = document.createElement("a");
        const fullResults = new URL(searchPage);
        fullResults.searchParams.set("q", query);
        more.className = "site-search-more";
        more.href = fullResults;
        more.textContent = zh ? "查看完整搜索结果 →" : "See all search results →";
        addResult(more);
      } catch {
        if (!signal.aborted) {
          showStatus(zh ? "搜索暂时不可用，请按回车重试。" : "Search is unavailable. Press Enter to retry.");
        }
      }
    }

    function cancelPreview() {
      window.clearTimeout(timer);
      preview?.abort();
    }

    function closePanel() {
      cancelPreview();
      panel.hidden = true;
    }

    function scheduleSearch() {
      cancelPreview();
      const query = input.value.trim();
      if (!query) {
        showRecommendations();
        return;
      }

      showStatus(zh ? "正在搜索…" : "Searching…");
      preview = new AbortController();
      const { signal } = preview;
      timer = window.setTimeout(() => showMatches(query, signal), 150);
    }

    input.addEventListener("focus", scheduleSearch);
    input.addEventListener("input", (event) => {
      if (!event.isComposing) scheduleSearch();
    });
    input.addEventListener("compositionstart", closePanel);
    input.addEventListener("compositionend", scheduleSearch);
    form.addEventListener("focusout", (event) => {
      if (!form.contains(event.relatedTarget)) closePanel();
    });
    document.addEventListener("pointerdown", (event) => {
      if (!form.contains(event.target)) closePanel();
    });
    form.addEventListener("keydown", (event) => {
      if (event.isComposing || panel.hidden) return;

      if (event.key === "Escape") {
        event.preventDefault();
        input.focus();
        closePanel();
      }
      if (event.key === "ArrowDown" && event.target === input) {
        const firstResult = results.querySelector("a, button");
        if (firstResult) {
          event.preventDefault();
          firstResult.focus();
        }
      }
    });
    form.addEventListener("click", (event) => {
      if (event.target === input && panel.hidden) scheduleSearch();
    });
  });
})();
