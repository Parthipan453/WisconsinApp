document.addEventListener("DOMContentLoaded", function () {
    const root = document.querySelector(".ppv");
    if (!root) return;

    const historyContainer = document.getElementById("ppvHistoryContainer");
    const historyUrl = root.dataset.historyUrl;

    function loadPage(page) {
        fetch(`${historyUrl}?page=${page}`, {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
            .then((res) => res.json())
            .then((data) => {
                historyContainer.innerHTML = data.html;
                if (window.lucide) lucide.createIcons();
                historyContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
            })
            .catch((err) => console.error("Failed to load visit history:", err));
    }

    historyContainer.addEventListener("click", function (e) {
        const btn = e.target.closest(".ppv__page-btn");
        if (!btn || btn.disabled) return;
        loadPage(btn.dataset.page);
    });
});