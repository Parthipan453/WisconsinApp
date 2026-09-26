
function toggleProfileMenu() {
    document.getElementById("profileMenu").classList.toggle("show");
}

document.addEventListener("click", function (event) {
    const dropdown = document.querySelector(".user-dropdown");

    if (dropdown && !dropdown.contains(event.target)) {
        document.getElementById("profileMenu").classList.remove("show");
    }
});

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

       
        document.querySelectorAll(".nav-section-wrap.open").forEach((wrap) => {
            wrap.classList.remove("open");
        });

        document.querySelectorAll(".nav-section-wrap.flyout-open").forEach((wrap) => {
            wrap.classList.remove("flyout-open");
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

    
    const isOpen = wrap.classList.contains("open");

    
    document.querySelectorAll(".nav-section-wrap.open").forEach((w) => {
        w.classList.remove("open");
    });

    
    if (!isOpen) {
        wrap.classList.add("open");
    }
}


document.addEventListener("click", function (event) {
    if (!sidebar.contains(event.target)) {
        document.querySelectorAll(".nav-section-wrap.flyout-open").forEach((wrap) => {
            wrap.classList.remove("flyout-open");
        });
    }
});