(() => {
  function redirect(page) {
    const current = new URL(window.location.href);
    const destination = new URL(page, current);
    destination.search = current.search;
    destination.hash = current.hash;
    window.location.replace(destination.href);
  }

  if (window.location.pathname.endsWith("/blog.html")) {
    redirect("index.html");
    return;
  }

  // Sections published at the previous homepage address.
  const overviewAnchors = new Set([
    "home-heading", "architecture-heading", "concept-field-slot", "concept-field",
    "concept-topics-title", "experiments", "research-findings", "research-content",
    "evidence-feature", "blog-preview", "evidence-heading", "panel-cut",
    "evidence-cut-title", "panel-wuji", "evidence-wuji-title", "panel-apple",
    "evidence-apple-title", "panel-cloth", "evidence-cloth-title", "panel-incline",
    "evidence-incline-title", "research-diagnosis", "answer-heading", "experiment-findings",
    "solver-map", "root-causes", "research-selection", "blog-guide", "blog-policy",
    "blog-learn", "next-heading", "physical-validity", "validity-heading",
  ]);

  function redirectOverviewBookmark() {
    if (overviewAnchors.has(window.location.hash.slice(1))) {
      redirect("research-overview.html");
    }
  }

  window.addEventListener("hashchange", redirectOverviewBookmark);
  redirectOverviewBookmark();
})();
