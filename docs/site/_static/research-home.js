// Keep published homepage fragments working after the global Sphinx labels
// moved to their destination pages.
if (location.hash === "#blog") {
  // Keep old links working without creating an English-CN history loop on Back.
  const blogPage = document.documentElement.lang === "en"
    ? "../../zh-cn/latest/blog.html"
    : "blog.html";
  location.replace(new URL(blogPage, location.href).href);
}

const legacyAnchorRoutes = {
  quickstart: 'quickstart.html',
  'live-lab': 'about.html#live-lab',
};
if (legacyAnchorRoutes[location.hash.slice(1)]) {
  location.replace(legacyAnchorRoutes[location.hash.slice(1)]);
}
