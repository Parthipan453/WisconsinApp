// /* kali's  code  */

(() => {
    'use strict';

    const sidebar       = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const backdrop      = document.getElementById('sidebarBackdrop');
    const mainWrapper   = document.getElementById('mainWrapper');
    const body          = document.body;

    const MOBILE_BREAK  = 992;   
    const COLLAPSED_KEY = 'uw_sidebar_collapsed';

    function initIcons() {
        if (window.lucide) lucide.createIcons();
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initIcons);
    } else {
        initIcons();
    }

    const isMobile = () => window.innerWidth < MOBILE_BREAK;

    function setAriaExpanded(btn, value) {
        btn.setAttribute('aria-expanded', String(value));
    }

    function openMobileSidebar() {
        sidebar.classList.add('open');
        backdrop.classList.add('visible');
        body.classList.add('sidebar-open');
        setAriaExpanded(sidebarToggle, true);
        backdrop.removeAttribute('aria-hidden');
    }

    function closeMobileSidebar() {
        sidebar.classList.remove('open');
        backdrop.classList.remove('visible');
        body.classList.remove('sidebar-open');
        setAriaExpanded(sidebarToggle, false);
        backdrop.setAttribute('aria-hidden', 'true');
    }

    function isCollapsed() {
        return localStorage.getItem(COLLAPSED_KEY) === '1';
    }

    function applyDesktopState() {
        if (isCollapsed()) {
            body.classList.add('sidebar-collapsed');
        } else {
            body.classList.remove('sidebar-collapsed');
        }
    }

    function toggleDesktopCollapse() {
        const nowCollapsed = !isCollapsed();
        localStorage.setItem(COLLAPSED_KEY, nowCollapsed ? '1' : '0');
        applyDesktopState();
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            if (isMobile()) {
                sidebar.classList.contains('open')
                    ? closeMobileSidebar()
                    : openMobileSidebar();
            } else {
                toggleDesktopCollapse();
            }
        });
    }

    
    if (backdrop) {
        backdrop.addEventListener('click', closeMobileSidebar);
    }

   
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && isMobile()) closeMobileSidebar();
    });

    
    window.addEventListener('resize', () => {
        if (!isMobile()) {
            closeMobileSidebar();  
            applyDesktopState();
        }
    });


    if (!isMobile()) {
        applyDesktopState();
    }

    const groupToggles = document.querySelectorAll('.sidebar__group-toggle');

    groupToggles.forEach(toggle => {
        const submenuId = toggle.getAttribute('aria-controls');
        const submenu   = submenuId ? document.getElementById(submenuId) : null;
        if (!submenu) return;

        toggle.addEventListener('click', () => {
            if (!isMobile() && isCollapsed()) {
                toggleDesktopCollapse();
                return;
            }

            const expanded = toggle.getAttribute('aria-expanded') === 'true';

            groupToggles.forEach(other => {
                if (other !== toggle) {
                    const otherId  = other.getAttribute('aria-controls');
                    const otherSub = otherId ? document.getElementById(otherId) : null;
                    if (otherSub) {
                        otherSub.classList.remove('open');
                        setAriaExpanded(other, false);
                    }
                }
            });

            submenu.classList.toggle('open', !expanded);
            setAriaExpanded(toggle, !expanded);
        });
    });

    /*  ACTIVE LINK DETECTION
     */
    function markActiveLinks() {
        const currentPath = window.location.pathname;

        document.querySelectorAll('.sidebar__item--single').forEach(link => {
            const href = link.getAttribute('href');
            if (href && href !== '#' && currentPath === href) {
                link.classList.add('active');
            }
        });

        document.querySelectorAll('.sidebar__subitem').forEach(link => {
            const href = link.getAttribute('href');
            if (href && href !== '#' && currentPath.startsWith(href) && href !== '/') {
                link.classList.add('active');

                const submenu = link.closest('.sidebar__submenu');
                if (submenu) {
                    submenu.classList.add('open');
                    const parentId = submenu.id;
                    const parentToggle = document.querySelector(`[aria-controls="${parentId}"]`);
                    if (parentToggle) setAriaExpanded(parentToggle, true);
                }
            }
        });
    }

    markActiveLinks();

    /* 
     SEARCH KEYBOARD SHORTCUT  */
    document.addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.navbar__search-input');
            if (searchInput) searchInput.focus();
        }
    });

    sidebar.querySelectorAll('.sidebar__subitem, .sidebar__item--single').forEach(link => {
        link.addEventListener('click', () => {
            if (isMobile()) closeMobileSidebar();
        });
    });

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function addRipple(el) {
        if (prefersReducedMotion) return;
        el.style.position = 'relative';
        el.style.overflow = 'hidden';

        el.addEventListener('click', function(e) {
            const rect   = el.getBoundingClientRect();
            const size   = Math.max(rect.width, rect.height);
            const x      = e.clientX - rect.left - size / 2;
            const y      = e.clientY - rect.top  - size / 2;

            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top:  ${y}px;
                background: rgba(197, 5, 11, 0.73);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple-expand 0.5s ease-out forwards;
                pointer-events: none;
            `;
            el.appendChild(ripple);
            ripple.addEventListener('animationend', () => ripple.remove());
        });
    }

    if (!prefersReducedMotion) {
        const styleEl = document.createElement('style');
        styleEl.textContent = `
            @keyframes ripple-expand {
                to { transform: scale(2.5); opacity: 0; }
            }
        `;
        document.head.appendChild(styleEl);
    }

    sidebar.querySelectorAll(
        '.sidebar__group-toggle, .sidebar__item--single, .sidebar__logout, .sidebar__subitem'
    ).forEach(addRipple);


    window.updateBadge = function(type, count) {
        const btn = document.querySelector(`.navbar__action-btn[aria-label="${type}"]`);
        if (!btn) return;
        let badge = btn.querySelector('.navbar__badge');
        if (count <= 0) {
            if (badge) badge.remove();
            return;
        }
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'navbar__badge';
            btn.appendChild(badge);
        }
        badge.textContent = count > 99 ? '99+' : count;
    };

    // Dominic Code Start's
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
    // Dominic Code End's
    

})();