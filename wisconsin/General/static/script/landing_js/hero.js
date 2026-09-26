
(function () {
    'use strict';

    const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    ).matches;

    
    function initFadeIn() {
        const tagline = document.querySelector('.hero-tagline');
        const ctaBar  = document.querySelector('.hero-cta-bar');

        if (!tagline || !ctaBar) return;

        if (prefersReducedMotion) {
            [tagline, ctaBar].forEach(el => (el.style.opacity = '1'));
            return;
        }

      
        [tagline, ctaBar].forEach(el => {
            el.style.opacity  = '0';
            el.style.transform = 'translateY(18px)';
            el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
        });

        
        requestAnimationFrame(() => {
            setTimeout(() => {
                tagline.style.opacity   = '1';
                tagline.style.transform = 'translateY(0)';
            }, 150);

            setTimeout(() => {
                ctaBar.style.opacity   = '1';
                ctaBar.style.transform = 'translateY(0)';
            }, 350);
        });
    }

   


    
    function initTrendingReveal() {
        if (prefersReducedMotion) return;

        const targets = document.querySelectorAll(
            '.trending-featured, .trending-card, .trending-footer-bar, .research-content, .purpose-col-text, .purpose-col-img'
        );
        if (!targets.length) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity   = '1';
                        entry.target.style.transform = 'translateY(0)';
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12 }
        );

        targets.forEach((el, i) => {
            el.style.opacity    = '0';
            el.style.transform  = 'translateY(20px)';
            el.style.transition = `opacity 0.55s ease ${i * 0.07}s, transform 0.55s ease ${i * 0.07}s`;
            observer.observe(el);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initFadeIn();
        initTrendingReveal();
    });
})();