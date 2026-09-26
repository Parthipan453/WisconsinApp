// Navina Code
/* ==========================================================
   LIBRARY DASHBOARD TOAST
========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    const container = document.getElementById("library-toast-container");

    if (!container) return;

    // ----------------------------------------
    // Django Messages
    // ----------------------------------------

    document.querySelectorAll(".django-toast").forEach((item) => {

        const type = item.dataset.type || "info";
        const message = item.dataset.message;

        let title = "";

        switch (type) {

            case "success":
                title = "Success";
                break;

            case "error":
                title = "Error";
                break;

            case "warning":
                title = "Warning";
                break;

            case "info":
                title = "Information";
                break;

            default:
                title = "Notice";
        }

        showToast(type, title, message);

    });

});


/* ==========================================================
   SHOW TOAST
========================================================== */

function showToast(type, title, message) {

    const container = document.getElementById("library-toast-container");

    const icons = {

        success: "✓",
        error: "✕",
        warning: "⚠",
        info: "i",
        notice: "🔔"

    };

    const toast = document.createElement("div");

    toast.className = `library-toast ${type}`;

    toast.innerHTML = `
<div class="toast-icon">
    ${icons[type]}
</div>

<div class="toast-body">

    <div class="toast-title">${title}</div>

    <div class="toast-message">${message}</div>

    <div class="toast-time">Just now</div>

</div>

<button type="button" class="toast-close">
    ✕
</button>

<div class="toast-progress">
    <span></span>
</div>
`;

    container.appendChild(toast);

    // ------------------------------------
    // Auto Remove
    // ------------------------------------

    const timer = setTimeout(() => {

        removeToast(toast);

    }, 4000);

    // ------------------------------------
    // Close Button
    // ------------------------------------

    toast.querySelector(".toast-close").onclick = () => {

        clearTimeout(timer);

        removeToast(toast);

    };

}


/* ==========================================================
   REMOVE TOAST
========================================================== */

function removeToast(toast) {

    toast.style.transition = ".35s";

    toast.style.opacity = "0";

    toast.style.transform = "translateX(100%)";

    setTimeout(() => {

        toast.remove();

    }, 350);

}