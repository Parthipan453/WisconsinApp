(function () {
    const socket = new WebSocket(
        (window.location.protocol === "https:" ? "wss://" : "ws://")
        + window.location.host + "/ws/notifications/"
    );

    socket.onmessage = function (e) {
        const payload = JSON.parse(e.data);

        if (payload.type === "notification") {
            if (typeof checkForNewNotifications === "function") {
                checkForNewNotifications();
            }
            window.dispatchEvent(new CustomEvent(payload.event, { detail: payload.data }));
        }
    };

    socket.onclose = function () {
        console.warn("Notifications socket closed.");
    };
})();