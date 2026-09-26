// kali code — firearm_view.html behaviour

(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", init);

    function init() {
        refreshIcons();
        wireScrollReveal();
        wireGunTilt();
    }

    function refreshIcons() {
        if (window.lucide) lucide.createIcons();
    }

 
    function wireScrollReveal() {
        const cards = document.querySelectorAll(".fv-firearm-card");
        if (!cards.length || !("IntersectionObserver" in window)) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.style.animationPlayState = "running";
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15 }
        );

        cards.forEach((card) => observer.observe(card));
    }

    
    function wireGunTilt() {
        const stage = document.querySelector(".fv-gun-stage");
        const hero = document.querySelector(".fv-hero");
        if (!stage || !hero || window.matchMedia("(pointer: coarse)").matches) return;

        hero.addEventListener("mousemove", (e) => {
            const rect = hero.getBoundingClientRect();
            const relX = (e.clientX - rect.left) / rect.width - 0.5;
            const relY = (e.clientY - rect.top) / rect.height - 0.5;
            stage.style.transform = `rotate3d(${-relY}, ${relX}, 0, 6deg)`;
        });

        hero.addEventListener("mouseleave", () => {
            stage.style.transform = "";
        });
    }
})();