// Dominic Code
self.addEventListener('install', function () {
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', function (event) {
    var data = {};
    try {
        data = event.data ? event.data.json() : {};
    } catch (e) {
        data = { title: 'Notification', body: event.data ? event.data.text() : '' };
    }

    var title = data.title || 'Notification';
    var body = data.body || '';
    var url = data.url || '/';
    var icon = data.icon || '/static/images/logo.png';
    var tag = data.tag || 'medical-notification';
    var notifId = data.id || null;

    function showOsNotification() {
        return self.registration.showNotification(title, {
            body: body,
            icon: icon,
            badge: icon,
            tag: tag,
            data: { url: url },
            requireInteraction: false,
        });
    }

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
            var focusedClient = null;
            for (var i = 0; i < clientList.length; i++) {
                var c = clientList[i];
                if (c.focused) {
                    focusedClient = c;
                    break;
                }
            }

            if (focusedClient) {
                focusedClient.postMessage({
                    type: 'medical-push-notification',
                    id: notifId,
                    title: title,
                    body: body,
                    url: url,
                    icon: icon,
                    tag: tag,
                });
                return;
            }

            return showOsNotification();
        })
    );
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    var targetUrl = (event.notification.data && event.notification.data.url) || '/';

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
            for (var i = 0; i < clientList.length; i++) {
                var client = clientList[i];
                if (client.url.indexOf(targetUrl) !== -1 && 'focus' in client) {
                    return client.focus();
                }
            }
            if (self.clients.openWindow) {
                return self.clients.openWindow(targetUrl);
            }
        })
    );
});