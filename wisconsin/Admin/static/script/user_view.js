// /* kali's code */

(function () {
  "use strict";

  const page = document.querySelector(".uv-page");
  if (!page) return;

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const animatedEls = document.querySelectorAll("[data-animate]");

  if (prefersReducedMotion || !("IntersectionObserver" in window)) {
    animatedEls.forEach(function (el) { el.classList.add("uv-in-view"); });
  } else {
    const revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("uv-in-view");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    );
    animatedEls.forEach(function (el) { revealObserver.observe(el); });
  }

  const gridCards = document.querySelectorAll(".uv-grid > .uv-card[data-animate]");
  if (!prefersReducedMotion && gridCards.length) {
    gridCards.forEach(function (card, i) {
      card.style.transitionDelay = Math.min(i * 40, 320) + "ms";
    });
  }


  const avatarImg = document.getElementById("uv-avatar-img");
  if (avatarImg) {
    avatarImg.addEventListener("error", function () {
      const wrap = avatarImg.closest(".uv-hero__avatar-wrap");
      if (!wrap) return;
      const initial = (page.dataset.userId || "U").toString().charAt(0).toUpperCase();
      avatarImg.remove();
      const fallback = document.createElement("div");
      fallback.className = "uv-hero__avatar uv-hero__avatar--fallback";
      fallback.textContent = initial;
      wrap.prepend(fallback);
    }, { once: true });
  }

 
  const avatarWrap = document.querySelector(".uv-hero__avatar-wrap");
  const canHover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  if (avatarWrap && canHover && !prefersReducedMotion) {
    let rafId = null;

    avatarWrap.addEventListener("mousemove", function (e) {
      if (rafId) return;
      rafId = requestAnimationFrame(function () {
        const rect = avatarWrap.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        avatarWrap.style.transform = "translate(" + (x * 6).toFixed(2) + "px, " + (y * 6).toFixed(2) + "px)";
        rafId = null;
      });
    });

    avatarWrap.addEventListener("mouseleave", function () {
      avatarWrap.style.transform = "";
    });
  }

})();