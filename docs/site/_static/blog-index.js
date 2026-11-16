/* Progressive reveal keeps the Blog readable without JavaScript. */
(() => {
  "use strict";

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reducedMotion || !("IntersectionObserver" in window)) {
    return;
  }

  function revealGroup(root, selector, threshold) {
    const items = selector ? [...root.querySelectorAll(selector)] : [root];
    if (items.length === 0) {
      return;
    }

    root.classList.add("is-reveal-ready");
    items.forEach((item, index) => item.style.setProperty("--reveal-order", index));

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) {
            continue;
          }
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        }
      },
      {
        threshold,
        rootMargin: "0px 0px -8% 0px",
      },
    );

    items.forEach((item) => observer.observe(item));
  }

  const verdicts = document.querySelector(".blog-verdict-grid");
  const evidence = document.querySelector(".blog-evidence-grid");
  const evidenceMatrix = document.querySelector(".blog-evidence-matrix");
  if (verdicts) {
    revealGroup(verdicts, ".blog-verdict", 0.3);
  }
  if (evidence) {
    revealGroup(evidence, ".blog-evidence-card", 0.1);
  }
  if (evidenceMatrix) {
    revealGroup(evidenceMatrix, null, 0.2);
  }
})();
