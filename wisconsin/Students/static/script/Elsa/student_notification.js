(function () {
    const socket = new WebSocket(
        (window.location.protocol === "https:" ? "wss://" : "ws://")
        + window.location.host + "/ws/notifications/"
    );

    socket.onmessage = function (e) {
        const payload = JSON.parse(e.data);

        if (payload.type === "broadcast" && payload.event === "research_opportunity_published") {
            if (typeof checkForNewNotifications === "function") {
                checkForNewNotifications();
            }
            window.dispatchEvent(new CustomEvent("researchOpportunityPublished", { detail: payload.data }));
        }

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