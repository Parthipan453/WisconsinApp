(function () {
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }

    const socket = new WebSocket(
        (window.location.protocol === "https:" ? "wss://" : "ws://")
        + window.location.host + "/ws/notifications/"
    );

    socket.onmessage = function (e) {
        const payload = JSON.parse(e.data);

        if (payload.type === "admin_alert" && payload.event === "grade_request_created") {
            const d = payload.data;

            showBrowserNotification(d.title, d.message);

            if (typeof window.refreshAdminBell === "function") {
                window.refreshAdminBell();
            }

            if (window.location.pathname.includes("score_request")) {
            if (getCurrentPageNumber() === 1) {
                insertLiveRequestRow(d);
            }
                bumpStat(0, +1); // Total
                bumpStat(1, +1); // Pending
            }
        }
    };

    socket.onclose = function () {
        console.warn("Notifications socket closed.");
    };

    function showBrowserNotification(title, body) {
        if (!("Notification" in window)) {
            console.log(`${title}: ${body}`);
            return;
        }
        if (Notification.permission === "granted") {
            const n = new Notification(title, { body: body, icon: "/static/images/logo.png" });
            n.onclick = () => window.focus();
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then((perm) => {
                if (perm === "granted") {
                    new Notification(title, { body: body, icon: "/static/images/logo.png" });
                }
            });
        }
    }

    function getCurrentPageNumber() {
        const params = new URLSearchParams(window.location.search);
        return parseInt(params.get("page") || "1", 10);
    }

    function bumpStat(index, delta) {
        const headers = document.querySelectorAll(".stat-card .stat-right h3");
        if (headers[index]) {
            headers[index].textContent = (parseInt(headers[index].textContent, 10) || 0) + delta;
        }
    }

    function esc(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : str;
        return div.innerHTML;
    }

    function insertLiveRequestRow(d) {
        const tbody = document.querySelector(".sr-table tbody");
        if (!tbody) return;

        // Remove the "No Requests Found" placeholder row if present
        const emptyRow = tbody.querySelector("td.empty");
        if (emptyRow) emptyRow.closest("tr").remove();

        const tr = document.createElement("tr");
        tr.className = "live-new-row";
        tr.innerHTML = `
            <td>#${esc(d.request_id)}</td>
            <td>${esc(d.faculty_employee_id)}<br>(${esc(d.faculty_name)})</td>
            <td>${esc(d.student_id)}<br>(${esc(d.student_name)})</td>
            <td>${esc(d.course_code)}<br>(${esc(d.course_name)})</td>
            <td>${esc(d.current_score)}</td>
            <td class="highlight">${esc(d.requested_score)}</td>
            <td class="reason">${esc(d.reason)}</td>
            <td><span class="badge pending">Pending</span></td>
            <td class="sr-action-cell">
                <button type="button" class="btn approve" data-approve-url="${d.approve_url}">Approve</button>
                <button type="button" class="btn reject" data-reject-url="${d.reject_url}">Reject</button>
            </td>
        `;
        tbody.insertBefore(tr, tbody.firstChild);

        tr.style.transition = "background-color 1.5s ease";
        tr.style.backgroundColor = "#fff3cd";
        setTimeout(() => { tr.style.backgroundColor = ""; }, 1600);
    }
})();