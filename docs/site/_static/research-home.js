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
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

let scheduled = 0;
let evidenceObserver;

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
