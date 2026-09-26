(function () {
    'use strict';

    if (window.__apnInit) return;
    window.__apnInit = true;

    var POLL_INTERVAL = 8000;
    var NOTIF_ICON = '/static/images/apply-uw.png';
    var seenIds = {};
    var bells = Array.prototype.slice.call(document.querySelectorAll('.apn-bell'));
    if (!bells.length) return;

    function getCookie(name) {
        var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? match[2] : '';
    }

    function escapeHTML(str) {
        var div = document.createElement('div');
        div.textContent = str == null ? '' : String(str);
        return div.innerHTML;
    }

    function renderList(list, items) {
        list.innerHTML = '';
        if (!items.length) {
            var empty = document.createElement('li');
            empty.className = 'apn-dropdown__empty';
            empty.textContent = 'No notifications yet';
            list.appendChild(empty);
            return;
        }
        items.forEach(function (n) {
            var li = document.createElement('li');
            li.className = 'apn-dropdown__item' + (n.is_read ? '' : ' is-unread');
            var link = document.createElement('a');
            link.href = n.link || 'javascript:void(0)';
            link.dataset.id = n.id;
            link.innerHTML =
                '<span class="apn-dropdown__icon"><i class="fas ' + escapeHTML(n.icon || 'fa-info-circle') + '"></i></span>' +
                '<span class="apn-dropdown__body">' +
                '<span class="apn-dropdown__title">' + escapeHTML(n.title) + '</span>' +
                '<span class="apn-dropdown__msg">' + escapeHTML(n.message) + '</span>' +
                '<span class="apn-dropdown__time">' + escapeHTML(n.time_ago) + '</span>' +
                '</span>';
            var row = document.createElement('div');
            row.className = 'apn-dropdown__row';
            row.appendChild(link);
            var dismiss = document.createElement('button');
            dismiss.type = 'button';
            dismiss.className = 'apn-dropdown__dismiss';
            dismiss.setAttribute('aria-label', 'Dismiss notification');
            dismiss.dataset.id = n.id;
            dismiss.dataset.url = n.delete_url;
            dismiss.innerHTML = '<i class="fas fa-times"></i>';
            row.appendChild(dismiss);
            li.appendChild(row);
            list.appendChild(li);
            link.addEventListener('click', function (e) {
                var id = this.dataset.id;
                if (id) markRead(id, this);
            });
            dismiss.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                deleteNotification(this.dataset.id, this);
            });
        });
    }

    function markRead(id, linkEl) {
        fetch(READ_ALL_URL, { method: 'POST', headers: csrfHeaders() })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (!data.success) return;
                var li = linkEl ? closestLi(linkEl) : null;
                if (li) li.classList.remove('is-unread');
                updateBadge(data.unread_count);
            })
            .catch(function () {});
    }

    function deleteNotification(id, btnEl) {
        fetch(btnEl.dataset.url, {
            method: 'POST',
            headers: csrfHeaders(),
        })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (!data.success) return;
                var li = closestLi(btnEl);
                if (li) {
                    li.parentNode.removeChild(li);
                    refreshEmptyState();
                }
                updateBadge(data.unread_count);
            })
            .catch(function () {});
    }

    function closestLi(el) {
        while (el && el.tagName !== 'LI') el = el.parentNode;
        return el;
    }

    function refreshEmptyState() {
        if (!list.querySelector('.apn-dropdown__item')) {
            var empty = document.createElement('li');
            empty.className = 'apn-dropdown__empty';
            empty.textContent = 'No notifications yet';
            list.appendChild(empty);
        }
    }

    function csrfHeaders() {
        return {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken'),
        };
    }

    bells.forEach(function (bell) {
        var RECENT_URL = bell.dataset.recentUrl;
        var READ_ALL_URL = bell.dataset.readAllUrl;

        var badge = bell.querySelector('.apn-bell__badge');
        var toggle = bell.querySelector('.apn-bell__toggle');
        var dropdown = bell.querySelector('.apn-dropdown');
        var list = bell.querySelector('.apn-dropdown__list');
        var markAll = bell.querySelector('.apn-dropdown__mark-all');
        var lastUnread = -1;

        function updateBadge(count) {
            if (lastUnread >= 0 && count > lastUnread) {
                try {
                    new Audio('/static/sounds/notification_1.mp3').play().catch(function () {});
                } catch (e) {}
                bell.classList.remove('apn-bell--shake');
                void bell.offsetWidth;
                bell.classList.add('apn-bell--shake');
            }
            lastUnread = count;
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.hidden = false;
            } else {
                badge.hidden = true;
                bell.classList.remove('apn-bell--shake');
            }
        }

        function fireBrowserNotifications(data, historyUrl) {
            if (!('Notification' in window)) return;
            if (Notification.permission !== 'granted') return;
            var history = historyUrl || '/applicants/notifications/';
            if (!window.__apnBoot) {
                window.__apnBoot = true;
                (data.notifications || []).forEach(function (n) { seenIds[n.id] = true; });
            }
            (data.notifications || []).forEach(function (n) {
                if (n.is_read || seenIds[n.id]) return;
                seenIds[n.id] = true;
                try {
                    var notif = new Notification(n.title, {
                        body: n.message || (n.time_ago ? 'Received ' + n.time_ago : ''),
                        icon: NOTIF_ICON,
                        tag: 'applicant-notification-' + n.id,
                    });
                    notif.onclick = function () {
                        try { window.focus(); } catch (e) {}
                        window.location.href = n.link || history;
                    };
                } catch (e) {}
            });
        }

        function fetchNotifications() {
            fetch(RECENT_URL, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    if (!data.success) return;
                    renderList(list, data.notifications);
                    updateBadge(data.unread_count);
                    fireBrowserNotifications(data, bell.dataset.historyUrl);
                })
                .catch(function () {});
        }

        function markAllRead() {
            var items = list.querySelectorAll('.apn-dropdown__item.is-unread');
            items.forEach(function (li) { li.classList.remove('is-unread'); });
            fetch(READ_ALL_URL, {
                method: 'POST',
                headers: csrfHeaders(),
            })
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    if (!data.success) return;
                    updateBadge(0);
                    fetchNotifications();
                })
                .catch(function () {});
        }

        if (markAll) {
            markAll.addEventListener('click', function (e) {
                e.stopPropagation();
                e.preventDefault();
                markAllRead();
            });
        }

        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            if ('Notification' in window && Notification.permission === 'default') {
                Notification.requestPermission().catch(function () {});
            }
            bell.classList.remove('apn-bell--shake');
            dropdown.hidden = !dropdown.hidden;
            if (!dropdown.hidden) {
                fetchNotifications();
            }
        });

        setInterval(fetchNotifications, POLL_INTERVAL);
        fetchNotifications();
    });

    document.addEventListener('click', function (e) {
        bells.forEach(function (bell) {
            if (!bell.contains(e.target)) {
                bell.querySelector('.apn-dropdown').hidden = true;
            }
        });
    });

    document.addEventListener('live:swapped', function () {
        bells.forEach(function (bell) {
            bell.querySelector('.apn-dropdown__list').innerHTML = '<li class="apn-dropdown__empty">Loading…</li>';
            fetchRecent(bell);
        });
    });

    function fetchRecent(bell) {
        fetch(bell.dataset.recentUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (!data.success) return;
                renderList(bell.querySelector('.apn-dropdown__list'), data.notifications);
                var badge = bell.querySelector('.apn-bell__badge');
                if (data.unread_count > 0) {
                    badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
                    badge.hidden = false;
                } else {
                    badge.hidden = true;
                }
                fireBrowserNotifications(data, bell.dataset.historyUrl);
            })
            .catch(function () {});
    }
})();