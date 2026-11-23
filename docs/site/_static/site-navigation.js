(() => {
  const navigation = document.querySelector(".site-nav");
  const sections = [...navigation.querySelectorAll("details")];

  for (const section of sections) {
    section.addEventListener("toggle", () => {
      if (!section.open) return;
      for (const other of sections) {
        if (other !== section) other.open = false;
      }
    });
  }

  function closeMenu() {
    navigation.querySelector("details[open]")?.removeAttribute("open");
  }

  document.addEventListener("pointerdown", (event) => {
    if (!navigation.contains(event.target)) closeMenu();
  });
  navigation.addEventListener("focusout", (event) => {
    if (!navigation.contains(event.relatedTarget)) closeMenu();
  });
  navigation.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });
  navigation.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const open = navigation.querySelector("details[open]");
    if (!open) return;

    event.preventDefault();
    open.open = false;
    open.querySelector("summary").focus();
  });
})();
