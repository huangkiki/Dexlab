// Keep published homepage fragments working after the global Sphinx labels
// moved to their destination pages.
if (location.hash === "#blog") {
  location.replace(new URL("#experiments", location.href).href);
}

const legacyAnchorRoutes = {
  quickstart: 'quickstart.html',
  'live-lab': 'about.html#live-lab',
};
if (legacyAnchorRoutes[location.hash.slice(1)]) {
  location.replace(legacyAnchorRoutes[location.hash.slice(1)]);
}

const pageProgress = document.querySelector(".page-progress span");
const conceptField = document.querySelector(".concept-field");
const storyHero = document.querySelector(".story-hero");
const evidenceSequence = document.querySelector(".evidence-sequence");
const evidencePanels = [...document.querySelectorAll("[data-evidence-reveal]")];
const homeSearchForm = document.querySelector(".home-search");
const homeSearchInput = homeSearchForm?.querySelector('input[name="q"]');
const homeSearchResults = document.querySelector("#home-search-results");
const homeSearchClose = document.querySelector(".home-search-close");
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const homeSearchLanguage = document.documentElement.lang.startsWith("zh") ? "zh" : "en";
const homeSearchRecommendations = {
  zh: [
    ["斜面", "实验比较"],
    ["接触力", "概念"],
    ["切割", "实验"],
    ["Sim-to-Real", "研究总论"],
    ["NeuralActuator", "研究专题"],
    ["LIBERO", "评测"],
  ],
  en: [
    ["incline", "Experiment"],
    ["contact force", "Concept"],
    ["cutting", "Experiment"],
    ["Sim-to-Real", "Synthesis"],
    ["NeuralActuator", "Research topic"],
    ["LIBERO", "Evaluation"],
  ],
}[homeSearchLanguage];

let scheduled = 0;
let evidenceObserver;
let homeSearchIndexPromise;
let homeSearchTimer = 0;
let homeSearchRequest = 0;

function updateReadingProgress() {
  scheduled = 0;
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const pageRatio = scrollable > 0 ? clamp(window.scrollY / scrollable, 0, 1) : 0;
  if (pageProgress) {
    pageProgress.style.transform = `scaleX(${pageRatio})`;
  }
  if (conceptField && !reduceMotion.matches) {
    const fieldRect = conceptField.getBoundingClientRect();
    const viewportHeight = window.innerHeight || storyHero?.offsetHeight || 1;
    const revealStart = viewportHeight * .82;
    const revealEnd = viewportHeight * .42;
    const conceptReveal = clamp(
      (revealStart - fieldRect.top) / Math.max(1, revealStart - revealEnd),
      0,
      1,
    );
    conceptField.style.setProperty(
      "--concept-reveal",
      conceptReveal.toFixed(3),
    );
    conceptField.classList.toggle("is-ready", conceptReveal >= .2);
  }
}

function scheduleReadingProgress() {
  if (!scheduled) {
    scheduled = window.requestAnimationFrame(updateReadingProgress);
  }
}

function clearHomeSearchResults() {
  homeSearchRequest += 1;
  document.body.classList.remove("home-search-active");
  if (homeSearchResults) {
    homeSearchResults.hidden = true;
    homeSearchResults.replaceChildren();
  }
}

function showHomeSearchRecommendations() {
  if (!homeSearchResults) {
    return;
  }
  homeSearchRequest += 1;
  document.body.classList.remove("home-search-active");
  const label = document.createElement("p");
  label.className = "home-search-recommendations-label";
  label.textContent = homeSearchLanguage === "zh"
    ? "推荐搜索"
    : "Suggested searches";
  const list = document.createElement("div");
  list.className = "home-search-recommendations";
  homeSearchRecommendations.forEach(([query, detail]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "home-search-recommendation";
    const text = document.createElement("span");
    text.textContent = query;
    const hint = document.createElement("small");
    hint.textContent = detail;
    button.append(text, hint);
    button.addEventListener("click", () => {
      homeSearchInput.value = query;
      const requestId = homeSearchRequest + 1;
      homeSearchRequest = requestId;
      performHomeSearch(query, requestId);
    });
    list.append(button);
  });
  homeSearchResults.replaceChildren(label, list);
  homeSearchResults.hidden = false;
}

