/* Use the same Sphinx index and ranking in the masthead and on search.html. */
(() => {
  "use strict";

  const searchResultsPage = document.currentScript.hasAttribute("data-search-page");

  // Sphinx looks for partial title matches even when the keyword is indexed in full text.
  function queryMatches(query) {
    const parsed = Search._parseQuery(query);
    const [, terms, , words] = parsed;
    const { terms: body, titleterms: titles, docnames } = Search._index;
    const exact = new Map();
    for (const term of terms) {
      const files = [body, titles].flatMap((table) => Object.hasOwn(table, term) ? table[term] : []);
      if (files.length) exact.set(term, new Set(files.map((file) => docnames[file])));
    }

    const required = [...exact.values()];
    const results = Search._performSearch(...parsed).reverse().filter(([docName, , , , , , kind]) =>
      kind !== SearchResultKind.text || required.every((docs) => docs.has(docName)),
    );
    const partial = [...terms].filter((term) => term.length > 2 && !exact.has(term));
    const latinWord = /^[\p{Script=Latin}\p{Number}]+$/u;
    const literal = [...words].filter((word) => !latinWord.test(word));
    literal.sort((left, right) => right.length - left.length);
    const tokens = new RegExp([...literal.map(_escapeRegExp), "[\\p{Script=Latin}\\p{Number}]+"].join("|"), "giu");
    const stemmer = new Stemmer();

    function findMatches(text) {
      return [...text.matchAll(tokens)].filter(([token]) => {
        const word = token.toLowerCase();
        if (words.has(word)) return true;
        if (!latinWord.test(word)) return false;
        const stem = stemmer.stemWord(word);
        return terms.has(stem) || partial.some((term) => stem.includes(term));
      });
    }

    return { results, findMatches };
  }

  function highlight(element, text, matches, start = 0, end = text.length) {
    let offset = start;
    for (const { 0: word, index } of matches) {
      if (index < start) continue;
      if (index + word.length > end) break;
      element.append(text.slice(offset, index));
      const mark = document.createElement("mark");
      mark.textContent = word;
      element.append(mark);
      offset = index + word.length;
    }
    element.append(text.slice(offset, end));
  }

  async function loadExcerpt(container, url, anchor, findMatches, signal) {
    try {
      const response = await fetch(url, { signal });
      if (!response.ok) return;
      const html = await response.text();
      if (signal?.aborted) return;

      const text = Search.htmlToText(html, anchor).replace(/\s+/g, " ").trim();
      const matches = findMatches(text);
      if (!matches.length) return;

      const [first] = matches;
      const start = Math.max(0, first.index - (signal ? 24 : 56));
      const end = Math.min(text.length, first.index + first[0].length + (signal ? 90 : 150));
      const excerpt = document.createElement(signal ? "span" : "p");
      excerpt.className = signal ? "site-search-excerpt" : "context";
      if (start) excerpt.append("…");
      highlight(excerpt, text, matches, start, end);
      if (end < text.length) excerpt.append("…");
      container.append(excerpt);
    } catch {
      // A failed excerpt request leaves the result title and link available.
    }
  }

  function renderResult([docName, title, anchor, description, score, , kind], searchPage, findMatches, signal) {
    const item = document.createElement("li");
    const link = item.appendChild(document.createElement("a"));
    const url = new URL(`${docName}.html`, searchPage);
    link.href = `${url}${anchor}`;
    link.dataset.score = score;
    item.classList.add(`kind-${kind}`);
    highlight(link, title, findMatches(title));

    const container = signal ? link : item;
    if (description) {
      const excerpt = container.appendChild(document.createElement("span"));
      if (signal) excerpt.className = "site-search-excerpt";
      const text = signal ? description : ` (${description})`;
      highlight(excerpt, text, findMatches(text));
    } else if (signal || DOCUMENTATION_OPTIONS.SHOW_SEARCH_SUMMARY) {
      loadExcerpt(container, url, anchor, findMatches, signal);
    }
    return item;
  }

  if (searchResultsPage) {
    Search.query = (query) => {
      const { results, findMatches } = queryMatches(query);
      for (const result of results) {
        Search.output.append(renderResult(result, window.location.href, findMatches));
      }
      _finishSearch(results.length);
    };
  } else {
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

    async function showMatches(query, signal) {
      try {
        await loadIndex();
        if (signal.aborted) return;

        const { results: matches, findMatches } = queryMatches(query);
        const pages = new Set();

        if (matches.length === 0) {
          showStatus(zh ? "没有匹配的文章" : "No matching pages");
          return;
        }

        showStatus(zh ? "匹配文章" : "Matching pages");
        for (const match of matches) {
          const [docName] = match;
          if (pages.has(docName)) continue;
          pages.add(docName);
          results.append(renderResult(match, searchPage, findMatches, signal));
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
