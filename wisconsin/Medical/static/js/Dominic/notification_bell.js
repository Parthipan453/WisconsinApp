(function () {
    'use strict';

    var config = window.notifConfig || {};
    var bellBtn = document.getElementById('notifBellBtn');
    var bellBadge = document.getElementById('notifBellBadge');
    var dropdown = document.getElementById('notifDropdown');
    var notifSound = document.getElementById('notifSound');
    var seenUnreadIds = null;
    if (!bellBtn || !dropdown || !config.listUrl) return;

    function playNotifSound() {
        if (!notifSound) return;
        try {
            notifSound.currentTime = 0;
            var p = notifSound.play();
            if (p && typeof p.catch === 'function') {
                p.catch(function () {});
            }
        } catch (e) {}
    }

    function checkForNewUnread(data, suppressDing) {
        var currentUnreadIds = (data.notifications || [])
            .filter(function (n) { return !n.is_read; })
            .map(function (n) { return n.id; });

        if (seenUnreadIds === null) {
            seenUnreadIds = currentUnreadIds.slice();
            return;
        }

        var hasNew = currentUnreadIds.some(function (id) {
            return seenUnreadIds.indexOf(id) === -1;
        });

        seenUnreadIds = currentUnreadIds.slice();

        if (hasNew && !suppressDing) playNotifSound();
    }

    function ensureToastStack() {
        var stack = document.getElementById('medToastStack');
        if (stack) return stack;

        stack = document.createElement('div');
        stack.id = 'medToastStack';
        stack.style.cssText =
            'position:fixed;bottom:20px;right:20px;z-index:99999;' +
            'display:flex;flex-direction:column-reverse;gap:12px;' +
            'width:360px;max-width:calc(100vw - 40px);pointer-events:none;';
        document.body.appendChild(stack);
        return stack;
    }

    function showInAppToast(data) {
        var stack = ensureToastStack();

        var toast = document.createElement('a');
        toast.href = data.url || '#';
        toast.style.cssText =
            'position:relative;display:flex;gap:12px;align-items:flex-start;' +
            'background:#111827;border-radius:14px;' +
            'box-shadow:0 12px 32px rgba(0,0,0,0.28);' +
            'padding:14px 16px;text-decoration:none;color:inherit;' +
            'pointer-events:auto;opacity:0;transform:translateY(16px) scale(0.98);' +
            'transition:opacity .2s ease,transform .2s ease;font-family:inherit;' +
            'cursor:pointer;overflow:hidden;';

        var accent = document.createElement('span');
        accent.style.cssText =
            'position:absolute;left:0;top:0;bottom:0;width:4px;' +
            'background:linear-gradient(180deg,#ff5a5f,#c5050c);';
        toast.appendChild(accent);

        var iconBadge = document.createElement('span');
        iconBadge.style.cssText =
            'flex-shrink:0;width:36px;height:36px;border-radius:10px;' +
            'background:rgba(197,5,12,0.18);display:flex;align-items:center;' +
            'justify-content:center;margin-left:4px;overflow:hidden;';
        var iconImg = document.createElement('img');
        iconImg.src = data.icon || '/static/images/logo.png';
        iconImg.style.cssText = 'width:20px;height:20px;object-fit:contain;border-radius:4px;';
        iconImg.onerror = function () { iconBadge.style.background = 'rgba(197,5,12,0.18)'; iconImg.remove(); };
        iconBadge.appendChild(iconImg);
        toast.appendChild(iconBadge);

        var body = document.createElement('div');
        body.style.cssText = 'flex:1;min-width:0;padding-right:18px;';

        var titleRow = document.createElement('div');
        titleRow.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:3px;';
        var dot = document.createElement('span');
        dot.style.cssText = 'width:7px;height:7px;border-radius:50%;background:#ff5a5f;flex-shrink:0;';
        var titleText = document.createElement('span');
        titleText.style.cssText = 'font-weight:600;font-size:14px;color:#f9fafb;letter-spacing:.1px;';
        titleText.textContent = data.title || 'Notification';
        titleRow.appendChild(dot);
        titleRow.appendChild(titleText);

        var bodyText = document.createElement('div');
        bodyText.style.cssText = 'font-size:13px;color:#d1d5db;line-height:1.4;';
        bodyText.textContent = data.body || '';

        body.appendChild(titleRow);
        body.appendChild(bodyText);
        toast.appendChild(body);

        var closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.setAttribute('aria-label', 'Dismiss notification');
        closeBtn.textContent = '\u00D7';
        closeBtn.style.cssText =
            'position:absolute;top:8px;right:8px;border:none;background:transparent;' +
            'font-size:18px;line-height:1;color:#9ca3af;cursor:pointer;' +
            'width:22px;height:22px;border-radius:6px;flex-shrink:0;';
        closeBtn.addEventListener('mouseenter', function () { closeBtn.style.background = 'rgba(255,255,255,0.08)'; closeBtn.style.color = '#f3f4f6'; });
        closeBtn.addEventListener('mouseleave', function () { closeBtn.style.background = 'transparent'; closeBtn.style.color = '#9ca3af'; });
        closeBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            removeToast();
        });
        toast.appendChild(closeBtn);

        toast.addEventListener('click', function () {
            if (data.id) markRead(data.id);
        });

        stack.appendChild(toast);
        requestAnimationFrame(function () {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0) scale(1)';
        });

        function removeToast() {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(16px) scale(0.98)';
            setTimeout(function () {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 200);
        }
    }

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('message', function (event) {
            var msg = event.data;
            if (!msg || msg.type !== 'medical-push-notification') return;

            showInAppToast(msg);
            playNotifSound();
            fetchList(true);
        });
    }

    function getCsrfToken() {
        var el = document.querySelector('#noteCsrfForm [name=csrfmiddlewaretoken]') ||
                 document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

    function timeAgo(isoString) {
        var diffMs = Date.now() - new Date(isoString).getTime();
        var mins = Math.floor(diffMs / 60000);
        if (mins < 1) return 'just now';
        if (mins < 60) return mins + 'm ago';
        var hours = Math.floor(mins / 60);
        if (hours < 24) return hours + 'h ago';
        return Math.floor(hours / 24) + 'd ago';
    }

    function renderList(data, suppressDing) {
        checkForNewUnread(data, suppressDing);

        dropdown.innerHTML = '';

        var header = document.createElement('div');
        header.className = 'notif-dropdown__header';
        header.innerHTML = '<span>Notifications</span>';
        if (data.unread_count > 0) {
            var markAllBtn = document.createElement('button');
            markAllBtn.type = 'button';
            markAllBtn.className = 'notif-dropdown__mark-all';
            markAllBtn.textContent = 'Mark all read';
            markAllBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                markRead('all');
            });
            header.appendChild(markAllBtn);
        }
        dropdown.appendChild(header);

        var list = document.createElement('div');
        list.className = 'notif-dropdown__list';

        if (!data.notifications || data.notifications.length === 0) {
            var empty = document.createElement('div');
            empty.className = 'notif-dropdown__empty';
            empty.textContent = 'No notifications yet.';
            list.appendChild(empty);
        } else {
            data.notifications.forEach(function (n) {
                var item = document.createElement('a');
                item.href = n.link_url || '#';
                item.className = 'notif-dropdown__item' + (n.is_read ? '' : ' is-unread');
                item.innerHTML =
                    '<span class="notif-dropdown__icon"><i data-lucide="' + (n.icon || 'bell') + '"></i></span>' +
                    '<span class="notif-dropdown__body">' +
                    '<span class="notif-dropdown__msg"></span>' +
                    '<span class="notif-dropdown__time">' + timeAgo(n.created_at) + '</span>' +
                    '</span>';
                item.querySelector('.notif-dropdown__msg').textContent = n.message;

                item.addEventListener('click', function () {
                    if (!n.is_read) markRead(n.id);
                });
                list.appendChild(item);
            });
        }
        dropdown.appendChild(list);

        if (window.lucide && typeof window.lucide.createIcons === 'function') {
            window.lucide.createIcons();
        }

        updateBadge(data.unread_count);
    }

    function updateBadge(count) {
        if (!bellBadge) return;
        if (count > 0) {
            bellBadge.textContent = count > 9 ? '9+' : String(count);
            bellBadge.hidden = false;
        } else {
            bellBadge.hidden = true;
        }
    }

    function fetchList(suppressDing) {
        fetch(config.listUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.json(); })
            .then(function (data) { renderList(data, suppressDing); })
            .catch(function () {});
    }

    function markRead(idOrAll) {
        var url = config.markReadUrlTemplate.replace('__ID__', idOrAll);
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
            .then(function () { fetchList(); })
            .catch(function () {});
    }

    var isOpen = false;
    function toggleDropdown() {
        isOpen = !isOpen;
        dropdown.hidden = !isOpen;
        bellBtn.setAttribute('aria-expanded', String(isOpen));
        if (isOpen) fetchList();
    }

    bellBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleDropdown();
    });

    document.addEventListener('click', function (e) {
        if (isOpen && !dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
            isOpen = false;
            dropdown.hidden = true;
            bellBtn.setAttribute('aria-expanded', 'false');
        }
    });

    window.refreshNotifBell = function () {
        fetchList();
    };

    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) fetchList();
    });

    fetchList();
    setInterval(fetchList, 60000);
})();