document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.querySelector(".navbar-menu__toggle");
  var list = document.getElementById("navbarMenuList");
  if (!toggle || !list) return;
  toggle.addEventListener("click", function () {
    var isOpen = list.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });
});

