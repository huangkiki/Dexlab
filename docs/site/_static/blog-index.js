/* Progressive reveal keeps the Blog readable without JavaScript. */
(() => {
  "use strict";

  const grid = document.querySelector(".blog-verdict-grid");
  const cards = grid ? [...grid.querySelectorAll(".blog-verdict")] : [];
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!grid || cards.length === 0 || reducedMotion || !("IntersectionObserver" in window)) {
    return;
  }

  grid.classList.add("is-reveal-ready");
  cards.forEach((card, index) => card.style.setProperty("--reveal-order", index));

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
      threshold: 0.3,
      rootMargin: "0px 0px -8% 0px",
    },
  );

  cards.forEach((card) => observer.observe(card));
})();
