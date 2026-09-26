(function () {
    'use strict';

    var config = window.pushConfig || {};
    if (!config.vapidPublicKey || !config.subscribeUrl) return;
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.warn('Push notifications not supported in this browser.');
        return;
    }

    function urlBase64ToUint8Array(base64String) {
        var padding = '='.repeat((4 - (base64String.length % 4)) % 4);
        var base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        var rawData = window.atob(base64);
        var outputArray = new Uint8Array(rawData.length);
        for (var i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    function getCsrfToken() {
        var el = document.querySelector('#noteCsrfForm [name=csrfmiddlewaretoken]') ||
                 document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

    function arrayBufferToBase64Url(buffer) {
        var bytes = new Uint8Array(buffer);
        var binary = '';
        for (var i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
        return window.btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    function saveSubscription(subscription) {
        return fetch(config.subscribeUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(subscription.toJSON()),
        });
    }

    function createFreshSubscription(registration) {
        return registration.pushManager
            .subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(config.vapidPublicKey),
            })
            .then(saveSubscription)
            .catch(function (err) {
                console.warn('Push subscription failed:', err);
            });
    }

    function subscribeUser(registration) {
        return registration.pushManager.getSubscription().then(function (existing) {
            if (!existing) return createFreshSubscription(registration);

            var existingKey = existing.options && existing.options.applicationServerKey
                ? arrayBufferToBase64Url(existing.options.applicationServerKey)
                : null;
            var currentKey = (config.vapidPublicKey || '').replace(/=+$/, '');

            if (existingKey === currentKey) {
                return saveSubscription(existing);
            }

            return existing.unsubscribe().then(function () {
                return createFreshSubscription(registration);
            }).catch(function () {
                return createFreshSubscription(registration);
            });
        });
    }

    function init() {
        if (Notification.permission === 'denied') return;

        navigator.serviceWorker
            .register('/sw.js', { scope: '/' })
            .then(function (registration) {
                if (Notification.permission === 'granted') {
                    subscribeUser(registration);
                    return;
                }
                if (Notification.permission === 'default') {
                    Notification.requestPermission().then(function (permission) {
                        if (permission === 'granted') subscribeUser(registration);
                    });
                }
            })
            .catch(function (err) {
                console.warn('Service worker registration failed:', err);
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();