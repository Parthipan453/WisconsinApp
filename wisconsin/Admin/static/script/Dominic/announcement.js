(function () {
    'use strict';

    function getCsrfToken() {
        const el = document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

    function initToggleButtons() {
    document.querySelectorAll('.announce-toggle-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const url = btn.getAttribute('data-url');
            if (!url) return;

            btn.disabled = true;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    if (!data.success) {
                        if (typeof window.showToast === 'function') {
                            window.showToast('error', data.message || 'Could not update announcement.');
                        }
                        return;
                    }

                    const card = btn.closest('.announce-card');
                    const statusEl = card ? card.querySelector('.announce-status') : null;
                    const iconName = data.is_active ? 'toggle-right' : 'toggle-left';

                    const oldIcon = btn.querySelector('svg, i');
                    const freshIcon = document.createElement('i');
                    freshIcon.setAttribute('data-lucide', iconName);
                    freshIcon.classList.add('announce-icon-pop');

                    if (oldIcon) {
                        oldIcon.replaceWith(freshIcon);
                    } else {
                        btn.appendChild(freshIcon);
                    }

                    btn.setAttribute('title', data.is_active ? 'Disable' : 'Enable');
                    btn.setAttribute('aria-label', (data.is_active ? 'Disable' : 'Enable') + ' announcement');

                    if (statusEl) {
                        statusEl.className = 'announce-status announce-status-' + data.status + ' announce-status-pop';
                        statusEl.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                    }

                    if (window.lucide) window.lucide.createIcons();

                    const statusText = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                    if (typeof window.showToast === 'function') {
                        window.showToast('success', 'Announcement ' + statusText.toLowerCase() + ' successfully!');
                    }
                })
                .catch(function (error) {
                    console.error('Toggle error:', error);
                    if (typeof window.showToast === 'function') {
                        window.showToast('error', 'Could not update announcement. Try again.');
                    }
                })
                .finally(function () {
                    btn.disabled = false;
                });
        });
    });
}

    function initDeleteConfirm() {
        document.querySelectorAll('.announce-delete-form').forEach(function (form) {
            form.addEventListener('submit', function (e) {
                const btn = form.querySelector('[data-confirm]');
                const msg = btn ? btn.getAttribute('data-confirm') : 'Are you sure?';
                if (!window.confirm(msg)) {
                    e.preventDefault();
                }
            });
        });
    }

    function initAnnouncementModal() {
        const modal = document.querySelector('[data-announce-modal]');
        if (!modal) {
            console.warn('[announce] modal element [data-announce-modal] not found in DOM');
            return;
        }

        const titleEl    = modal.querySelector('[data-modal-title]');
        const messageEl  = modal.querySelector('[data-modal-message]');
        const dateEl     = modal.querySelector('[data-modal-date]');
        const timeEl     = modal.querySelector('[data-modal-time]');
        const priorityEl = modal.querySelector('[data-modal-priority]');
        let lastFocused = null;

        function open(data) {
            lastFocused = document.activeElement;
            if (titleEl)   titleEl.textContent   = data.title   || '';
            if (messageEl) messageEl.textContent = data.message || '';
            if (dateEl)    dateEl.textContent    = data.date    || '—';
            if (timeEl)    timeEl.textContent    = data.time    || '—';
            if (priorityEl) {
                priorityEl.textContent = data.priority || 'Announcement';
                priorityEl.setAttribute('data-priority-level', (data.priorityLevel || 'info').toLowerCase());
            }
            modal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
            const closer = modal.querySelector('.announce-modal-close');
            if (closer) closer.focus();
            try { if (window.lucide) window.lucide.createIcons(); } catch (e) { console.warn('lucide icon error', e); }
        }

        function close() {
            modal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
            if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus();
        }

        modal.addEventListener('click', function (e) {
            if (e.target.closest('[data-announce-close]')) close();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && modal.getAttribute('aria-hidden') === 'false') close();
        });

        window.AnnounceModal = { open: open, close: close };
    }

    function initAnnouncementTicker() {
        document.addEventListener('click', function (e) {
            const item = e.target.closest('[data-ticker-item]');
            if (!item) return;

            if (!window.AnnounceModal) {
                console.warn('[announce] AnnounceModal not initialized — check that [data-announce-modal] partial is included on this page');
                return;
            }

            window.AnnounceModal.open({
                title:    item.getAttribute('data-title'),
                message:  item.getAttribute('data-message'),
                date:     item.getAttribute('data-date'),
                time:     item.getAttribute('data-time'),
                priority: item.getAttribute('data-priority'),
                priorityLevel: (item.className.match(/announce-ticker-(info|warning|urgent)/) || [])[1] || 'info',
            });
        });
    }

    function initFixedReparenting() {
        const ticker = document.querySelector('[data-ticker]');
        const modal = document.querySelector('[data-announce-modal]');
        if (ticker && ticker.parentElement !== document.body) {
            document.body.appendChild(ticker);
        }
        if (modal && modal.parentElement !== document.body) {
            document.body.appendChild(modal);
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        initToggleButtons();
        initDeleteConfirm();

        function setupAnnounceWidgets() {
            const ready = document.querySelector('[data-ticker]') || document.querySelector('[data-announce-modal]');
            if (ready) {
                initFixedReparenting();
                initAnnouncementModal();
                initAnnouncementTicker();
                if (window.lucide) window.lucide.createIcons();
                return true;
            }
            return false;
        }

        if (!setupAnnounceWidgets()) {
            const observer = new MutationObserver(function () {
                if (setupAnnounceWidgets()) observer.disconnect();
            });
            observer.observe(document.body, { childList: true, subtree: true });

            setTimeout(function () { observer.disconnect(); }, 8000);
        }

        if (window.lucide) window.lucide.createIcons();
    });
})();