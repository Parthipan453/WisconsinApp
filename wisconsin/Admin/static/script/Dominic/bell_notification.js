(function () {
    const LIST_URL = document.body.dataset.notifListUrl;
    const READ_URL = document.body.dataset.notifReadUrl;
    const VIEW_URL = document.body.dataset.notifViewUrl;
    const POLL_INTERVAL = 15000;

    if (!LIST_URL) return;

    const badge = document.getElementById('notifBadge');
    const dropdown = document.getElementById('notifDropdown');
    const list = document.getElementById('notifList');
    const toggle = document.getElementById('notifToggle');
    const sound = document.getElementById('notifSound');
        const ICON_MAP = {
        new: 'megaphone',
        tournament_applied: 'trophy',
    };

    let lastUnreadCount = 0;
    let firstLoad = true;
    let isRemoving = false;
    let knownIds = new Set();


    async function requestBrowserNotificationPermission() {
    if (!('Notification' in window)) {
        console.warn('This browser does not support desktop notifications.');
        return;
    }

    if (Notification.permission === 'default') {
        try {
            const permission = await Notification.requestPermission();
            console.log('Browser notification permission:', permission);
        } catch (error) {
            console.warn('Notification permission request failed:', error);
        }
    }
}





function showDesktopNotification(notification) {

    console.log('showDesktopNotification() called');

    if (!('Notification' in window)) {

        console.warn(
            'Browser does not support desktop notifications.'
        );

        return;
    }

    console.log(
        'Notification permission:',
        Notification.permission
    );

    if (Notification.permission !== 'granted') {

        console.warn(
            'Desktop notification permission is not granted.'
        );

        return;
    }



    let title = 'University Notification';

    if (notification.event === 'tournament_applied') {
        title = 'Tournament Invitation';
    }

    if (notification.event === 'new') {
        title = 'New Notification';
    }

 

    const desktopNotification = new Notification(
        title,
        {
            body: notification.message,

            icon: '/static/images/favicon.png',

            tag: `notification-${notification.id}`,

            renotify: true
        }
    );



    desktopNotification.onclick = function () {

        window.focus();

        desktopNotification.close();

        const historyUrl =
            document.getElementById(
                'notifToggle'
            )?.dataset.historyUrl;

        if (historyUrl) {
            window.location.href = historyUrl;
        }
    };

    // -----------------------------------------------------
    // Auto close
    // -----------------------------------------------------

    setTimeout(() => {
        desktopNotification.close();
    }, 6000);
}

    async function fetchNotifications() {
        if (isRemoving) return;
        try {
            const res = await fetch(LIST_URL, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
            });
            if (!res.ok) return;

            const data = await res.json();
            if (!data.success) return;

            if (!firstLoad) {
                data.notifications
                    .filter(n => !n.is_read && !knownIds.has(n.id))
                    .forEach(n => showDesktopNotification(n));
            }
            data.notifications.forEach(n => knownIds.add(n.id));

            renderList(data.notifications);
            updateBadge(data.unread_count);
        } catch (e) {
            console.error('Notification fetch failed:', e);
        }
    }

    const TYPE_ICON = {
        INFO: 'info-circle',
        SUCCESS: 'circle-check',
        WARNING: 'alert-triangle',
        ERROR: 'circle-x',
        REQUEST: 'clipboard-check',
        SYSTEM: 'settings',
    };

    function itemIcon(n) {
        if (n.type && TYPE_ICON[n.type]) return TYPE_ICON[n.type];
        if (n.event === 'new') return 'megaphone';
        return 'clock-alert';
    }

    function renderList(notifications) {
        list.innerHTML = '';
        if (!notifications.length) {
            list.innerHTML = '<li class="notif__item">No notifications yet</li>';
        } else {
            notifications.forEach(n => {
                const li = document.createElement('li');
                li.className = `notif__item ${n.is_read ? '' : 'unread'}`;
                li.dataset.id = n.id;
                li.innerHTML = `
                    <div class="notif__icon">
                        <i data-lucide="${itemIcon(n)}"></i>
                    </div>
                    <div class="notif__item-body">
                        <span class="notif__item-msg">${escapeHTML(n.title || n.message || 'Notification')}</span>
                        ${n.message && n.title ? `<span class="notif__item-msg-sub">${escapeHTML(n.message)}</span>` : ''}
                        <span class="notif__item-time">${n.time_ago || n.created_at || ''}</span>
                    </div>
                `;
                if (n.link) li.addEventListener('click', () => { window.location.href = n.link; });
                list.append(li);
            });
        }
        if (VIEW_URL && !document.getElementById('notifViewAll')) {
            const foot = document.createElement('a');
            foot.id = 'notifViewAll';
            foot.href = VIEW_URL;
            foot.className = 'notif__view-all';
            foot.textContent = 'View all notifications →';
            dropdown.append(foot);
        }
        notifications.forEach(n => {
            const li = document.createElement('li');
            li.className = `notif__item notif__item--${n.event} ${n.is_read ? '' : 'unread'}`;
            li.dataset.id = n.id;
            li.innerHTML = `
                <div class="notif__icon">
                    <i data-lucide="${ICON_MAP[n.event] || 'clock-alert'}"></i>
                </div>
                <div class="notif__item-body">
                    <span class="notif__item-msg">${escapeHTML(n.message)}</span>
                    <span class="notif__item-time">${n.created_at}</span>
                </div>
            `;
            list.append(li);
        });
        if (window.lucide) lucide.createIcons();
    }

   

    function updateBadge(count) {

    if (!firstLoad && count > lastUnreadCount) {
        playSound();
    }

    firstLoad = false;
    lastUnreadCount = count;

    const countLabel = document.getElementById('notifCount');

    if (count > 0) {
        badge.style.display = 'inline-block';
        badge.textContent = count > 9 ? '9+' : count;

        if (countLabel) {
            countLabel.hidden = false;
            countLabel.textContent = `${count} new`;
        }
    } else {
        badge.style.display = 'none';

        if (countLabel) {
            countLabel.hidden = true;
        }
    }
}

    function escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    

    function playSound() {
        if (!sound) {
            console.warn('Notification sound element not found.');
            return;
        }

        sound.currentTime = 0;

        const playPromise = sound.play();

        if (playPromise !== undefined) {
            playPromise
                .then(() => {
                    console.log(' Notification sound played');
                })
                .catch(error => {
                    console.warn('Notification sound blocked:', error);
                });
        }
    }


    async function markAllRead() {
        try {
            await fetch(READ_URL, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
            });
            lastUnreadCount = 0;
            updateBadge(0);
        } catch (e) {
            console.error('Mark read failed:', e);
        }
    }

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? match[2] : '';
    }

    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.hidden = !dropdown.hidden;
        if (!dropdown.hidden) markAllRead();
    });

    document.addEventListener('click', (e) => {
        if (!toggle.contains(e.target)) dropdown.hidden = true;
    });

    document.addEventListener('DOMContentLoaded', () => {
        requestBrowserNotificationPermission();
        fetchNotifications();
        setInterval(fetchNotifications, POLL_INTERVAL);
    });
})();