function loadHomeSearchIndex() {
  if (typeof Search !== "undefined" && Search.hasIndex()) {
    return Promise.resolve();
  }
  if (homeSearchIndexPromise) {
    return homeSearchIndexPromise;
  }
  const indexUrl = homeSearchForm?.dataset.searchIndex;
  if (!indexUrl) {
    return Promise.reject(new Error("Search index URL is missing"));
  }
  homeSearchIndexPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = indexUrl;
    script.addEventListener("load", () => resolve(), { once: true });
    script.addEventListener("error", reject, { once: true });
    document.head.append(script);
  }).then(() => {
    if (typeof Search === "undefined" || !Search.hasIndex()) {
      throw new Error("Search index did not initialize");
    }
  }).catch((error) => {
    homeSearchIndexPromise = undefined;
    throw error;
  });
  return homeSearchIndexPromise;
}

function highlightHomeSearchText(element, query) {
  const terms = [...new Set(
    query.trim().split(/\s+/).filter(Boolean),
  )].sort((left, right) => right.length - left.length);
  if (!element || !terms.length) {
    return;
  }
  const escaped = terms.map((term) =>
    term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  );
  const pattern = new RegExp(escaped.join("|"), "giu");
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    nodes.push(walker.currentNode);
  }
  nodes.forEach((node) => {
    const text = node.nodeValue;
    pattern.lastIndex = 0;
    if (!text || !pattern.test(text)) {
      return;
    }
    pattern.lastIndex = 0;
    const fragment = document.createDocumentFragment();
    let cursor = 0;
    let match;
    while ((match = pattern.exec(text))) {
      fragment.append(document.createTextNode(text.slice(cursor, match.index)));
      const highlighted = document.createElement("mark");
      highlighted.textContent = match[0];
      fragment.append(highlighted);
      cursor = match.index + match[0].length;
    }
    if (!fragment.childNodes.length) {
      return;
    }
    fragment.append(document.createTextNode(text.slice(cursor)));
    node.replaceWith(fragment);
  });
}

function renderHomeSearchResults(query, results, searchTerms) {
  if (!homeSearchResults) {
    return;
  }
  const status = document.createElement("p");
  status.className = "home-search-status";
  const resultLabel = homeSearchLanguage === "zh"
    ? `找到 ${results.length} 个页面，显示前 ${Math.min(results.length, 6)} 个`
    : `${results.length} pages found; showing the top ${Math.min(results.length, 6)}`;
  status.textContent = results.length
    ? resultLabel
    : homeSearchLanguage === "zh"
      ? "没有匹配页面"
      : "No matching pages";

  const list = document.createElement("ul");
  list.className = "home-search-list";
  results.slice(0, 6).forEach(([docName, title, anchor, description]) => {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `${docName}.html${anchor || ""}`;
    link.textContent = title;
    highlightHomeSearchText(link, query);
    item.append(link);
    if (description) {
      const detail = document.createElement("small");
      detail.textContent = description;
      highlightHomeSearchText(detail, query);
      item.append(detail);
    } else {
      fetch(`${docName}.html`)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to load search result");
          }
          return response.text();
        })
        .then((html) => {
          const summary = Search.makeSearchSummary(html, searchTerms, anchor);
          if (summary && item.isConnected) {
            highlightHomeSearchText(summary, query);
            item.append(summary);
          }
        })
        .catch(() => {});
    }
    list.append(item);
  });

  const more = document.createElement("a");
  more.className = "home-search-more";
  more.href = `search.html?q=${encodeURIComponent(query)}`;
  more.textContent = homeSearchLanguage === "zh"
    ? "查看完整搜索结果 →"
    : "Open all search results →";

  homeSearchResults.replaceChildren(status, list, more);
  homeSearchResults.hidden = false;
}

