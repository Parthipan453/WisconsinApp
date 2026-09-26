
(() => {
    'use strict';

    function handleBrokenImages() {
        document.querySelectorAll('.tv-banner__img, .tv-logo').forEach(img => {
            if (img.tagName !== 'IMG') return;
            img.addEventListener('error', () => {
                img.style.display = 'none';
            }, { once: true });
        });
    }

    function init() {
        handleBrokenImages();

        if (window.lucide) {
            lucide.createIcons();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();