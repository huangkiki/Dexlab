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
const revealPanels = [...document.querySelectorAll(`
  .home-opening [data-home-reveal],
  .story-home :is(
    .concept-topics, .directory-entry, .home-section-head, [data-evidence-reveal],
    .home-answer-grid, .home-next-grid, .validity-boundary, .validity-chain,
    .validity-records
  ),
  .global-site-footer
`)];
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

let scheduled = 0;
let previousScrollY = window.scrollY;

function updateReadingProgress() {
  scheduled = 0;
  const height = window.innerHeight;
  const scrollY = window.scrollY;
  const scrollingUp = scrollY < previousScrollY;
  previousScrollY = scrollY;
  const scrollable = document.documentElement.scrollHeight - height;
  const pageRatio = scrollable > 0 ? clamp(scrollY / scrollable, 0, 1) : 0;
  if (pageProgress) {
    pageProgress.style.transform = `scaleX(${pageRatio})`;
  }
  if (conceptField && !reduceMotion.matches) {
    const fieldRect = conceptField.getBoundingClientRect();
    const viewportHeight = height || storyHero?.offsetHeight || 1;
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
  if (!reduceMotion.matches) {
    const revealDistance = Math.max(1, Math.min(height * .30, 280));
    const atBottom = scrollable > 0 && scrollY >= scrollable - 1;
    const positions = revealPanels.map(panel => [panel, panel.getBoundingClientRect().top]);
    for (const [panel, top] of positions) {
      if (scrollingUp && top < height) {
        continue;
      }
      const progress = atBottom ? 1 : clamp((height - top) / revealDistance, 0, 1);
      const opacity = progress * progress * (3 - 2 * progress);
      panel.style.setProperty("--home-reveal-opacity", opacity.toFixed(3));
    }
  }
}

function scheduleReadingProgress() {
  if (!scheduled) {
    scheduled = window.requestAnimationFrame(updateReadingProgress);
  }
}

function setupScrollReveal() {
  revealPanels.forEach(panel => panel.classList.toggle("home-scroll-reveal", !reduceMotion.matches));
}

setupScrollReveal();
if (pageProgress || conceptField || revealPanels.length) {
  window.addEventListener("scroll", scheduleReadingProgress, { passive: true });
  window.addEventListener("resize", scheduleReadingProgress);
  window.addEventListener("pageshow", scheduleReadingProgress);
  updateReadingProgress();
}

reduceMotion.addEventListener("change", () => {
  setupScrollReveal();
  if (reduceMotion.matches && conceptField) {
    conceptField.style.removeProperty("--concept-reveal");
    conceptField.classList.add("is-ready");
  }
  scheduleReadingProgress();
});
