function toggleProfileMenu() {
    document.getElementById("profileMenu").classList.toggle("show");
}

document.addEventListener("click", function (event) {
    const dropdown = document.querySelector(".user-dropdown");

    if (dropdown && !dropdown.contains(event.target)) {
        document.getElementById("profileMenu").classList.remove("show");
    }
});

// Sidebar
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("sidebarOverlay");

function isMobile() {
    return window.innerWidth <= 768;
}

function toggleSidebar() {

    if (isMobile()) {
        sidebar.classList.toggle("mobile-open");
        overlay.classList.toggle("show");
    } else {
        sidebar.classList.toggle("collapsed");

        document.querySelectorAll(".submenu.open").forEach((sm) => {
            sm.classList.remove("open");
            sm.previousElementSibling.classList.remove("open");
        });

        document.querySelectorAll(".nav-section-wrap.flyout-open").forEach((w) => {
            w.classList.remove("flyout-open");
        });
    }
}

function closeMobileSidebar() {
    sidebar.classList.remove("mobile-open");
    overlay.classList.remove("show");
}

window.addEventListener("resize", () => {
    if (isMobile()) {
        sidebar.classList.remove("collapsed");
    } else {
        sidebar.classList.remove("mobile-open");
        overlay.classList.remove("show");
    }
});

function toggleSection(label) {

    const wrap = label.closest(".nav-section-wrap");
    const submenu = label.nextElementSibling;

    if (sidebar.classList.contains("collapsed") && !isMobile()) {

        const isFlyoutOpen = wrap.classList.contains("flyout-open");

        document.querySelectorAll(".nav-section-wrap.flyout-open").forEach((w) => {
            w.classList.remove("flyout-open");
        });

        if (!isFlyoutOpen) {
            wrap.classList.add("flyout-open");
        }

        return;
    }

    const isOpen = submenu.classList.contains("open");

    document.querySelectorAll(".submenu.open").forEach((sm) => {
        sm.classList.remove("open");
        sm.previousElementSibling.classList.remove("open");
    });

    if (!isOpen) {
        submenu.classList.add("open");
        label.classList.add("open");
    }
}

document.addEventListener("click", function (event) {

    if (!sidebar.contains(event.target)) {

        document.querySelectorAll(".nav-section-wrap.flyout-open").forEach((w) => {
            w.classList.remove("flyout-open");
        });

    }

});

// ============================================================
// KEYBOARD SHORTCUTS
// ============================================================
document.addEventListener("keydown", function (e) {
    // Escape key - close mobile sidebar and profile menu
    if (e.key === "Escape") {
        closeMobileSidebar();
        document.getElementById("profileMenu").classList.remove("show");
    }
});

// ============================================================
// ENSURE FOOTER VISIBILITY AT ALL SIZES
// ============================================================
function ensureFooterVisibility() {
    const footer = document.querySelector(".footer");
    const main = document.querySelector(".main");
    
    if (footer && main) {
        // Footer should always be at bottom
        footer.style.display = "flex";
        footer.style.flexShrink = "0";
    }
}

// Run on load and resize
document.addEventListener("DOMContentLoaded", ensureFooterVisibility);
window.addEventListener("resize", ensureFooterVisibility);

console.log(" Student Base loaded successfully!");