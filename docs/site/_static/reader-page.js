/* The reader remains fully usable without JavaScript. */
(() => {
  "use strict";

  const menu = document.querySelector(".chapter-menu");
  if (menu) {
    menu.open = !window.matchMedia("(max-width: 800px)").matches;
  }
})();
