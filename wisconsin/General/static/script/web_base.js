(function () {
    'use strict';

    const toggle     = document.getElementById('uwMobileToggle');
    const mobileMenu = document.getElementById('uwMobileMenu');
    const navbarCard = document.getElementById('uwNavbarCard');
    const icon       = document.getElementById('uwToggleIcon');

    if (!toggle || !mobileMenu || !navbarCard || !icon) return;

    function openMenu() {
        mobileMenu.classList.add('open');
        navbarCard.classList.add('mobile-open');
        toggle.setAttribute('aria-expanded', 'true');
        icon.className = 'fa-solid fa-xmark';
    }

    function closeMenu() {
        mobileMenu.classList.remove('open');
        navbarCard.classList.remove('mobile-open');
        toggle.setAttribute('aria-expanded', 'false');
        icon.className = 'fa-solid fa-bars';
    }

    function syncTopNavOnLoad() {
        const activeEl = document.querySelector('.uw-nav .top-nav-link.active[data-nav-key]');
        if (!activeEl) return;
        const key = activeEl.dataset.navKey;
        document.querySelectorAll('.uw-mobile-top-links a[data-nav-key]').forEach(function (el) {
            el.classList.toggle('active', el.dataset.navKey === key);
        });
    }

    function syncMainNavOnLoad() {
        const activeEl = document.querySelector('.uw-main-nav .nav-link.active[data-main-nav-key]');
        if (!activeEl) return;
        const key = activeEl.dataset.mainNavKey;
        document.querySelectorAll('.uw-mobile-main-links a[data-main-nav-key]').forEach(function (el) {
            el.classList.toggle('active', el.dataset.mainNavKey === key);
        });
    }

    syncTopNavOnLoad();
    syncMainNavOnLoad();

    toggle.addEventListener('click', function (e) {
        e.stopPropagation();
        mobileMenu.classList.contains('open') ? closeMenu() : openMenu();
    });

    mobileMenu.querySelectorAll('.uw-mobile-main-links a').forEach(function (link) {
        link.addEventListener('click', closeMenu);
    });

    document.addEventListener('click', function (e) {
        if (!navbarCard.contains(e.target)) closeMenu();
    });

    window.addEventListener('resize', function () {
        if (window.innerWidth > 768) closeMenu();
    });
})();
