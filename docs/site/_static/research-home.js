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
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

let scheduled = 0;

function updateReadingProgress() {
  scheduled = 0;
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const pageRatio = scrollable > 0 ? clamp(window.scrollY / scrollable, 0, 1) : 0;
  if (pageProgress) {
    pageProgress.style.transform = `scaleX(${pageRatio})`;
  }
  if (conceptField && !reduceMotion.matches) {
    const revealDistance = Math.max(
      220,
      Math.min((storyHero?.offsetHeight || window.innerHeight) * .48, 520),
    );
    const conceptReveal = clamp(window.scrollY / revealDistance, 0, 1);
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

if (pageProgress || conceptField) {
  window.addEventListener("scroll", scheduleReadingProgress, { passive: true });
  window.addEventListener("resize", scheduleReadingProgress);
  updateReadingProgress();
}

reduceMotion.addEventListener("change", () => {
  if (reduceMotion.matches && conceptField) {
    conceptField.style.removeProperty("--concept-reveal");
    conceptField.classList.add("is-ready");
  } else if (conceptField) {
    updateReadingProgress();
  }
});
