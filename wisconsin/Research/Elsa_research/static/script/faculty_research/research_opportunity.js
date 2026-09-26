function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
// ====== TOGGLE=============================================================================
document.querySelectorAll(".status-toggle").forEach(toggle => {
    toggle.addEventListener("change", function () {
        const checkbox = this;
        const row = checkbox.closest("tr");
        const statusBadge = row.querySelector(".ro-badge");
        const editContainer = row.querySelector(".edit-container");
        fetch(this.dataset.url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.status === "OPEN") {
                    statusBadge.textContent = "Open";
                    statusBadge.className = "ro-badge ro-open";
                    editContainer.innerHTML = `
                        <a href="/your-edit-url/"
                        class="action-btn action-btn-edit">
                            <i class="bi bi-pencil"></i>
                        </a>`;
                } else {
                    statusBadge.textContent = "Closed";
                    statusBadge.className = "ro-badge ro-closed";
                    editContainer.innerHTML = `
                        <span class="action-btn action-btn-edit disabled">
                            <i class="bi bi-pencil"></i>
                        </span>`;
                }
            } else {
                checkbox.checked = !checkbox.checked;
            }
        })
        .catch(() => {
            checkbox.checked = !checkbox.checked;
        });

    });

});