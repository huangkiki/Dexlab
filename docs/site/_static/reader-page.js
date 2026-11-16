/* The reader remains fully usable without JavaScript. */
(() => {
  "use strict";

  const menu = document.querySelector(".chapter-menu");
  if (menu) {
    menu.open = !window.matchMedia("(max-width: 800px)").matches;
  }

  const current = [...document.querySelectorAll(".reader-navigation a")].find(
    (link) =>
      link.href === window.location.href ||
      link.href === window.location.href.split("#")[0],
  );
  if (current) current.setAttribute("aria-current", "page");
})();
