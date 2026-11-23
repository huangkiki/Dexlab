(() => {
  const index = document.querySelector(".paper-index");
  const panel = index.querySelector("details");
  const summary = panel.querySelector("summary");
  const outline = panel.querySelector("nav");
  const position = summary.querySelector(".paper-index-position");
  const wide = window.matchMedia("(min-width: 1000px)");
  const entries = Array.from(outline.querySelectorAll("a"), (link) => ({
    link,
    target: document.getElementById(link.hash.slice(1)),
  }));
  let current;
  let frame = 0;

  function setExpanded(entry, expanded) {
    for (let item = entry.link.closest("li"); item; item = item.parentElement.closest("li")) {
      item.classList.toggle("is-expanded", expanded);
    }
  }

  function revealCurrent() {
    if (!panel.open || !current) return;

    const row = current.link.getBoundingClientRect();
    const viewport = outline.getBoundingClientRect();
    if (row.top < viewport.top || row.bottom > viewport.bottom) {
      outline.scrollTop += (row.top + row.bottom - viewport.top - viewport.bottom) / 2;
    }
  }

  function update() {
    frame = 0;
    const readingLine = wide.matches ? 110 : summary.getBoundingClientRect().bottom + 48;
    let next = entries[0];
    for (const entry of entries) {
      if (entry.target.getBoundingClientRect().top > readingLine) break;
      next = entry;
    }
    if (next === current) return;

    if (current) {
      current.link.removeAttribute("aria-current");
      setExpanded(current, false);
    }
    current = next;
    setExpanded(current, true);
    current.link.setAttribute("aria-current", "location");
    position.textContent = current.link.querySelector(".paper-zh").textContent;
    revealCurrent();
  }

  function scheduleUpdate() {
    if (!frame) frame = requestAnimationFrame(update);
  }

  function fitViewport() {
    panel.open = wide.matches;
    scheduleUpdate();
  }

  outline.addEventListener("click", (event) => {
    const link = event.target.closest("a");
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }
    const target = document.getElementById(link.hash.slice(1));
    target.setAttribute("tabindex", "-1");
    if (!wide.matches) panel.open = false;
    target.focus({ preventScroll: true });
  });

  index.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && panel.open) {
      panel.open = false;
      summary.focus();
    }
  });
  panel.addEventListener("toggle", revealCurrent);
  wide.addEventListener("change", fitViewport);
  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", scheduleUpdate);
  window.addEventListener("hashchange", scheduleUpdate);
  window.addEventListener("load", scheduleUpdate);

  index.dataset.enhanced = "";
  fitViewport();
})();
