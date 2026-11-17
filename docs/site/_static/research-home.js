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
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

let scheduled = 0;

function updateReadingProgress() {
  scheduled = 0;
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const pageRatio = scrollable > 0 ? clamp(window.scrollY / scrollable, 0, 1) : 0;
  if (pageProgress) {
    pageProgress.style.transform = `scaleX(${pageRatio})`;
  }
}

function scheduleReadingProgress() {
  if (!scheduled) {
    scheduled = window.requestAnimationFrame(updateReadingProgress);
  }
}

if (pageProgress) {
  window.addEventListener("scroll", scheduleReadingProgress, { passive: true });
  window.addEventListener("resize", scheduleReadingProgress);
  updateReadingProgress();
}