async function performHomeSearch(query, requestId) {
  if (!homeSearchResults) {
    return;
  }
  homeSearchResults.hidden = false;
  document.body.classList.add("home-search-active");
  const loading = document.createElement("p");
  loading.className = "home-search-status";
  loading.textContent = homeSearchLanguage === "zh" ? "正在搜索…" : "Searching…";
  homeSearchResults.replaceChildren(loading);
  try {
    await loadHomeSearchIndex();
    if (requestId !== homeSearchRequest || homeSearchInput?.value.trim() !== query) {
      return;
    }
    const [
      searchQuery,
      searchTerms,
      excludedTerms,
      highlightTerms,
      objectTerms,
    ] = Search._parseQuery(query);
    const results = Search._performSearch(
      searchQuery,
      searchTerms,
      excludedTerms,
      highlightTerms,
      objectTerms,
    );
    renderHomeSearchResults(query, results, searchTerms);
  } catch {
    if (requestId !== homeSearchRequest) {
      return;
    }
    const error = document.createElement("p");
    error.className = "home-search-status";
    error.textContent = homeSearchLanguage === "zh"
      ? "搜索索引暂时不可用，请按回车打开完整搜索页。"
      : "Search is temporarily unavailable. Press Enter to open the full search page.";
    homeSearchResults.replaceChildren(error);
  }
}

if (homeSearchForm && homeSearchInput) {
  homeSearchInput.addEventListener("focus", () => {
    loadHomeSearchIndex().catch(() => {});
    if (!homeSearchInput.value.trim()) {
      showHomeSearchRecommendations();
    }
  });
  homeSearchInput.addEventListener("input", () => {
    window.clearTimeout(homeSearchTimer);
    const query = homeSearchInput.value.trim();
    if (!query) {
      showHomeSearchRecommendations();
      return;
    }
    const requestId = homeSearchRequest + 1;
    homeSearchRequest = requestId;
    homeSearchTimer = window.setTimeout(() => {
      performHomeSearch(query, requestId);
    }, 160);
  });
  homeSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      homeSearchInput.value = "";
      clearHomeSearchResults();
      homeSearchInput.blur();
    }
  });
  homeSearchClose?.addEventListener("click", () => {
    homeSearchInput.value = "";
    clearHomeSearchResults();
    homeSearchInput.focus();
  });
  document.addEventListener("pointerdown", (event) => {
    if (
      !homeSearchInput.value.trim()
      && !homeSearchForm.contains(event.target)
      && !homeSearchResults?.contains(event.target)
    ) {
      clearHomeSearchResults();
    }
  });
}

if (pageProgress || conceptField) {
  window.addEventListener("scroll", scheduleReadingProgress, { passive: true });
  window.addEventListener("resize", scheduleReadingProgress);
  updateReadingProgress();
}

function setupEvidenceReveal() {
  evidenceObserver?.disconnect();
  if (!evidenceSequence || !evidencePanels.length) {
    return;
  }
  evidencePanels.forEach((panel) => panel.classList.remove("is-visible"));
  if (reduceMotion.matches || !("IntersectionObserver" in window)) {
    evidenceSequence.classList.remove("is-scroll-enabled");
    evidencePanels.forEach((panel) => panel.classList.add("is-visible"));
    return;
  }
  evidenceSequence.classList.add("is-scroll-enabled");
  evidenceObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) {
        return;
      }
      entry.target.classList.add("is-visible");
      evidenceObserver.unobserve(entry.target);
    });
  }, {
    threshold: .12,
    rootMargin: "0px 0px -8% 0px",
  });
  evidencePanels.forEach((panel) => {
    if (panel.getBoundingClientRect().top < window.innerHeight * .88) {
      panel.classList.add("is-visible");
    } else {
      evidenceObserver.observe(panel);
    }
  });
}

setupEvidenceReveal();

reduceMotion.addEventListener("change", () => {
  setupEvidenceReveal();
  if (reduceMotion.matches && conceptField) {
    conceptField.style.removeProperty("--concept-reveal");
    conceptField.classList.add("is-ready");
  } else if (conceptField) {
    updateReadingProgress();
  }
});
